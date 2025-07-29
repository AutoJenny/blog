#!/usr/bin/env python3
"""
Image Processing Script for Blog Images
Processes all images in the blog-images directory structure:
1. Optimizes to efficient web format
2. Adds watermark to bottom right
3. Adds 'AI-generated image' text to bottom left
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse
from datetime import datetime

def find_image_directories(base_path):
    """Find all raw image directories in the blog-images structure."""
    raw_dirs = []
    base_path = Path(base_path)
    
    # Look for pattern: posts/{post_id}/sections/{section_id}/raw/
    for post_dir in base_path.glob("posts/*"):
        if post_dir.is_dir():
            for section_dir in post_dir.glob("sections/*"):
                if section_dir.is_dir():
                    raw_dir = section_dir / "raw"
                    if raw_dir.exists() and raw_dir.is_dir():
                        raw_dirs.append(raw_dir)
    
    return raw_dirs

def get_supported_image_files(directory):
    """Get all supported image files in a directory."""
    supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    image_files = []
    
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            image_files.append(file_path)
    
    return image_files

def load_watermark(watermark_path):
    """Load the watermark image."""
    try:
        watermark = Image.open(watermark_path)
        return watermark
    except Exception as e:
        print(f"❌ Error loading watermark: {e}")
        return None

def get_font(size=20):
    """Get a font for text rendering."""
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
    except:
        try:
            # Fallback to default font
            font = ImageFont.load_default()
        except:
            # Last resort - no font
            font = None
    
    return font

def add_watermark(image, watermark, position='bottom-right'):
    """Add watermark to image with 0% transparency against 80% transparent background."""
    if watermark is None:
        return image
    
    # Resize watermark to reasonable size (max 200px width)
    watermark_width = min(200, image.width // 4)
    watermark_height = int(watermark.height * (watermark_width / watermark.width))
    watermark_resized = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
    
    # Create watermark with 0% transparency (fully visible)
    watermark_with_alpha = Image.new('RGBA', watermark_resized.size, (0, 0, 0, 0))
    watermark_with_alpha.paste(watermark_resized, (0, 0))
    
    # Keep watermark fully visible (no transparency applied)
    # watermark_alpha = watermark_with_alpha.split()[3]
    # watermark_alpha = watermark_alpha.point(lambda x: 0)  # Set alpha to 0 (completely transparent)
    # watermark_with_alpha.putalpha(watermark_alpha)
    
    # Calculate position with 10px margins
    margin = 10
    if position == 'bottom-right':
        x = image.width - watermark_width - margin
        y = image.height - watermark_height - margin
    else:
        x = margin
        y = image.height - watermark_height - margin
    
    # Create new image with alpha channel if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create grey background with 80% transparency (20% opacity)
    grey_bg = Image.new('RGBA', (watermark_width + 20, watermark_height + 20), (128, 128, 128, 51))  # Grey with 20% alpha (80% transparent)
    
    # Paste grey background first
    bg_x = x - 10
    bg_y = y - 10
    image.paste(grey_bg, (bg_x, bg_y), grey_bg)
    
    # Paste fully visible watermark
    image.paste(watermark_with_alpha, (x, y), watermark_with_alpha)
    
    return image

def add_ai_generated_text(image):
    """Add 'AI-generated image' text to bottom left."""
    draw = ImageDraw.Draw(image)
    font = get_font(16)
    
    text = "AI-generated image"
    text_color = (128, 128, 128, 180)  # Grey with transparency
    
    # Calculate text position (bottom left with padding)
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 8  # Approximate width
        text_height = 16
    
    x = 20
    y = image.height - text_height - 20
    
    # Draw text
    if font:
        draw.text((x, y), text, fill=text_color, font=font)
    else:
        # Fallback without font
        draw.text((x, y), text, fill=text_color)
    
    return image

def optimize_image(image, output_path):
    """Optimize image for web and save."""
    try:
        # Convert to RGB if saving as JPEG
        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            if image.mode in ('RGBA', 'LA'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
        
        # Save with optimization
        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            image.save(output_path, 'JPEG', quality=85, optimize=True)
        elif output_path.suffix.lower() == '.png':
            image.save(output_path, 'PNG', optimize=True)
        elif output_path.suffix.lower() == '.webp':
            image.save(output_path, 'WEBP', quality=85, method=6)
        else:
            image.save(output_path, optimize=True)
        
        return True
    except Exception as e:
        print(f"❌ Error saving image {output_path}: {e}")
        return False

def process_single_image(image_path, watermark, output_dir):
    """Process a single image with watermark and optimization."""
    try:
        print(f"🖼️  Processing: {image_path.name}")
        
        # Load image
        image = Image.open(image_path)
        
        # Add watermark
        image = add_watermark(image, watermark, 'bottom-right')
        
        # Add AI-generated text
        image = add_ai_generated_text(image)
        
        # Create output filename
        stem = image_path.stem
        if not stem.endswith('_processed'):
            output_filename = f"{stem}_processed{image_path.suffix}"
        else:
            output_filename = f"{stem}{image_path.suffix}"
        
        output_path = output_dir / output_filename
        
        # Optimize and save
        success = optimize_image(image, output_path)
        
        if success:
            print(f"✅ Saved: {output_filename}")
            return True
        else:
            print(f"❌ Failed to save: {output_filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {image_path.name}: {e}")
        return False

def process_all_images(base_path, watermark_path, dry_run=False, post_id=None):
    """Process all images in the blog-images directory structure."""
    print(f"🔍 Scanning for images in: {base_path}")
    
    # Load watermark
    watermark = load_watermark(watermark_path)
    if watermark is None:
        print("⚠️  Warning: Could not load watermark, proceeding without it")
    
    # Find all raw directories
    if post_id:
        # Process specific post only
        post_path = Path(base_path) / "posts" / str(post_id)
        if not post_path.exists():
            print(f"❌ Post directory does not exist: {post_path}")
            return
        
        raw_dirs = []
        for section_dir in post_path.glob("sections/*"):
            if section_dir.is_dir():
                raw_dir = section_dir / "raw"
                if raw_dir.exists() and raw_dir.is_dir():
                    raw_dirs.append(raw_dir)
        
        print(f"📁 Found {len(raw_dirs)} raw directories for post {post_id}")
    else:
        # Process all posts
        raw_dirs = find_image_directories(base_path)
        print(f"📁 Found {len(raw_dirs)} raw directories")
    
    if dry_run:
        print("🔍 DRY RUN - No files will be modified")
    
    total_images = 0
    processed_images = 0
    failed_images = 0
    
    # Process each directory
    for raw_dir in raw_dirs:
        print(f"\n📂 Processing directory: {raw_dir}")
        
        # Get image files
        image_files = get_supported_image_files(raw_dir)
        print(f"   Found {len(image_files)} images")
        
        if not image_files:
            continue
        
        # Create optimized directory
        optimized_dir = raw_dir.parent / "optimized"
        if not dry_run:
            optimized_dir.mkdir(exist_ok=True)
            print(f"   📁 Created optimized directory: {optimized_dir}")
        
        total_images += len(image_files)
        
        # Process each image
        for image_path in image_files:
            if dry_run:
                print(f"   🔍 Would process: {image_path.name} -> {optimized_dir}")
                processed_images += 1
            else:
                success = process_single_image(image_path, watermark, optimized_dir)
                if success:
                    processed_images += 1
                else:
                    failed_images += 1
    
    # Summary
    print(f"\n📊 Processing Summary:")
    print(f"   Total images found: {total_images}")
    print(f"   Successfully processed: {processed_images}")
    print(f"   Failed: {failed_images}")
    
    if dry_run:
        print("🔍 This was a dry run - no files were modified")
    else:
        print("✅ Processing complete!")

def main():
    parser = argparse.ArgumentParser(description='Process blog images with watermark and optimization')
    parser.add_argument('--base-path', 
                       default='/Users/nickfiddes/Code/projects/blog/blog-images/static/content',
                       help='Base path for content directory')
    parser.add_argument('--watermark-path',
                       default='/Users/nickfiddes/Code/projects/blog/blog-images/static/images/site/clan-watermark.png',
                       help='Path to watermark image')
    parser.add_argument('--post-id', type=int,
                       help='Process only a specific post ID')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without making changes')
    
    args = parser.parse_args()
    
    # Validate paths
    base_path = Path(args.base_path)
    watermark_path = Path(args.watermark_path)
    
    if not base_path.exists():
        print(f"❌ Base path does not exist: {base_path}")
        sys.exit(1)
    
    if not watermark_path.exists():
        print(f"❌ Watermark path does not exist: {watermark_path}")
        sys.exit(1)
    
    print("🚀 Starting image processing...")
    print(f"📁 Base path: {base_path}")
    print(f"🖼️  Watermark: {watermark_path}")
    if args.post_id:
        print(f"📝 Post ID: {args.post_id}")
    
    # Process images
    process_all_images(base_path, watermark_path, args.dry_run, args.post_id)

if __name__ == "__main__":
    main()