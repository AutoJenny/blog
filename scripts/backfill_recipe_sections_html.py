#!/usr/bin/env python3
"""
Backfill script to render existing recipe sections from JSON to HTML.

This script finds all recipe sections that have JSON in post_section_elements
but don't have proper HTML in the polished field, and renders them.
"""

import os
import sys
import json
import logging

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager
from utils.recipe_section_renderer import render_recipe_section

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backfill_recipe_sections():
    """Backfill recipe sections by rendering JSON to HTML."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Find all recipe sections with post_section_elements but raw JSON in polished
                cursor.execute("""
                    SELECT id, post_id, section_type, section_heading,
                           post_section_elements, polished, draft
                    FROM post_section
                    WHERE section_type LIKE 'recipe_%'
                      AND section_type != 'recipe_image_style'
                      AND post_section_elements IS NOT NULL
                    ORDER BY post_id, section_order
                """)
                
                sections = cursor.fetchall()
                logger.info(f"Found {len(sections)} recipe sections to process")
                
                updated_count = 0
                skipped_count = 0
                error_count = 0
                
                for section in sections:
                    section_id = section['id']
                    post_id = section['post_id']
                    section_type = section['section_type']
                    section_heading = section['section_heading']
                    
                    # Check if polished contains raw JSON
                    polished = section.get('polished', '')
                    is_json = False
                    if polished:
                        polished_stripped = polished.strip()
                        if polished_stripped.startswith('{') or polished_stripped.startswith('[') or '```json' in polished_stripped.lower():
                            is_json = True
                    
                    # Only process if polished is JSON or empty
                    if not is_json and polished:
                        logger.info(f"Skipping section {section_id} ({section_heading}) - already has HTML in polished")
                        skipped_count += 1
                        continue
                    
                    # Parse post_section_elements
                    post_section_elements = section.get('post_section_elements')
                    if not post_section_elements:
                        logger.warning(f"Skipping section {section_id} ({section_heading}) - no post_section_elements")
                        skipped_count += 1
                        continue
                    
                    try:
                        # Parse JSON if it's a string
                        if isinstance(post_section_elements, str):
                            section_elements = json.loads(post_section_elements)
                        else:
                            section_elements = post_section_elements
                        
                        # Render to HTML
                        draft_content = section.get('draft', '')
                        # Filter out JSON from draft if present
                        if draft_content:
                            draft_stripped = draft_content.strip()
                            if draft_stripped.startswith('{') or draft_stripped.startswith('[') or '```json' in draft_stripped.lower():
                                draft_content = None
                        
                        rendered_html = render_recipe_section(
                            section_type,
                            section_elements,
                            draft_content if draft_content and not draft_content.strip().startswith('{') else None
                        )
                        
                        # Update the polished field
                        cursor.execute("""
                            UPDATE post_section
                            SET polished = %s
                            WHERE id = %s
                        """, (rendered_html, section_id))
                        
                        updated_count += 1
                        logger.info(f"✅ Rendered section {section_id} ({section_heading}) for post {post_id}")
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"❌ Error rendering section {section_id} ({section_heading}): {e}")
                        import traceback
                        traceback.print_exc()
                
                conn.commit()
                
                logger.info(f"\n=== Backfill Complete ===")
                logger.info(f"Updated: {updated_count}")
                logger.info(f"Skipped: {skipped_count}")
                logger.info(f"Errors: {error_count}")
                logger.info(f"Total: {len(sections)}")
                
    except Exception as e:
        logger.error(f"Error in backfill: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    backfill_recipe_sections()






