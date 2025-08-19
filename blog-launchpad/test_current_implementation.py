#!/usr/bin/env python3
"""
Test script to verify our current implementation works with the same test data
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
    
    # Test data that we know works from our direct API test
    test_post_data = {
        'id': 999,  # Add required id field
        'title': 'Test Post from Current Implementation',
        'url_key': 'test-post-current-impl-002',
        'short_content': 'This is a test post to verify our current implementation works.',
        'status': 2,
        'categories': [14, 15],
        'list_thumbnail': '/blog/test-image.jpg',
        'post_thumbnail': '/blog/test-image.jpg',
        'meta_title': 'Test Post Meta Title',
        'meta_tags': 'test,implementation,verification',
        'meta_description': 'Test post for verifying current implementation works'
    }
    
    # Test HTML content
    test_html_content = """
    <div class="mpblog-post">
        <header class="blog-post-header">
            <h1>Test Post from Current Implementation</h1>
        </header>
        <div class="post-content">
            <p>This is a simple test post to verify our current implementation.</p>
        </div>
    </div>
    """
    
    logger.info("Testing ClanPublisher initialization")
    publisher = ClanPublisher()
    logger.info(f"✅ ClanPublisher initialized successfully")
    
    # Test the createPost endpoint using our current implementation
    logger.info("Testing createPost endpoint with our current implementation")
    
    result = publisher.create_or_update_post(test_post_data, test_html_content, False, {})
    
    if result['success']:
        logger.info("✅ Post creation succeeded!")
        logger.info(f"Result: {result}")
    else:
        logger.error("❌ Post creation failed")
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
    
    logger.info("✅ Test completed")
    
except Exception as e:
    logger.error(f"❌ Test failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
