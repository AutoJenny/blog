#!/usr/bin/env python3
"""
Test script to isolate the publishing issue by testing each component separately
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clan_publisher import ClanPublisher
from app import get_post_with_development, get_post_sections_with_images

def test_database_queries():
    """Test database queries to see if they're hanging"""
    print("Testing database queries...")
    try:
        post = get_post_with_development(53)
        print(f"✅ Post query successful: {post.get('id')} - {post.get('title')}")
        
        sections = get_post_sections_with_images(53)
        print(f"✅ Sections query successful: {len(sections)} sections")
        
        return post, sections
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return None, None

def test_image_finding():
    """Test image finding functions"""
    print("\nTesting image finding functions...")
    try:
        from app import find_header_image, find_section_image
        
        header_path = find_header_image(53)
        print(f"✅ Header image found: {header_path}")
        
        sections = get_post_sections_with_images(53)
        for i, section in enumerate(sections[:2]):  # Test first 2 sections
            section_path = find_section_image(53, section['id'])
            print(f"✅ Section {i+1} image found: {section_path}")
            
        return True
    except Exception as e:
        print(f"❌ Image finding failed: {e}")
        return False

def test_clan_publisher_instantiation():
    """Test if ClanPublisher can be instantiated"""
    print("\nTesting ClanPublisher instantiation...")
    try:
        publisher = ClanPublisher()
        print("✅ ClanPublisher instantiated successfully")
        return publisher
    except Exception as e:
        print(f"❌ ClanPublisher instantiation failed: {e}")
        return None

def test_image_processing(publisher, post, sections):
    """Test image processing step"""
    print("\nTesting image processing...")
    try:
        uploaded_images = publisher.process_images(post, sections)
        print(f"✅ Image processing successful: {len(uploaded_images)} images uploaded")
        print(f"Uploaded images: {uploaded_images}")
        return uploaded_images
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_html_rendering(publisher, post, sections, uploaded_images):
    """Test HTML rendering step"""
    print("\nTesting HTML rendering...")
    try:
        html_content = publisher.render_post_html(post, sections, uploaded_images)
        if html_content:
            print(f"✅ HTML rendering successful: {len(html_content)} characters")
            print(f"First 200 chars: {html_content[:200]}...")
            return html_content
        else:
            print("❌ HTML rendering returned None")
            return None
    except Exception as e:
        print(f"❌ HTML rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests"""
    print("=== ISOLATED PUBLISHING TEST ===")
    
    # Test 1: Database queries
    post, sections = test_database_queries()
    if not post or not sections:
        print("❌ Cannot proceed without database data")
        return
    
    # Test 2: Image finding
    if not test_image_finding():
        print("❌ Cannot proceed without image finding")
        return
    
    # Test 3: ClanPublisher instantiation
    publisher = test_clan_publisher_instantiation()
    if not publisher:
        print("❌ Cannot proceed without ClanPublisher")
        return
    
    # Test 4: Image processing
    uploaded_images = test_image_processing(publisher, post, sections)
    if uploaded_images is None:
        print("❌ Cannot proceed without image processing")
        return
    
    # Test 5: HTML rendering
    html_content = test_html_rendering(publisher, post, sections, uploaded_images)
    if not html_content:
        print("❌ Cannot proceed without HTML rendering")
        return
    
    print("\n✅ All tests passed! The issue is likely in the final API call")
    print("Ready to test create_or_update_post...")

if __name__ == "__main__":
    main()
