# Imaging Blueprint - Standalone image generation workflow
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config.database import db_manager
import logging
import json
import os
import requests

# Import the same sections API function used by authoring
from blueprints.authoring_api_sections import api_get_sections as sections_api_func

logger = logging.getLogger(__name__)

def imaging_generate_dalle_image(image_prompt, post_id, section_id, parameters):
    """Generate image using DALL-E API - generates both landscape and portrait versions"""
    try:
        # Load OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not found in environment'}
        
        # Extract parameters
        landscape_size = parameters.get('size', '1792x1024')  # Default landscape
        quality = parameters.get('quality', 'hd')  # DALL-E 3: 'standard' or 'hd'
        style = parameters.get('style', 'natural')
        portrait_size = parameters.get('portrait_size', '1024x1792')  # Default portrait
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Create directory structure
        if section_id == 'header':
            landscape_dir = f"static/content/posts/{post_id}/header/raw"
            portrait_dir = f"static/content/posts/{post_id}/header/portrait/raw"
            landscape_filename = "header.png"
            portrait_filename = "header_portrait.png"
        else:
            landscape_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            portrait_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
            landscape_filename = f"{section_id}.png"
            portrait_filename = f"{section_id}_portrait.png"
        
        os.makedirs(landscape_dir, exist_ok=True)
        os.makedirs(portrait_dir, exist_ok=True)
        
        landscape_path = f"{landscape_dir}/{landscape_filename}"
        landscape_exists = os.path.exists(landscape_path)
        
        # Generate landscape version only if it doesn't exist
        if not landscape_exists:
            landscape_data = {
                'model': 'dall-e-3',
                'prompt': image_prompt,
                'n': 1,
                'size': landscape_size,
                'quality': quality,
                'style': style
            }
            
            logger.info(f"DALL-E landscape API request: {landscape_data}")
            landscape_response = requests.post('https://api.openai.com/v1/images/generations', 
                                   headers=headers, json=landscape_data, timeout=120)
            
            if landscape_response.status_code != 200:
                return {'success': False, 'error': f'DALL-E landscape API error: {landscape_response.status_code} - {landscape_response.text}'}
            
            landscape_result = landscape_response.json()
            if 'data' not in landscape_result or not landscape_result['data']:
                return {'success': False, 'error': 'No image data returned from DALL-E landscape'}
            
            # Download landscape image
            landscape_url = landscape_result['data'][0]['url']
            landscape_image_response = requests.get(landscape_url, timeout=30)
            if landscape_image_response.status_code != 200:
                return {'success': False, 'error': f'Failed to download landscape image: {landscape_image_response.status_code}'}
            
            with open(landscape_path, 'wb') as f:
                f.write(landscape_image_response.content)
            logger.info(f"Generated landscape image: {landscape_path}")
        else:
            logger.info(f"Landscape image already exists, skipping generation: {landscape_path}")
        
        # Generate portrait version with same prompt but portrait dimensions
        portrait_data = {
            'model': 'dall-e-3',
            'prompt': image_prompt,
            'n': 1,
            'size': portrait_size,
            'quality': quality,
            'style': style
        }
        
        logger.info(f"DALL-E portrait API request: {portrait_data}")
        portrait_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=portrait_data, timeout=120)
        
        portrait_success = False
        portrait_path = None
        if portrait_response.status_code == 200:
            portrait_result = portrait_response.json()
            if 'data' in portrait_result and portrait_result['data']:
                # Download portrait image
                portrait_url = portrait_result['data'][0]['url']
                portrait_image_response = requests.get(portrait_url, timeout=30)
                if portrait_image_response.status_code == 200:
                    portrait_path = f"{portrait_dir}/{portrait_filename}"
                    with open(portrait_path, 'wb') as f:
                        f.write(portrait_image_response.content)
                    portrait_success = True
                    logger.info(f"Successfully generated portrait: {portrait_path}")
                else:
                    error_msg = f"Failed to download portrait image: {portrait_image_response.status_code}"
                    logger.warning(error_msg)
                    print(f"ERROR: {error_msg}")  # Also print for script visibility
            else:
                error_msg = "No image data returned from DALL-E portrait"
                logger.warning(error_msg)
                print(f"ERROR: {error_msg}")
        else:
            error_msg = f"DALL-E portrait API error: {portrait_response.status_code} - {portrait_response.text}"
            logger.warning(error_msg)
            print(f"ERROR: {error_msg}")  # Print for visibility when called from script
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{landscape_filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{landscape_filename}",
            'local_path': landscape_path,
            'portrait_generated': portrait_success,
            'portrait_path': f"/static/content/posts/{post_id}/header/portrait/raw/{portrait_filename}" if section_id == 'header' and portrait_success else (f"/static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{portrait_filename}" if portrait_success else None)
        }
        
    except Exception as e:
        logger.error(f"DALL-E generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

def imaging_generate_gpt_image_1(image_prompt, post_id, section_id, parameters):
    """Generate image using GPT-Image-1 API - generates both landscape and portrait versions"""
    try:
        # Load OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not found in environment'}
        
        # Extract parameters with proper type coercion
        landscape_size = parameters.get('size', '1024x1024')  # Default landscape
        portrait_size = parameters.get('portrait_size', '1024x1792')  # Default portrait
        quality = parameters.get('quality', 'high')
        # Coerce n to int; API requires integer
        try:
            n = int(parameters.get('n', 1))
        except (ValueError, TypeError):
            n = 1
        # Optional parameters
        seed_raw = parameters.get('seed')
        try:
            seed = int(seed_raw) if seed_raw is not None and str(seed_raw).strip() != '' else None
        except (ValueError, TypeError):
            seed = None
        background = parameters.get('background')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Create directory structure
        if section_id == 'header':
            landscape_dir = f"static/content/posts/{post_id}/header/raw"
            portrait_dir = f"static/content/posts/{post_id}/header/portrait/raw"
            landscape_filename = "header.png"
            portrait_filename = "header_portrait.png"
        else:
            landscape_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            portrait_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
            landscape_filename = f"{section_id}.png"
            portrait_filename = f"{section_id}_portrait.png"
        
        os.makedirs(landscape_dir, exist_ok=True)
        os.makedirs(portrait_dir, exist_ok=True)
        
        # Generate landscape version
        landscape_data = {
            'model': 'gpt-image-1',
            'prompt': image_prompt,
            'size': landscape_size,
            'n': n,
            'quality': quality
        }
        if seed is not None:
            landscape_data['seed'] = seed
        if background:
            landscape_data['background'] = background
        
        logger.info(f"GPT-Image-1 landscape API request: {landscape_data}")
        landscape_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=landscape_data, timeout=120)
        
        if landscape_response.status_code != 200:
            logger.error(f"GPT-Image-1 landscape API error: {landscape_response.text}")
            return {'success': False, 'error': f'GPT-Image-1 landscape API error: {landscape_response.status_code} - {landscape_response.text}'}
        
        landscape_result = landscape_response.json()
        logger.info(f"GPT-Image-1 landscape API response: {landscape_result}")
        
        if 'data' not in landscape_result or not landscape_result['data']:
            return {'success': False, 'error': 'No image data returned from GPT-Image-1 landscape'}
        
        # Handle landscape image data
        landscape_image_data = landscape_result['data'][0]
        if 'url' in landscape_image_data:
            landscape_image_url = landscape_image_data['url']
            landscape_image_response = requests.get(landscape_image_url, timeout=30)
            if landscape_image_response.status_code != 200:
                return {'success': False, 'error': f'Failed to download landscape image: {landscape_image_response.status_code}'}
            landscape_image_content = landscape_image_response.content
        elif 'b64_json' in landscape_image_data:
            import base64
            landscape_image_content = base64.b64decode(landscape_image_data['b64_json'])
        else:
            return {'success': False, 'error': 'No valid landscape image data found in GPT-Image-1 response'}
        
        landscape_path = f"{landscape_dir}/{landscape_filename}"
        with open(landscape_path, 'wb') as f:
            f.write(landscape_image_content)
        
        # Generate portrait version
        portrait_data = {
            'model': 'gpt-image-1',
            'prompt': image_prompt,
            'size': portrait_size,
            'n': n,
            'quality': quality
        }
        if seed is not None:
            portrait_data['seed'] = seed
        if background:
            portrait_data['background'] = background
        
        logger.info(f"GPT-Image-1 portrait API request: {portrait_data}")
        portrait_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=portrait_data, timeout=120)
        
        portrait_success = False
        portrait_path = None
        if portrait_response.status_code == 200:
            portrait_result = portrait_response.json()
            if 'data' in portrait_result and portrait_result['data']:
                portrait_image_data = portrait_result['data'][0]
                if 'url' in portrait_image_data:
                    portrait_image_url = portrait_image_data['url']
                    portrait_image_response = requests.get(portrait_image_url, timeout=30)
                    if portrait_image_response.status_code == 200:
                        portrait_path = f"{portrait_dir}/{portrait_filename}"
                        with open(portrait_path, 'wb') as f:
                            f.write(portrait_image_response.content)
                        portrait_success = True
                elif 'b64_json' in portrait_image_data:
                    import base64
                    portrait_image_content = base64.b64decode(portrait_image_data['b64_json'])
                    portrait_path = f"{portrait_dir}/{portrait_filename}"
                    with open(portrait_path, 'wb') as f:
                        f.write(portrait_image_content)
                    portrait_success = True
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{landscape_filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{landscape_filename}",
            'local_path': landscape_path,
            'portrait_generated': portrait_success,
            'portrait_path': f"/static/content/posts/{post_id}/header/portrait/raw/{portrait_filename}" if section_id == 'header' and portrait_success else (f"/static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{portrait_filename}" if portrait_success else None)
        }
        
    except Exception as e:
        logger.error(f"GPT-Image-1 generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

def imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters):
    """Generate image using SDXL - generates both landscape and portrait versions"""
    try:
        # Extract parameters
        landscape_width = parameters.get('width', 1024)
        landscape_height = parameters.get('height', 1024)
        portrait_width = parameters.get('portrait_width', 1024)
        portrait_height = parameters.get('portrait_height', 1792)
        steps = parameters.get('steps', 20)
        cfg = parameters.get('cfg', 7.5)
        lora_scale = parameters.get('lora_scale', 0.85)
        seed = parameters.get('seed', None)
        
        # Call SDXL script
        import subprocess
        
        # Use the virtual environment
        venv_python = os.path.join(os.getcwd(), 'venv_sdxl', 'bin', 'python')
        if not os.path.exists(venv_python):
            return {'success': False, 'error': 'SDXL virtual environment not found. Please run setup_sdxl.sh first.'}
        
        # Create directory structure
        if section_id == 'header':
            landscape_dir = f"static/content/posts/{post_id}/header/raw"
            portrait_dir = f"static/content/posts/{post_id}/header/portrait/raw"
            landscape_filename = "header.png"
            portrait_filename = "header_portrait.png"
        else:
            landscape_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            portrait_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
            landscape_filename = f"{section_id}.png"
            portrait_filename = f"{section_id}_portrait.png"
        
        os.makedirs(landscape_dir, exist_ok=True)
        os.makedirs(portrait_dir, exist_ok=True)
        
        # Generate landscape version
        landscape_cmd = [
            venv_python, 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', str(section_id),
            '--width', str(landscape_width),
            '--height', str(landscape_height),
            '--steps', str(steps),
            '--cfg', str(cfg),
            '--lora_scale', str(lora_scale)
        ]
        
        if seed:
            landscape_cmd.extend(['--seed', str(seed)])
        
        landscape_result = subprocess.run(landscape_cmd, capture_output=True, text=True, timeout=300)
        
        if landscape_result.returncode != 0:
            return {'success': False, 'error': f'SDXL landscape generation failed: {landscape_result.stderr}'}
        
        landscape_path = os.path.join(landscape_dir, landscape_filename)
        if not os.path.exists(landscape_path):
            return {'success': False, 'error': 'SDXL landscape generated but image file not found'}
        
        # Generate portrait version
        portrait_cmd = [
            venv_python, 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', f"{section_id}_portrait",
            '--width', str(portrait_width),
            '--height', str(portrait_height),
            '--steps', str(steps),
            '--cfg', str(cfg),
            '--lora_scale', str(lora_scale)
        ]
        
        if seed:
            portrait_cmd.extend(['--seed', str(seed)])
        
        portrait_result = subprocess.run(portrait_cmd, capture_output=True, text=True, timeout=300)
        
        portrait_success = False
        portrait_path = None
        if portrait_result.returncode == 0:
            # Check if the script created the portrait file (it might use a different naming)
            portrait_temp_path = os.path.join(portrait_dir, portrait_filename)
            # Try to find the generated file
            portrait_candidate = f"static/content/posts/{post_id}/sections/{section_id}_portrait/raw/{section_id}_portrait.png"
            if os.path.exists(portrait_candidate):
                # Move/copy to the correct location
                os.makedirs(portrait_dir, exist_ok=True)
                import shutil
                shutil.move(portrait_candidate, portrait_temp_path)
                portrait_path = portrait_temp_path
                portrait_success = True
            elif os.path.exists(portrait_temp_path):
                portrait_path = portrait_temp_path
                portrait_success = True
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{landscape_filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{landscape_filename}",
            'local_path': landscape_path,
            'portrait_generated': portrait_success,
            'portrait_path': f"/static/content/posts/{post_id}/header/portrait/raw/{portrait_filename}" if section_id == 'header' and portrait_success else (f"/static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{portrait_filename}" if portrait_success else None)
        }
        
    except Exception as e:
        logger.error(f"SDXL generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

def _process_single_image_optimization(raw_image_path, optimized_image_path, watermark_path,
                                       watermark_enabled, text_overlay_enabled, overlay_text,
                                       text_size, watermark_margin, bg_opacity, quality):
    """Helper function to process a single image (landscape or portrait)"""
    from PIL import Image, ImageDraw, ImageFont
    import os
    
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
    
    return {'success': True}

def optimize_image_with_watermark(post_id, section_id, params=None):
    """Optimize image with watermark and AI caption - processes both landscape and portrait in parallel"""
    try:
        import os
        import concurrent.futures
        
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
            landscape_raw = f"static/content/posts/{post_id}/header/raw/header.png"
            landscape_optimized = f"static/content/posts/{post_id}/header/optimized/header.jpg"
            portrait_raw = f"static/content/posts/{post_id}/header/portrait/raw/header_portrait.png"
            portrait_optimized = f"static/content/posts/{post_id}/header/portrait/header_portrait.jpg"
        else:
            landscape_raw = f"static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
            landscape_optimized = f"static/content/posts/{post_id}/sections/{section_id}/optimized/{section_id}.jpg"
            portrait_raw = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{section_id}_portrait.png"
            portrait_optimized = f"static/content/posts/{post_id}/sections/{section_id}/portrait/{section_id}_portrait.jpg"
        
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

# Create blueprint
bp = Blueprint('imaging', __name__, url_prefix='/imaging')

@bp.route('/posts/<int:post_id>/sections/image-generation')
def imaging_sections_image_generation(post_id):
    """Image Generation page - standalone imaging workflow"""
    try:
        # CRITICAL: Check for week context in URL params to determine correct post
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        
        with db_manager.get_cursor() as cursor:
            # Get post data with taxonomy illustration_method using the correct post_id
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id, content_type.illustration_method
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (target_post_id,))
            
            post = cursor.fetchone()
            if not post:
                return f"Post {target_post_id} not found", 404
            
            # Get illustration_method from taxonomy (default to 'LLM-creation' if null/not found)
            illustration_method = post.get('illustration_method') or 'LLM-creation'
            
            # If Photo-harvesting, redirect to photo-selection route
            if illustration_method == 'Photo-harvesting':
                redirect_url = url_for('imaging.imaging_sections_photo_selection', post_id=post_id)
                if url_year and url_week:
                    redirect_url += f'?year={url_year}&week={url_week}'
                return redirect(redirect_url)
            
            # Format dates for display
            post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
            post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post['updated_at'] else 'Unknown'
            
        return render_template('imaging/sections/image_generation.html', 
                             post_id=post_id,
                             page_title='Image Generation',
                             post_title=post['title'],
                             post_status=post['status'],
                             post_created=post_created,
                             post_updated=post_updated,
                             currentStage='imaging',
                             currentSubstage='image-generation',
                             illustration_method=illustration_method)
    except Exception as e:
        logger.error(f"Error rendering image generation page: {str(e)}")
        return f"Error: {str(e)}", 500

@bp.route('/posts/<int:post_id>/sections/optimise')
def imaging_sections_optimise(post_id):
    """Optimise page - imaging workflow substage"""
    try:
        # CRITICAL: Check for week context in URL params to determine correct post
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        
        with db_manager.get_cursor() as cursor:
            # Get post data with taxonomy illustration_method using the correct post_id
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id, content_type.illustration_method
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()
            if not post:
                return f"Post {target_post_id} not found", 404

            # Get illustration_method from taxonomy (default to 'LLM-creation' if null/not found)
            illustration_method = post.get('illustration_method') or 'LLM-creation'

            post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
            post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post['updated_at'] else 'Unknown'

        return render_template('imaging/sections/optimise.html',
                               post_id=post_id,
                               page_title='Optimise',
                               post_title=post['title'],
                               post_status=post['status'],
                               post_created=post_created,
                               post_updated=post_updated,
                               currentStage='imaging',
                               currentSubstage='optimise',
                               illustration_method=illustration_method)
    except Exception as e:
        logger.error(f"Error rendering optimise page: {str(e)}")
        return f"Error: {str(e)}", 500

@bp.route('/posts/<int:post_id>/sections/photo-selection')
def imaging_sections_photo_selection(post_id):
    """Photo Selection page - for Photo-harvesting illustration method"""
    try:
        # CRITICAL: Check for week context in URL params to determine correct post
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        
        with db_manager.get_cursor() as cursor:
            # Get post data with taxonomy illustration_method using the correct post_id
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id, content_type.illustration_method
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (target_post_id,))
            
            post = cursor.fetchone()
            if not post:
                return f"Post {target_post_id} not found", 404
            
            # Get illustration_method from taxonomy (default to 'LLM-creation' if null/not found)
            illustration_method = post.get('illustration_method') or 'LLM-creation'
            
            # If not Photo-harvesting, redirect to image-generation route
            if illustration_method != 'Photo-harvesting':
                redirect_url = url_for('imaging.imaging_sections_image_generation', post_id=post_id)
                if url_year and url_week:
                    redirect_url += f'?year={url_year}&week={url_week}'
                return redirect(redirect_url)
            
            # Format dates for display
            post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
            post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post['updated_at'] else 'Unknown'
            
        return render_template('imaging/sections/photo_selection.html',
                             post_id=target_post_id,
                             page_title='Photo Selection',
                             post_title=post['title'],
                             post_status=post['status'],
                             post_created=post_created,
                             post_updated=post_updated,
                             currentStage='imaging',
                             currentSubstage='photo-selection',
                             illustration_method=illustration_method)
    except Exception as e:
        logger.error(f"Error rendering photo selection page: {str(e)}")
        return f"Error: {str(e)}", 500

@bp.route('/api/posts/<int:post_id>')
def api_get_post(post_id):
    """Get post data for imaging workflow"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get basic post data
            cursor.execute("""
                SELECT id, title, summary, status, created_at, updated_at
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get development data
            cursor.execute("""
                SELECT idea_seed, expanded_idea, basic_idea, provisional_title
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            development = cursor.fetchone()
            
            # Combine post and development data
            post_data = dict(post)
            if development:
                post_data.update(dict(development))
            
            return jsonify({
                'success': True,
                'post': post_data
            })
    except Exception as e:
        logger.error(f"Error getting post data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get sections data for imaging workflow - use same logic as authoring"""
    return sections_api_func(post_id)

@bp.route('/prompts/image-generation', methods=['GET', 'PUT'])
def imaging_prompts_image_generation():
    """Get or update the image generation prompt - imaging standalone version"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'GET':
                # Get the prompt
                cursor.execute("""
                    SELECT id, name, prompt_text, description
                    FROM llm_prompt
                    WHERE name = 'Image Generation'
                """)
                prompt = cursor.fetchone()
                
                if prompt:
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'id': prompt['id'],
                            'name': prompt['name'],
                            'text': prompt['prompt_text'],
                            'description': prompt['description']
                        }
                    })
                else:
                    return jsonify({'success': False, 'error': 'Prompt not found'})
            
            elif request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                prompt_text = data.get('text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt
                    SET prompt_text = %s, updated_at = NOW()
                    WHERE name = 'Image Generation'
                """, (prompt_text,))
                
                return jsonify({'success': True, 'message': 'Prompt updated successfully'})
                
    except Exception as e:
        logger.error(f"Error with Image Generation prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/save-config', methods=['POST'])
def imaging_save_llm_config():
    """Save LLM configuration for imaging workflow"""
    try:
        data = request.get_json()
        
        # Extract configuration data
        image_model = data.get('image_model')
        system_prompt = data.get('system_prompt')
        user_prompt = data.get('user_prompt')
        llm_provider = data.get('llm_provider')
        llm_model = data.get('llm_model')
        temperature = data.get('temperature')
        max_tokens = data.get('max_tokens')
        parameters = data.get('parameters', {})
        
        # For now, just log the configuration (could be saved to database later)
        logger.info(f"Imaging LLM Config saved: image_model={image_model}, llm_provider={llm_provider}, llm_model={llm_model}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving imaging LLM configuration: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/image-generation/posts/<int:post_id>/sections/<int:section_id>/generate-image', methods=['POST'])
def imaging_generate_image(post_id, section_id):
    """Generate image for a specific section - simplified version using only full image prompt"""
    try:
        import time
        
        data = request.get_json()
        model_name = data.get('model_name', 'gpt-image-1')
        parameters = data.get('parameters', {})
        
        # Get the raw image prompt directly from the database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT image_prompts FROM post_section 
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            section_row = cursor.fetchone()
            
            if not section_row or not section_row['image_prompts']:
                return jsonify({'success': False, 'error': 'No image prompt found for this section'})
            
            # Extract the image prompt from JSON
            prompt_data = section_row['image_prompts']
            if isinstance(prompt_data, str):
                try:
                    parsed_data = json.loads(prompt_data)
                    if isinstance(parsed_data, dict):
                        image_prompt = parsed_data.get('image_prompt', '')
                    else:
                        image_prompt = prompt_data.strip()
                except (json.JSONDecodeError, TypeError):
                    image_prompt = prompt_data.strip()
            elif isinstance(prompt_data, dict):
                image_prompt = prompt_data.get('image_prompt', '')
            else:
                image_prompt = str(prompt_data)
            
            if not image_prompt:
                return jsonify({'success': False, 'error': 'No image prompt content found'})
        
        # Verify section exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading
                FROM post_section
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'})
            
            # Provide minimal debug info context
            debug_info = {'source': 'database', 'model_key': model_name}

            # Start timing
            start_time = time.time()
            
            # Route to appropriate image generation function based on model
            if model_name == 'gpt-image-1':
                result = imaging_generate_gpt_image_1(image_prompt, post_id, section_id, parameters)
            elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                result = imaging_generate_dalle_image(image_prompt, post_id, section_id, parameters)
            elif model_name.startswith('sdxl'):
                result = imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters)
            else:
                return jsonify({'success': False, 'error': f'Unsupported model: {model_name}'})
            
            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            if result['success']:
                
                return jsonify({
                    'success': True,
                    'image_path': result['image_path'],
                    'message': 'Image generated successfully',
                    'debug_info': debug_info,
                    'generation_time_ms': generation_time_ms
                })
            else:
                
                return jsonify({'success': False, 'error': result['error']})
                
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Accept string section IDs like "section_1" and map to numeric via section_order
@bp.route('/api/image-generation/posts/<int:post_id>/sections/<section_id>/generate-image', methods=['POST'])
def imaging_generate_image_flexible(post_id, section_id):
    """Generate image accepting string section IDs (e.g., section_1). Maps to post_section by section_order."""
    try:
        import time
        from modules.prompt_service import prompt_service
        
        data = request.get_json() or {}
        model_name = data.get('model_name', 'dall-e-3')
        parameters = data.get('parameters', {})
        use_renderer = data.get('use_renderer', True)  # Feature flag

        # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
        resolved_section_id = None
        if section_id.isdigit():
            resolved_section_id = int(section_id)
        else:
            # Try to parse trailing number from patterns like section_1
            import re
            m = re.search(r'(\d+)$', section_id)
            if m:
                section_order = int(m.group(1))
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id FROM post_section
                        WHERE post_id = %s AND section_order = %s
                        """,
                        (post_id, section_order),
                    )
                    row = cursor.fetchone()
                    if row:
                        resolved_section_id = row['id']

        if resolved_section_id is None:
            return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

        # Get rendered prompt using the new system
        if use_renderer:
            rendered_prompt, debug_info = prompt_service.render_prompt_for_model(
                post_id, resolved_section_id, model_name, use_override=True
            )
            
            if not rendered_prompt:
                return jsonify({'success': False, 'error': 'No prompt available for this section'})
            
            image_prompt = rendered_prompt
        else:
            # Fallback to original prompt from request
            image_prompt = data.get('image_prompt', '')
            debug_info = {'source': 'fallback', 'model_key': model_name}
        
        # Validate that we have a prompt
        if not image_prompt:
            return jsonify({'success': False, 'error': 'No image prompt provided'})

        # Start timing
        start_time = time.time()

        # Route to appropriate image generation function based on model
        if model_name == 'gpt-image-1':
            result = imaging_generate_gpt_image_1(image_prompt, post_id, resolved_section_id, parameters)
        elif model_name.startswith('dall-e') or model_name.startswith('openai'):
            result = imaging_generate_dalle_image(image_prompt, post_id, resolved_section_id, parameters)
        elif model_name.startswith('sdxl'):
            result = imaging_generate_sdxl_image(image_prompt, post_id, resolved_section_id, parameters)
        else:
            return jsonify({'success': False, 'error': f'Unsupported model: {model_name}'})

        if result['success']:
            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # Log generation event
            prompt_service.log_generation_event(
                post_id=post_id,
                section_id=resolved_section_id,
                model_key=model_name,
                params=parameters,
                prompt_text=image_prompt,
                rendered_prompt=image_prompt,
                result_path=result['image_path'],
                success=True,
                generation_time_ms=generation_time_ms
            )
            
            return jsonify(
                {
                    'success': True,
                    'image_path': result['image_path'],
                    'resolved_section_id': resolved_section_id,
                    'message': 'Image generated successfully',
                    'debug_info': debug_info,
                    'generation_time_ms': generation_time_ms
                }
            )
        else:
            # Log failed generation
            prompt_service.log_generation_event(
                post_id=post_id,
                section_id=resolved_section_id,
                model_key=model_name,
                params=parameters,
                prompt_text=image_prompt,
                rendered_prompt=image_prompt,
                result_path='',
                success=False,
                error_message=result['error']
            )
            
            return jsonify({'success': False, 'error': result['error']})

    except Exception as e:
        logger.error(f"Error generating image (flex): {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/diagnostic/posts/<int:post_id>/sections/<section_id>/prompt-pipeline', methods=['GET'])
def diagnostic_prompt_pipeline(post_id, section_id):
    """Comprehensive diagnostic for prompt rendering pipeline"""
    import traceback
    from modules.prompt_service import prompt_service
    from modules.prompt_renderers import PromptRendererFactory
    
    results = {
        'post_id': post_id,
        'section_id': section_id,
        'stages': {},
        'overall_status': 'pending'
    }
    
    try:
        # Stage 1: Database Retrieval
        with db_manager.get_cursor() as cursor:
            # Check post exists
            cursor.execute("SELECT id, title, extra_settings FROM post WHERE id = %s", (post_id,))
            post_row = cursor.fetchone()
            
            results['stages']['database'] = {
                'post_exists': bool(post_row),
                'post_title': post_row['title'] if post_row else None,
                'extra_settings_exists': bool(post_row and post_row['extra_settings']),
                'imaging_settings_exists': bool(post_row and post_row.get('extra_settings', {}).get('imaging')),
                'styles_array_exists': False,
                'active_style_exists': False,
                'active_style_json': None
            }
            
            if post_row and post_row.get('extra_settings'):
                imaging = post_row['extra_settings'].get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                results['stages']['database']['styles_array_exists'] = bool(styles)
                results['stages']['database']['styles_count'] = len(styles) if isinstance(styles, list) else 0
                results['stages']['database']['active_index'] = active_index
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]
                    results['stages']['database']['active_style_exists'] = True
                    results['stages']['database']['active_style_name'] = active_style.get('name')
                    results['stages']['database']['active_style_json'] = active_style.get('style_json')
            
            # Check section data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            results['stages']['database']['post_development_exists'] = bool(dev_row)
            
            if dev_row and dev_row['sections']:
                import json
                sections_data = dev_row['sections']
                if isinstance(sections_data, str):
                    sections_data = json.loads(sections_data)
                
                if isinstance(sections_data, dict) and 'sections' in sections_data:
                    sections_list = sections_data['sections']
                    results['stages']['database']['sections_count'] = len(sections_list)
                    
                    # Find target section
                    for section in sections_list:
                        if str(section.get('id')) == str(section_id):
                            results['stages']['database']['section_found'] = True
                            results['stages']['database']['section_has_image_prompts'] = bool(section.get('image_prompts'))
                            if section.get('image_prompts'):
                                prompt_data = section['image_prompts']
                                if isinstance(prompt_data, dict):
                                    results['stages']['database']['image_prompt_length'] = len(prompt_data.get('image_prompt', ''))
                                    results['stages']['database']['image_prompt_preview'] = prompt_data.get('image_prompt', '')[:100]
                            break
        
        # Stage 2: Canonical Prompt Creation
        try:
            canonical, style_json = prompt_service.get_canonical_prompt(post_id, section_id)
            results['stages']['canonical_prompt'] = {
                'success': True,
                'canonical_subject_length': len(canonical.subject),
                'canonical_subject_preview': canonical.subject[:100] if canonical.subject else None,
                'canonical_style': canonical.style,
                'canonical_constraints': canonical.constraints,
                'canonical_negatives': canonical.negatives,
                'style_json_received': bool(style_json),
                'style_json_keys': list(style_json.keys()) if isinstance(style_json, dict) else None
            }
        except Exception as e:
            results['stages']['canonical_prompt'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            results['overall_status'] = 'failed'
            return jsonify(results)
        
        # Stage 3: Renderer Selection
        model_key = request.args.get('model_key', 'gpt-image-1')
        try:
            constraints = {'max_prompt_chars': 2000 if model_key == 'gpt-image-1' else 400}
            renderer = PromptRendererFactory.create_renderer(model_key, constraints)
            results['stages']['renderer'] = {
                'success': True,
                'renderer_class': type(renderer).__name__,
                'model_key': model_key,
                'constraints': constraints
            }
        except Exception as e:
            results['stages']['renderer'] = {
                'success': False,
                'error': str(e)
            }
            results['overall_status'] = 'failed'
            return jsonify(results)
        
        # Stage 4: Style Integration (call internal method)
        try:
            style_description = renderer._integrate_style_details(canonical, style_json)
            results['stages']['style_integration'] = {
                'success': True,
                'style_description': style_description,
                'style_description_length': len(style_description) if style_description else 0,
                'contains_watercolor': 'watercolor' in (style_description or '').lower(),
                'contains_pastel': 'pastel' in (style_description or '').lower()
            }
        except Exception as e:
            results['stages']['style_integration'] = {
                'success': False,
                'error': str(e)
            }
        
        # Stage 5: Full Rendering
        try:
            rendered_prompt = renderer.render(canonical, style_json)
            results['stages']['rendering'] = {
                'success': True,
                'prompt_length': len(rendered_prompt),
                'prompt_preview_first_200': rendered_prompt[:200],
                'prompt_preview_last_200': rendered_prompt[-200:],
                'contains_watercolor': 'watercolor' in rendered_prompt.lower(),
                'contains_pastel': 'pastel' in rendered_prompt.lower(),
                'contains_white_margins': 'white margin' in rendered_prompt.lower(),
                'contains_visible_brushstrokes': 'visible brushstroke' in rendered_prompt.lower(),
                'contains_pen_and_ink': 'pen and ink' in rendered_prompt.lower(),
                'contains_avoiding_dark': 'avoiding dark' in rendered_prompt.lower(),
                'contains_avoiding_saturated': 'avoiding saturated' in rendered_prompt.lower(),
                'contains_avoiding_digital': 'avoiding digital' in rendered_prompt.lower()
            }
        except Exception as e:
            results['stages']['rendering'] = {
                'success': False,
                'error': str(e)
            }
            results['overall_status'] = 'failed'
            return jsonify(results)
        
        # Stage 6: API Integration Test
        try:
            # Test the actual API path
            rendered_via_service, metadata = prompt_service.render_prompt_for_model(
                post_id, section_id, model_key, use_override=True
            )
            results['stages']['api_integration'] = {
                'success': True,
                'service_prompt_length': len(rendered_via_service),
                'matches_direct_render': rendered_via_service == rendered_prompt,
                'metadata': metadata
            }
        except Exception as e:
            results['stages']['api_integration'] = {
                'success': False,
                'error': str(e)
            }
        
        # Overall assessment
        all_stages_passed = all(
            stage.get('success', False) 
            for stage in results['stages'].values() 
            if 'success' in stage
        )
        results['overall_status'] = 'passed' if all_stages_passed else 'failed'
        
        return jsonify(results)
        
    except Exception as e:
        results['overall_status'] = 'error'
        results['error'] = str(e)
        results['error_trace'] = traceback.format_exc()
        return jsonify(results), 500

@bp.route('/api/model-selection', methods=['GET', 'POST'])
def imaging_model_selection():
    """Get or save model selection configuration (per-post persistent)"""
    try:
        if request.method == 'GET':
            # Prefer per-post selection from post_development; fallback to ui_user_preferences
            post_id = request.args.get('post_id', type=int)
            with db_manager.get_cursor() as cursor:
                if post_id:
                    cursor.execute(
                        """
                        SELECT imaging_model_selection, imaging_model_parameters 
                        FROM post_development 
                        WHERE post_id = %s
                        """,
                        (post_id,)
                    )
                    row = cursor.fetchone()
                    if row and row.get('imaging_model_selection'):
                        parameters = {}
                        if row.get('imaging_model_parameters'):
                            try:
                                parameters = json.loads(row['imaging_model_parameters'])
                            except (json.JSONDecodeError, TypeError):
                                parameters = {}
                        return jsonify({'success': True, 'model': row['imaging_model_selection'], 'parameters': parameters})

                # Fallback to global preference
                cursor.execute(
                    """
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE preference_key = 'imaging_model_selection'
                    """
                )
                pref = cursor.fetchone()
                if pref:
                    config = json.loads(pref['preference_value'])
                    return jsonify({'success': True, 'model': config.get('model', 'sdxl-lora'), 'parameters': config.get('parameters', {})})

                # Default
                return jsonify({'success': True, 'model': 'sdxl-lora', 'parameters': {}})
        
        elif request.method == 'POST':
            # Save per-post selection to post_development; also update ui_user_preferences for global default
            data = request.get_json()
            model = data.get('model', 'sdxl-lora')
            parameters = data.get('parameters', {})
            post_id = data.get('post_id')

            with db_manager.get_cursor() as cursor:
                if post_id:
                    # Update per-post selection
                    parameters_json = json.dumps(parameters) if parameters else None
                    cursor.execute(
                        """
                        UPDATE post_development
                        SET imaging_model_selection = %s, imaging_model_parameters = %s, updated_at = NOW()
                        WHERE post_id = %s
                        """,
                        (model, parameters_json, post_id)
                    )
                    # If no row updated, attempt insert minimal row (best-effort)
                    if cursor.rowcount == 0:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO post_development (post_id, imaging_model_selection, imaging_model_parameters, created_at, updated_at)
                                VALUES (%s, %s, %s, NOW(), NOW())
                                """,
                                (post_id, model, parameters_json)
                            )
                        except Exception as _ignore:
                            logger.warning(f"Could not insert post_development for post_id={post_id}: {_ignore}")

                # Also update global preference for convenience
                config_data = {'model': model, 'parameters': parameters}
                cursor.execute(
                    """
                    INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category, is_global)
                    VALUES (1, 'imaging_model_selection', %s, 'json', 'imaging', false)
                    ON CONFLICT (user_id, preference_key)
                    DO UPDATE SET preference_value = EXCLUDED.preference_value, updated_at = NOW()
                    """,
                    (json.dumps(config_data),)
                )
                cursor.connection.commit()

                return jsonify({'success': True, 'message': 'Model selection saved for post'})
                
    except Exception as e:
        logger.error(f"Error with model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/model-specs', methods=['GET'])
def imaging_get_model_specs():
    """Get model specifications and parameter defaults for UI"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all image generation models from llm_model table
            cursor.execute("""
                SELECT lm.id, lm.name, lm.description, lm.api_params, lp.name as provider_name
                FROM llm_model lm
                JOIN llm_provider lp ON lm.provider_id = lp.id
                WHERE lm.api_params->>'type' = 'image'
                ORDER BY lm.name
            """)
            models = cursor.fetchall()
            
            # Get parameter defaults for each model
            cursor.execute("""
                SELECT model_key, param_key, default_value, param_type, min_value, max_value, options
                FROM model_param_default
                ORDER BY model_key, param_key
            """)
            param_defaults = cursor.fetchall()
            
            # Organize parameter defaults by model
            params_by_model = {}
            for param in param_defaults:
                model_key = param['model_key']
                if model_key not in params_by_model:
                    params_by_model[model_key] = []
                params_by_model[model_key].append({
                    'key': param['param_key'],
                    'default_value': param['default_value'],
                    'type': param['param_type'],
                    'min_value': param['min_value'],
                    'max_value': param['max_value'],
                    'options': param['options']
                })
            
            # Build response with model specs
            model_specs = []
            for model in models:
                model_key = model['name']
                api_params = model['api_params'] or {}
                
                spec = {
                    'model_key': model_key,
                    'name': model['name'],
                    'description': model['description'],
                    'provider': model['provider_name'],
                    'supports_lora': model_key == 'sdxl-lora',
                    'constraints': {
                        'max_prompt_chars': api_params.get('max_prompt_chars', 1000),
                        'supported_sizes': api_params.get('sizes', []),
                        'supported_qualities': api_params.get('quality', []),
                        'supported_styles': api_params.get('style', [])
                    },
                    'parameters': params_by_model.get(model_key, [])
                }
                model_specs.append(spec)
            
            return jsonify({
                'success': True,
                'models': model_specs
            })
            
    except Exception as e:
        logger.error(f"Error getting model specs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/prompt-override/posts/<int:post_id>/sections/<int:section_id>/<model_key>', methods=['GET', 'POST', 'DELETE'])
def imaging_prompt_override(post_id, section_id, model_key):
    """Handle model-specific prompt overrides"""
    try:
        from modules.prompt_service import prompt_service
        
        if request.method == 'GET':
            # Get override for specific model
            override = prompt_service.get_prompt_override(post_id, section_id, model_key)
            return jsonify({
                'success': True,
                'override': override,
                'has_override': override is not None
            })
        
        elif request.method == 'POST':
            # Save override
            data = request.get_json()
            prompt_text = data.get('prompt_text', '')
            
            if not prompt_text.strip():
                return jsonify({'success': False, 'error': 'Prompt text cannot be empty'}), 400
            
            success = prompt_service.save_prompt_override(post_id, section_id, model_key, prompt_text)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Prompt override saved successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to save override'}), 500
        
        elif request.method == 'DELETE':
            # Delete override (deactivate)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE image_prompt_override 
                    SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s AND section_id = %s AND model_key = %s
                """, (post_id, section_id, model_key))
                cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Prompt override deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error with prompt override: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/debug-prompt/posts/<int:post_id>/sections/<int:section_id>', methods=['GET'])
def imaging_debug_prompt(post_id, section_id):
    """Debug endpoint to test prompt parsing"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT image_prompts FROM post_section 
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Section not found'})
            
            prompt_data = result['image_prompts']
            
            # Test parsing
            from modules.prompt_renderers import parse_legacy_prompt
            
            if isinstance(prompt_data, dict):
                prompt_text = prompt_data.get('image_prompt', '') or prompt_data.get('base_concept', '')
                canonical = parse_legacy_prompt(prompt_text)
            else:
                canonical = parse_legacy_prompt(prompt_data)
            
            return jsonify({
                'raw_data': prompt_data,
                'raw_type': type(prompt_data).__name__,
                'extracted_text': prompt_text if isinstance(prompt_data, dict) else prompt_data,
                'canonical': canonical.to_dict(),
                'canonical_subject': canonical.subject
            })
            
    except Exception as e:
        return jsonify({'error': str(e)})

@bp.route('/api/generation-events', methods=['GET'])
def imaging_get_generation_events():
    """Get generation events for audit/debugging"""
    try:
        from modules.prompt_service import prompt_service
        
        # Get query parameters
        post_id = request.args.get('post_id', type=int)
        section_id = request.args.get('section_id', type=int)
        model_key = request.args.get('model_key')
        limit = request.args.get('limit', 100, type=int)
        
        events = prompt_service.get_generation_events(
            post_id=post_id,
            section_id=section_id,
            model_key=model_key,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error getting generation events: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/admin/generation-events')
def imaging_admin_generation_events():
    """Admin page for viewing generation events"""
    return render_template('imaging/admin/generation_events.html')

@bp.route('/api/optimize/posts/<int:post_id>/sections/<section_id>/optimize-image', methods=['POST'])
def imaging_optimize_image(post_id, section_id):
    """Optimize image with watermark and caption for a specific section"""
    try:
        # Get parameters from request
        params = request.get_json() or {}
        
        # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
        resolved_section_id = None
        if section_id.isdigit():
            resolved_section_id = int(section_id)
        else:
            # Try to parse trailing number from patterns like section_1
            import re
            m = re.search(r'(\d+)$', section_id)
            if m:
                section_order = int(m.group(1))
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id FROM post_section
                        WHERE post_id = %s AND section_order = %s
                        """,
                        (post_id, section_order),
                    )
                    row = cursor.fetchone()
                    if row:
                        resolved_section_id = row['id']

        if resolved_section_id is None:
            return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

        # Verify section exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading
                FROM post_section
                WHERE id = %s AND post_id = %s
            """, (resolved_section_id, post_id))
            
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'})
        
        # Optimize the image with parameters
        result = optimize_image_with_watermark(post_id, resolved_section_id, params)
        
        if result['success']:
            # Save optimized image to image table and create post_images link
            with db_manager.get_cursor() as cursor:
                # Get optimized image path
                optimized_path = result['optimized_path'].lstrip('/')  # Remove leading /
                
                # Insert or update image record
                cursor.execute("""
                    INSERT INTO image (filename, path, alt_text, caption)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (path) DO UPDATE 
                    SET filename = EXCLUDED.filename, alt_text = EXCLUDED.alt_text, caption = EXCLUDED.caption
                    RETURNING id
                """, (
                    f"{resolved_section_id}_optimized.jpg",
                    f"/{optimized_path}",
                    f"Optimized image for {section.get('section_heading', 'section')}",
                    "AI-generated image"
                ))
                image_record = cursor.fetchone()
                image_id = image_record['id']
                
                # Delete any existing post_images link for this section's optimized image
                cursor.execute("""
                    DELETE FROM post_images 
                    WHERE section_id = %s AND image_type = 'section_optimized'
                """, (resolved_section_id,))
                
                # Create post_images link
                cursor.execute("""
                    INSERT INTO post_images (section_id, image_id, image_type)
                    VALUES (%s, %s, 'section_optimized')
                """, (resolved_section_id, image_id))
            
            return jsonify({
                'success': True,
                'optimized_path': result['optimized_path'],
                'message': 'Image optimized successfully'
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logger.error(f"Error optimizing image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/optimize/posts/<int:post_id>/optimize-all', methods=['POST'])
def imaging_optimize_all_images(post_id):
    """Optimize all images for a post with watermark and caption"""
    try:
        # Get all sections with raw images
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
        
        if not sections:
            return jsonify({'success': False, 'error': 'No sections found'})
        
        results = []
        successful = 0
        failed = 0
        
        for section in sections:
            section_id = section['id']
            raw_image_path = f"static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
            
            # Skip if raw image doesn't exist
            if not os.path.exists(raw_image_path):
                results.append({
                    'section_id': section_id,
                    'section_heading': section['section_heading'],
                    'success': False,
                    'error': 'Raw image not found',
                    'skipped': True
                })
                continue
            
            # Optimize the image
            result = optimize_image_with_watermark(post_id, section_id)
            
            if result['success']:
                results.append({
                    'section_id': section_id,
                    'section_heading': section['section_heading'],
                    'success': True,
                    'optimized_path': result['optimized_path'],
                    'skipped': False
                })
                successful += 1
            else:
                results.append({
                    'section_id': section_id,
                    'section_heading': section['section_heading'],
                    'success': False,
                    'error': result['error'],
                    'skipped': False
                })
                failed += 1
        
        return jsonify({
            'success': True,
            'total_sections': len(sections),
            'successful': successful,
            'failed': failed,
            'results': results,
            'message': f'Optimization complete: {successful} successful, {failed} failed'
        })
        
    except Exception as e:
        logger.error(f"Error optimizing all images: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/raw-image')
def imaging_get_raw_image(post_id, section_id):
    """Get raw image path for a section, accepting both numeric and string section IDs"""
    try:
        # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
        resolved_section_id = None
        if section_id.isdigit():
            resolved_section_id = int(section_id)
        else:
            # Try to parse trailing number from patterns like section_1
            import re
            m = re.search(r'(\d+)$', section_id)
            if m:
                section_order = int(m.group(1))
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id FROM post_section
                        WHERE post_id = %s AND section_order = %s
                        """,
                        (post_id, section_order),
                    )
                    row = cursor.fetchone()
                    if row:
                        resolved_section_id = row['id']

        if resolved_section_id is None:
            return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

        # Check for raw image
        raw_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/raw/{resolved_section_id}.png"
        
        if os.path.exists(raw_path):
            return jsonify({
                'success': True,
                'path': f"/static/content/posts/{post_id}/sections/{resolved_section_id}/raw/{resolved_section_id}.png",
                'type': 'raw'
            })
        else:
            return jsonify({'success': False, 'message': 'No raw image found for this section'})

    except Exception as e:
        logger.error(f"Error getting raw image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/photo-search/posts/<int:post_id>/sections/<int:section_id>/search', methods=['POST'])
def api_photo_search(post_id, section_id):
    """Search for photos from Pexels/Unsplash"""
    try:
        # Verify section belongs to post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM post_section
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'}), 404
        
        # Get request data
        data = request.get_json() or {}
        search_term = data.get('search_term', '').strip()
        provider = data.get('provider', 'both')
        per_page = int(data.get('per_page', 20))
        
        if not search_term:
            return jsonify({'success': False, 'error': 'search_term is required'}), 400
        
        # Import photo API utilities
        from utils.photo_apis import search_pexels, search_unsplash, merge_search_results
        import os
        from datetime import datetime
        
        # Get API keys from environment
        pexels_key = os.getenv('PEXELS_API_KEY')
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        
        results = []
        pexels_results = []
        unsplash_results = []
        
        # Search Pexels if requested
        if provider in ('pexels', 'both') and pexels_key:
            pexels_results = search_pexels(pexels_key, search_term, per_page)
        
        # Search Unsplash if requested
        if provider in ('unsplash', 'both') and unsplash_key:
            unsplash_results = search_unsplash(unsplash_key, search_term, per_page)
        
        # Combine results based on provider
        if provider == 'both':
            results = merge_search_results(pexels_results, unsplash_results)
        elif provider == 'pexels':
            results = pexels_results
        elif provider == 'unsplash':
            results = unsplash_results
        
        # Store results in database
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update photo_search_results (replace existing)
                cursor.execute("""
                    UPDATE post_section
                    SET photo_search_results = %s::jsonb,
                        image_search_terms = COALESCE(
                            CASE 
                                WHEN image_search_terms IS NULL THEN '[]'::jsonb
                                ELSE image_search_terms
                            END || %s::jsonb,
                            '[]'::jsonb || %s::jsonb
                        ),
                        updated_at = NOW()
                    WHERE id = %s AND post_id = %s
                    RETURNING id
                """, (json.dumps(results), json.dumps([search_term]), json.dumps([search_term]), section_id, post_id))
                
                if not cursor.fetchone():
                    return jsonify({'success': False, 'error': 'Failed to save search results'}), 500
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'search_term': search_term,
            'provider': provider
        })
        
    except Exception as e:
        logger.error(f"Error in photo search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/photo-search/posts/<int:post_id>/sections/<int:section_id>/results', methods=['GET'])
def api_photo_results(post_id, section_id):
    """Get stored photo search results for a section"""
    try:
        # Verify section belongs to post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT photo_search_results
                FROM post_section
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'}), 404
            
            # Get results (default to empty array)
            results = section['photo_search_results']
            if results is None:
                results = []
            elif isinstance(results, str):
                results = json.loads(results)
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results) if isinstance(results, list) else 0
            })
            
    except Exception as e:
        logger.error(f"Error fetching photo results: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/photo-search/posts/<int:post_id>/sections/<int:section_id>/select', methods=['POST'])
def api_photo_select(post_id, section_id):
    """Select a photo from search results"""
    try:
        # Get request data
        data = request.get_json() or {}
        provider = data.get('provider')
        image_id = data.get('image_id')
        
        if not provider or not image_id:
            return jsonify({'success': False, 'error': 'provider and image_id are required'}), 400
        
        # Verify section belongs to post and get current results
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT photo_search_results
                    FROM post_section
                    WHERE id = %s AND post_id = %s
                """, (section_id, post_id))
                section = cursor.fetchone()
                if not section:
                    return jsonify({'success': False, 'error': 'Section not found'}), 404
                
                # Get current results
                results = section['photo_search_results']
                if results is None:
                    results = []
                elif isinstance(results, str):
                    results = json.loads(results)
                
                if not isinstance(results, list):
                    results = []
                
                # Find and update selected photo
                selected_photo = None
                updated_results = []
                
                for photo in results:
                    if photo.get('provider') == provider and str(photo.get('image_id')) == str(image_id):
                        # Mark as selected
                        photo['selected'] = True
                        photo['selected_at'] = datetime.now().isoformat()
                        selected_photo = photo
                    else:
                        # Unselect all others
                        photo['selected'] = False
                        photo.pop('selected_at', None)
                    updated_results.append(photo)
                
                if not selected_photo:
                    return jsonify({'success': False, 'error': 'Photo not found in search results'}), 404
                
                # Save updated results
                cursor.execute("""
                    UPDATE post_section
                    SET photo_search_results = %s::jsonb,
                        updated_at = NOW()
                    WHERE id = %s AND post_id = %s
                    RETURNING id
                """, (json.dumps(updated_results), section_id, post_id))
                
                if not cursor.fetchone():
                    return jsonify({'success': False, 'error': 'Failed to save selection'}), 500
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'selected_photo': selected_photo
                })
                
    except Exception as e:
        logger.error(f"Error selecting photo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/photo-search/posts/<int:post_id>/sections/<int:section_id>/selected', methods=['GET'])
def api_photo_selected(post_id, section_id):
    """Get currently selected photo for a section"""
    try:
        # Verify section belongs to post and get results
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT photo_search_results
                FROM post_section
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'}), 404
            
            # Get results and find selected photo
            results = section['photo_search_results']
            if results is None:
                results = []
            elif isinstance(results, str):
                results = json.loads(results)
            
            if not isinstance(results, list):
                results = []
            
            # Find selected photo
            selected_photo = None
            for photo in results:
                if photo.get('selected') is True:
                    selected_photo = photo
                    break
            
            return jsonify({
                'success': True,
                'selected_photo': selected_photo
            })
            
    except Exception as e:
        logger.error(f"Error fetching selected photo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/image')
def imaging_get_section_image(post_id, section_id):
    """Get persisted image path for a section, accepting both numeric and string section IDs"""
    try:
        # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
        resolved_section_id = None
        if section_id.isdigit():
            resolved_section_id = int(section_id)
        else:
            # Try to parse trailing number from patterns like section_1
            import re
            m = re.search(r'(\d+)$', section_id)
            if m:
                section_order = int(m.group(1))
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id FROM post_section
                        WHERE post_id = %s AND section_order = %s
                        """,
                        (post_id, section_order),
                    )
                    row = cursor.fetchone()
                    if row:
                        resolved_section_id = row['id']

        if resolved_section_id is None:
            return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

        # Optimise page must not fall back to raw; only return optimized if it exists
        optimized_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/optimized/{resolved_section_id}.jpg"
        if os.path.exists(optimized_path):
            return jsonify({
                'success': True,
                'path': f"/static/content/posts/{post_id}/sections/{resolved_section_id}/optimized/{resolved_section_id}.jpg",
                'type': 'optimized'
            })
        # No optimized image available
        return jsonify({'success': False, 'message': 'No optimized image found for this section'})

    except Exception as e:
        logger.error(f"Error getting section image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
