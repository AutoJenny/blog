#!/usr/bin/env python3
"""
Test script to debug the image upload process
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
    from app import find_header_image, find_section_image
    
    logger.info("✅ Successfully imported required modules")
    
    # Test image finding
    post_id = 53
    logger.info(f"Testing image finding for post {post_id}")
    
    header_path = find_header_image(post_id)
    logger.info(f"Header image path: {header_path}")
    
    section_path = find_section_image(post_id, 710)
    logger.info(f"Section 710 image path: {section_path}")
    
    # Test ClanPublisher initialization
    logger.info("Testing ClanPublisher initialization")
    publisher = ClanPublisher()
    logger.info(f"✅ ClanPublisher initialized successfully")
    logger.info(f"API base URL: {publisher.api_base_url}")
    logger.info(f"API user: {publisher.api_user}")
    logger.info(f"API key: {publisher.api_key[:10]}...")
    
    # Test image upload
    if header_path:
        logger.info("Testing header image upload")
        filename = f"test_header_{post_id}_{int(__import__('time').time())}.jpg"
        logger.info(f"Uploading with filename: {filename}")
        
        uploaded_url = publisher.upload_image(header_path, filename)
        if uploaded_url:
            logger.info(f"✅ Header image uploaded successfully: {uploaded_url}")
        else:
            logger.error("❌ Header image upload failed")
    else:
        logger.warning("No header image found to test")
    
    logger.info("✅ Test completed successfully")
    
except Exception as e:
    logger.error(f"❌ Test failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
