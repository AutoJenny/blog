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
        """Generate header image: landscape and portrait, then optimize both"""
        try:
            data = request.get_json()
            image_prompt = data.get('image_prompt', '').strip()
            model_name = data.get('model_name', 'gpt-image-1')
            parameters = data.get('parameters', {})
            reference_image_url = data.get('reference_image_url')  # For profile posts
            
            if not image_prompt:
                return jsonify({'error': 'No image prompt provided'}), 400
            
            # Get dimensions from parameters
            landscape_size = parameters.get('size', '1536x1024')
            portrait_size = parameters.get('portrait_size', '1024x1536')
            quality = parameters.get('quality', 'high')
            
            # Import generators
            from blueprints.imaging_generators import imaging_generate_gpt_image_1, imaging_generate_dalle_image, imaging_generate_sdxl_image
            
            # Generate landscape image
            logger.info(f"[HEADER_IMAGE] Generating landscape image for post {post_id}")
            landscape_params = {'size': landscape_size, 'quality': quality}
            if reference_image_url:
                landscape_params['reference_image_url'] = reference_image_url
            if model_name == 'gpt-image-1':
                landscape_result = imaging_generate_gpt_image_1(image_prompt, post_id, 'header', landscape_params, 'landscape')
            elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                landscape_result = imaging_generate_dalle_image(image_prompt, post_id, 'header', landscape_params, 'landscape')
            elif model_name.startswith('sdxl'):
                landscape_result = imaging_generate_sdxl_image(image_prompt, post_id, 'header', landscape_params, 'landscape')
            else:
                return jsonify({'error': f'Unknown model: {model_name}'}), 400
            
            if not landscape_result.get('success'):
                return jsonify({'error': f'Landscape generation failed: {landscape_result.get("error")}'}), 500
            
            # Generate portrait image
            logger.info(f"[HEADER_IMAGE] Generating portrait image for post {post_id}")
            portrait_params = {'portrait_size': portrait_size, 'quality': quality}
            if reference_image_url:
                portrait_params['reference_image_url'] = reference_image_url
            if model_name == 'gpt-image-1':
                portrait_result = imaging_generate_gpt_image_1(image_prompt, post_id, 'header', portrait_params, 'portrait')
            elif model_name.startswith('dall-e') or model_name.startswith('openai'):
                portrait_result = imaging_generate_dalle_image(image_prompt, post_id, 'header', portrait_params, 'portrait')
            elif model_name.startswith('sdxl'):
                portrait_result = imaging_generate_sdxl_image(image_prompt, post_id, 'header', portrait_params, 'portrait')
            else:
                return jsonify({'error': f'Unknown model: {model_name}'}), 400
            
            if not portrait_result.get('success'):
                return jsonify({'error': f'Portrait generation failed: {portrait_result.get("error")}'}), 500
            
            # Optimize both images
            logger.info(f"[HEADER_IMAGE] Optimizing images for post {post_id}")
            from blueprints.imaging_optimization import optimize_image_with_watermark
            optimize_result = optimize_image_with_watermark(post_id, 'header', parameters)
            
            if not optimize_result.get('success'):
                return jsonify({'error': f'Optimization failed: {optimize_result.get("error")}'}), 500
            
            # Save optimized image to database (same logic as api_optimize_header_image)
            optimized_path = optimize_result.get('optimized_path')
            if optimized_path:
                with db_manager.get_cursor() as cursor:
                    # Normalize path
                    optimized_path = optimized_path.lstrip('/')
                    if not optimized_path.startswith('static/'):
                        optimized_path = 'static/' + optimized_path.lstrip('/')
                    optimized_path = '/' + optimized_path
                    
                    # Get caption from post
                    cursor.execute("SELECT header_image_caption, header_image_id FROM post WHERE id = %s", (post_id,))
                    post_row = cursor.fetchone()
                    caption = post_row['header_image_caption'] if post_row else None
                    existing_header_image_id = post_row['header_image_id'] if post_row else None
                    
                    # Check if we need to use image_archive or images table
                    # First check what post_images references
                    cursor.execute("""
                        SELECT pi.image_id, 
                               CASE WHEN EXISTS (SELECT 1 FROM image_archive WHERE id = pi.image_id) THEN 'image_archive'
                                    WHEN EXISTS (SELECT 1 FROM images WHERE id = pi.image_id) THEN 'images'
                                    ELSE NULL END as table_name
                        FROM post_images pi
                        WHERE pi.post_id = %s AND pi.image_type = 'header_optimized'
                        LIMIT 1
                    """, (post_id,))
                    existing_link = cursor.fetchone()
                    
                    # Determine which table to use based on existing data or default to image_archive
                    use_image_archive = True
                    if existing_link and existing_link.get('table_name'):
                        use_image_archive = (existing_link['table_name'] == 'image_archive')
                    else:
                        # Check if image_archive table exists and has the right structure
                        cursor.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'image_archive' AND column_name = 'path'
                        """)
                        if cursor.fetchone():
                            use_image_archive = True
                        else:
                            use_image_archive = False
                    
                    if use_image_archive:
                        # Use image_archive table (path column)
                        if existing_header_image_id:
                            cursor.execute("""
                                UPDATE image_archive 
                                SET filename = %s, path = %s, alt_text = %s, caption = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, ('header.jpg', optimized_path, 'Header image', caption, existing_header_image_id))
                            image_id = existing_header_image_id
                        else:
                            cursor.execute("""
                                INSERT INTO image_archive (filename, path, alt_text, caption)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, ('header.jpg', optimized_path, 'Header image', caption))
                            image_record = cursor.fetchone()
                            image_id = image_record['id']
                            cursor.execute("UPDATE post SET header_image_id = %s WHERE id = %s", (image_id, post_id))
                    else:
                        # Use images table (file_path column)
                        if existing_header_image_id:
                            cursor.execute("""
                                UPDATE images 
                                SET filename = %s, file_path = %s, alt_text = %s, caption = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, ('header.jpg', optimized_path, 'Header image', caption, existing_header_image_id))
                            image_id = existing_header_image_id
                        else:
                            cursor.execute("""
                                INSERT INTO images (filename, file_path, alt_text, caption)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, ('header.jpg', optimized_path, 'Header image', caption))
                            image_record = cursor.fetchone()
                            image_id = image_record['id']
                            cursor.execute("UPDATE post SET header_image_id = %s WHERE id = %s", (image_id, post_id))
                    
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
                    
                    logger.info(f"[HEADER_IMAGE] Saved optimized image to database: image_id={image_id}, path={optimized_path}")
            
            # Return success with paths
            return jsonify({
                'success': True,
                'landscape_raw': landscape_result.get('image_path'),
                'portrait_raw': portrait_result.get('image_path'),
                'landscape_optimized': optimize_result.get('optimized_path'),
                'portrait_optimized': optimize_result.get('portrait_path')
            })
            
        except Exception as e:
            logger.error(f"Error generating header image for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
                # Save optimized image to database and create post_images link
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
                    
                    # Get the caption from the post's header_image_caption field
                    cursor.execute("SELECT header_image_caption, header_image_id FROM post WHERE id = %s", (post_id,))
                    post_row = cursor.fetchone()
                    caption = post_row['header_image_caption'] if post_row else None
                    existing_header_image_id = post_row['header_image_id'] if post_row else None
                    
                    # Check if we need to use image_archive or images table
                    # First check what post_images references
                    cursor.execute("""
                        SELECT pi.image_id, 
                               CASE WHEN EXISTS (SELECT 1 FROM image_archive WHERE id = pi.image_id) THEN 'image_archive'
                                    WHEN EXISTS (SELECT 1 FROM images WHERE id = pi.image_id) THEN 'images'
                                    ELSE NULL END as table_name
                        FROM post_images pi
                        WHERE pi.post_id = %s AND pi.image_type = 'header_optimized'
                        LIMIT 1
                    """, (post_id,))
                    existing_link = cursor.fetchone()
                    
                    # Determine which table to use based on existing data or default to image_archive
                    use_image_archive = True
                    if existing_link and existing_link.get('table_name'):
                        use_image_archive = (existing_link['table_name'] == 'image_archive')
                    else:
                        # Check if image_archive table exists and has the right structure
                        cursor.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'image_archive' AND column_name = 'path'
                        """)
                        if cursor.fetchone():
                            use_image_archive = True
                        else:
                            use_image_archive = False
                    
                    if use_image_archive:
                        # Use image_archive table (path column)
                        if existing_header_image_id:
                            cursor.execute("""
                                UPDATE image_archive 
                                SET filename = %s, path = %s, alt_text = %s, caption = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, ('header.jpg', optimized_path, 'Header image', caption, existing_header_image_id))
                            image_id = existing_header_image_id
                        else:
                            cursor.execute("""
                                INSERT INTO image_archive (filename, path, alt_text, caption)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, ('header.jpg', optimized_path, 'Header image', caption))
                            image_record = cursor.fetchone()
                            image_id = image_record['id']
                            cursor.execute("UPDATE post SET header_image_id = %s WHERE id = %s", (image_id, post_id))
                    else:
                        # Use images table (file_path column)
                        if existing_header_image_id:
                            cursor.execute("""
                                UPDATE images 
                                SET filename = %s, file_path = %s, alt_text = %s, caption = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, ('header.jpg', optimized_path, 'Header image', caption, existing_header_image_id))
                            image_id = existing_header_image_id
                        else:
                            cursor.execute("""
                                INSERT INTO images (filename, file_path, alt_text, caption)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, ('header.jpg', optimized_path, 'Header image', caption))
                            image_record = cursor.fetchone()
                            image_id = image_record['id']
                            cursor.execute("UPDATE post SET header_image_id = %s WHERE id = %s", (image_id, post_id))
                    
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
                    
                    logger.info(f"[HEADER_IMAGE] Saved optimized image to database: image_id={image_id}, path={optimized_path}, table={'image_archive' if use_image_archive else 'images'}")
                
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

