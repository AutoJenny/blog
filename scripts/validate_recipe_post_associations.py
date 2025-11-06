#!/usr/bin/env python3
"""
Validate that all recipe posts have correct recipe_week_number associations.
Fixes any mismatches by matching post.title to calendar_recipes.recipe_title.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_and_fix_recipe_associations():
    """Validate and fix recipe post associations"""
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all recipe posts
            cursor.execute("""
                SELECT p.id, p.title, p.recipe_week_number
                FROM post p
                WHERE p.recipe_week_number IS NOT NULL
            """)
            recipe_posts = cursor.fetchall()
            
            logger.info(f"Found {len(recipe_posts)} recipe posts to validate")
            
            fixed_count = 0
            for post in recipe_posts:
                post_id = post['id']
                post_title = post['title']
                current_week = post['recipe_week_number']
                
                # Find the correct week_number for this recipe title
                cursor.execute("""
                    SELECT week_number, recipe_title
                    FROM calendar_recipes
                    WHERE recipe_title = %s
                    LIMIT 1
                """, (post_title,))
                correct_recipe = cursor.fetchone()
                
                if not correct_recipe:
                    logger.warning(f"Post {post_id} ('{post_title}') - No matching recipe found in calendar_recipes")
                    continue
                
                correct_week = correct_recipe['week_number']
                recipe_title = correct_recipe['recipe_title']
                
                if current_week != correct_week:
                    logger.warning(f"Post {post_id} ('{post_title}') - Mismatch: recipe_week_number={current_week}, should be {correct_week} (recipe: {recipe_title})")
                    
                    # Fix it
                    cursor.execute("""
                        UPDATE post
                        SET recipe_week_number = %s
                        WHERE id = %s
                    """, (correct_week, post_id))
                    
                    fixed_count += 1
                    logger.info(f"  Fixed: Updated post {post_id} to recipe_week_number = {correct_week}")
                else:
                    logger.debug(f"Post {post_id} ('{post_title}') - Correct: recipe_week_number={current_week}")
            
            conn.commit()
            logger.info(f"Validation complete. Fixed {fixed_count} mismatched associations.")

if __name__ == '__main__':
    validate_and_fix_recipe_associations()

