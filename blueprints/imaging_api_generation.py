"""
Image Generation API Endpoints
Generates landscape and/or portrait images based on request
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
import logging
import json
import os
import re

from blueprints.imaging_generators import (
    imaging_generate_dalle_image,
    imaging_generate_gpt_image_1,
    imaging_generate_sdxl_image
)

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register image generation API routes with the blueprint"""
    
    @bp.route('/api/image-generation/posts/<int:post_id>/sections/<section_id>/generate-image', methods=['POST'])
    def imaging_generate_image(post_id, section_id):
        """
        Generate landscape and/or portrait images for a section.
        Reads prompt from database, uses model and parameters from request.
        """
        try:
            data = request.get_json() or {}
            model_name = data.get('model_name', 'gpt-image-1')
            parameters = data.get('parameters', {})
            generate_landscape = data.get('generate_landscape', True)
            generate_portrait = data.get('generate_portrait', True)
            
            # Resolve section_id
            resolved_section_id = None
            if section_id.isdigit():
                resolved_section_id = int(section_id)
            else:
                m = re.search(r'(\d+)$', section_id)
                if m:
                    section_order = int(m.group(1))
                    with db_manager.get_cursor() as cursor:
                        cursor.execute(
                            "SELECT id FROM post_section WHERE post_id = %s AND section_order = %s",
                            (post_id, section_order),
                        )
                        row = cursor.fetchone()
                        if row:
                            resolved_section_id = row['id']

            if resolved_section_id is None:
                return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400
            
            # Get image prompt from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT image_prompts FROM post_section 
                    WHERE id = %s AND post_id = %s
                """, (resolved_section_id, post_id))
                section_row = cursor.fetchone()
                
                if not section_row or not section_row['image_prompts']:
                    return jsonify({'success': False, 'error': 'No image prompt found for this section'})
                
                # Extract image prompt
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
                """, (resolved_section_id, post_id))
                
                section = cursor.fetchone()
                if not section:
                    return jsonify({'success': False, 'error': 'Section not found'})
            
            results = {
                'landscape_generated': False,
                'portrait_generated': False,
                'landscape_path': None,
                'portrait_path': None
            }
            
            # Generate landscape image if requested
            if generate_landscape:
                landscape_params = parameters.copy()
                landscape_result = None
                
                if model_name == 'gpt-image-1':
                    landscape_result = imaging_generate_gpt_image_1(image_prompt, post_id, resolved_section_id, landscape_params, 'landscape')
                elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                    landscape_result = imaging_generate_dalle_image(image_prompt, post_id, resolved_section_id, landscape_params, 'landscape')
                elif model_name.startswith('sdxl'):
                    landscape_result = imaging_generate_sdxl_image(image_prompt, post_id, resolved_section_id, landscape_params, 'landscape')
                
                if landscape_result and landscape_result.get('success'):
                    results['landscape_generated'] = True
                    results['landscape_path'] = landscape_result.get('image_path')
            
            # Generate portrait image if requested
            if generate_portrait:
                portrait_params = parameters.copy()
                # Generator functions check portrait_size/portrait_width/portrait_height directly
                # No need to transform - just pass through
                
                portrait_result = None
                
                if model_name == 'gpt-image-1':
                    portrait_result = imaging_generate_gpt_image_1(image_prompt, post_id, resolved_section_id, portrait_params, 'portrait')
                elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                    portrait_result = imaging_generate_dalle_image(image_prompt, post_id, resolved_section_id, portrait_params, 'portrait')
                elif model_name.startswith('sdxl'):
                    portrait_result = imaging_generate_sdxl_image(image_prompt, post_id, resolved_section_id, portrait_params, 'portrait')
                
                if portrait_result and portrait_result.get('success'):
                    results['portrait_generated'] = True
                    results['portrait_path'] = portrait_result.get('image_path')
            
            # Return response
            response_data = {
                'success': True,
                'landscape_generated': results['landscape_generated'],
                'portrait_generated': results['portrait_generated'],
                'landscape_path': results['landscape_path'],
                'portrait_path': results['portrait_path']
            }
            
            return jsonify(response_data)
                    
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)})

