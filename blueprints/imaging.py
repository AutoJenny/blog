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
    """Generate image using DALL-E API - imaging standalone version"""
    try:
        # Load OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not found in environment'}
        
        # Extract parameters
        size = parameters.get('size', '1792x1024')
        quality = parameters.get('quality', 'standard')
        style = parameters.get('style', 'natural')
        
        # Call DALL-E API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'dall-e-3',
            'prompt': image_prompt,
            'n': 1,
            'size': size,
            'quality': quality,
            'style': style
        }
        
        response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'DALL-E API error: {response.status_code} - {response.text}'}
        
        result = response.json()
        
        if 'data' not in result or not result['data']:
            return {'success': False, 'error': 'No image data returned from DALL-E'}
        
        # Download the image
        image_url = result['data'][0]['url']
        image_response = requests.get(image_url, timeout=30)
        
        if image_response.status_code != 200:
            return {'success': False, 'error': f'Failed to download image: {image_response.status_code}'}
        
        # Create directory structure - support both sections and header
        if section_id == 'header':
            image_dir = f"static/content/posts/{post_id}/header/raw"
            filename = "header.png"
        else:
            image_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            filename = f"{section_id}.png"
        
        os.makedirs(image_dir, exist_ok=True)
        
        # Save image
        image_path = f"{image_dir}/{filename}"
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{filename}",
            'local_path': image_path
        }
        
    except Exception as e:
        logger.error(f"DALL-E generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

def imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters):
    """Generate image using SDXL - imaging standalone version"""
    try:
        # Extract parameters
        width = parameters.get('width', 1024)
        height = parameters.get('height', 1024)
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
        
        cmd = [
            venv_python, 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', str(section_id),
            '--width', str(width),
            '--height', str(height),
            '--steps', str(steps),
            '--cfg', str(cfg),
            '--lora_scale', str(lora_scale)
        ]
        
        if seed:
            cmd.extend(['--seed', str(seed)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {'success': False, 'error': f'SDXL generation failed: {result.stderr}'}
        
        # The script should have created the image file - support both sections and header
        if section_id == 'header':
            image_path = f"/static/content/posts/{post_id}/header/raw/header.png"
            local_path = f"static/content/posts/{post_id}/header/raw/header.png"
        else:
            image_path = f"/static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
            local_path = f"static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
        
        if os.path.exists(local_path):
            return {
                'success': True,
                'image_path': image_path,
                'local_path': local_path
            }
        else:
            return {'success': False, 'error': 'SDXL generated but image file not found'}
        
    except Exception as e:
        logger.error(f"SDXL generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

def optimize_image_with_watermark(post_id, section_id, params=None):
    """Optimize image with watermark and AI caption"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        
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
        
        # Paths - support both sections and header
        if section_id == 'header':
            raw_image_path = f"static/content/posts/{post_id}/header/raw/header.png"
            optimized_dir = f"static/content/posts/{post_id}/header/optimized"
            optimized_image_path = f"{optimized_dir}/header.jpg"
        else:
            raw_image_path = f"static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
            optimized_dir = f"static/content/posts/{post_id}/sections/{section_id}/optimized"
            optimized_image_path = f"{optimized_dir}/{section_id}.jpg"
        
        watermark_path = "static/images/site/clan-watermark.png"
        
        # Check if raw image exists
        if not os.path.exists(raw_image_path):
            return {'success': False, 'error': f'Raw image not found: {raw_image_path}'}
        
        # Create optimized directory
        os.makedirs(optimized_dir, exist_ok=True)
        
        # Load images
        image = Image.open(raw_image_path)
        
        # Convert to RGBA if needed
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Add watermark if enabled
        if watermark_enabled:
            # Check if watermark exists
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
        image.save(optimized_image_path, 'JPEG', quality=quality, optimize=True)
        
        return {
            'success': True,
            'optimized_path': f"/{optimized_image_path}",
            'message': 'Image optimized successfully'
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
        with db_manager.get_cursor() as cursor:
            # Get post data for header
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return f"Post {post_id} not found", 404
            
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
                             currentSubstage='image-generation')
    except Exception as e:
        logger.error(f"Error rendering image generation page: {str(e)}")
        return f"Error: {str(e)}", 500

@bp.route('/posts/<int:post_id>/sections/optimise')
def imaging_sections_optimise(post_id):
    """Optimise page - imaging workflow substage"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            if not post:
                return f"Post {post_id} not found", 404

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
                               currentSubstage='optimise')
    except Exception as e:
        logger.error(f"Error rendering optimise page: {str(e)}")
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
    """Generate image for a specific section - imaging standalone version with model-aware rendering"""
    try:
        import time
        from modules.prompt_service import prompt_service
        
        data = request.get_json()
        model_name = data.get('model_name', 'dall-e-3')
        parameters = data.get('parameters', {})
        use_renderer = data.get('use_renderer', True)  # Feature flag
        
        # Get rendered prompt using the new system
        if use_renderer:
            rendered_prompt, debug_info = prompt_service.render_prompt_for_model(
                post_id, section_id, model_name, use_override=True
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
            
            # Start timing
            start_time = time.time()
            
            # Route to appropriate image generation function based on model
            if model_name.startswith('dall-e') or model_name.startswith('openai'):
                result = imaging_generate_dalle_image(image_prompt, post_id, section_id, parameters)
            elif model_name.startswith('sdxl'):
                result = imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters)
            else:
                return jsonify({'success': False, 'error': f'Unsupported model: {model_name}'})
            
            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            if result['success']:
                # Log generation event
                prompt_service.log_generation_event(
                    post_id=post_id,
                    section_id=section_id,
                    model_key=model_name,
                    params=parameters,
                    prompt_text=image_prompt,
                    rendered_prompt=image_prompt,
                    result_path=result['image_path'],
                    success=True,
                    generation_time_ms=generation_time_ms
                )
                
                return jsonify({
                    'success': True,
                    'image_path': result['image_path'],
                    'message': 'Image generated successfully',
                    'debug_info': debug_info,
                    'generation_time_ms': generation_time_ms
                })
            else:
                # Log failed generation event
                prompt_service.log_generation_event(
                    post_id=post_id,
                    section_id=section_id,
                    model_key=model_name,
                    params=parameters,
                    prompt_text=image_prompt,
                    rendered_prompt=image_prompt,
                    result_path='',
                    success=False,
                    error_message=result['error'],
                    generation_time_ms=generation_time_ms
                )
                
                return jsonify({'success': False, 'error': result['error']})
                
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Accept string section IDs like "section_1" and map to numeric via section_order
@bp.route('/api/image-generation/posts/<int:post_id>/sections/<section_id>/generate-image', methods=['POST'])
def imaging_generate_image_flexible(post_id, section_id):
    """Generate image accepting string section IDs (e.g., section_1). Maps to post_section by section_order."""
    try:
        data = request.get_json() or {}
        model_name = data.get('model_name', 'dall-e-3')
        parameters = data.get('parameters', {})
        image_prompt = data.get('image_prompt', '')

        if not image_prompt:
            return jsonify({'success': False, 'error': 'No image prompt provided'})

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

        # Route to appropriate image generation function based on model
        if model_name.startswith('dall-e') or model_name.startswith('openai'):
            result = imaging_generate_dalle_image(image_prompt, post_id, resolved_section_id, parameters)
        elif model_name.startswith('sdxl'):
            result = imaging_generate_sdxl_image(image_prompt, post_id, resolved_section_id, parameters)
        else:
            return jsonify({'success': False, 'error': f'Unsupported model: {model_name}'})

        if result['success']:
            return jsonify(
                {
                    'success': True,
                    'image_path': result['image_path'],
                    'resolved_section_id': resolved_section_id,
                    'message': 'Image generated successfully',
                }
            )
        else:
            return jsonify({'success': False, 'error': result['error']})

    except Exception as e:
        logger.error(f"Error generating image (flex): {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/model-selection', methods=['GET', 'POST'])
def imaging_model_selection():
    """Get or save model selection configuration"""
    try:
        if request.method == 'GET':
            # Load saved model selection from ui_user_preferences
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE preference_key = 'imaging_model_selection'
                """)
                result = cursor.fetchone()
                
                if result:
                    config = json.loads(result['preference_value'])
                    return jsonify({
                        'success': True,
                        'model': config.get('model', 'sdxl-lora'),
                        'parameters': config.get('parameters', {})
                    })
                else:
                    # Return default configuration
                    return jsonify({
                        'success': True,
                        'model': 'sdxl-lora',
                        'parameters': {
                            'image_dimensions': '1024x1024',
                            'steps': 20,
                            'cfg': 7,
                            'seed': None
                        }
                    })
        
        elif request.method == 'POST':
            # Save model selection to ui_user_preferences
            data = request.get_json()
            model = data.get('model', 'sdxl-lora')
            parameters = data.get('parameters', {})
            
            config_data = {
                'model': model,
                'parameters': parameters,
                'last_used': '2024-01-01T12:00:00Z'
            }
            
            with db_manager.get_cursor() as cursor:
                # Insert or update in ui_user_preferences
                try:
                    result = cursor.execute("""
                        INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category, is_global)
                        VALUES (1, 'imaging_model_selection', %s, 'json', 'imaging', false)
                        ON CONFLICT (user_id, preference_key) 
                        DO UPDATE SET preference_value = %s, updated_at = NOW()
                    """, (json.dumps(config_data), json.dumps(config_data)))
                    cursor.connection.commit()  # Explicit commit
                    logger.info(f"Successfully saved model selection: {config_data}, result: {result}")
                except Exception as db_error:
                    logger.error(f"Database error saving model selection: {db_error}")
                    return jsonify({'success': False, 'error': str(db_error)}), 500
                
                return jsonify({
                    'success': True,
                    'message': 'Model selection saved successfully'
                })
                
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

@bp.route('/api/render-prompt/posts/<int:post_id>/sections/<int:section_id>/<model_key>', methods=['GET'])
def imaging_render_prompt(post_id, section_id, model_key):
    """Render prompt for specific model with debug info"""
    try:
        from modules.prompt_service import prompt_service
        
        # Get rendered prompt with debug info
        rendered_prompt, debug_info = prompt_service.render_prompt_for_model(
            post_id, section_id, model_key, use_override=True
        )
        
        return jsonify({
            'success': True,
            'rendered_prompt': rendered_prompt,
            'debug_info': debug_info
        })
        
    except Exception as e:
        logger.error(f"Error rendering prompt: {e}")
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

        # Check for existing images in order of preference: optimized > raw
        optimized_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/optimized/{resolved_section_id}.jpg"
        raw_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/raw/{resolved_section_id}.png"
        
        if os.path.exists(optimized_path):
            return jsonify({
                'success': True,
                'path': f"/static/content/posts/{post_id}/sections/{resolved_section_id}/optimized/{resolved_section_id}.jpg",
                'type': 'optimized'
            })
        elif os.path.exists(raw_path):
            return jsonify({
                'success': True,
                'path': f"/static/content/posts/{post_id}/sections/{resolved_section_id}/raw/{resolved_section_id}.png",
                'type': 'raw'
            })
        else:
            return jsonify({'success': False, 'message': 'No image found for this section'})

    except Exception as e:
        logger.error(f"Error getting section image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
