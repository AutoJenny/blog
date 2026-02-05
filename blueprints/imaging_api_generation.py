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
    imaging_generate_sdxl_image,
)
from blueprints.launchpad.workbench_api import _create_run_record, _complete_run_record

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register image generation API routes with the blueprint"""
    
    @bp.route('/api/image-generation/posts/<int:post_id>/sections/<section_id>/generate-image', methods=['POST'])
    def imaging_generate_image(post_id, section_id):
        """
        Generate landscape and/or portrait images for a section.
        Reads prompt from database, uses model and parameters from request.

        Phase I-1A: For blog_post images, record an immutable generation_runs row
        with the exact image_prompt used and engine_id before calling the generator,
        and complete the run after generation (success/failed) with output_refs.
        """
        run_id = None
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

            # Phase I-1A: create a single run record for this blog_post image generation
            # (section-level, primary slot). Platform/channel_type are API-level parameters;
            # default to facebook/blog_post for compatibility if not provided.
            platform = data.get('platform', 'facebook')
            channel_type = data.get('channel_type') or data.get('content_type', 'blog_post')
            engine_id = f"image/{model_name}"
            trigger = data.get('trigger', 'user')
            prompt_snapshot = {'image_prompt': image_prompt}

            try:
                run_id = _create_run_record(
                    content_ref=post_id,
                    platform=platform,
                    channel_type=channel_type,
                    engine_id=engine_id,
                    trigger=trigger,
                    prompt_snapshot=prompt_snapshot,
                    slot_identifier='primary',
                )
            except Exception as e:
                logger.error(f"[IMAGE_GENERATION] Failed to create image run record for post {post_id}, section {resolved_section_id}: {e}", exc_info=True)
                return jsonify({'success': False, 'error': 'Failed to create image run record'}), 500

            if not run_id:
                logger.error(f"[IMAGE_GENERATION] _create_run_record returned None for post {post_id}, section {resolved_section_id}")
                return jsonify({'success': False, 'error': 'Failed to create image run record'}), 500
            
            results = {
                'landscape_generated': False,
                'portrait_generated': False,
                'landscape_path': None,
                'portrait_path': None,
            }
            
            # Generate landscape image if requested
            if generate_landscape:
                landscape_params = parameters.copy()
                landscape_result = None
                
                logger.info(f"[IMAGE_GENERATION] Starting landscape generation for section {resolved_section_id} with model {model_name}")
                
                try:
                    if model_name == 'gpt-image-1':
                        landscape_result = imaging_generate_gpt_image_1(image_prompt, post_id, resolved_section_id, landscape_params, 'landscape')
                    elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                        landscape_result = imaging_generate_dalle_image(image_prompt, post_id, resolved_section_id, landscape_params, 'landscape')
                    elif model_name.startswith('sdxl'):
                        landscape_result = imaging_generate_sdxl_image(image_prompt, post_id, resolved_section_id, landscape_params, 'landscape')
                    else:
                        landscape_result = {'success': False, 'error': f'Unknown model: {model_name}'}
                except Exception as e:
                    logger.error(f"[IMAGE_GENERATION] Exception during landscape generation for section {resolved_section_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    landscape_result = {'success': False, 'error': f'Exception: {str(e)}'}
                
                if landscape_result is None:
                    logger.error(f"[IMAGE_GENERATION] Landscape generation returned None for section {resolved_section_id}")
                    landscape_result = {'success': False, 'error': 'Generator function returned None'}
                
                logger.info(f"[IMAGE_GENERATION] Landscape generation result: {landscape_result}")
                
                if landscape_result and landscape_result.get('success'):
                    results['landscape_generated'] = True
                    results['landscape_path'] = landscape_result.get('image_path')
                    logger.info(f"[IMAGE_GENERATION] Landscape generation succeeded: {results['landscape_path']}")
                else:
                    error_msg = landscape_result.get('error', 'Unknown error') if landscape_result else 'No result returned'
                    logger.error(f"[IMAGE_GENERATION] Landscape generation failed for section {resolved_section_id}: {error_msg}")
                    results['landscape_error'] = error_msg
            
            # Generate portrait image if requested
            if generate_portrait:
                portrait_params = parameters.copy()
                # Generator functions check portrait_size/portrait_width/portrait_height directly
                # No need to transform - just pass through
                
                portrait_result = None
                
                logger.info(f"[IMAGE_GENERATION] Starting portrait generation for section {resolved_section_id} with model {model_name}")
                
                try:
                    if model_name == 'gpt-image-1':
                        portrait_result = imaging_generate_gpt_image_1(image_prompt, post_id, resolved_section_id, portrait_params, 'portrait')
                    elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                        portrait_result = imaging_generate_dalle_image(image_prompt, post_id, resolved_section_id, portrait_params, 'portrait')
                    elif model_name.startswith('sdxl'):
                        portrait_result = imaging_generate_sdxl_image(image_prompt, post_id, resolved_section_id, portrait_params, 'portrait')
                    else:
                        portrait_result = {'success': False, 'error': f'Unknown model: {model_name}'}
                except Exception as e:
                    logger.error(f"[IMAGE_GENERATION] Exception during portrait generation for section {resolved_section_id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    portrait_result = {'success': False, 'error': f'Exception: {str(e)}'}
                
                if portrait_result is None:
                    logger.error(f"[IMAGE_GENERATION] Portrait generation returned None for section {resolved_section_id}")
                    portrait_result = {'success': False, 'error': 'Generator function returned None'}
                
                logger.info(f"[IMAGE_GENERATION] Portrait generation result: {portrait_result}")
                
                if portrait_result and portrait_result.get('success'):
                    results['portrait_generated'] = True
                    results['portrait_path'] = portrait_result.get('image_path')
                    logger.info(f"[IMAGE_GENERATION] Portrait generation succeeded: {results['portrait_path']}")
                else:
                    error_msg = portrait_result.get('error', 'Unknown error') if portrait_result else 'No result returned'
                    logger.error(f"[IMAGE_GENERATION] Portrait generation failed for section {resolved_section_id}: {error_msg}")
                    results['portrait_error'] = error_msg
            
            # Return response
            response_data = {
                'success': True,
                'landscape_generated': results['landscape_generated'],
                'portrait_generated': results['portrait_generated'],
                'landscape_path': results['landscape_path'],
                'portrait_path': results['portrait_path']
            }
            
            # Include error messages if generation failed
            if 'landscape_error' in results:
                response_data['landscape_error'] = results['landscape_error']
            if 'portrait_error' in results:
                response_data['portrait_error'] = results['portrait_error']
            
            logger.info(
                f"[IMAGE_GENERATION] Final response for section {resolved_section_id}: "
                f"landscape={results['landscape_generated']}, portrait={results['portrait_generated']}"
            )

            # Phase I-1A: complete run record with output_refs and status
            if run_id:
                try:
                    output_refs = {
                        'type': 'blog_post_section_image',
                        'post_id': post_id,
                        'section_id': resolved_section_id,
                        'landscape_generated': results['landscape_generated'],
                        'portrait_generated': results['portrait_generated'],
                        'landscape_path': results['landscape_path'],
                        'portrait_path': results['portrait_path'],
                    }
                    if 'landscape_error' in results:
                        output_refs['landscape_error'] = results['landscape_error']
                    if 'portrait_error' in results:
                        output_refs['portrait_error'] = results['portrait_error']

                    # Success if at least one orientation generated; otherwise failed.
                    run_status = 'success' if (results['landscape_generated'] or results['portrait_generated']) else 'failed'
                    error_message = None
                    if run_status == 'failed':
                        error_message = results.get('portrait_error') or results.get('landscape_error')

                    _complete_run_record(run_id, run_status, output_refs, error_message)
                except Exception as e:
                    logger.error(f"[IMAGE_GENERATION] Failed to complete image run record {run_id}: {e}", exc_info=True)

            return jsonify(response_data)

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Best-effort: mark run as failed if it was created
            if run_id:
                try:
                    _complete_run_record(run_id, 'failed', None, str(e))
                except Exception:
                    logger.error(f"[IMAGE_GENERATION] Failed to mark run {run_id} as failed after exception", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

