#!/usr/bin/env python3
"""
Facebook Image Resize Script
Resizes all optimized images for a specific post to Facebook dimensions (1200x630)
"""

import os
import sys
from pathlib import Path
from PIL import Image
import argparse
from datetime import datetime

def resize_image_to_facebook(image_path, output_path, target_width=1200, target_height=630):
    """Resize image to Facebook dimensions while maintaining aspect ratio."""
    try:
        # Open image
        with Image.open(image_path) as img:
            print(f"   📏 Original size: {img.size[0]}x{img.size[1]}")
            
            # Calculate new dimensions maintaining aspect ratio
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Image is wider than target - fit to width
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # Image is taller than target - fit to height
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            print(f"   📐 Resizing to: {new_width}x{new_height}")
            
            # Resize image using high-quality LANCZOS resampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create a new image with target dimensions and white background
            final_img = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            
            # Calculate position to center the resized image
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            # Paste the resized image onto the white background
            final_img.paste(resized_img, (x_offset, y_offset))
            
            # Save the final image
            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                final_img.save(output_path, 'JPEG', quality=95, optimize=True)
            elif output_path.suffix.lower() == '.png':
                final_img.save(output_path, 'PNG', optimize=True)
            elif output_path.suffix.lower() == '.webp':
                final_img.save(output_path, 'WEBP', quality=95, method=6)
            else:
                final_img.save(output_path, optimize=True)
            
            print(f"   ✅ Saved: {output_path.name}")
            return True
            
    except Exception as e:
        print(f"   ❌ Error resizing {image_path.name}: {e}")
        return False

def process_post_images(post_id, base_path, dry_run=False):
    """Process all optimized images for a specific post."""
    print(f"🔍 Processing images for post {post_id}")
    print(f"📁 Base path: {base_path}")
    
    post_path = Path(base_path) / "posts" / str(post_id)
    if not post_path.exists():
        print(f"❌ Post directory does not exist: {post_path}")
        return
    
    # Find all section optimized directories
    section_dirs = []
    for section_dir in post_path.glob("sections/*"):
        if section_dir.is_dir():
            optimized_dir = section_dir / "optimized"
            if optimized_dir.exists() and optimized_dir.is_dir():
                section_dirs.append(optimized_dir)
                print(f"   📁 Found section optimized directory: {optimized_dir}")
    
    # Find header optimized directory
    header_optimized_dir = post_path / "header" / "optimized"
    if header_optimized_dir.exists() and header_optimized_dir.is_dir():
        section_dirs.append(header_optimized_dir)
        print(f"   📁 Found header optimized directory: {header_optimized_dir}")
    
    if not section_dirs:
        print("❌ No optimized directories found")
        return
    
    total_images = 0
    processed_images = 0
    failed_images = 0
    
    # Process each directory
    for optimized_dir in section_dirs:
        print(f"\n📂 Processing directory: {optimized_dir}")
        
        # Get all image files
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.gif', '*.bmp']:
            image_files.extend(optimized_dir.glob(ext))
        
        print(f"   Found {len(image_files)} images")
        
        if not image_files:
            continue
        
        # Create facebook directory
        facebook_dir = optimized_dir.parent / "facebook"
        if not dry_run:
            facebook_dir.mkdir(exist_ok=True)
            print(f"   📁 Created facebook directory: {facebook_dir}")
        
        total_images += len(image_files)
        
        # Process each image
        for image_path in image_files:
            if dry_run:
                print(f"   🔍 Would resize: {image_path.name} -> {facebook_dir}")
                processed_images += 1
            else:
                # Create output filename
                output_filename = f"{image_path.stem}_facebook{image_path.suffix}"
                output_path = facebook_dir / output_filename
                
                print(f"   🖼️  Resizing: {image_path.name}")
                success = resize_image_to_facebook(image_path, output_path)
                
                if success:
                    processed_images += 1
                else:
                    failed_images += 1
    
    # Summary
    print(f"\n📊 Resize Summary:")
    print(f"   Total images found: {total_images}")
    print(f"   Successfully processed: {processed_images}")
    print(f"   Failed: {failed_images}")
    
    if dry_run:
        print("🔍 This was a dry run - no files were modified")
    else:
        print("✅ Facebook resize complete!")

def main():
    parser = argparse.ArgumentParser(description='Resize blog images to Facebook dimensions (1200x630)')
    parser.add_argument('--post-id', type=int, required=True,
                       help='Post ID to process')
    parser.add_argument('--base-path', 
                       default='/Users/nickfiddes/Code/projects/blog/blog-images/static/content',
                       help='Base path for content directory')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without making changes')
    
    args = parser.parse_args()
    
    # Validate paths
    base_path = Path(args.base_path)
    if not base_path.exists():
        print(f"❌ Base path does not exist: {base_path}")
        sys.exit(1)
    
    print("🚀 Starting Facebook image resize...")
    print(f"📁 Base path: {base_path}")
    print(f"📝 Post ID: {args.post_id}")
    
    # Process images
    process_post_images(args.post_id, base_path, args.dry_run)

if __name__ == "__main__":
    main()




