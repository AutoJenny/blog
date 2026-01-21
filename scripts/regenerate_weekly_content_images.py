#!/usr/bin/env python3
"""
Regenerate all weekly content images using the v2 renderer
This ensures all production images use the new font sizes and layout
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.weekly_content_data_extractor import extract_weekly_content_data
from utils.weekly_content_image_renderer_v2 import render_weekly_content_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def regenerate_all_weekly_images():
    """
    Regenerate images for all weekly content posts (ready, pending, and recent published)
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Get all weekly content posts that need images
            cursor.execute("""
                SELECT DISTINCT idea_id, content_type
                FROM posting_queue
                WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
                AND idea_id IS NOT NULL
                ORDER BY content_type, idea_id
            """)
            posts = cursor.fetchall()
            
            logger.info(f"Found {len(posts)} unique weekly content items to regenerate")
            
            regenerated = 0
            failed = 0
            
            for post in posts:
                idea_id = post['idea_id']
                content_type = post['content_type']
                
                try:
                    logger.info(f"Regenerating {content_type} for idea_id {idea_id}...")
                    
                    # Extract data
                    formatted_data = extract_weekly_content_data(idea_id, content_type)
                    
                    # Generate image using v2 renderer
                    result = render_weekly_content_image(
                        category=formatted_data['category'],
                        title=formatted_data['title'],
                        scots_text=formatted_data['scots_text'],
                        translation=formatted_data['translation'],
                        series_footer=formatted_data['series_footer'],
                        logo_path=formatted_data['logo_path'],
                        output_path=formatted_data['output_path'],
                        usage_examples=formatted_data.get('usage_examples', []),
                        notes=formatted_data.get('notes', '')
                    )
                    
                    if result['success']:
                        logger.info(f"✅ Successfully regenerated image: {result['output_path']}")
                        regenerated += 1
                        
                        # Update posting_queue rows with new image path
                        cursor.execute("""
                            UPDATE posting_queue
                            SET image_path = %s, updated_at = NOW()
                            WHERE idea_id = %s AND content_type = %s
                        """, (result['output_path'], idea_id, content_type))
                    else:
                        logger.error(f"❌ Failed to regenerate image for idea_id {idea_id}: {result.get('error')}")
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error regenerating image for idea_id {idea_id}: {e}")
                    failed += 1
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Regeneration complete:")
            logger.info(f"  ✅ Successfully regenerated: {regenerated}")
            logger.info(f"  ❌ Failed: {failed}")
            logger.info(f"{'='*60}")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting weekly content image regeneration...")
    regenerate_all_weekly_images()
    logger.info("Done.")
