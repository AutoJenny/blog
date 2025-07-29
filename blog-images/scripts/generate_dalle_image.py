#!/usr/bin/env python3
"""
DALL-E Image Generation Script
Generates images using DALL-E 3 and saves them to the blog-images directory structure.
"""

import os
import sys
import argparse
import requests
import openai
from pathlib import Path
from datetime import datetime
import json

def setup_openai_client(api_key):
    """Initialize OpenAI client with API key."""
    try:
        client = openai.OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {str(e)}")
        return None

def generate_image(client, prompt, size="1792x1024"):
    """Generate image using DALL-E 3."""
    try:
        print(f"🎨 Generating image with prompt: {prompt[:100]}...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1
        )
        
        if response.data and response.data[0].url:
            image_url = response.data[0].url
            print(f"✅ Image generated successfully!")
            print(f"📸 Image URL: {image_url}")
            return image_url
        else:
            print("❌ No image URL in response")
            return None
            
    except Exception as e:
        print(f"❌ Image generation failed: {str(e)}")
        return None

def download_image(image_url, save_path):
    """Download image from URL and save to local path."""
    try:
        print(f"📥 Downloading image to: {save_path}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Save the image
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Image saved successfully to: {save_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download/save image: {str(e)}")
        return False

def save_metadata(post_id, section_id, prompt, image_path, metadata_path):
    """Save metadata about the generated image."""
    try:
        metadata = {
            "post_id": post_id,
            "section_id": section_id,
            "prompt": prompt,
            "image_path": image_path,
            "generated_at": datetime.now().isoformat(),
            "model": "dall-e-3",
            "size": "1792x1024"
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Metadata saved to: {metadata_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save metadata: {str(e)}")
        return False

def main():
    """Main function to handle image generation and saving."""
    parser = argparse.ArgumentParser(description='Generate DALL-E images for blog posts')
    parser.add_argument('--prompt', required=True, help='Image generation prompt')
    parser.add_argument('--post-id', required=True, type=int, help='Post ID')
    parser.add_argument('--section-id', required=True, type=int, help='Section ID')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_AUTH_TOKEN env var)')
    parser.add_argument('--size', default='1792x1024', help='Image size (default: 1792x1024)')
    parser.add_argument('--filename', help='Custom filename (without extension)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENAI_AUTH_TOKEN')
    if not api_key:
        print("❌ OpenAI API key required. Set OPENAI_AUTH_TOKEN environment variable or use --api-key")
        sys.exit(1)
    
    # Initialize OpenAI client
    client = setup_openai_client(api_key)
    if not client:
        sys.exit(1)
    
    # Generate image
    image_url = generate_image(client, args.prompt, args.size)
    if not image_url:
        sys.exit(1)
    
    # Set up file paths
    base_dir = Path("/Users/nickfiddes/Code/projects/blog/blog-images/static/content/posts")
    post_dir = base_dir / str(args.post_id) / "sections" / str(args.section_id) / "raw"
    
    # Create filename
    if args.filename:
        filename = f"{args.filename}.png"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dalle_generated_{timestamp}.png"
    
    image_path = post_dir / filename
    metadata_path = post_dir / f"{filename.replace('.png', '_metadata.json')}"
    
    # Download and save image
    if not download_image(image_url, str(image_path)):
        sys.exit(1)
    
    # Save metadata
    if not save_metadata(args.post_id, args.section_id, args.prompt, str(image_path), str(metadata_path)):
        print("⚠️  Image saved but metadata failed")
    
    print(f"\n🎉 Success! Image generated and saved:")
    print(f"📁 Directory: {post_dir}")
    print(f"🖼️  Image: {filename}")
    print(f"📄 Metadata: {filename.replace('.png', '_metadata.json')}")

if __name__ == "__main__":
    main()