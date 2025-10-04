# Imaging Blueprint - Standalone image generation workflow
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config.database import db_manager
import logging
import json
import os
import requests

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
        
        # Create directory structure
        image_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
        os.makedirs(image_dir, exist_ok=True)
        
        # Save image with section-based naming
        image_path = f"{image_dir}/{section_id}.png"
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png",
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
        seed = parameters.get('seed', None)
        
        # Call SDXL script
        import subprocess
        
        cmd = [
            'python3', 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', str(section_id),
            '--width', str(width),
            '--height', str(height),
            '--steps', str(steps),
            '--cfg', str(cfg)
        ]
        
        if seed:
            cmd.extend(['--seed', str(seed)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {'success': False, 'error': f'SDXL generation failed: {result.stderr}'}
        
        # The script should have created the image file
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

# Create blueprint
bp = Blueprint('imaging', __name__, url_prefix='/imaging')

@bp.route('/posts/<int:post_id>/sections/image-generation')
def imaging_sections_image_generation(post_id):
    """Image Generation page - standalone imaging workflow"""
    try:
        return render_template('imaging/sections/image_generation.html', 
                             post_id=post_id)
    except Exception as e:
        logger.error(f"Error rendering image generation page: {str(e)}")
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
    """Get sections data for imaging workflow"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description,
                       image_prompts, image_captions, selected_image_concept
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'sections': [dict(section) for section in sections]
            })
    except Exception as e:
        logger.error(f"Error getting sections data: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    """Generate image for a specific section - imaging standalone version"""
    try:
        data = request.get_json()
        model_name = data.get('model_name', 'dall-e-3')
        parameters = data.get('parameters', {})
        
        with db_manager.get_cursor() as cursor:
            # Get section data including image_prompts
            cursor.execute("""
                SELECT id, section_order, section_heading, image_prompts
                FROM post_section
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'})
            
            # Parse image_prompts JSON to get the actual prompt
            image_prompts_data = json.loads(section['image_prompts']) if section['image_prompts'] else {}
            image_prompt = image_prompts_data.get('image_prompt', '')
            
            if not image_prompt:
                return jsonify({'success': False, 'error': 'No image prompt found for this section'})
            
            # Route to appropriate image generation function based on model
            if model_name.startswith('dall-e') or model_name.startswith('openai'):
                result = imaging_generate_dalle_image(image_prompt, post_id, section_id, parameters)
            elif model_name.startswith('sdxl'):
                result = imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters)
            else:
                return jsonify({'success': False, 'error': f'Unsupported model: {model_name}'})
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'image_path': result['image_path'],
                    'message': 'Image generated successfully'
                })
            else:
                return jsonify({'success': False, 'error': result['error']})
                
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
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
