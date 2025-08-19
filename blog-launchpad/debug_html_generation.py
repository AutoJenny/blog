#!/usr/bin/env python3
"""
Debug HTML generation step by step to find why safe_html isn't working
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
    
    logger.info("=== TESTING SAFE_HTML FUNCTION DIRECTLY ===")
    
    # Test the safe_html function directly with real content
    publisher = ClanPublisher()
    
    # Get the safe_html function from the instance
    safe_html_func = None
    for attr_name in dir(publisher):
        if attr_name == 'render_post_html':
            # Get the function object
            render_func = getattr(publisher, attr_name)
            # Extract the safe_html function from the closure
            import inspect
            if hasattr(render_func, '__code__'):
                logger.info("Found render_post_html function")
                # We need to access the inner function differently
                break
    
    # Test with actual section content
    if real_sections:
        logger.info(f"Testing with {len(real_sections)} sections")
        
        for i, section in enumerate(real_sections[:2]):  # Test first 2 sections
            logger.info(f"\n--- Section {i+1}: {section.get('section_heading')} ---")
            
            content = section.get('polished') or section.get('draft') or ''
            if content:
                logger.info(f"Original content length: {len(content)}")
                logger.info(f"Original content preview: {content[:200]}...")
                
                # Test the safe_html function from the instance
                try:
                    # Call render_post_html and capture the HTML
                    html_content = publisher.render_post_html(real_post, [section])
                    
                    if html_content:
                        logger.info(f"Generated HTML length: {len(html_content)}")
                        
                        # Look for the section content in the generated HTML
                        if 'section-text' in html_content:
                            # Extract the section-text div
                            import re
                            section_match = re.search(r'<div class="section-text">(.*?)</div>', html_content, re.DOTALL)
                            if section_match:
                                section_html = section_match.group(1)
                                logger.info(f"Section HTML found: {section_html[:200]}...")
                                
                                # Check for double <p> tags
                                if '<p><p>' in section_html:
                                    logger.error("❌ Double <p> tags still present!")
                                else:
                                    logger.info("✅ No double <p> tags found")
                                
                                # Check for </html> tags
                                if '</html>' in section_html:
                                    logger.error("❌ </html> tags still present!")
                                else:
                                    logger.info("✅ No </html> tags found")
                            else:
                                logger.error("❌ section-text div not found in HTML")
                        else:
                            logger.error("❌ section-text class not found in HTML")
                    else:
                        logger.error("❌ No HTML content generated")
                        
                except Exception as e:
                    logger.error(f"❌ Error testing section {i+1}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
    
    logger.info("\n=== DEBUG COMPLETE ===")
    
except Exception as e:
    logger.error(f"❌ Debug failed with error: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
