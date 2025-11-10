#!/usr/bin/env python3
"""
Generate portrait versions ONLY for existing sections with landscape images.
Does not regenerate landscape versions.
"""

import sys
import os
import requests
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_manager

def get_sections_with_landscape_images(post_id):
    """Get sections that have landscape raw images."""
    sections_with_images = []
    
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, section_order, section_heading, image_prompts
            FROM post_section 
            WHERE post_id = %s 
            ORDER BY section_order
        """, (post_id,))
        sections = cursor.fetchall()
    
    for section in sections:
        section_id = section['id']
        landscape_raw = f"static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
        
        if os.path.exists(landscape_raw):
            # Extract image prompt
            image_prompts = section.get('image_prompts')
            if isinstance(image_prompts, str):
                try:
                    prompt_data = json.loads(image_prompts)
                    image_prompt = prompt_data.get('image_prompt', '') if isinstance(prompt_data, dict) else image_prompts
                except:
                    image_prompt = image_prompts
            elif isinstance(image_prompts, dict):
                image_prompt = image_prompts.get('image_prompt', '')
            else:
                image_prompt = str(image_prompts) if image_prompts else ''
            
            if image_prompt:
                sections_with_images.append({
                    'section_id': section_id,
                    'section_order': section['section_order'],
                    'section_heading': section['section_heading'],
                    'image_prompt': image_prompt,
                    'landscape_path': landscape_raw
                })
    
    return sections_with_images

def generate_portrait_for_section(post_id, section_id, image_prompt):
    """Generate portrait version only for a section using direct API call."""
    # Use the imaging API with portrait dimensions
    try:
        response = requests.post(
            f'http://localhost:5000/imaging/api/image-generation/posts/{post_id}/sections/{section_id}/generate-image',
            json={
                'model_name': 'dall-e-3',  # Default to DALL-E
                'parameters': {
                    'size': '1792x1024',  # This will generate landscape
                    'portrait_size': '1024x1792',  # And portrait
                    'quality': 'high',
                    'style': 'natural'
                }
            },
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            # The API now generates both, so check for portrait_path in response
            # But we need to check the actual implementation
            # Actually, let's call the function directly
            return {'success': True, 'method': 'api', 'data': data}
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Cannot connect to Flask app (port 5000). Trying direct function call...")
    except Exception as e:
        print(f"  ⚠️  API call failed: {e}")
    
    # Fallback: call function directly
    try:
        from blueprints.imaging_generators import imaging_generate_dalle_image
        
        result = imaging_generate_dalle_image(
            image_prompt, 
            post_id, 
            section_id,
            {
                'size': '1792x1024',  # Landscape (will be skipped if exists)
                'portrait_size': '1024x1792',  # Portrait
                'quality': 'hd',  # DALL-E 3 supports 'standard' or 'hd', not 'high'
                'style': 'natural'
            }
        )
        
        # Check if portrait was generated - verify file exists
        if result.get('success') and result.get('portrait_generated'):
            portrait_path = result.get('portrait_path')
            # Portrait path is a URL path like /static/content/posts/78/sections/1/portrait/raw/1_portrait.png
            if portrait_path:
                file_path = portrait_path.lstrip('/')  # Remove leading /
                if os.path.exists(file_path):
                    return {
                        'success': True,
                        'portrait_path': portrait_path,
                        'method': 'direct',
                        'file_path': file_path
                    }
                else:
                    return {'success': False, 'error': f'Portrait file not found at {file_path} (path returned but file missing)'}
            else:
                return {'success': False, 'error': 'portrait_generated=True but portrait_path is None'}
        elif not result.get('success'):
            return {'success': False, 'error': result.get('error', 'Generation failed')}
        else:
            return {'success': False, 'error': 'Portrait generation returned success but portrait_generated=False'}
    except Exception as e:
        print(f"  ⚠️  Direct function call failed: {e}")
    
    return {'success': False, 'error': 'All generation methods failed'}

def main():
    import sys
    if len(sys.argv) > 1:
        post_id = int(sys.argv[1])
    else:
        # Find most recent post with images
        post_id = None
        for pid in [78, 69, 81]:
            if os.path.exists(f"static/content/posts/{pid}/sections"):
                post_id = pid
                break
        if not post_id:
            print("No post found with sections/images")
            return
        print(f"Using post {post_id} (most recent with images)")
    
    print(f"\n{'='*60}")
    print(f"Generating portrait versions for Post ID: {post_id}")
    print(f"{'='*60}\n")
    
    # Get sections with landscape images
    sections = get_sections_with_landscape_images(post_id)
    
    if not sections:
        print(f"No sections found with landscape images for post {post_id}")
        return
    
    print(f"Found {len(sections)} sections with landscape images:\n")
    
    success_count = 0
    failed_count = 0
    
    for section in sections:
        section_id = section['section_id']
        print(f"Section {section['section_order']} (ID {section_id}): {section['section_heading']}")
        print(f"  Prompt: {section['image_prompt'][:60]}...")
        
        # Check if portrait raw already exists
        portrait_raw = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{section_id}_portrait.png"
        if os.path.exists(portrait_raw):
            print(f"  ⚠️  Portrait raw already exists, skipping generation")
            success_count += 1
            continue
        
        result = generate_portrait_for_section(
            post_id, section_id, section['image_prompt']
        )
        
        # Wait a moment for file to be written
        time.sleep(1)
        
        # Verify file actually exists
        portrait_raw_check = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{section_id}_portrait.png"
        file_exists = os.path.exists(portrait_raw_check)
        
        if result.get('success') and result.get('portrait_generated') and file_exists:
            portrait_path = result.get('portrait_path', result.get('file_path', portrait_raw_check))
            print(f"  ✅ Portrait generated: {portrait_path}")
            success_count += 1
        elif file_exists:
            # File exists even if result says otherwise
            print(f"  ✅ Portrait file exists: {portrait_raw_check}")
            success_count += 1
        else:
            error_msg = result.get('error', 'Unknown error')
            if not result.get('portrait_generated'):
                error_msg = 'Portrait generation returned False (API may have failed silently - check logs)'
            print(f"  ❌ Failed: {error_msg}")
            failed_count += 1
        
        # Small delay between API calls to avoid rate limits
        time.sleep(2)
        print()
    
    print(f"{'='*60}")
    print(f"Summary: {success_count} successful, {failed_count} failed")
    print(f"{'='*60}\n")
    
    if success_count > 0:
        print("Next step: Run optimization to process portrait images with watermarking")
        print("Visit: http://localhost:5000/imaging/posts/81/sections/optimise")

if __name__ == "__main__":
    main()

