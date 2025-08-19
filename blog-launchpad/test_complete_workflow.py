#!/usr/bin/env python3
"""
Comprehensive test of the complete publishing workflow
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
    from clan_publisher import ClanPublisher, publish_to_clan
    from app import find_header_image, find_section_image
    
    logger.info("✅ Successfully imported required modules")
    
    # Test data that mimics what would come from the database
    test_post = {
        'id': 53,
        'title': 'Test Post 53 - Complete Workflow Test',
        'summary': 'This is a test post to verify the complete publishing workflow works end-to-end.',
        'created_at': None,  # Will be handled by the code
        'keywords': ['test', 'workflow', 'verification']
    }
    
    test_sections = [
        {
            'id': 710,
            'section_heading': 'Test Section 1',
            'polished': 'This is the content for test section 1.',
            'draft': 'This is the draft content for test section 1.'
        },
        {
            'id': 711,
            'section_heading': 'Test Section 2', 
            'polished': 'This is the content for test section 2.',
            'draft': 'This is the draft content for test section 2.'
        }
    ]
    
    logger.info("=== TESTING COMPLETE WORKFLOW ===")
    logger.info(f"Post ID: {test_post['id']}")
    logger.info(f"Post title: {test_post['title']}")
    logger.info(f"Number of sections: {len(test_sections)}")
    
    # Test 1: Image finding functions
    logger.info("\n=== TEST 1: Image Finding Functions ===")
    try:
        header_path = find_header_image(test_post['id'])
        logger.info(f"Header image path: {header_path}")
        
        for section in test_sections:
            section_id = section['id']
            section_path = find_section_image(test_post['id'], section_id)
            logger.info(f"Section {section_id} image path: {section_path}")
    except Exception as e:
        logger.error(f"❌ Image finding failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Test 2: Individual API functions
    logger.info("\n=== TEST 2: Individual API Functions ===")
    try:
        publisher = ClanPublisher()
        logger.info("✅ ClanPublisher initialized")
        
        # Test image upload if we have a header image
        if header_path and os.path.exists(header_path):
            logger.info("Testing image upload...")
            filename = f"test_header_{test_post['id']}_{int(__import__('time').time())}.jpg"
            uploaded_url = publisher.upload_image(header_path, filename)
            if uploaded_url:
                logger.info(f"✅ Image upload succeeded: {uploaded_url}")
            else:
                logger.error("❌ Image upload failed")
        else:
            logger.warning("No header image found to test upload")
            
    except Exception as e:
        logger.error(f"❌ API functions test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Test 3: Complete publishing workflow
    logger.info("\n=== TEST 3: Complete Publishing Workflow ===")
    try:
        result = publish_to_clan(test_post, test_sections)
        logger.info(f"Publishing result: {result}")
        
        if result['success']:
            logger.info("✅ Complete workflow succeeded!")
        else:
            logger.error(f"❌ Complete workflow failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Complete workflow test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    logger.info("\n=== WORKFLOW TEST COMPLETED ===")
    
except Exception as e:
    logger.error(f"❌ Test setup failed: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")


