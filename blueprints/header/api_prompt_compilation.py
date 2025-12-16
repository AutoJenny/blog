"""Prompt compilation API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .llm_service import LLMService
import logging
import json

logger = logging.getLogger(__name__)


def _is_valid_input_data(text):
    """
    Validate that input data is meaningful (not placeholder text).
    
    Args:
        text: The text to validate
        
    Returns:
        bool: True if text is valid, False if it's placeholder/empty
    """
    if not text:
        return False
    
    text = text.strip()
    
    # List of placeholder texts to reject
    PLACEHOLDER_TEXTS = [
        'Loading...',
        'No theme selected',
        'No expanded idea generated',
        ''
    ]
    
    if text in PLACEHOLDER_TEXTS:
        return False
    
    # Reject whitespace-only strings
    if not text or text.isspace():
        return False
    
    return True


def register_routes(bp):
    """Register prompt compilation API routes"""
    
    @bp.route('/api/posts/<int:post_id>/compile-header-prompt', methods=['POST'])
    def api_compile_header_prompt(post_id):
        """Compile header prompt from theme name and expanded idea using LLM"""
        try:
            # Check if this is a recipe post - if so, return hero_image_prompt directly
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            if post_type == 'recipe':
                # For recipe posts, use the hero_image_prompt from recipe_image_style section
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT post_section_elements
                        FROM post_section
                        WHERE post_id = %s AND section_type = 'recipe_image_style'
                        LIMIT 1
                    """, (post_id,))
                    style_section = cursor.fetchone()
                    
                    if style_section and style_section.get('post_section_elements'):
                        try:
                            elements = style_section['post_section_elements']
                            if isinstance(elements, str):
                                elements = json.loads(elements)
                            
                            if elements and elements.get('hero_image_prompt'):
                                hero_prompt = elements['hero_image_prompt']
                                # Extract description if it's an object
                                if isinstance(hero_prompt, dict):
                                    prompt_text = hero_prompt.get('description') or hero_prompt.get('image_prompt') or hero_prompt.get('prompt') or ''
                                elif isinstance(hero_prompt, str):
                                    prompt_text = hero_prompt
                                else:
                                    prompt_text = str(hero_prompt)
                                
                                if prompt_text and prompt_text.strip():
                                    return jsonify({
                                        'success': True,
                                        'compiled_prompt': prompt_text.strip(),
                                        'source': 'recipe_hero_prompt'
                                    })
                        except (json.JSONDecodeError, TypeError, KeyError) as e:
                            logger.warning(f"Failed to extract hero prompt from recipe_image_style: {e}")
                
                # If we couldn't get the recipe prompt, return an error
                return jsonify({
                    'success': False,
                    'error': 'No hero image prompt found. Please generate prompts at the Image Style & Prompts stage first.'
                }), 400
            
            # Get the selected model and illustration method from request data
            data = request.get_json() or {}
            selected_model = data.get('model', 'gpt-image-1')
            illustration_method = request.args.get('illustration_method', 'LLM-creation')
            
            # Get year/week from query parameters for week persistence
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            # Get theme_name and expanded_idea from request body
            theme_name = data.get('theme_name')
            expanded_idea = data.get('expanded_idea')
            
            # Validate input data - if invalid, fetch from database
            theme_name_valid = _is_valid_input_data(theme_name)
            expanded_idea_valid = _is_valid_input_data(expanded_idea)
            
            logger.info(f"[PROMPT_COMPILATION] Received data - theme_name valid: {theme_name_valid}, expanded_idea valid: {expanded_idea_valid}")
            if not theme_name_valid:
                logger.warning(f"[PROMPT_COMPILATION] Invalid theme_name received: '{theme_name}' - will fetch from database")
            if not expanded_idea_valid:
                logger.warning(f"[PROMPT_COMPILATION] Invalid expanded_idea received: '{expanded_idea}' - will fetch from database")
            
            # If either is invalid, fetch from database using the resolved post_id
            # NOTE: We use post_id directly (already resolved by route handler), not resolve_post_for_week again
            if not theme_name_valid or not expanded_idea_valid:
                with db_manager.get_cursor() as cursor:
                    # Get post type to determine data source
                    post_type = get_post_type(post_id)
                    
                    if post_type == 'recipe':
                        # For recipe posts, get recipe title and description
                        cursor.execute("""
                            SELECT cr.recipe_title, cr.recipe_description, cr.seasonal_context
                            FROM post p
                            LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                            WHERE p.id = %s
                        """, (post_id,))
                        recipe_data = cursor.fetchone()
                        if recipe_data:
                            if not theme_name_valid:
                                theme_name = recipe_data.get('recipe_title') or ''
                            if not expanded_idea_valid:
                                expanded_idea = recipe_data.get('recipe_description') or ''
                                if recipe_data.get('seasonal_context'):
                                    expanded_idea = f"{expanded_idea}\n\nSeasonal Context: {recipe_data['seasonal_context']}".strip()
                    elif post_type == 'profile':
                        # For profile posts, get profile data
                        cursor.execute("""
                            SELECT title, subtitle
                            FROM post
                            WHERE id = %s
                        """, (post_id,))
                        profile_data = cursor.fetchone()
                        if profile_data:
                            if not theme_name_valid:
                                theme_name = profile_data.get('title') or ''
                            if not expanded_idea_valid:
                                expanded_idea = profile_data.get('subtitle') or ''
                    else:
                        # For themed posts, get theme and expanded idea
                        if year and week:
                            # Get selected theme for this week
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public' 
                                    AND table_name = 'calendar_week_selection'
                                )
                            """)
                            has_new_table = cursor.fetchone()['exists']
                            
                            if has_new_table:
                                cursor.execute("""
                                    SELECT ct.theme_title
                                    FROM calendar_week_selection cws
                                    JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                                    WHERE cws.year = %s AND cws.week_number = %s
                                """, (year, week))
                            else:
                                cursor.execute("""
                                    SELECT ct.theme_title
                                    FROM calendar_schedule cs
                                    JOIN calendar_themes ct ON cs.theme_id = ct.id
                                    WHERE cs.year = %s AND cs.week_number = %s
                                    LIMIT 1
                                """, (year, week))
                            
                            theme_result = cursor.fetchone()
                            if theme_result and not theme_name_valid:
                                theme_name = theme_result.get('theme_title')
                        
                        # Get expanded idea from post_development
                        cursor.execute("""
                            SELECT expanded_idea
                            FROM post_development
                            WHERE post_id = %s
                        """, (post_id,))
                        idea_result = cursor.fetchone()
                        if idea_result and not expanded_idea_valid:
                            expanded_idea = idea_result.get('expanded_idea')
                    
                    logger.info(f"[PROMPT_COMPILATION] Fetched from database - theme_name: '{theme_name[:50] if theme_name else None}...', expanded_idea: '{expanded_idea[:50] if expanded_idea else None}...'")
            
            # Final validation - both must be valid
            if not _is_valid_input_data(theme_name) or not _is_valid_input_data(expanded_idea):
                logger.error(f"[PROMPT_COMPILATION] Failed to get valid input data - theme_name: '{theme_name}', expanded_idea: '{expanded_idea}'")
                return jsonify({
                    'error': 'Theme name and expanded idea are required and must be valid. Please ensure the Planning stage is complete.'
                }), 400
            
            # Get prompts from database - use Photo-harvesting prompt if applicable
            with db_manager.get_cursor() as cursor:
                if illustration_method == 'Photo-harvesting':
                    cursor.execute("""
                        SELECT 
                            system_prompt,
                            prompt_text as task_prompt
                        FROM llm_prompt
                        WHERE name = 'Header Image Generation Prompt (Photo-harvesting)'
                    """)
                    result = cursor.fetchone()
                    
                    if not result:
                        return jsonify({'error': 'Header Image Generation Prompt (Photo-harvesting) not found'}), 404
                else:
                    # For LLM-creation route, use workflow step prompts (step 64)
                    cursor.execute("""
                        SELECT 
                            sp.system_prompt,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                        JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                        WHERE wsp.step_id = 64
                    """)
                    result = cursor.fetchone()
                    
                    if not result:
                        return jsonify({'error': 'Header prompt compilation prompts not found'}), 404
                
                system_prompt = result.get('system_prompt', '')
                task_prompt = result.get('task_prompt', '')
                
                # Determine style guidelines based on selected model and illustration method
                style_guidelines = ""
                if illustration_method == 'Photo-harvesting':
                    style_guidelines = "Professional photography style, high-resolution quality, natural lighting, photorealistic representation"
                elif selected_model == 'dall-e-3':
                    style_guidelines = "Use 'photorealistic' style with brushstrokes fading to white edges"
                elif selected_model == 'sdxl':
                    style_guidelines = "Use 'inkwash and watercolour' style with brushstrokes fading to white edges"
                else:
                    style_guidelines = "Use 'photorealistic' style with brushstrokes fading to white edges"  # Default
                
                # Use LLM service to compile prompts
                llm_service = LLMService()
                
                # Fetch section image prompts from database
                section_prompts_list = []
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT section_order, image_prompts, section_heading
                        FROM post_section
                        WHERE post_id = %s 
                          AND image_prompts IS NOT NULL 
                          AND image_prompts != ''
                        ORDER BY section_order
                        LIMIT 7
                    """, (post_id,))
                    sections = cursor.fetchall()
                    
                    for section in sections:
                        prompts_data = section.get('image_prompts', '')
                        if not prompts_data:
                            continue
                        
                        # Extract prompt text - handle both JSON and plain string formats
                        prompt_text = None
                        if isinstance(prompts_data, str):
                            try:
                                # Try parsing as JSON
                                prompts_dict = json.loads(prompts_data)
                                if isinstance(prompts_dict, dict):
                                    prompt_text = prompts_dict.get('image_prompt') or prompts_dict.get('prompt') or prompts_dict.get('text')
                                elif isinstance(prompts_dict, str):
                                    prompt_text = prompts_dict
                            except (json.JSONDecodeError, TypeError):
                                # Not JSON, use as-is
                                prompt_text = prompts_data
                        elif isinstance(prompts_data, dict):
                            prompt_text = prompts_data.get('image_prompt') or prompts_data.get('prompt') or prompts_data.get('text')
                        
                        if prompt_text and prompt_text.strip():
                            # Format without section numbers/headings to avoid LLM including them in output
                            # Just use the prompt text directly - section context is not needed in output
                            section_prompts_list.append(prompt_text.strip())
                
                # Format section prompts for template
                if section_prompts_list:
                    section_prompts_text = "\n\n".join(section_prompts_list)
                    logger.info(f"[PROMPT_COMPILATION] Found {len(section_prompts_list)} section prompts for post {post_id}")
                else:
                    section_prompts_text = "No section image prompts available yet. Please generate section image prompts first."
                    logger.warning(f"[PROMPT_COMPILATION] No section prompts found for post {post_id}")
                
                # Format the prompt with theme name, expanded idea, and section prompts
                formatted_prompt = task_prompt.replace('[data:theme_name]', theme_name or '')
                formatted_prompt = formatted_prompt.replace('[data:expanded_idea]', expanded_idea or '')
                formatted_prompt = formatted_prompt.replace('{theme_name}', theme_name or '')
                formatted_prompt = formatted_prompt.replace('{expanded_idea}', expanded_idea or '')
                
                # Insert section prompts into template (this is the key fix!)
                formatted_prompt = formatted_prompt.replace('{section_prompts}', section_prompts_text)
                formatted_prompt = formatted_prompt.replace('[data:section_prompts]', section_prompts_text)
                
                # Add theme and expanded idea as additional context for LLM guidance
                context_note = f"\n\nTheme Context: {theme_name}\nExpanded Idea Context: {expanded_idea[:200]}..." if theme_name and expanded_idea else ""
                if context_note and '{section_prompts}' not in task_prompt:
                    # If template doesn't have section_prompts placeholder, append context
                    formatted_prompt += context_note
                
                # Replace style_guidelines and model placeholders
                formatted_prompt = formatted_prompt.replace('{style_guidelines}', style_guidelines)
                formatted_prompt = formatted_prompt.replace('{model}', selected_model)
                
                # Prepare messages for LLM
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": formatted_prompt}
                ]
                
                # Generate compiled prompt using LLM
                try:
                    llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                    
                    if 'error' in llm_response:
                        logger.error(f"LLM compilation failed: {llm_response['error']}")
                        raise Exception("LLM failed")
                    
                    compiled_prompt = llm_response.get('content', '').strip()
                    
                    if not compiled_prompt:
                        raise Exception("Empty response")
                        
                    # Ensure brushstrokes fading to white edges is included
                    if "brushstrokes fading to white edges" not in compiled_prompt.lower():
                        compiled_prompt += " with brushstrokes fading to white edges"
                        
                except Exception as e:
                    logger.error(f"LLM service error: {e}")
                    return jsonify({'error': f'LLM compilation failed: {str(e)}'}), 500
                
                # Save compiled prompt to database
                try:
                    with db_manager.get_cursor() as cursor:
                        # Check if post already has a header image
                        cursor.execute("""
                            SELECT header_image_id FROM post WHERE id = %s
                        """, (post_id,))
                        post_result = cursor.fetchone()
                        
                        if post_result and post_result.get('header_image_id'):
                            # Update existing image record with the compiled prompt
                            # Note: foreign key references image_archive, so update there
                            cursor.execute("""
                                UPDATE image_archive 
                                SET image_prompt = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (compiled_prompt, post_result['header_image_id']))
                            logger.info(f"[PROMPT_COMPILATION] Updated header image prompt for post {post_id} in image_archive {post_result['header_image_id']}")
                        else:
                            # Create new image record with just the prompt (no actual image yet)
                            # Note: foreign key references image_archive.id, so insert there
                            cursor.execute("""
                                INSERT INTO image_archive (filename, original_filename, path, image_prompt, alt_text, caption)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING id
                            """, (
                                'header.jpg',
                                'placeholder.png',
                                f'/static/content/posts/{post_id}/header/header.jpg',
                                compiled_prompt,
                                'Header image prompt',
                                'Generated header image prompt'
                            ))
                            image_result = cursor.fetchone()
                            if not image_result:
                                raise Exception("Failed to create image record - no ID returned")
                            image_id = image_result['id']
                            
                            # Link to post
                            cursor.execute("""
                                UPDATE post 
                                SET header_image_id = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (image_id, post_id))
                            logger.info(f"[PROMPT_COMPILATION] Created new header image prompt for post {post_id} with image_archive id {image_id}")
                            
                            # Verify the save worked
                            cursor.execute("""
                                SELECT image_prompt FROM image_archive WHERE id = %s
                            """, (image_id,))
                            verify_result = cursor.fetchone()
                            if verify_result and verify_result.get('image_prompt'):
                                logger.info(f"[PROMPT_COMPILATION] Verified prompt saved successfully ({len(verify_result['image_prompt'])} chars)")
                            else:
                                logger.error(f"[PROMPT_COMPILATION] WARNING: Prompt save verification failed for image_id {image_id}")
                        
                        # Note: Connection has autocommit=True, so no explicit commit needed
                except Exception as e:
                    logger.error(f"[PROMPT_COMPILATION] Error saving compiled header prompt to database: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Still return success - prompt was generated, just not saved
                    # This allows the user to see the prompt even if save fails
                
                return jsonify({
                    'success': True,
                    'compiled_prompt': compiled_prompt
                })
                
        except Exception as e:
            logger.error(f"Error compiling header prompt for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-profile-header-prompt', methods=['POST'])
    def api_generate_profile_header_prompt(post_id):
        """Generate header image prompt for profile posts based on product information"""
        try:
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            if post_type != 'profile':
                return jsonify({
                    'success': False,
                    'error': 'This endpoint is only for profile posts'
                }), 400
            
            data = request.get_json() or {}
            product_name = data.get('product_name', '')
            product_description = data.get('product_description', '')
            product_type = data.get('product_type', '')
            post_title = data.get('post_title', '')
            post_summary = data.get('post_summary', '')
            
            # If product data not provided, fetch from database
            if not product_name:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT cp.name, cp.short_description, cp.description, cp.additional_data
                        FROM post p
                        LEFT JOIN clan_products cp ON cp.id = p.profile_product_id
                        WHERE p.id = %s
                    """, (post_id,))
                    product_data = cursor.fetchone()
                    
                    if product_data:
                        product_name = product_data.get('name', '')
                        product_description = product_data.get('short_description', '') or product_data.get('description', '')
                        if product_data.get('additional_data'):
                            additional = product_data['additional_data']
                            if isinstance(additional, dict):
                                product_type = additional.get('product_type', '')
            
            # Get post title and summary if not provided
            if not post_title or not post_summary:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT title, summary
                        FROM post
                        WHERE id = %s
                    """, (post_id,))
                    post_data = cursor.fetchone()
                    if post_data:
                        if not post_title:
                            post_title = post_data.get('title', '')
                        if not post_summary:
                            post_summary = post_data.get('summary', '')
            
            if not product_name:
                return jsonify({
                    'success': False,
                    'error': 'Product name is required'
                }), 400
            
            # Use a specific system prompt for profile header image generation
            system_prompt = """You are a creative assistant specialized in generating detailed, inspiring image prompts for product photography. Your prompts should be vivid, specific, and create compelling visual scenes that showcase products in authentic, traditional settings."""
            
            # Get product image URL for reference
            product_image_url = None
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cp.image_url
                    FROM post p
                    LEFT JOIN clan_products cp ON cp.id = p.profile_product_id
                    WHERE p.id = %s
                """, (post_id,))
                product_data = cursor.fetchone()
                if product_data and product_data.get('image_url'):
                    product_image_url = product_data['image_url']
            
            # Create profile-specific prompt with traditional setting requirement
            # CRITICAL: Must include instructions to use the product from the reference image
            reference_image_instruction = ""
            if product_image_url:
                reference_image_instruction = f"""

CRITICAL REQUIREMENT - REFERENCE IMAGE:
- A reference image of the product is provided at: {product_image_url}
- The main item/product shown in this reference image MUST be included EXACTLY as a focus in the generated image
- The product from the reference image should be the central focus of the scene
- Use the exact appearance, design, and details of the product as shown in the reference image
- The generated image should feature this specific product prominently, integrated into the traditional setting"""

            profile_prompt = f"""Generate a detailed, inspiring image prompt for a header image for a product profile blog post.

POST CONTENT (use this as the primary inspiration):
- Post Title: {post_title if post_title else product_name}
- Post Summary: {post_summary[:300] if post_summary else 'No summary available'}

PRODUCT INFORMATION:
- Product Name: {product_name}
- Product Type: {product_type if product_type else 'Product'}
- Product Description: {product_description[:500] if product_description else 'No description available'}{reference_image_instruction}

REQUIREMENTS:
- Create an inspiring, professional, high-quality product photography prompt
- Base the scene and mood on the post title and summary provided above
- Show the product IN USE in a traditional setting (e.g., traditional Scottish home, heritage context, classic environment)
- Integrate the product naturally into a traditional scene that reflects its heritage and cultural context
- Focus on showcasing the product being used or displayed in an authentic, traditional lifestyle context
- Include specific details about lighting, composition, styling, and atmosphere that evoke tradition and heritage
- Consider the product type and category when suggesting the traditional setting
- Make it suitable for a blog header image (horizontal/landscape orientation)
- Keep it detailed but concise (2-4 sentences)
- The prompt should be inspiring and create a compelling visual scene

Return ONLY the image prompt text, no explanations, no markdown formatting, no code blocks, just the plain text prompt."""

            # Use LLM to generate the prompt
            llm_service = LLMService()
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': profile_prompt}
            ]
            
            logger.info(f"[Profile Header Prompt] Generating prompt for post {post_id}")
            logger.info(f"[Profile Header Prompt] Title: {post_title}, Summary: {post_summary[:100] if post_summary else 'None'}...")
            logger.info(f"[Profile Header Prompt] Product: {product_name}, Image URL: {product_image_url}")
            
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                # Fallback to a simple prompt
                generated_prompt = f"Professional product photography of {product_name}, high quality, well-lit, lifestyle setting, horizontal composition, suitable for blog header"
            else:
                generated_prompt = llm_response.get('content', '').strip()
                # Clean up the prompt
                generated_prompt = generated_prompt.strip('"').strip("'").strip()
                # Remove any markdown code blocks
                if generated_prompt.startswith('```'):
                    lines = generated_prompt.split('\n')
                    generated_prompt = '\n'.join(lines[1:-1]) if len(lines) > 2 else generated_prompt
                # Fallback if empty
                if not generated_prompt:
                    generated_prompt = f"Professional product photography of {product_name}, high quality, well-lit, lifestyle setting, horizontal composition, suitable for blog header"
            
            return jsonify({
                'success': True,
                'prompt': generated_prompt,
                'reference_image_url': product_image_url  # Return product image URL for use in generation
            })
            
        except Exception as e:
            logger.error(f"Error generating profile header prompt: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/posts/<int:post_id>/prompt-assembly-data', methods=['GET'])
    def api_get_prompt_assembly_data(post_id):
        """Get system/task prompts and section data for Prompt Assembly display"""
        try:
            # Check illustration_method from query parameter or window context
            illustration_method = request.args.get('illustration_method', 'LLM-creation')
            
            with db_manager.get_cursor() as cursor:
                # For Photo-harvesting route, use the new photorealistic prompt
                if illustration_method == 'Photo-harvesting':
                    cursor.execute("""
                        SELECT 
                            system_prompt,
                            prompt_text as task_prompt
                        FROM llm_prompt
                        WHERE name = 'Header Image Generation Prompt (Photo-harvesting)'
                    """)
                    prompt_result = cursor.fetchone()
                    
                    if not prompt_result:
                        return jsonify({'error': 'Header Image Generation Prompt (Photo-harvesting) not found'}), 404
                else:
                    # For LLM-creation route, use workflow step prompts (step 64)
                    cursor.execute("""
                        SELECT 
                            sp.system_prompt,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                        JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                        WHERE wsp.step_id = 64
                    """)
                    prompt_result = cursor.fetchone()
                    
                    if not prompt_result:
                        return jsonify({'error': 'Header prompt compilation prompts not found'}), 404
                
                # Get year/week from query parameters for week persistence
                year = request.args.get('year', type=int)
                week = request.args.get('week', type=int)
                
                # For header images, use theme name and expanded idea (not sections)
                # BUT: For recipe/profile posts, use recipe/profile data instead
                from utils.taxonomy_helpers import get_post_type
                post_type = get_post_type(post_id)
                
                theme_name = None
                expanded_idea = None
                
                if post_type == 'recipe':
                    # For recipe posts, get recipe title and description
                    cursor.execute("""
                        SELECT cr.recipe_title, cr.recipe_description, cr.seasonal_context
                        FROM post p
                        LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                        WHERE p.id = %s
                    """, (post_id,))
                    recipe_data = cursor.fetchone()
                    if recipe_data:
                        theme_name = recipe_data.get('recipe_title') or ''
                        expanded_idea = recipe_data.get('recipe_description') or ''
                        if recipe_data.get('seasonal_context'):
                            expanded_idea = f"{expanded_idea}\n\nSeasonal Context: {recipe_data['seasonal_context']}".strip()
                elif post_type == 'profile':
                    # For profile posts, get profile data
                    cursor.execute("""
                        SELECT title, subtitle
                        FROM post
                        WHERE id = %s
                    """, (post_id,))
                    profile_data = cursor.fetchone()
                    if profile_data:
                        theme_name = profile_data.get('title') or ''
                        expanded_idea = profile_data.get('subtitle') or ''
                elif year and week:
                    # For themed posts, get theme and expanded idea from V2 week-persistence.
                    # Use calendar_week_selection_v2 view (or table alias) and post_development for expanded_idea.
                    cursor.execute("""
                        SELECT ct.theme_title
                        FROM calendar_week_selection_v2 cws
                        JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                        WHERE cws.year = %s AND cws.week_number = %s
                    """, (year, week))
                    theme_result = cursor.fetchone()
                    if theme_result:
                        theme_name = theme_result.get('theme_title')

                    # Get expanded idea for this post directly (do NOT resolve different post_id)
                    cursor.execute("""
                        SELECT expanded_idea
                        FROM post_development
                        WHERE post_id = %s
                    """, (post_id,))
                    idea_result = cursor.fetchone()
                    if idea_result:
                        expanded_idea = idea_result.get('expanded_idea')
                else:
                    # No explicit week context: get expanded_idea directly for this post_id;
                    # do NOT use any legacy calendar_schedule/calendar_week_posts fallbacks.
                    cursor.execute("""
                        SELECT expanded_idea
                        FROM post_development
                        WHERE post_id = %s
                    """, (post_id,))
                    idea_result = cursor.fetchone()
                    if idea_result:
                        expanded_idea = idea_result.get('expanded_idea')
                
                # Fail clearly if we still don't have the required inputs
                if not theme_name or not expanded_idea:
                    msg = "Theme and expanded idea data not available. Please ensure the Planning stage is complete."
                    logger.error(f"[Prompt Assembly] {msg} (post_id={post_id}, post_type={post_type}, year={year}, week={week})")
                    return jsonify({
                        'success': False,
                        'error': msg,
                        'theme_name': theme_name,
                        'expanded_idea': expanded_idea
                    }), 400

                return jsonify({
                    'success': True,
                    'system_prompt': prompt_result.get('system_prompt', ''),
                    'task_prompt': prompt_result.get('task_prompt', ''),
                    'theme_name': theme_name,
                    'expanded_idea': expanded_idea
                })
                
        except Exception as e:
            logger.error(f"Error getting prompt assembly data for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

