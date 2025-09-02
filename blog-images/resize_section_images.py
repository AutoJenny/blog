#!/usr/bin/env python3
"""
Resize section images to Facebook dimensions (1200x630) in place.
ONLY modifies the 7 section images in the optimized directories.
"""

import os
from PIL import Image
import sys

def resize_image_to_facebook(image_path, target_width=1200, target_height=630):
    """Resize image to Facebook dimensions while maintaining aspect ratio."""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate aspect ratio
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Image is wider than target ratio - crop width
                new_height = target_height
                new_width = int(target_height * img_ratio)
                left = (new_width - target_width) // 2
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img = img.crop((left, 0, left + target_width, target_height))
            else:
                # Image is taller than target ratio - crop height
                new_width = target_width
                new_height = int(target_width / img_ratio)
                top = (new_height - target_height) // 2
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img = img.crop((0, top, target_width, top + target_height))
            
            # Save in place, overwriting the original
            img.save(image_path, quality=95, optimize=True)
            print(f"✅ Resized {image_path} to {target_width}x{target_height}")
            return True
            
    except Exception as e:
        print(f"❌ Error resizing {image_path}: {str(e)}")
        return False

def main():
    """Resize the 7 section images for post 53."""
    base_path = "/Users/nickfiddes/Code/projects/blog/blog-images/static/content/posts/53"
    
    # Define the 7 section images to resize
    section_images = [
        "sections/710/optimized/art-nouveau-mirror_109_1_processed.jpeg",
        "sections/711/optimized/generated_image_20250727_145859_processed.png", 
        "sections/712/optimized/712_processed.png",
        "sections/713/optimized/713_processed.png",
        "sections/714/optimized/714_processed.png",
        "sections/715/optimized/715_processed.png",
        "sections/716/optimized/716_processed.png"
    ]
    
    print("Resizing 7 section images to Facebook dimensions (1200x630)...")
    print("=" * 60)
    
    success_count = 0
    total_count = len(section_images)
    
    for image_path in section_images:
        full_path = os.path.join(base_path, image_path)
        if os.path.exists(full_path):
            if resize_image_to_facebook(full_path):
                success_count += 1
        else:
            print(f"❌ Image not found: {full_path}")
    
    print("=" * 60)
    print(f"Resize complete: {success_count}/{total_count} images processed successfully")
    
    if success_count == total_count:
        print("✅ All section images have been resized to Facebook dimensions")
        print("These images will now be uploaded to Clan.com at 1200x630")
    else:
        print("⚠️  Some images failed to resize")

if __name__ == "__main__":
    main()


