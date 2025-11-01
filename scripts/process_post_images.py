#!/usr/bin/env python3
"""
Process images for a blog post: optimization → watermarking → portrait generation.
This script triggers the full image processing pipeline for a specific post.
"""

import requests
import sys
import time
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager

def get_most_recent_post():
    """Get the most recent blog post."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, title 
            FROM post 
            WHERE status != 'deleted'
            ORDER BY id DESC 
            LIMIT 1
        """)
        post = cursor.fetchone()
        return post

def process_post_images(post_id):
    """Process all images for a post: optimize → watermark → portrait."""
    
    print(f"\n{'='*60}")
    print(f"Processing images for Post ID: {post_id}")
    print(f"{'='*60}\n")
    
    base_url = "http://localhost:5005"
    
    # Step 1: Optimize images
    print("Step 1: Optimizing images...")
    try:
        optimize_response = requests.post(
            f"{base_url}/api/optimize/rename/{post_id}",
            json={"settings": "webp_1200_85"},
            timeout=300
        )
        
        if optimize_response.status_code == 200:
            optimize_data = optimize_response.json()
            optimized_count = optimize_data.get('optimized_count', 0)
            print(f"✅ Optimized {optimized_count} images")
        else:
            print(f"⚠️  Optimization returned {optimize_response.status_code}: {optimize_response.text}")
            # Continue anyway - images might already be optimized
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to blog-images service (port 5005)")
        print("   Please ensure the service is running.")
        return False
    except Exception as e:
        print(f"⚠️  Optimization error (may already be done): {e}")
    
    time.sleep(1)
    
    # Step 2: Watermark images
    print("\nStep 2: Watermarking images...")
    try:
        watermark_response = requests.post(
            f"{base_url}/api/watermark/process/{post_id}",
            timeout=300
        )
        
        if watermark_response.status_code == 200:
            watermark_data = watermark_response.json()
            watermarked_count = watermark_data.get('watermarked_count', 0)
            print(f"✅ Watermarked {watermarked_count} images")
        else:
            print(f"⚠️  Watermarking returned {watermark_response.status_code}: {watermark_response.text}")
            # Continue anyway - images might already be watermarked
    except Exception as e:
        print(f"⚠️  Watermarking error (may already be done): {e}")
    
    time.sleep(1)
    
    # Step 3: Generate portrait versions
    print("\nStep 3: Generating portrait versions...")
    try:
        portrait_response = requests.post(
            f"{base_url}/api/portrait/generate-all/{post_id}",
            timeout=300
        )
        
        if portrait_response.status_code == 200:
            portrait_data = portrait_response.json()
            if portrait_data.get('success'):
                results = portrait_data.get('results', {})
                success_count = results.get('success_count', 0)
                failed_count = results.get('failed_count', 0)
                print(f"✅ Generated {success_count} portrait images")
                if failed_count > 0:
                    print(f"⚠️  {failed_count} portrait generations failed")
                    if results.get('header') and not results['header'].get('success'):
                        print(f"   - Header portrait: {results['header'].get('error')}")
                    for section in results.get('sections', []):
                        if not section.get('success'):
                            print(f"   - Section {section.get('section_id')}: {section.get('error')}")
            else:
                print(f"❌ Portrait generation failed: {portrait_data.get('error')}")
                return False
        else:
            print(f"❌ Portrait generation returned {portrait_response.status_code}: {portrait_response.text}")
            return False
    except Exception as e:
        print(f"❌ Portrait generation error: {e}")
        return False
    
    print(f"\n{'='*60}")
    print(f"✅ Image processing complete for Post ID: {post_id}")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            post_id = int(sys.argv[1])
        except ValueError:
            print("Error: Post ID must be a number")
            sys.exit(1)
    else:
        # Get most recent post
        post = get_most_recent_post()
        if not post:
            print("No posts found in database")
            sys.exit(1)
        post_id = post['id']
        print(f"Using most recent post: ID={post_id}, Title={post['title']}")
    
    success = process_post_images(post_id)
    sys.exit(0 if success else 1)

