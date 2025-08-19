#!/usr/bin/env python3
"""
Debug what we're actually sending to clan.com API
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
    
    logger.info("=== ANALYZING API PAYLOAD ===")
    
    # Create publisher and generate content like the real workflow
    publisher = ClanPublisher()
    
    # Generate HTML content (without actually uploading images)
    html_content = publisher.render_post_html(real_post, real_sections)
    
    if html_content:
        logger.info(f"Generated HTML length: {len(html_content)}")
        
        # Save HTML to file for inspection
        with open('api_payload_html.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info("HTML saved to 'api_payload_html.html'")
        
        # Generate the exact API parameters that would be sent
        # Mimic the create_or_update_post function logic
        is_update = bool(real_post.get('clan_post_id'))
        
        # Get the metadata that would be sent
        json_args = {
            'title': real_post.get('title', 'Untitled Post'),
            'url_key': publisher._generate_url_key(real_post),
            'short_content': real_post.get('summary', '')[:200] if real_post.get('summary') else 'No summary available',
            'status': 2,
            'categories': [14, 15],
            'list_thumbnail': '/blog/default-thumbnail.jpg',
            'post_thumbnail': '/blog/default-thumbnail.jpg',
            'meta_title': real_post.get('title', 'Untitled Post'),
            'meta_tags': publisher._generate_meta_tags(real_post),
            'meta_description': real_post.get('summary', '')[:160] if real_post.get('summary') else 'No description available'
        }
        
        if is_update and real_post.get('clan_post_id'):
            json_args['post_id'] = real_post['clan_post_id']
        
        logger.info("=== API PARAMETERS ===")
        for key, value in json_args.items():
            logger.info(f"{key}: {value}")
        
        # Save API parameters to file
        with open('api_payload_params.json', 'w', encoding='utf-8') as f:
            json.dump(json_args, f, indent=2, default=str)
        logger.info("API parameters saved to 'api_payload_params.json'")
        
        # Check for potential issues
        logger.info("=== POTENTIAL ISSUES CHECK ===")
        
        # Check HTML content for problematic patterns
        if '<p><p>' in html_content:
            logger.error("❌ Double <p> tags found in HTML!")
        else:
            logger.info("✅ No double <p> tags")
            
        if '</html>' in html_content:
            logger.error("❌ </html> tags found in HTML!")
        else:
            logger.info("✅ No </html> tags")
            
        if len(html_content) > 100000:  # Very large content
            logger.warning(f"⚠️ HTML content is very large: {len(html_content)} characters")
        else:
            logger.info(f"✅ HTML content size reasonable: {len(html_content)} characters")
            
        # Check for empty required fields
        empty_fields = [k for k, v in json_args.items() if not v]
        if empty_fields:
            logger.error(f"❌ Empty required fields: {empty_fields}")
        else:
            logger.info("✅ All required fields have values")
            
        # Check URL key format
        url_key = json_args.get('url_key', '')
        if not url_key or len(url_key) < 3:
            logger.error(f"❌ Invalid URL key: '{url_key}'")
        else:
            logger.info(f"✅ URL key looks valid: '{url_key}'")
            
        logger.info("=== DEBUG COMPLETE ===")
        logger.info("Check the generated files:")
        logger.info("- api_payload_html.html (the HTML content)")
        logger.info("- api_payload_params.json (the API parameters)")
        
    else:
        logger.error("❌ No HTML content generated")
        
except Exception as e:
    logger.error(f"❌ Debug failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
