"""Select weekly words and phrases from calendar_ideas for newsletter."""

from __future__ import annotations

from typing import Any, Dict, Optional
from config.database import db_manager


def get_words_of_the_week(*, week_number: int) -> Dict[str, Any]:
    """Get the weekly word and phrase for a specific week number.
    
    Args:
        week_number: Week number (1-52)
    
    Returns:
        Dict with 'word' and 'phrase' keys, each containing:
        - id, title, description, seasonal_context
        Empty dict if not found
    """
    if week_number < 1 or week_number > 53:
        return {}
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if item_classification column exists
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_ideas' AND column_name = 'item_classification'
                """)
                has_classification = cur.fetchone() is not None
                
                if has_classification:
                    # Get word and phrase using item_classification
                    cur.execute(
                        """
                        SELECT id, idea_title, idea_description, seasonal_context
                        FROM calendar_ideas
                        WHERE week_number = %s
                        AND item_classification IN ('weekly_word', 'weekly_phrase')
                        """,
                        (week_number,)
                    )
                else:
                    # Fallback to content_type if item_classification doesn't exist
                    cur.execute(
                        """
                        SELECT id, idea_title, idea_description, seasonal_context
                        FROM calendar_ideas
                        WHERE week_number = %s
                        AND content_type IN ('weekly_word', 'weekly_phrase')
                        """,
                        (week_number,)
                    )
                
                rows = cur.fetchall() or []
                result = {}
                
                for row in rows:
                    item = dict(row)
                    title = item.get('idea_title', '')
                    
                    # Determine if it's a word or phrase based on title or classification
                    if 'word' in title.lower() or (has_classification and 'word' in str(item.get('item_classification', '')).lower()):
                        result['word'] = {
                            'id': item.get('id'),
                            'title': title.replace('Weekly Word: ', '').replace('Word: ', '').strip(),
                            'description': item.get('idea_description', ''),
                            'seasonal_context': item.get('seasonal_context')
                        }
                    elif 'phrase' in title.lower() or (has_classification and 'phrase' in str(item.get('item_classification', '')).lower()):
                        result['phrase'] = {
                            'id': item.get('id'),
                            'title': title.replace('Weekly Phrase: ', '').replace('Phrase: ', '').strip(),
                            'description': item.get('idea_description', ''),
                            'seasonal_context': item.get('seasonal_context')
                        }
                
                # If we didn't find by title pattern, check the classification directly
                if has_classification and ('word' not in result or 'phrase' not in result):
                    cur.execute(
                        """
                        SELECT id, idea_title, idea_description, seasonal_context, item_classification
                        FROM calendar_ideas
                        WHERE week_number = %s
                        AND item_classification IN ('weekly_word', 'weekly_phrase')
                        """,
                        (week_number,)
                    )
                    rows = cur.fetchall() or []
                    for row in rows:
                        item = dict(row)
                        classification = item.get('item_classification', '')
                        title = item.get('idea_title', '').replace('Weekly Word: ', '').replace('Weekly Phrase: ', '').replace('Word: ', '').replace('Phrase: ', '').strip()
                        
                        if 'word' in classification.lower() and 'word' not in result:
                            result['word'] = {
                                'id': item.get('id'),
                                'title': title,
                                'description': item.get('idea_description', ''),
                                'seasonal_context': item.get('seasonal_context')
                            }
                        elif 'phrase' in classification.lower() and 'phrase' not in result:
                            result['phrase'] = {
                                'id': item.get('id'),
                                'title': title,
                                'description': item.get('idea_description', ''),
                                'seasonal_context': item.get('seasonal_context')
                            }
                
                return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting words of the week: {e}", exc_info=True)
        return {}



