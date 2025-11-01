"""Clean subscription text from existing synopses in database."""

from __future__ import annotations

import logging
from typing import Dict, Any
from config.database import db_manager
from newsletter.services.news_synopsis_service import clean_subscription_text
from psycopg.types.json import Json

logger = logging.getLogger(__name__)


def clean_all_synopses() -> Dict[str, Any]:
    """Clean subscription text from all existing synopses in database.
    
    Returns:
        Dict with results
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get all news items with synopses
            cur.execute("""
                SELECT id, raw_data
                FROM newsletter_source_item
                WHERE category = 'news'
                  AND raw_data IS NOT NULL
                  AND raw_data->>'synopsis' IS NOT NULL
            """)
            
            rows = cur.fetchall() or []
            logger.info(f"Found {len(rows)} news items with synopses to clean")
            
            updated_count = 0
            unchanged_count = 0
            
            for row in rows:
                item_id = row['id']
                raw_data = row['raw_data'] or {}
                original_synopsis = raw_data.get('synopsis', '')
                
                if not original_synopsis:
                    continue
                
                # Clean the synopsis
                cleaned_synopsis = clean_subscription_text(original_synopsis)
                
                # Only update if it changed
                if cleaned_synopsis != original_synopsis:
                    raw_data['synopsis'] = cleaned_synopsis
                    
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(raw_data), item_id))
                    
                    updated_count += 1
                    logger.debug(f"Cleaned synopsis for item {item_id}")
                else:
                    unchanged_count += 1
            
            conn.commit()
            
            return {
                'total': len(rows),
                'updated': updated_count,
                'unchanged': unchanged_count,
            }


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../../..')
    
    result = clean_all_synopses()
    print(f"Cleaned {result['updated']} synopses, {result['unchanged']} unchanged")

