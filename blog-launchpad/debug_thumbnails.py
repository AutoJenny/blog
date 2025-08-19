#!/usr/bin/env python3
"""
Debug the thumbnail logic
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
    
    logger.info("✅ Successfully imported ClanPublisher")
    
    # Create publisher
    publisher = ClanPublisher()
    
    # Test data - simulate what we get from the database
    test_post = {
        'id': 53,
        'title': 'Test Post',
        'summary': 'Test summary',
        'header_image': {
            'path': '/static/content/posts/53/header/optimized/header_processed.jpg'
        }
    }
    
    # Simulate uploaded_images dictionary
    uploaded_images = {
        '/static/content/posts/53/header/optimized/header_processed.jpg': 'https://static.clan.com/media/blog/header_53_1755653000.jpg'
    }
    
    logger.info("=== TESTING THUMBNAIL LOGIC ===")
    logger.info(f"Test post: {test_post}")
    logger.info(f"Uploaded images: {uploaded_images}")
    
    # Test the thumbnail logic
    header_image_path = None
    if test_post.get('header_image') and test_post['header_image'].get('path'):
        header_image_path = test_post['header_image']['path']
    
    logger.info(f"DEBUG: header_image_path = {header_image_path}")
    logger.info(f"DEBUG: uploaded_images keys = {list(uploaded_images.keys()) if uploaded_images else 'None'}")
    logger.info(f"DEBUG: uploaded_images values = {list(uploaded_images.values()) if uploaded_images else 'None'}")
    
    # Set thumbnails based on uploaded header image availability
    list_thumbnail = '/blog/placeholder.jpg'
    post_thumbnail = '/blog/placeholder.jpg'
    
    if uploaded_images and header_image_path and header_image_path in uploaded_images:
        logger.info("✅ Header image found in uploaded_images!")
        uploaded_url = uploaded_images[header_image_path]
        if uploaded_url and '/media/blog/' in uploaded_url:
            media_path = uploaded_url.split('/media/')[-1]
            thumbnail_path = f"/{media_path}"
            list_thumbnail = thumbnail_path
            post_thumbnail = thumbnail_path
            logger.info(f"✅ Using uploaded header image for thumbnails: {thumbnail_path}")
        else:
            logger.warning(f"❌ Unexpected uploaded URL format: {uploaded_url}")
    else:
        logger.error("❌ Header image NOT found in uploaded_images!")
        logger.error(f"uploaded_images exists: {bool(uploaded_images)}")
        logger.error(f"header_image_path exists: {bool(header_image_path)}")
        logger.error(f"header_image_path in uploaded_images: {header_image_path in uploaded_images if uploaded_images else False}")
    
    logger.info(f"Final thumbnails: list={list_thumbnail}, post={post_thumbnail}")
        
except Exception as e:
    logger.error(f"❌ Debug failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")

