#!/usr/bin/env python3
"""
Test the URL key conflict theory by using a unique URL key
"""

import os
import sys
import logging
import time

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
    
    # Fix field mapping like the Flask endpoint does
    if real_post.get('post_id') and not real_post.get('id'):
        real_post['id'] = real_post['post_id']
    if not real_post.get('summary'):
        real_post['summary'] = real_post.get('intro_blurb', 'No summary available')
    if real_post.get('created_at') and not isinstance(real_post['created_at'], str):
        real_post['created_at'] = real_post['created_at'].isoformat() if hasattr(real_post['created_at'], 'isoformat') else str(real_post['created_at'])
    
    logger.info(f"Original post title: {real_post.get('title')}")
    logger.info(f"Original slug: {real_post.get('slug')}")
    
    # MODIFY: Force a unique URL key by removing the slug
    # This will force the function to generate a new one with post ID
    logger.info("=== TESTING URL KEY CONFLICT THEORY ===")
    
    # Remove slug to force unique URL key generation
    if 'slug' in real_post:
        original_slug = real_post['slug']
        del real_post['slug']
        logger.info(f"Removed original slug: {original_slug}")
    
    # Test the URL key generation
    publisher = ClanPublisher()
    new_url_key = publisher._generate_url_key(real_post)
    logger.info(f"New unique URL key: {new_url_key}")
    
    # Test with timestamp for extra uniqueness
    timestamp = int(time.time())
    real_post['test_timestamp'] = timestamp
    
    # Override the URL key generation to include timestamp
    def generate_unique_url_key(post):
        title = post.get('title', 'Untitled Post')
        import re
        url_key = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        url_key = re.sub(r'\s+', '-', url_key).strip('-')
        
        # Add timestamp for extra uniqueness
        timestamp = int(time.time())
        if not url_key:
            url_key = f'post-{post["id"]}-{timestamp}'
        else:
            url_key = f'{url_key}-{post["id"]}-{timestamp}'
        
        return url_key
    
    # Monkey patch for this test
    publisher._generate_url_key = generate_unique_url_key
    
    unique_url_key = publisher._generate_url_key(real_post)
    logger.info(f"Timestamp-based unique URL key: {unique_url_key}")
    
    # Now test the API call with the unique URL key
    logger.info(f"=== TESTING API CALL WITH UNIQUE URL KEY ===")
    
    # Create simple HTML for test
    test_html = f"""
    <div class="mpblog-post">
        <h1>{real_post.get('title', 'Test Post')}</h1>
        <p>{real_post.get('summary', 'Test content')}</p>
    </div>
    """
    
    # Test the create_or_update_post function
    result = publisher.create_or_update_post(real_post, test_html, False, {})
    
    logger.info(f"API call result: {result}")
    
    if result['success']:
        logger.info("✅ SUCCESS! URL key conflict was the issue!")
        logger.info(f"Post created with ID: {result.get('clan_post_id')}")
        logger.info(f"Post URL: {result.get('url')}")
    else:
        logger.error("❌ Still failed - URL key conflict was not the issue")
        logger.error(f"Error: {result.get('error')}")
    
except Exception as e:
    logger.error(f"❌ Test failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")


