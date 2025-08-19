#!/usr/bin/env python3
"""
Test script to debug the post creation API endpoint
"""

import os
import sys
import logging
import json
import requests
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from clan_publisher import ClanPublisher
    from app import find_header_image, find_section_image
    
    logger.info("✅ Successfully imported required modules")
    
    # Test data similar to what we send in the real request
    test_post_data = {
        'title': 'Test Post from API Debug',
        'url_key': 'test-post-api-debug-001',
        'short_content': 'This is a test post to debug the API endpoint issues.',
        'status': 2,
        'categories': [14, 15],
        'list_thumbnail': '/blog/test-image.jpg',
        'post_thumbnail': '/blog/test-image.jpg',
        'meta_title': 'Test Post Meta Title',
        'meta_tags': 'test,debug,api',
        'meta_description': 'Test post for debugging API endpoint issues'
    }
    
    # Test HTML content
    test_html_content = """
    <div class="mpblog-post">
        <header class="blog-post-header">
            <h1>Test Post from API Debug</h1>
        </header>
        <div class="post-content">
            <p>This is a simple test post to debug the API endpoint.</p>
        </div>
    </div>
    """
    
    logger.info("Testing ClanPublisher initialization")
    publisher = ClanPublisher()
    logger.info(f"✅ ClanPublisher initialized successfully")
    logger.info(f"API base URL: {publisher.api_base_url}")
    logger.info(f"API user: {publisher.api_user}")
    logger.info(f"API key: {publisher.api_key[:10]}...")
    
    # Test the createPost endpoint directly
    logger.info("Testing createPost endpoint directly")
    
    endpoint = f"{publisher.api_base_url}createPost"
    logger.info(f"Endpoint: {endpoint}")
    
    # Prepare API data exactly as our code does
    api_data = {
        'api_user': publisher.api_user,
        'api_key': publisher.api_key,
        'json_args': json.dumps(test_post_data)
    }
    
    logger.info(f"API data: {api_data}")
    logger.info(f"JSON args content: {test_post_data}")
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(test_html_content)
        temp_file_path = temp_file.name
    
    logger.info(f"Temporary HTML file: {temp_file_path}")
    logger.info(f"HTML content length: {len(test_html_content)} characters")
    
    try:
        # Send the request exactly as our code does
        with open(temp_file_path, 'rb') as html_file:
            files = {'html_file': ('test_post.html', html_file, 'text/html')}
            
            logger.info("Sending POST request to createPost endpoint...")
            response = requests.post(endpoint, data=api_data, files=files, timeout=60)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response text: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"Response JSON: {result}")
                    
                    if result.get('success') or result.get('status') == 'success':
                        logger.info("✅ Post creation succeeded!")
                        if result.get('post_id'):
                            logger.info(f"Post ID: {result.get('post_id')}")
                        if result.get('url'):
                            logger.info(f"Post URL: {result.get('url')}")
                    else:
                        logger.error("❌ Post creation failed")
                        logger.error(f"Error: {result.get('error', 'Unknown error')}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response: {response.text}")
            else:
                logger.error(f"❌ HTTP error {response.status_code}")
                logger.error(f"Response text: {response.text}")
                
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)
        
    logger.info("✅ Test completed")
    
except Exception as e:
    logger.error(f"❌ Test failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
