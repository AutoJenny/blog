"""
Image Generation API Endpoints
API routes for generating images via different models
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from modules.prompt_service import prompt_service
import logging
import json
import time
import os
import re

from blueprints.imaging_generators import (
    imaging_generate_dalle_image,
    imaging_generate_gpt_image_1,
    imaging_generate_sdxl_image
)
from blueprints.imaging_optimization import optimize_image_with_watermark
from utils.taxonomy_helpers import get_post_type

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register image generation API routes with the blueprint"""
    
    @bp.route('/api/image-generation/posts/<int:post_id>/sections/<int:section_id>/generate-image', methods=['POST'])
    def imaging_generate_image(post_id, section_id):
        """Generate image for a specific section - simplified version using only full image prompt"""
        try:
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

    @bp.route('/api/image-generation/posts/<int:post_id>/sections/<section_id>/generate-image', methods=['POST'])
    def imaging_generate_image_flexible(post_id, section_id):
        """Generate image accepting string section IDs (e.g., section_1). Maps to post_section by section_order."""
        try:
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
            
            # For recipe posts, ensure landscape dimensions
            post_type = get_post_type(post_id)
            if post_type == 'recipe':
                # Set landscape dimensions for recipe images
                if model_name == 'gpt-image-1':
                    parameters['size'] = '1536x1024'  # Landscape (max supported by GPT-Image-1)
                    parameters['portrait_size'] = '1024x1792'  # Portrait (for header)
                elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                    parameters['size'] = '1792x1024'  # Landscape (DALL-E supports this)
                elif model_name.startswith('sdxl'):
                    parameters['width'] = 1792
                    parameters['height'] = 1024
            
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
                
                # Automatically optimize and watermark the section image after generation
                logger.info(f"Automatically optimizing section image for post {post_id}, section {resolved_section_id}")
                optimize_params = {
                    'quality': 50,
                    'overlay_text': 'AI-generated image',
                    'watermark': True,
                    'text_overlay': True
                }
                watermark_result = optimize_image_with_watermark(post_id, resolved_section_id, optimize_params)
                
                if watermark_result.get('success'):
                    optimized_path = watermark_result.get('optimized_path')
                    logger.info(f"Optimization successful, optimized_path: {optimized_path}")
                    # Save optimized image to database
                    with db_manager.get_cursor() as cursor:
                        # Get optimized image path
                        optimized_path_db = optimized_path.lstrip('/') if optimized_path else None
                        
                        if optimized_path_db:
                            logger.info(f"Saving optimized image to database: {optimized_path_db}")
                            # Insert or update image record
                            cursor.execute("""
                                INSERT INTO image (filename, path, alt_text, caption)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (path) DO UPDATE 
                                SET filename = EXCLUDED.filename, alt_text = EXCLUDED.alt_text, caption = EXCLUDED.caption
                                RETURNING id
                            """, (
                                f"{resolved_section_id}_optimized.jpg",
                                f"/{optimized_path_db}",
                                f"Optimized image for section {resolved_section_id}",
                                "AI-generated image"
                            ))
                            image_record = cursor.fetchone()
                            if image_record:
                                image_id = image_record['id']
                                logger.info(f"Image record created/updated with ID: {image_id}")
                                
                                # Delete any existing post_images link for this section's optimized image
                                cursor.execute("""
                                    DELETE FROM post_images 
                                    WHERE section_id = %s AND image_type = 'section_optimized'
                                """, (resolved_section_id,))
                                
                                # Create post_images link (include post_id as required by schema)
                                cursor.execute("""
                                    INSERT INTO post_images (post_id, section_id, image_id, image_type)
                                    VALUES (%s, %s, %s, 'section_optimized')
                                """, (post_id, resolved_section_id, image_id))
                                
                                cursor.connection.commit()
                                logger.info(f"post_images link created: post_id={post_id}, section_id={resolved_section_id}, image_id={image_id}")
                            else:
                                logger.error(f"Failed to get image_id after INSERT/UPDATE")
                        else:
                            logger.error(f"optimized_path_db is None or empty")
                else:
                    error_msg = watermark_result.get('error', 'Unknown error')
                    logger.error(f"Section image optimization failed: {error_msg}")
                    # Continue anyway - raw image was generated successfully
                
                # Log generation event
                prompt_service.log_generation_event(
                    post_id=post_id,
                    section_id=resolved_section_id,
                    model_key=model_name,
                    params=parameters,
                    prompt_text=image_prompt,
                    rendered_prompt=image_prompt,
                    result_path=watermark_result.get('optimized_path') or result['image_path'],
                    success=True,
                    generation_time_ms=generation_time_ms
                )
                
                # Return response with optimization status
                response_data = {
                    'success': True,
                    'image_path': result['image_path'],
                    'resolved_section_id': resolved_section_id,
                    'message': 'Image generated successfully',
                    'debug_info': debug_info,
                    'generation_time_ms': generation_time_ms
                }
                
                # Include optimization status in response
                if watermark_result.get('success'):
                    response_data['optimized_path'] = watermark_result.get('optimized_path')
                    response_data['optimization_success'] = True
                    response_data['message'] = 'Image generated and optimized successfully'
                else:
                    response_data['optimization_success'] = False
                    response_data['optimization_error'] = watermark_result.get('error', 'Unknown error')
                    response_data['message'] = f"Image generated but optimization failed: {watermark_result.get('error', 'Unknown error')}"
                
                return jsonify(response_data)
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

