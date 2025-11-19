"""
Image Optimization Functions
Watermarking, text overlay, and image optimization utilities
"""

import os
import logging
import concurrent.futures
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def _process_single_image_optimization(raw_image_path, optimized_image_path, watermark_path,
                                       watermark_enabled, text_overlay_enabled, overlay_text,
                                       text_size, watermark_margin, bg_opacity, quality):
    """Helper function to process a single image (landscape or portrait)"""
    # Check if raw image exists
    if not os.path.exists(raw_image_path):
        return {'success': False, 'error': f'Raw image not found: {raw_image_path}'}
    
    # Create optimized directory
    os.makedirs(os.path.dirname(optimized_image_path), exist_ok=True)
    
    # Load image
    image = Image.open(raw_image_path)
    
    # Convert to RGBA if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Add watermark if enabled
    if watermark_enabled:
        if not os.path.exists(watermark_path):
            return {'success': False, 'error': f'Watermark not found: {watermark_path}'}
        
        watermark = Image.open(watermark_path)
        
        # Add watermark (bottom-right)
        watermark_width = min(200, image.width // 4)
        watermark_height = int(watermark.height * (watermark_width / watermark.width))
        watermark_resized = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
        
        # Create watermark with alpha
        watermark_with_alpha = Image.new('RGBA', watermark_resized.size, (0, 0, 0, 0))
        watermark_with_alpha.paste(watermark_resized, (0, 0))
        
        # For portrait images, apply reduced opacity (60% for Instagram)
        is_portrait = 'portrait' in raw_image_path
        if is_portrait:
            alpha = watermark_with_alpha.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.6))  # 60% opacity
            watermark_with_alpha.putalpha(alpha)
        
        # Calculate position (bottom-right with margin)
        x = image.width - watermark_width - watermark_margin
        y = image.height - watermark_height - watermark_margin
        
        # Create grey background with specified opacity
        opacity_value = int(255 * (bg_opacity / 100))
        grey_bg = Image.new('RGBA', (watermark_width + 20, watermark_height + 20), (128, 128, 128, opacity_value))
        
        # Paste grey background first
        bg_x = x - 10
        bg_y = y - 10
        image.paste(grey_bg, (bg_x, bg_y), grey_bg)
        
        # Paste watermark
        image.paste(watermark_with_alpha, (x, y), watermark_with_alpha)
    
    # Add AI-generated text if enabled
    if text_overlay_enabled:
        draw = ImageDraw.Draw(image)
        
        # Try to get font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", text_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        text_color = (128, 128, 128, 180)  # Grey with transparency
        
        # Calculate text position (bottom-left with 20px padding)
        if font:
            bbox = draw.textbbox((0, 0), overlay_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(overlay_text) * 8  # Approximate width
            text_height = text_size
        
        text_x = 20
        text_y = image.height - text_height - 20
        
        # Draw text
        if font:
            draw.text((text_x, text_y), overlay_text, fill=text_color, font=font)
        else:
            draw.text((text_x, text_y), overlay_text, fill=text_color)
    
    # Convert to RGB for JPG saving
    if image.mode == 'RGBA':
        # Create white background
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
        image = rgb_image
    
    # Save as JPG with specified quality
    # For portrait, optimize to keep under 1MB
    saved_quality = quality
    image.save(optimized_image_path, 'JPEG', quality=saved_quality, optimize=True)
    
    # Check file size for portrait images (must be <= 1MB for Instagram)
    is_portrait = 'portrait' in optimized_image_path
    if is_portrait:
        file_size = os.path.getsize(optimized_image_path)
        max_size = 1024 * 1024  # 1MB
        if file_size > max_size:
            for q in range(quality - 5, 50, -5):
                image.save(optimized_image_path, 'JPEG', quality=q, optimize=True)
                if os.path.getsize(optimized_image_path) <= max_size:
                    saved_quality = q
                    break
    
    # Verify the optimized image file was actually created
    if not os.path.exists(optimized_image_path):
        return {'success': False, 'error': f'Failed to create optimized image: {optimized_image_path}'}
    
    return {'success': True, 'optimized_path': optimized_image_path}


def optimize_image_with_watermark(post_id, section_id, params=None):
    """Optimize image with watermark and AI caption - processes both landscape and portrait in parallel"""
    try:
        # Default parameters
        if params is None:
            params = {}
            
        quality = params.get('quality', 50)
        overlay_text = params.get('overlay_text', 'AI-generated image')
        text_size = params.get('text_size', 16)
        watermark_enabled = params.get('watermark', True)
        text_overlay_enabled = params.get('text_overlay', True)
        watermark_margin = params.get('watermark_margin', 10)
        bg_opacity = params.get('bg_opacity', 20)
        
        watermark_path = "static/images/site/clan-watermark.png"
        
        # Determine paths for landscape and portrait
        if section_id == 'header':
            landscape_raw = f"static/content/posts/{post_id}/header/landscape/raw/header.png"
            landscape_optimized = f"static/content/posts/{post_id}/header/optimized/header.jpg"
            portrait_raw = f"static/content/posts/{post_id}/header/portrait/raw/header_portrait.png"
            portrait_optimized = f"static/content/posts/{post_id}/header/portrait/optimized/header_portrait.jpg"
        else:
            landscape_raw = f"static/content/posts/{post_id}/sections/{section_id}/landscape/raw/{section_id}.png"
            landscape_optimized = f"static/content/posts/{post_id}/sections/{section_id}/optimized/{section_id}.jpg"
            portrait_raw = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{section_id}_portrait.png"
            portrait_optimized = f"static/content/posts/{post_id}/sections/{section_id}/portrait/optimized/{section_id}_portrait.jpg"
        
        # Check if landscape raw exists (required)
        if not os.path.exists(landscape_raw):
            return {'success': False, 'error': f'Landscape raw image not found: {landscape_raw}'}
        
        # Process both images in parallel
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit landscape processing
            landscape_future = executor.submit(
                _process_single_image_optimization,
                landscape_raw, landscape_optimized, watermark_path,
                watermark_enabled, text_overlay_enabled, overlay_text,
                text_size, watermark_margin, bg_opacity, quality
            )
            
            # Submit portrait processing (if raw exists)
            portrait_future = None
            portrait_exists = os.path.exists(portrait_raw)
            if portrait_exists:
                portrait_future = executor.submit(
                    _process_single_image_optimization,
                    portrait_raw, portrait_optimized, watermark_path,
                    watermark_enabled, text_overlay_enabled, overlay_text,
                    text_size, watermark_margin, bg_opacity, quality
                )
            
            # Get landscape result
            landscape_result = landscape_future.result()
            results['landscape'] = landscape_result
            
            # Get portrait result if it was processed
            if portrait_future:
                portrait_result = portrait_future.result()
                results['portrait'] = portrait_result
            else:
                results['portrait'] = {'success': False, 'error': 'Portrait raw image not found'}
        
        # Build response
        if results['landscape']['success']:
            response = {
                'success': True,
                'optimized_path': f"/{landscape_optimized}",
                'message': 'Landscape image optimized successfully'
            }
            if results['portrait']['success']:
                response['portrait_path'] = f"/{portrait_optimized}"
                response['message'] = 'Landscape and portrait images optimized successfully'
            return response
        else:
            return {
                'success': False,
                'error': results['landscape'].get('error', 'Landscape optimization failed')
            }
        
    except Exception as e:
        logger.error(f"Error optimizing image: {str(e)}")
        return {'success': False, 'error': str(e)}

