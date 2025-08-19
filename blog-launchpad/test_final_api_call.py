#!/usr/bin/env python3
"""
Test script to test just the final create_or_update_post API call
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clan_publisher import ClanPublisher
from app import get_post_with_development, get_post_sections_with_images

def test_final_api_call():
    """Test the final create_or_update_post API call"""
    print("=== TESTING FINAL API CALL ===")
    
    try:
        # Get post and sections
        post = get_post_with_development(53)
        sections = get_post_sections_with_images(53)
        print(f"✅ Got post: {post.get('id')} - {post.get('title')}")
        print(f"✅ Got {len(sections)} sections")
        
        # Create publisher
        publisher = ClanPublisher()
        print("✅ Created ClanPublisher")
        
        # Process images (we know this works now)
        print("\n📸 Processing images...")
        uploaded_images = publisher.process_images(post, sections)
        print(f"✅ Uploaded {len(uploaded_images)} images")
        
        # Render HTML (we know this works now)
        print("\n📝 Rendering HTML...")
        html_content = publisher.render_post_html(post, sections, uploaded_images)
        print(f"✅ HTML rendered: {len(html_content)} characters")
        
        # Test the final API call
        print("\n🚀 Testing final API call...")
        print(f"Post has clan_post_id: {post.get('clan_post_id')}")
        is_update = bool(post.get('clan_post_id'))
        print(f"Is update: {is_update}")
        
        # Call create_or_update_post
        result = publisher.create_or_update_post(post, html_content, is_update, uploaded_images)
        
        print(f"\n📊 API Call Result:")
        print(f"Success: {result.get('success')}")
        print(f"Error: {result.get('error')}")
        print(f"Full result: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_final_api_call()
