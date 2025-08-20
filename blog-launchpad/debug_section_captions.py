#!/usr/bin/env python3
"""
Debug script to test section image caption rendering
"""

from clan_publisher import ClanPublisher
from app import get_post_with_development, get_post_sections_with_images

def debug_section_captions():
    """Debug why section image captions are not appearing"""
    
    # Test with post 53
    post = get_post_with_development(53)
    sections = get_post_sections_with_images(53)
    
    if not post or not sections:
        print("Failed to get post data")
        return
    
    print(f"Post ID: {post['id']}")
    print(f"Number of sections: {len(sections)}")
    
    publisher = ClanPublisher()
    
    # Process images first
    print("\n=== PROCESSING IMAGES ===")
    uploaded_images = publisher.process_images(post, sections)
    print(f"Uploaded images count: {len(uploaded_images)}")
    
    # Test section image rendering step by step
    print("\n=== TESTING SECTION IMAGE RENDERING ===")
    
    for i, section in enumerate(sections):
        print(f"\n--- Section {i+1} ---")
        
        if section.get('image'):
            img = section['image']
            print(f"Image path: {img.get('path')}")
            print(f"Image caption: {img.get('caption')}")
            print(f"Image alt_text: {img.get('alt_text')}")
            
            # Check if this image path exists in uploaded_images
            if img.get('path') in uploaded_images:
                clan_url = uploaded_images[img.get('path')]
                print(f"✅ Found in uploaded_images: {clan_url}")
                
                # Test the safe_url function
                safe_path = publisher._safe_url_test(img['path'], uploaded_images)
                print(f"safe_url result: {safe_path}")
                
                # Test caption rendering
                if img.get('caption'):
                    caption_html = f'<figcaption>{publisher._safe_html_test(img["caption"])}</figcaption>'
                    print(f"Caption HTML: {caption_html}")
                else:
                    print("❌ No caption found in image data")
            else:
                print(f"❌ Image path NOT found in uploaded_images")
                print(f"Available keys: {list(uploaded_images.keys())}")
        else:
            print("No image data")
    
    # Test full HTML rendering
    print("\n=== TESTING FULL HTML RENDERING ===")
    html_content = publisher.render_post_html(post, sections, uploaded_images)
    
    if html_content:
        print(f"HTML length: {len(html_content)}")
        
        # Check for section images and captions
        if 'section-image' in html_content:
            print("✅ Section images found in HTML")
            
            # Count figcaption tags
            figcaption_count = html_content.count('<figcaption>')
            print(f"Figcaption count: {figcaption_count}")
            
            # Show a sample section image
            import re
            section_matches = re.findall(r'<figure class="section-image">.*?</figure>', html_content, re.DOTALL)
            if section_matches:
                print(f"\nFound {len(section_matches)} section image figures")
                for i, match in enumerate(section_matches[:2]):
                    print(f"\nSection image {i+1}:")
                    print(match)
            else:
                print("❌ No section image figures found")
        else:
            print("❌ No section images found in HTML")
    else:
        print("HTML rendering failed")

if __name__ == "__main__":
    debug_section_captions()
