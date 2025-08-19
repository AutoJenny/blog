#!/usr/bin/env python3
"""
Compare the exact payloads between working test data and real database data
"""

import os
import sys
import logging
import json

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
    logger.info("=== GETTING REAL DATABASE DATA ===")
    post_id = 53
    real_post = get_post_with_development(post_id)
    real_sections = get_post_sections_with_images(post_id)
    
    # Fix field mapping like the Flask endpoint does
    if real_post.get('post_id') and not real_post.get('id'):
        real_post['id'] = real_post['post_id']
    if not real_post.get('summary'):
        real_post['summary'] = real_post.get('intro_blurb', 'No summary available')
    if real_post.get('created_at') and not isinstance(real_post['created_at'], str):
        real_post['created_at'] = real_post['created_at'].isoformat() if hasattr(real_post['created_at'], 'isoformat') else str(real_post['created_at'])
    
    # Create working test data (what succeeded)
    logger.info("=== CREATING WORKING TEST DATA ===")
    test_post = {
        'id': 999,
        'title': 'Test Post from Current Implementation',
        'summary': 'This is a test post to verify our current implementation works.',
        'created_at': None,
        'keywords': ['test', 'implementation', 'verification']
    }
    
    test_sections = [
        {
            'id': 710,
            'section_heading': 'Test Section 1',
            'polished': 'This is the content for test section 1.',
            'draft': 'This is the draft content for test section 1.'
        }
    ]
    
    logger.info("=== COMPARING DATA STRUCTURES ===")
    
    # Compare post data
    logger.info("POST DATA COMPARISON:")
    logger.info(f"Real post keys: {sorted(real_post.keys())}")
    logger.info(f"Test post keys: {sorted(test_post.keys())}")
    
    logger.info("KEY DIFFERENCES:")
    for key in real_post.keys():
        if key not in test_post:
            logger.info(f"  Real has extra key: '{key}' = {real_post[key]}")
    
    for key in test_post.keys():
        if key not in real_post:
            logger.info(f"  Test has extra key: '{key}' = {test_post[key]}")
        elif real_post[key] != test_post[key]:
            logger.info(f"  Different values for '{key}':")
            logger.info(f"    Real: {real_post[key]} (type: {type(real_post[key])})")
            logger.info(f"    Test: {test_post[key]} (type: {type(test_post[key])})")
    
    # Generate API payloads for comparison
    logger.info("\n=== GENERATING API PAYLOADS ===")
    
    publisher = ClanPublisher()
    
    # Generate real payload
    logger.info("Generating real payload...")
    real_url_key = publisher._generate_url_key(real_post)
    real_meta_tags = publisher._generate_meta_tags(real_post)
    
    real_payload = {
        'title': real_post.get('title', 'Untitled Post'),
        'url_key': real_url_key,
        'short_content': real_post.get('summary', '')[:200] if real_post.get('summary') else 'No summary available',
        'status': 2,
        'categories': [14, 15],
        'list_thumbnail': '/blog/default-thumbnail.jpg',
        'post_thumbnail': '/blog/default-thumbnail.jpg',
        'meta_title': real_post.get('title', 'Untitled Post'),
        'meta_tags': real_meta_tags,
        'meta_description': real_post.get('summary', '')[:160] if real_post.get('summary') else 'No description available'
    }
    
    # Generate test payload
    logger.info("Generating test payload...")
    test_url_key = publisher._generate_url_key(test_post)
    test_meta_tags = publisher._generate_meta_tags(test_post)
    
    test_payload = {
        'title': test_post.get('title', 'Untitled Post'),
        'url_key': test_url_key,
        'short_content': test_post.get('summary', '')[:200] if test_post.get('summary') else 'No summary available',
        'status': 2,
        'categories': [14, 15],
        'list_thumbnail': '/blog/default-thumbnail.jpg',
        'post_thumbnail': '/blog/default-thumbnail.jpg',
        'meta_title': test_post.get('title', 'Untitled Post'),
        'meta_tags': test_meta_tags,
        'meta_description': test_post.get('summary', '')[:160] if test_post.get('summary') else 'No description available'
    }
    
    logger.info("\n=== API PAYLOAD COMPARISON ===")
    logger.info("REAL PAYLOAD:")
    for key, value in real_payload.items():
        logger.info(f"  '{key}': '{value}' (len: {len(str(value))}, type: {type(value).__name__})")
    
    logger.info("\nTEST PAYLOAD:")
    for key, value in test_payload.items():
        logger.info(f"  '{key}': '{value}' (len: {len(str(value))}, type: {type(value).__name__})")
    
    logger.info("\n=== PAYLOAD DIFFERENCES ===")
    for key in real_payload.keys():
        if real_payload[key] != test_payload[key]:
            logger.info(f"DIFFERENCE in '{key}':")
            logger.info(f"  Real: '{real_payload[key]}'")
            logger.info(f"  Test: '{test_payload[key]}'")
    
    # Check for problematic values
    logger.info("\n=== PROBLEMATIC VALUE ANALYSIS ===")
    
    # Check URL key
    real_url_key = real_payload['url_key']
    test_url_key = test_payload['url_key']
    
    logger.info(f"URL KEY ANALYSIS:")
    logger.info(f"  Real URL key: '{real_url_key}' (length: {len(real_url_key)})")
    logger.info(f"  Test URL key: '{test_url_key}' (length: {len(test_url_key)})")
    
    if len(real_url_key) > 100:
        logger.error(f"❌ POTENTIAL ISSUE: Real URL key is very long ({len(real_url_key)} chars)")
    
    if ' ' in real_url_key:
        logger.error(f"❌ POTENTIAL ISSUE: Real URL key contains spaces")
    
    special_chars = set(real_url_key) - set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
    if special_chars:
        logger.error(f"❌ POTENTIAL ISSUE: Real URL key contains special characters: {special_chars}")
    
    # Check title length
    real_title = real_payload['title']
    if len(real_title) > 255:
        logger.error(f"❌ POTENTIAL ISSUE: Real title is very long ({len(real_title)} chars)")
    
    # Check meta tags
    real_meta_tags = real_payload['meta_tags']
    if len(real_meta_tags) > 255:
        logger.error(f"❌ POTENTIAL ISSUE: Real meta_tags is very long ({len(real_meta_tags)} chars)")
    
    logger.info("\n=== COMPARISON COMPLETED ===")
    
except Exception as e:
    logger.error(f"❌ Test failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")


