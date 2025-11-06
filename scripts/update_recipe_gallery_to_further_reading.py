#!/usr/bin/env python3
"""
Update existing recipe posts: replace recipe_gallery sections with recipe_further_reading
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_recipe_gallery_sections():
    """Update recipe_gallery sections to recipe_further_reading"""
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Find all recipe_gallery sections
            cursor.execute("""
                SELECT id, post_id, section_heading, section_description
                FROM post_section
                WHERE section_type = 'recipe_gallery'
            """)
            gallery_sections = cursor.fetchall()
            
            logger.info(f"Found {len(gallery_sections)} recipe_gallery sections to update")
            
            for section in gallery_sections:
                section_id = section['id']
                post_id = section['post_id']
                
                # Update section type and description
                cursor.execute("""
                    UPDATE post_section
                    SET section_type = 'recipe_further_reading',
                        section_heading = 'Further Reading',
                        section_description = 'Search for 2-5 authoritative sources for background information about this recipe. Focus on: cultural/heritage sites, Wikipedia articles, historical sources, ingredient provenance sites, and tourism/heritage organizations. AVOID competing recipe sites or cooking blogs. For each source, provide: Title & Link, Why It''s Good (brief explanation of the source''s value), and Use Case in Your Content (how to reference this source in the recipe sections above). Sources should support the Background, Ingredients, Variations, and Serving Suggestions sections.'
                    WHERE id = %s
                """, (section_id,))
                
                logger.info(f"Updated section {section_id} for post {post_id}: recipe_gallery -> recipe_further_reading")
            
            conn.commit()
            logger.info(f"Successfully updated {len(gallery_sections)} sections")

if __name__ == '__main__':
    update_recipe_gallery_sections()

