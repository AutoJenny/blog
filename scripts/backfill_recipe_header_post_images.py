#!/usr/bin/env python3
"""
Backfill missing post_images records for recipe post header images.

This script finds recipe posts that have header_image_id set but no corresponding
post_images record, and creates the missing post_images records so they can be
published correctly.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_recipe_header_post_images(dry_run=True):
    """
    Find recipe posts with header images but no post_images records and create them.
    
    Args:
        dry_run: If True, only report what would be done without making changes
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Find recipe posts with header_image_id but no post_images record
            cursor.execute("""
                SELECT 
                    p.id as post_id,
                    p.title,
                    p.header_image_id,
                    i.id as image_id,
                    i.file_path as image_path,
                    i.filename
                FROM post p
                JOIN images i ON p.header_image_id = i.id
                LEFT JOIN post_images pi ON pi.post_id = p.id 
                    AND pi.section_id IS NULL 
                    AND pi.image_type = 'header_optimized'
                WHERE p.recipe_week_number IS NOT NULL
                    AND p.header_image_id IS NOT NULL
                    AND pi.id IS NULL
                ORDER BY p.id
            """)
            
            posts_to_fix = cursor.fetchall()
            
            if not posts_to_fix:
                logger.info("✅ No recipe posts found that need post_images records")
                return
            
            logger.info(f"Found {len(posts_to_fix)} recipe posts with header images but no post_images records:")
            
            for post in posts_to_fix:
                logger.info(f"  Post {post['post_id']}: {post['title']}")
                logger.info(f"    Header image ID: {post['header_image_id']}")
                logger.info(f"    Image path: {post['image_path']}")
                
                if not dry_run:
                    # Delete any existing post_images record (shouldn't exist, but be safe)
                    cursor.execute("""
                        DELETE FROM post_images 
                        WHERE post_id = %s AND section_id IS NULL AND image_type = 'header_optimized'
                    """, (post['post_id'],))
                    
                    # Create post_images record
                    cursor.execute("""
                        INSERT INTO post_images (post_id, section_id, image_id, image_type)
                        VALUES (%s, NULL, %s, 'header_optimized')
                    """, (post['post_id'], post['header_image_id']))
                    
                    logger.info(f"    ✅ Created post_images record for post {post['post_id']}")
            
            if not dry_run:
                db_manager.commit()
                logger.info(f"\n✅ Successfully created post_images records for {len(posts_to_fix)} recipe posts")
            else:
                logger.info(f"\n⚠️  DRY RUN: Would create post_images records for {len(posts_to_fix)} recipe posts")
                logger.info("   Run with dry_run=False to apply changes")
    
    except Exception as e:
        logger.error(f"❌ Error during backfill: {e}", exc_info=True)
        if not dry_run:
            db_manager.rollback()
        raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill missing post_images records for recipe post header images')
    parser.add_argument('--apply', action='store_true', 
                       help='Actually apply changes (default is dry run)')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    if dry_run:
        logger.info("🔍 Running in DRY RUN mode (no changes will be made)")
        logger.info("   Use --apply to actually create the records\n")
    else:
        logger.info("⚠️  APPLYING CHANGES (this will modify the database)\n")
    
    backfill_recipe_header_post_images(dry_run=dry_run)

