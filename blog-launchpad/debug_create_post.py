#!/usr/bin/env python3
"""
Debug the complete publish_to_clan function
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from clan_publisher import ClanPublisher
    from app import get_post_with_development, get_post_sections_with_images
    
    logger.info("✅ Successfully imported required modules")
    
    # Get real database data
    post_id = 53
    real_post = get_post_with_development(post_id)
    real_sections = get_post_sections_with_images(post_id)
    
    logger.info(f"Retrieved post: {real_post.get('title', 'Unknown')}")
    logger.info(f"Retrieved {len(real_sections)} sections")
    
    # Fix field mapping like the Flask endpoint does
    if real_post.get('post_id') and not real_post.get('id'):
        real_post['id'] = real_post['post_id']
    if not real_post.get('summary'):
        real_post['summary'] = real_post.get('intro_blurb', 'No summary available')
    if real_post.get('created_at') and not isinstance(real_post['created_at'], str):
        real_post['created_at'] = real_post['created_at'].isoformat() if hasattr(real_post['created_at'], 'isoformat') else str(real_post['created_at'])
    
    logger.info("=== TESTING COMPLETE publish_to_clan FUNCTION ===")
    
    # Create publisher instance and call the method
    publisher = ClanPublisher()
    result = publisher.publish_to_clan(real_post, real_sections)
    
    logger.info(f"Final Result: {result}")
    
    if result.get('success'):
        logger.info("✅ SUCCESS: Complete publishing workflow succeeded")
    else:
        logger.error(f"❌ FAILED: {result.get('error')}")
        
except Exception as e:
    logger.error(f"❌ Debug failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
