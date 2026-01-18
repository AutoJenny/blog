"""
Weekly Content Data Extractor
Extracts data from calendar_ideas and formats for image/caption generation
"""

import os
import logging
from typing import Dict, Optional
from config.database import db_manager
from config.weekly_content_image_config import (
    CATEGORY_TITLES,
    SERIES_FOOTER_TEXT,
    LOGO_PATH,
    OUTPUT_BASE_DIR
)

logger = logging.getLogger(__name__)


def extract_weekly_content_data(
    idea_id: int,
    category: str  # 'weekly_word', 'weekly_phrase', or 'weekly_insult'
) -> Dict:
    """
    Extract data from calendar_ideas for image/caption generation.
    
    Parameters
    ----------
    idea_id:
        calendar_ideas.id for the weekly Content Item.
    category:
        Must be 'weekly_word', 'weekly_phrase', or 'weekly_insult'.
    
    Returns
    -------
    Dict with data contract structure:
    {
        'category': 'weekly_word|weekly_phrase|weekly_insult',
        'title': 'SCOTS WORD OF THE WEEK',
        'scots_text': 'braw',
        'translation': 'good, fine',
        'usage_examples': ['Usage example 1', 'Usage example 2'],  # List (weekly_word only)
        'series_footer': 'Scots Language Series',
        'logo_path': '/absolute/path/to/logo.png',
        'output_path': '/absolute/path/to/output/image.png',
        'notes': 'Provenance/notes from idea_description',
        'idea_id': 123
    }
    
    Raises
    ------
    ValueError:
        If idea_id not found or category is invalid.
    """
    if category not in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
        raise ValueError(
            f"category must be 'weekly_word', 'weekly_phrase', or 'weekly_insult', got: {category}"
        )
    
    # Fetch idea from database
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                idea_title,
                idea_description,
                item_classification
            FROM calendar_ideas
            WHERE id = %s
        """, (idea_id,))
        
        idea = cursor.fetchone()
        if not idea:
            raise ValueError(f"Idea {idea_id} not found in calendar_ideas")
    
    # Parse idea_description for translation, usage examples, and provenance/notes
    description = idea.get('idea_description') or ''
    translation = ''
    usage_examples = []
    notes = ''
    
    # Expected format: "Translation: ... | Usage: ... | Usage: ... | Provenance: ..."
    if 'Translation:' in description:
        parts = description.split('|')
        for part in parts:
            part = part.strip()
            if part.startswith('Translation:'):
                translation = part.replace('Translation:', '').strip()
            elif part.startswith('Usage:'):
                usage_text = part.replace('Usage:', '').strip()
                if usage_text:
                    usage_examples.append(usage_text)
            elif part.startswith('Provenance:'):
                notes = part.replace('Provenance:', '').strip()
            elif part.startswith('Notes:'):
                notes = part.replace('Notes:', '').strip()
    else:
        # If no explicit translation marker, use description as notes
        notes = description.strip()
    
    # Get title from config
    title = CATEGORY_TITLES.get(category, 'SCOTS WORD OF THE WEEK')
    
    # Get logo path (already absolute from config)
    logo_path = LOGO_PATH if os.path.exists(LOGO_PATH) else None
    
    if not logo_path:
        logger.warning(f"Logo file not found at {LOGO_PATH}, images will be generated without logo")
    
    # Generate output path
    output_dir = os.path.join(OUTPUT_BASE_DIR, category, str(idea_id))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.abspath(os.path.join(output_dir, 'square_image.png'))
    
    # Get Scots text from idea_title
    scots_text = idea.get('idea_title', '').strip()
    
    if not scots_text:
        raise ValueError(f"Idea {idea_id} has empty idea_title")
    
    return {
        'category': category,
        'title': title,
        'scots_text': scots_text,
        'translation': translation,
        'usage_examples': usage_examples,  # List of usage example strings
        'series_footer': SERIES_FOOTER_TEXT,
        'logo_path': logo_path,
        'output_path': output_path,
        'notes': notes,  # Provenance/notes
        'idea_id': idea_id
    }
