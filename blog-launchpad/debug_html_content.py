#!/usr/bin/env python3
"""
Debug script to see what HTML content is actually being generated.
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_html_generation():
    """Test HTML generation to see what's actually being created"""
    try:
        from app import get_post_with_development, get_post_sections_with_images
        from clan_publisher import ClanPublisher
        
        # Test with post ID 53
        post_id = 53
        logger.info(f"Testing HTML generation for post ID: {post_id}")
        
        # Get post data
        post_data = get_post_with_development(post_id)
        sections = get_post_sections_with_images(post_id)
        
        if not post_data or not sections:
            logger.error("Could not get post data or sections")
            return
        
        # Create publisher instance
        publisher = ClanPublisher()
        
        # Test HTML generation directly
        logger.info("Testing HTML generation...")
        html_content = publisher.render_post_html(post_data, sections)
        
        if html_content:
            logger.info(f"✅ HTML generation successful. Content length: {len(html_content)}")
            logger.info("=== HTML CONTENT PREVIEW ===")
            logger.info(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
            logger.info("=== END HTML PREVIEW ===")
            
            # Save to file for inspection
            with open("debug_generated_html.html", "w") as f:
                f.write(html_content)
            logger.info("✅ Full HTML saved to debug_generated_html.html")
            
        else:
            logger.error("❌ HTML generation failed")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_html_generation()

