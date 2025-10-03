"""
Image Generation API

Flask API endpoints for image generation functionality.
"""

import json
import logging
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .services import ImageGenerationService

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('image_generation_api', __name__, url_prefix='/api/image-generation')

# Initialize service
image_service = ImageGenerationService()


@bp.route('/prompts/image-generation', methods=['GET'])
def api_image_generation_prompt():
    """Get or update the image generation prompt"""
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
                
                # Get available image generation models
                cursor.execute("""
                    SELECT lm.id, lm.name, lm.description, lm.api_params,
                           lp.name as provider_name, lp.type as provider_type
                    FROM llm_model lm
                    JOIN llm_provider lp ON lm.provider_id = lp.id
                    WHERE lm.name IN ('sdxl-lora', 'dall-e-3', 'dall-e-2')
                    ORDER BY CASE 
                        WHEN lm.name = 'sdxl-lora' THEN 1
                        WHEN lm.name = 'dall-e-3' THEN 2
                        WHEN lm.name = 'dall-e-2' THEN 3
                        ELSE 4
                    END
                """)
                available_models = cursor.fetchall()
                
                if prompt:
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'id': prompt['id'],
                            'name': prompt['name'],
                            'prompt_text': prompt['prompt_text'],
                            'description': prompt['description']
                        },
                        'llm_config': {
                            'provider': 'Ollama',
                            'model': 'sdxl-lora',
                            'temperature': 0.7,
                            'max_tokens': 2000
                        },
                        'available_models': available_models
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


@bp.route('/posts/<int:post_id>/sections/<int:section_id>/generate-image', methods=['POST'])
def api_generate_image(post_id, section_id):
    """Generate image for a specific section using selected model"""
    try:
        # Get request data
        data = request.get_json() or {}
        model_name = data.get('model_name', 'sdxl-lora')
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
            
            # Generate image using the service
            result = image_service.generate_image(image_prompt, post_id, section_id, model_name, parameters)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'image_path': result['image_path'],
                    'message': result.get('message', 'Image generated successfully'),
                    'model_used': model_name.upper()
                })
            else:
                return jsonify({'success': False, 'error': result['error']})
                
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
