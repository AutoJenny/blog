#!/usr/bin/env python3
"""
Test to see what data the database functions are actually returning
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
    from app import get_post_with_development, get_post_sections_with_images
    
    logger.info("✅ Successfully imported database functions")
    
    # Test post ID 53
    post_id = 53
    
    logger.info(f"=== TESTING DATABASE FUNCTIONS FOR POST {post_id} ===")
    
    # Test 1: Get post data
    logger.info("\n=== TEST 1: Post Data ===")
    try:
        post = get_post_with_development(post_id)
        if post:
            logger.info(f"✅ Post found!")
            logger.info(f"Post keys: {list(post.keys())}")
            logger.info(f"Post title: {post.get('title', 'NO TITLE')}")
            logger.info(f"Post ID field: {post.get('id', 'NO ID')}")
            logger.info(f"Post ID field type: {type(post.get('id'))}")
            logger.info(f"Post summary: {post.get('summary', 'NO SUMMARY')}")
            logger.info(f"Post created_at: {post.get('created_at', 'NO DATE')}")
        else:
            logger.error("❌ Post not found")
    except Exception as e:
        logger.error(f"❌ Post retrieval failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Test 2: Get sections data
    logger.info("\n=== TEST 2: Sections Data ===")
    try:
        sections = get_post_sections_with_images(post_id)
        if sections:
            logger.info(f"✅ Found {len(sections)} sections")
            for i, section in enumerate(sections):
                logger.info(f"Section {i+1}:")
                logger.info(f"  ID: {section.get('id')}")
                logger.info(f"  Heading: {section.get('section_heading')}")
                logger.info(f"  Image path: {section.get('image', {}).get('path')}")
                logger.info(f"  Image placeholder: {section.get('image', {}).get('placeholder')}")
                logger.info(f"  Polished content: {section.get('polished', 'NO CONTENT')[:50]}...")
        else:
            logger.error("❌ No sections found")
    except Exception as e:
        logger.error(f"❌ Sections retrieval failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    logger.info("\n=== DATABASE TEST COMPLETED ===")
    
except Exception as e:
    logger.error(f"❌ Test setup failed: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")


