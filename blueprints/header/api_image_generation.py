"""Image generation API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .llm_service import LLMService
from blueprints.imaging_generators import imaging_generate_dalle_image, imaging_generate_gpt_image_1, imaging_generate_sdxl_image
import logging
import json
import re
import time

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register image generation API routes"""
    
    @bp.route('/api/model-specs', methods=['GET'])
    def header_get_model_specs():
        """Get model specifications for header imaging (shared with imaging blueprint)"""
        try:
            # Reuse the imaging blueprint's model specs endpoint
            from blueprints.imaging_api_config import imaging_get_model_specs_handler
            return imaging_get_model_specs_handler()
        except Exception as e:
            logger.error(f"Error getting model specs: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/model-selection', methods=['GET', 'POST'])
    def header_model_selection():
        """Get or save model selection configuration (shared with imaging blueprint)"""
        try:
            # Reuse the imaging blueprint's model selection endpoint
            from blueprints.imaging_api_config import imaging_model_selection_handler
            return imaging_model_selection_handler()
        except Exception as e:
            logger.error(f"Error with model selection: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-header-image', methods=['POST'])
    def api_generate_header_image(post_id):
        """Generate header image with custom dimensions and automatic watermarking using model-aware renderers"""
        try:
            from modules.prompt_service import prompt_service
            
            data = request.get_json()
            model_name = data.get('model_name', 'dall-e-3')
            parameters = data.get('parameters', {})
            use_renderer = data.get('use_renderer', True)  # Feature flag
            
            # Get illustration_method from query parameter or post taxonomy
            illustration_method = request.args.get('illustration_method', None)
            if illustration_method is None:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT ti.illustration_method
                        FROM post p
                        LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                        WHERE p.id = %s
                    """, (post_id,))
                    result = cursor.fetchone()
                    illustration_method = (result.get('illustration_method') if result else None) or 'LLM-creation'
            
            # Get rendered prompt using the new system
            if use_renderer:
                # For header images, we need to compile a collage prompt from all sections
                rendered_prompt, debug_info = prompt_service.render_header_prompt_for_model(
                    post_id, model_name, use_override=True, illustration_method=illustration_method
                )
                
                if not rendered_prompt:
                    return jsonify({'error': 'No sections available to create header prompt'}), 400
                
                image_prompt = rendered_prompt
            else:
                # Fallback to original prompt from request
                image_prompt = data.get('image_prompt', '')
                debug_info = {'source': 'fallback', 'model_key': model_name}
            
            if not image_prompt:
                return jsonify({'error': 'No image prompt provided'}), 400
            
            # Import imaging functions
            from blueprints.imaging_optimization import optimize_image_with_watermark
            
            # Set custom dimensions and style for header image
            # For Photo-harvesting route, use photorealistic settings
            if illustration_method == 'Photo-harvesting':
                # Photo-harvesting route: use gpt-image-1 with photorealistic settings
                if model_name == 'gpt-image-1':
                    parameters['size'] = '1536x1024'  # Landscape format
                    parameters['portrait_size'] = '1024x1536'  # Portrait format
                    parameters['quality'] = 'high'  # High quality for photorealistic (gpt-image-1 uses 'high' not 'hd')
                elif model_name == 'dall-e-3':
                    parameters['size'] = '1792x1024'
                    parameters['quality'] = 'hd'
                    parameters['style'] = 'natural'  # Photorealistic
                else:
                    # For other models, use photorealistic defaults
                    parameters['width'] = 2358
                    parameters['height'] = 1048
            elif model_name == 'dall-e-3':
                # DALL-E uses predefined sizes, closest to 2358x1048 is 1792x1024
                parameters['size'] = '1792x1024'
                # Fix quality parameter for DALL-E (must be string, not number)
                if 'quality' in parameters and isinstance(parameters['quality'], int):
                    parameters['quality'] = 'hd' if parameters['quality'] > 50 else 'standard'
                else:
                    parameters['quality'] = 'standard'
                # Set style parameter
                parameters['style'] = 'natural'
            else:
                # SDXL can use custom dimensions
                parameters['width'] = 2358
                parameters['height'] = 1048
            
            # Start timing
            start_time = time.time()
            
            # Generate both landscape and portrait images (same as section images)
            results = {
                'landscape_generated': False,
                'portrait_generated': False,
                'landscape_path': None,
                'portrait_path': None
            }
            
            # Generate landscape image
            logger.info(f"[HEADER_IMAGE_GENERATION] Starting landscape generation for post {post_id} with model {model_name}")
            landscape_result = None
            try:
                if model_name == 'gpt-image-1':
                    landscape_result = imaging_generate_gpt_image_1(image_prompt, post_id, 'header', parameters, 'landscape')
                elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                    landscape_result = imaging_generate_dalle_image(image_prompt, post_id, 'header', parameters, 'landscape')
                elif model_name.startswith('sdxl'):
                    landscape_result = imaging_generate_sdxl_image(image_prompt, post_id, 'header', parameters, 'landscape')
                else:
                    landscape_result = {'success': False, 'error': f'Unknown model: {model_name}'}
            except Exception as e:
                logger.error(f"[HEADER_IMAGE_GENERATION] Exception during landscape generation: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                landscape_result = {'success': False, 'error': f'Exception: {str(e)}'}
            
            if landscape_result and landscape_result.get('success'):
                results['landscape_generated'] = True
                results['landscape_path'] = landscape_result.get('image_path')
                logger.info(f"[HEADER_IMAGE_GENERATION] Landscape image generated: {results['landscape_path']}")
            else:
                logger.error(f"[HEADER_IMAGE_GENERATION] Landscape generation failed: {landscape_result.get('error') if landscape_result else 'No result'}")
            
            # Generate portrait image
            logger.info(f"[HEADER_IMAGE_GENERATION] Starting portrait generation for post {post_id} with model {model_name}")
            portrait_result = None
            try:
                if model_name == 'gpt-image-1':
                    portrait_result = imaging_generate_gpt_image_1(image_prompt, post_id, 'header', parameters, 'portrait')
                elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                    portrait_result = imaging_generate_dalle_image(image_prompt, post_id, 'header', parameters, 'portrait')
                elif model_name.startswith('sdxl'):
                    portrait_result = imaging_generate_sdxl_image(image_prompt, post_id, 'header', parameters, 'portrait')
                else:
                    portrait_result = {'success': False, 'error': f'Unknown model: {model_name}'}
            except Exception as e:
                logger.error(f"[HEADER_IMAGE_GENERATION] Exception during portrait generation: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                portrait_result = {'success': False, 'error': f'Exception: {str(e)}'}
            
            if portrait_result and portrait_result.get('success'):
                results['portrait_generated'] = True
                results['portrait_path'] = portrait_result.get('image_path')
                logger.info(f"[HEADER_IMAGE_GENERATION] Portrait image generated: {results['portrait_path']}")
            else:
                logger.error(f"[HEADER_IMAGE_GENERATION] Portrait generation failed: {portrait_result.get('error') if portrait_result else 'No result'}")
            
            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # At least one image must succeed
            if not results['landscape_generated'] and not results['portrait_generated']:
                error_msg = f"Both landscape and portrait generation failed. Landscape: {landscape_result.get('error') if landscape_result else 'No result'}, Portrait: {portrait_result.get('error') if portrait_result else 'No result'}"
                logger.error(f"[HEADER_IMAGE_GENERATION] {error_msg}")
                # Log failed generation event
                prompt_service.log_generation_event(
                    post_id=post_id,
                    section_id=None,  # Header images don't have section_id
                    model_key=model_name,
                    params=parameters,
                    prompt_text=image_prompt,
                    rendered_prompt=image_prompt,
                    result_path='',
                    success=False,
                    error_message=error_msg,
                    generation_time_ms=generation_time_ms
                )
                return jsonify({'error': error_msg}), 500
            
            # Use landscape result as primary result for compatibility
            result = landscape_result if results['landscape_generated'] else portrait_result
            
            # Automatically optimize and watermark the header image after generation
            logger.info(f"Automatically optimizing header image for post {post_id}")
            watermark_result = optimize_image_with_watermark(post_id, 'header', parameters)
            
            if not watermark_result.get('success'):
                logger.error(f"Header image optimization failed: {watermark_result.get('error', 'Unknown error')}")
                # NO FALLBACK - optimization must succeed for image to be shown
                return jsonify({
                    'success': False,
                    'error': f"Image generation succeeded but optimization failed: {watermark_result.get('error', 'Unknown error')}"
                }), 500
            
            # Create or update image table record
            with db_manager.get_cursor() as cursor:
                # Check if header image already exists
                cursor.execute("""
                    SELECT header_image_id FROM post WHERE id = %s
                """, (post_id,))
                
                existing_image_id = cursor.fetchone()
                
                # Get the optimized path - ONLY optimized, no fallback to raw
                new_path = watermark_result.get('optimized_path')
                if not new_path:
                    logger.error(f"No optimized path returned from watermark_result for post {post_id}")
                    return jsonify({
                        'success': False,
                        'error': 'Image optimization did not return an optimized path'
                    }), 500
                # Normalize path: strip leading slash, then ensure it starts with /static/
                # This matches the normalization in api_optimize_header_image for consistency
                if new_path:
                    new_path = new_path.lstrip('/')
                    if not new_path.startswith('static/'):
                        new_path = 'static/' + new_path.lstrip('/')
                    new_path = '/' + new_path  # Add leading slash
                
                # CRITICAL: Write to images table (plural) with file_path column - foreign keys point here
                if existing_image_id and existing_image_id['header_image_id']:
                    # Update existing image record
                    cursor.execute("""
                        UPDATE images 
                        SET filename = %s, original_filename = %s, file_path = %s, 
                            image_prompt = %s, alt_text = %s, caption = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        'header.jpg',
                        'original_header.png', 
                        new_path,
                        image_prompt,
                        'Header image for blog post',
                        'Generated header image',
                        existing_image_id['header_image_id']
                    ))
                    image_id = existing_image_id['header_image_id']
                else:
                    # Create new image record
                    cursor.execute("""
                        INSERT INTO images (filename, original_filename, file_path, image_prompt, alt_text, caption)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        'header.jpg',
                        'original_header.png', 
                        new_path,
                        image_prompt,
                        'Header image for blog post',
                        'Generated header image'
                    ))
                    
                    image_id = cursor.fetchone()['id']
                    
                    # Update post table with header image reference
                    cursor.execute("""
                        UPDATE post 
                        SET header_image_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (image_id, post_id))
                
                # CRITICAL: Create post_images record for publishing system (same as api_optimize_header_image)
                # Delete any existing post_images link for header_optimized
                cursor.execute("""
                    DELETE FROM post_images 
                    WHERE post_id = %s AND section_id IS NULL AND image_type = 'header_optimized'
                """, (post_id,))
                
                # Create post_images link for header_optimized
                cursor.execute("""
                    INSERT INTO post_images (post_id, section_id, image_id, image_type)
                    VALUES (%s, NULL, %s, 'header_optimized')
                """, (post_id, image_id))
                
                # Log successful generation event
                prompt_service.log_generation_event(
                    post_id=post_id,
                    section_id=None,  # Header images don't have section_id
                    model_key=model_name,
                    params=parameters,
                    prompt_text=image_prompt,
                    rendered_prompt=image_prompt,
                    result_path=new_path,
                    success=True,
                    generation_time_ms=generation_time_ms
                )
                
                # Build response with both landscape and portrait information
                response_data = {
                    'success': True,
                    'image_path': new_path,
                    'raw_path': result.get('local_path', ''),
                    'generation_time_ms': generation_time_ms,
                    'landscape_generated': results.get('landscape_generated', False),
                    'portrait_generated': results.get('portrait_generated', False)
                }
                
                # Include portrait path if available
                if results.get('portrait_path'):
                    response_data['portrait_path'] = results['portrait_path']
                
                # Add additional fields for compatibility
                response_data['image_id'] = image_id
                response_data['optimized_path'] = new_path
                response_data['dimensions'] = {'width': 2358, 'height': 1048}
                response_data['debug_info'] = debug_info
                
                return jsonify(response_data)
                
        except Exception as e:
            logger.error(f"Error generating header image for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/get-header-image', methods=['GET'])
    def api_get_header_image(post_id):
        """Get existing header image from database"""
        try:
            with db_manager.get_cursor() as cursor:
                # Note: foreign key references image_archive.id, so join there
                cursor.execute("""
                    SELECT i.id, i.filename, i.path, 
                           i.alt_text, i.caption, i.image_prompt
                    FROM post p
                    JOIN image_archive i ON p.header_image_id = i.id
                    WHERE p.id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'No header image found'}), 404
                
                return jsonify({
                    'success': True,
                    'image_id': result['id'],
                    'filename': result['filename'],
                    'path': result['path'],
                    'alt_text': result['alt_text'],
                    'caption': result['caption'],
                    'image_prompt': result['image_prompt']
                })
                
        except Exception as e:
            logger.error(f"Error getting header image for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-image-details', methods=['POST'])
    def api_generate_image_details(post_id):
        """Generate caption, alt text, and title for header image using LLM"""
        try:
            # Get the image prompt from the database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT i.image_prompt 
                    FROM post p
                    JOIN images i ON p.header_image_id = i.id
                    WHERE p.id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result or not result['image_prompt']:
                    return jsonify({'error': 'No header image found or no image prompt available'}), 404
                
                image_prompt = result['image_prompt']
            
            # Get prompts from database for image details generation (step 65)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                    JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                    WHERE wsp.step_id = 65
                """)
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'Image details generation prompts not found'}), 404
                
                system_prompt = result.get('system_prompt', '')
                task_prompt = result.get('task_prompt', '')
            
            # Use LLM service to generate details
            llm_service = LLMService()
            
            # Format the prompt with the image prompt
            formatted_prompt = task_prompt.format(image_prompt=image_prompt)
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_prompt}
            ]
            
            # Generate details using LLM
            try:
                llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                
                if 'error' in llm_response:
                    logger.error(f"LLM generation failed: {llm_response['error']}")
                    raise Exception("LLM failed")
                
                details_text = llm_response.get('content', '').strip()
                
                if not details_text:
                    raise Exception("Empty response")
                
                # Parse JSON response - clean up the text first
                
                # Try to extract JSON from the response (handle cases where LLM adds extra text)
                json_match = re.search(r'\{[\s\S]*\}', details_text)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = details_text
                
                # Remove any extra escaping and clean up
                json_text = json_text.replace('\\\\', '\\').replace('\\"', '"')
                
                # Try to parse
                try:
                    details_json = json.loads(json_text)
                    caption = details_json.get('caption', '')
                    alt_text = details_json.get('alt_text', '')
                    title = details_json.get('title', '')
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error: {je}, text: {repr(json_text)}")
                    raise je
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error parsing LLM response: {e}, text: {repr(details_text)}")
                # Fallback to simple generation based on image prompt
                caption = f"Header image collage"
                alt_text = f"Blog header image collage featuring multiple visual elements"
                title = "Blog Header Image"
            
            # Auto-save to database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE images 
                    SET caption = %s, alt_text = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT header_image_id FROM post WHERE id = %s
                    )
                """, (caption, alt_text, post_id))
            
            return jsonify({
                'success': True,
                'caption': caption,
                'alt_text': alt_text,
                'title': title
            })
            
        except Exception as e:
            logger.error(f"Error generating image details for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/save-image-details', methods=['POST'])
    def api_save_image_details(post_id):
        """Save image details to database"""
        try:
            data = request.get_json()
            caption = data.get('caption', '')
            alt_text = data.get('alt_text', '')
            title = data.get('title', '')
            
            with db_manager.get_cursor() as cursor:
                # Update images table with details
                cursor.execute("""
                    UPDATE images 
                    SET caption = %s, alt_text = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT header_image_id FROM post WHERE id = %s
                    )
                """, (caption, alt_text, post_id))
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'No header image found to update'}), 404
                
                return jsonify({'success': True})
                
        except Exception as e:
            logger.error(f"Error saving image details for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/optimize-header-image', methods=['POST'])
    def api_optimize_header_image(post_id):
        """Optimize header image with watermark"""
        try:
            # Import the optimization function
            from blueprints.imaging_optimization import optimize_image_with_watermark
            
            # Get parameters from request (optional)
            params = request.get_json() or {}
            
            # Optimize the header image (both landscape and portrait)
            result = optimize_image_with_watermark(post_id, 'header', params)
            
            if result['success']:
                # Save optimized image to image table and create post_images link
                with db_manager.get_cursor() as cursor:
                    # Get optimized image paths and normalize consistently
                    optimized_path = result.get('optimized_path')
                    if optimized_path:
                        # Normalize path: strip leading slash, then ensure it starts with /static/
                        # This matches the normalization in api_generate_header_image and load_header_image_from_db
                        optimized_path = optimized_path.lstrip('/')
                        if not optimized_path.startswith('static/'):
                            optimized_path = 'static/' + optimized_path.lstrip('/')
                        optimized_path = '/' + optimized_path  # Add leading slash
                    else:
                        optimized_path = None
                    
                    portrait_optimized_path = result.get('portrait_path', '').lstrip('/') if result.get('portrait_path') else None
                    
                    # CRITICAL: Write to image table (singular) with path column - foreign keys point here
                    # Get the caption from the post's header_image_caption field
                    cursor.execute("SELECT header_image_caption, header_image_id FROM post WHERE id = %s", (post_id,))
                    post_row = cursor.fetchone()
                    caption = post_row['header_image_caption'] if post_row else None
                    existing_header_image_id = post_row['header_image_id'] if post_row else None
                    
                    if existing_header_image_id:
                        # Update existing image record
                        cursor.execute("""
                            UPDATE images 
                            SET filename = %s, file_path = %s, alt_text = %s, caption = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            'header.jpg',
                            optimized_path,
                            'Header image',
                            caption,
                            existing_header_image_id
                        ))
                        image_id = existing_header_image_id
                    else:
                        # Insert new record
                        cursor.execute("""
                            INSERT INTO images (filename, file_path, alt_text, caption)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (
                            'header.jpg',
                            optimized_path,
                            'Header image',
                            caption
                        ))
                        image_record = cursor.fetchone()
                        image_id = image_record['id']
                    
                    # Delete any existing post_images link for header_optimized
                    cursor.execute("""
                        DELETE FROM post_images 
                        WHERE post_id = %s AND section_id IS NULL AND image_type = 'header_optimized'
                    """, (post_id,))
                    
                    # Create post_images link for header_optimized
                    cursor.execute("""
                        INSERT INTO post_images (post_id, section_id, image_id, image_type)
                        VALUES (%s, NULL, %s, 'header_optimized')
                    """, (post_id, image_id))
                    
                    # Update post.header_image_id to point to optimized version
                    cursor.execute("""
                        UPDATE post SET header_image_id = %s WHERE id = %s
                    """, (image_id, post_id))
                
                response = {
                    'success': True,
                    'optimized_path': result['optimized_path'],
                    'message': 'Image optimized successfully and database records created'
                }
                # Include portrait path if available
                if result.get('portrait_path'):
                    response['portrait_optimized_path'] = result['portrait_path']
                    response['message'] = 'Landscape and portrait images optimized successfully'
                
                return jsonify(response)
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Optimization failed')
                }), 500
                
        except Exception as e:
            logger.error(f"Error optimizing header image for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

