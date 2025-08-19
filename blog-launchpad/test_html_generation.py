#!/usr/bin/env python3
"""
Test HTML generation to see what content is actually being created
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
    
    # Fix field mapping like the Flask endpoint does
    if real_post.get('post_id') and not real_post.get('id'):
        real_post['id'] = real_post['post_id']
    if not real_post.get('summary'):
        real_post['summary'] = real_post.get('intro_blurb', 'No summary available')
    if real_post.get('created_at') and not isinstance(real_post['created_at'], str):
        real_post['created_at'] = real_post['created_at'].isoformat() if hasattr(real_post['created_at'], 'isoformat') else str(real_post['created_at'])
    
    logger.info("=== REAL DATA ANALYSIS ===")
    logger.info(f"Post title: {real_post.get('title')}")
    logger.info(f"Post summary: {real_post.get('summary')}")
    logger.info(f"Number of sections: {len(real_sections) if real_sections else 0}")
    
    if real_sections:
        for i, section in enumerate(real_sections):
            logger.info(f"Section {i+1}:")
            logger.info(f"  Heading: {section.get('section_heading')}")
            logger.info(f"  Polished content length: {len(section.get('polished', ''))}")
            logger.info(f"  Draft content length: {len(section.get('draft', ''))}")
            logger.info(f"  Has image: {bool(section.get('image'))}")
    
    # Test HTML generation
    logger.info("\n=== TESTING HTML GENERATION ===")
    publisher = ClanPublisher()
    
    # Generate HTML
    html_content = publisher.render_post_html(real_post, real_sections)
    
    logger.info(f"Generated HTML length: {len(html_content)}")
    logger.info(f"HTML preview (first 500 chars):")
    logger.info(html_content[:500])
    
    # Check for key content
    logger.info("\n=== CONTENT ANALYSIS ===")
    
    if '<h1>' in html_content:
        logger.info("✅ H1 title found in HTML")
    else:
        logger.error("❌ H1 title missing from HTML")
    
    if 'section-text' in html_content:
        logger.info("✅ Section text divs found in HTML")
    else:
        logger.error("❌ Section text divs missing from HTML")
    
    if 'blog-sections' in html_content:
        logger.info("✅ Blog sections container found in HTML")
    else:
        logger.error("❌ Blog sections container missing from HTML")
    
    # Check for actual content text
    if real_post.get('summary') and real_post['summary'] in html_content:
        logger.info("✅ Post summary found in HTML")
    else:
        logger.error("❌ Post summary missing from HTML")
    
    if real_sections:
        for i, section in enumerate(real_sections):
            content = section.get('polished') or section.get('draft') or ''
            if content and content in html_content:
                logger.info(f"✅ Section {i+1} content found in HTML")
            else:
                logger.error(f"❌ Section {i+1} content missing from HTML")
    
    # Save HTML to file for inspection
    with open('generated_html_debug.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"\n✅ HTML saved to 'generated_html_debug.html' for inspection")
    
except Exception as e:
    logger.error(f"❌ Test failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")

