"""
Authoring API - Image Prompts

Handles image prompt generation using proper system prompts.
Keeps file size under 300 lines as per user requirements.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from modules.llm_service import llm_service
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('authoring_prompts', __name__, url_prefix='/authoring')


def apply_model_aware_substitutions(text, max_chars):
    """
    Apply model-aware character limit substitutions to prompt text.
    Mirrors frontend llm-prompts-panel.js applyModelAwareSubstitutions().
    """
    if not text or not max_chars:
        return text
    
    import re
    
    t = str(text)
    
    # Replace common range caps like "380–400 characters" or "380-400 characters"
    t = re.sub(r'\b\d{2,4}\s*[–-]\s*\d{2,4}\s*characters?', 
               f'up to {max_chars} characters', t, flags=re.IGNORECASE)
    
    # Replace phrases like "exceeds 400 characters"
    t = re.sub(r'exceeds\s+\d{2,4}\s*characters?', 
               f'exceeds {max_chars} characters', t, flags=re.IGNORECASE)
    
    # Replace "≤ 400" or "<= 400"
    t = re.sub(r'(?:≤|<=)\s*\d{2,4}\b', 
               f'≤ {max_chars}', t, flags=re.IGNORECASE)
    
    # Replace solitary "400 characters" with "{max} characters" for typical caps (<= 1000)
    def replace_char_limit(match):
        num = int(match.group(1))
        return f'{max_chars} characters' if num <= 1000 else match.group(0)
    
    t = re.sub(r'\b(\d{2,4})\s*characters\b', replace_char_limit, t, flags=re.IGNORECASE)
    
    return t


def handle_exact_request(data):
    """Handle request using exact stored messages from Complete LLM Input field"""
    try:
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        exact_messages = data.get('exact_messages')
        exact_model = data.get('exact_model')
        exact_options = data.get('exact_options')
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
            
        if not exact_messages:
            return jsonify({'error': 'Missing exact_messages'}), 400
        
        logger.info(f"[DEBUG] Using exact stored messages for post_id={post_id}, section_id={section_id}")
        
        # Create intercept context
        intercept_context = {
            'post_id': post_id,
            'section_id': section_id
        }
        
        # Determine provider from model
        provider = 'ollama' if 'llama' in exact_model.lower() else 'openai'
        
        # Execute LLM request with exact stored messages
        result = llm_service.execute_llm_request(
            provider=provider,
            model=exact_model,
            messages=exact_messages,
            intercept_context=intercept_context
        )
        
        logger.info(f"[DEBUG] LLM result: {result}")
        
        if result:
            # The result contains the response content directly
            response_content = result.get('content', '') or result.get('response', '')
            logger.info(f"[DEBUG] LLM response content: {response_content[:200]}...")
            
            # Try to extract JSON from response
            try:
                import re
                json_match = re.search(r'\{[^}]*"image_prompt"[^}]*\}', response_content)
                if json_match:
                    import json
                    response_json = json.loads(json_match.group())
                    image_prompt = response_json.get('image_prompt', response_content)
                else:
                    image_prompt = response_content
            except Exception as e:
                logger.error(f"[DEBUG] JSON parsing error: {e}")
                image_prompt = response_content
            
            return jsonify({
                'success': True,
                'image_prompt': image_prompt,
                'message': 'Image prompt generated using exact stored messages',
                'actual_llm_messages': exact_messages,
                'character_limit': 2000,
                'compression_used': False,
                'expansion_used': False,
                'final_length': len(image_prompt)
            })
        else:
            logger.error(f"[DEBUG] LLM request failed: {result}")
            return jsonify({'error': 'LLM request failed'}), 500
            
    except Exception as e:
        logger.error(f"Error handling exact request: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/generate-image-prompt-from-builder-v2', methods=['POST'])
def api_generate_image_prompt_from_builder():
    """Generate image prompt using the compiled prompt from Prompt Builder"""
    try:
        data = request.get_json()
        
        # Check if we're using exact stored messages
        use_exact_request = data.get('use_exact_request', False)
        if use_exact_request:
            return handle_exact_request(data)
        
        compiled_prompt = data.get('compiled_prompt')
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        
        # Get concept data from frontend
        concept_content = data.get('concept_content')
        selected_concept = data.get('selected_concept')
        
        # Get user preferences for compression/expansion
        enable_compression = data.get('enable_compression', True)
        enable_expansion = data.get('enable_expansion', False)
        
        llm_provider = data.get('llm_provider', 'Ollama')
        llm_model = data.get('llm_model', 'llama3.2:latest')
        
        # Track all LLM calls for transparency
        pipeline_steps = []
        
        logger.info(f"[DEBUG] API received: post_id={post_id}, section_id={section_id}")
        logger.info(f"[DEBUG] Compiled prompt: {compiled_prompt[:100]}...")
        
        if not compiled_prompt:
            return jsonify({'error': 'Missing compiled_prompt'}), 400
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
        
        # Get section data from post_section table
        with db_manager.get_cursor() as cursor:
            # Get post data for context
            cursor.execute("""
                SELECT title, subtitle, summary FROM post WHERE id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get imaging model selection and character limit
            cursor.execute("""
                SELECT imaging_model_selection
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            imaging_model_row = cursor.fetchone()
            imaging_model_key = imaging_model_row['imaging_model_selection'] if imaging_model_row else 'sdxl-lora'
            
            # Get model specs for character limit
            cursor.execute("""
                SELECT api_params
                FROM llm_model
                WHERE name = %s
            """, (imaging_model_key,))
            
            model_spec_row = cursor.fetchone()
            max_chars = None
            if model_spec_row and model_spec_row['api_params']:
                api_params = model_spec_row['api_params']
                if isinstance(api_params, dict):
                    max_chars = api_params.get('max_prompt_chars')
                elif isinstance(api_params, str):
                    api_params_dict = json.loads(api_params)
                    max_chars = api_params_dict.get('max_prompt_chars')
            
            logger.info(f"[DEBUG] Imaging model: {imaging_model_key}, max_chars: {max_chars}")
            
            # Get section data
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get active image style
            cursor.execute("""
                SELECT extra_settings
                FROM post
                WHERE id = %s
            """, (post_id,))
            post_row = cursor.fetchone()
            
            active_style = None
            if post_row and post_row['extra_settings']:
                extra_settings = post_row['extra_settings']
                if isinstance(extra_settings, str):
                    extra_settings = json.loads(extra_settings)
                
                imaging = extra_settings.get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]
            
            logger.info(f"[DEBUG] Active style: {active_style['name'] if active_style else 'None'}")
            
            # Set topics to empty for now (topic allocation system removed)
            topics = []
            
            # Get the user-configured image prompts prompt (not hardcoded)
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Prompts Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'User-configured Image Prompts prompt not found. Please configure prompts in the LLM Prompts panel first.'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Apply model-aware substitutions if we have character limit
            if max_chars:
                prompt_text = apply_model_aware_substitutions(prompt_text, max_chars)
                system_prompt = apply_model_aware_substitutions(system_prompt, max_chars)
                logger.info(f"[DEBUG] Applied model-aware substitutions for {imaging_model_key} (max: {max_chars} chars)")
            
            logger.info(f"[DEBUG] System prompt length: {len(system_prompt) if system_prompt else 0}")
            logger.info(f"[DEBUG] System prompt preview: {system_prompt[:100] if system_prompt else 'None'}")
            logger.info(f"[DEBUG] *** SYSTEM PROMPT DEBUG ***")
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:idea_seed]', post_data['title'] or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['subtitle'] or '')
            prompt_text = prompt_text.replace('[data:title]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:section_text]', section.get('polished') or section.get('draft') or '')
            
            # Automatically extract concept data from database
            concept_text = ''
            
            # First try to get concept from image_concepts JSON data
            if section['image_concepts']:
                try:
                    image_concepts_data = json.loads(section['image_concepts']) if isinstance(section['image_concepts'], str) else section['image_concepts']
                    
                    # Look for the selected concept by ID
                    selected_concept_id = section.get('selected_image_concept')
                    if selected_concept_id and isinstance(image_concepts_data, dict):
                        concepts = image_concepts_data.get('concepts', [])
                        for concept in concepts:
                            if concept.get('concept_id') == selected_concept_id:
                                # Build concept text from the selected concept
                                concept_parts = []
                                if concept.get('concept_description'):
                                    concept_parts.append(concept['concept_description'])
                                if concept.get('concept_mood'):
                                    concept_parts.append(f"Mood: {concept['concept_mood']}")
                                if concept.get('key_visual_elements'):
                                    concept_parts.append(f"Key Elements: {concept['key_visual_elements']}")
                                concept_text = '\n'.join(concept_parts)
                                break
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    logger.warning(f"Error parsing image_concepts for section {section_id}: {e}")
            
            # Fallback to frontend data if database extraction failed
            if not concept_text:
                if concept_content and isinstance(concept_content, dict):
                    # Build concept text from the structured data
                    concept_parts = []
                    if concept_content.get('description'):
                        concept_parts.append(concept_content['description'])
                    if concept_content.get('mood'):
                        concept_parts.append(f"Mood: {concept_content['mood']}")
                    if concept_content.get('elements'):
                        concept_parts.append(f"Key Elements: {concept_content['elements']}")
                    concept_text = '\n'.join(concept_parts)
                elif selected_concept:
                    concept_text = selected_concept
                else:
                    concept_text = compiled_prompt or ''
            
            
            prompt_text = prompt_text.replace('[data:selected_concept]', concept_text)
            topics_text = '\n'.join([f'- {topic}' for topic in topics])
            prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
            # Add style information to prompt
            style_text = ""
            if active_style:
                style_name = active_style.get('name', '')
                style_json = active_style.get('style_json', {})
                
                # Format style information
                style_parts = []
                if style_name:
                    style_parts.append(f"Style: {style_name}")
                
                if style_json:
                    # Add key style elements
                    if style_json.get('medium'):
                        style_parts.append(f"Medium: {style_json['medium']}")
                    if style_json.get('technique'):
                        style_parts.append(f"Technique: {style_json['technique']}")
                    if style_json.get('palette'):
                        palette = ', '.join(style_json['palette'])
                        style_parts.append(f"Color Palette: {palette}")
                    if style_json.get('constraints'):
                        constraints = ', '.join(style_json['constraints'])
                        style_parts.append(f"Constraints: {constraints}")
                    if style_json.get('negatives'):
                        negatives = ', '.join(style_json['negatives'])
                        style_parts.append(f"Avoid: {negatives}")
                
                style_text = '\n'.join(style_parts)
                logger.info(f"[DEBUG] Style text: {style_text}")
            
            # Replace [data:style] placeholder with actual style information
            if '[data:style]' in prompt_text:
                if style_text:
                    prompt_text = prompt_text.replace('[data:style]', style_text)
                else:
                    prompt_text = prompt_text.replace('[data:style]', '')
            else:
                # If placeholder not found, append style information to prompt
                if style_text:
                    prompt_text += f"\n\nStyle Guidelines:\n{style_text}"
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
                logger.info(f"[DEBUG] Added system message: {len(system_prompt)} chars")
            else:
                logger.info(f"[DEBUG] No system prompt to add")
            messages.append({'role': 'user', 'content': prompt_text})
            
            logger.info(f"[DEBUG] Messages prepared: {len(messages)} messages")
            logger.info(f"[DEBUG] System message included: {any(m['role'] == 'system' for m in messages)}")
            logger.info(f"[DEBUG] First message role: {messages[0]['role'] if messages else 'None'}")
            
            # Execute LLM request with retry logic for valid JSON
            max_retries = 3
            generated_prompt = None
            
            for attempt in range(max_retries):
                # Add intercept context for message capture
                intercept_context = {
                    'post_id': post_id,
                    'section_id': section_id
                }
                result = llm_service.execute_llm_request(llm_provider.lower(), llm_model, messages, intercept_context=intercept_context)
                
                if 'error' in result:
                    if attempt == max_retries - 1:  # Last attempt
                        return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
                    continue
                
                raw_content = result['content']
                
                # Try to parse as JSON first
                try:
                    parsed_json = json.loads(raw_content)
                    if 'image_prompt' in parsed_json:
                        generated_prompt = parsed_json['image_prompt']
                        break
                except json.JSONDecodeError:
                    pass
                
                # If not JSON, use the raw content
                generated_prompt = raw_content.strip()
                break
            
            if not generated_prompt:
                return jsonify({'error': 'Failed to generate prompt after retries'}), 500
            
            # Log the generation step
            pipeline_steps.append({
                'step': 'initial_generation',
                'input': prompt_text,
                'output': generated_prompt,
                'llm_call': {'provider': llm_provider, 'model': llm_model, 'messages': messages, 'system_prompt': system_prompt}
            })
            
            # Get model-specific character limit first
            imaging_limit = 2000  # Default for GPT-Image-1
            if 'sdxl' in llm_model.lower():
                imaging_limit = 400
            
            # Apply compression if enabled and needed (only for SDXL models)
            compression_used = False
            if enable_compression and 'sdxl' in llm_model.lower() and len(generated_prompt) > imaging_limit:
                # Simple compression - truncate to model's character limit (SDXL only)
                generated_prompt = generated_prompt[:imaging_limit].rsplit(' ', 1)[0] + '.'
                compression_used = True
                
                pipeline_steps.append({
                    'step': 'compression',
                    'input': generated_prompt,
                    'output': generated_prompt,
                    'llm_call': None
                })
            
            # Apply expansion if enabled and needed
            expansion_used = False
            if enable_expansion and len(generated_prompt) < 200:
                # Simple expansion - add descriptive details
                expanded_prompt = f"{generated_prompt} The scene features rich atmospheric details, intricate textures, and dramatic lighting that creates a sense of depth and mystery."
                if len(expanded_prompt) <= 400:
                    generated_prompt = expanded_prompt
                    expansion_used = True
                    
                    pipeline_steps.append({
                        'step': 'expansion',
                        'input': generated_prompt,
                        'output': generated_prompt,
                        'llm_call': None
                    })
            
            # imaging_limit already calculated above
            
            # Save to database
            try:
                # Update the post_section table with the generated prompt
                image_prompts_json = json.dumps({
                    'image_prompt': generated_prompt,
                    'base_concept': compiled_prompt
                })
                
                cursor.execute("""
                    UPDATE post_section 
                    SET image_prompts = %s 
                    WHERE post_id = %s AND id = %s
                """, (image_prompts_json, post_id, section_id))
                    
            except Exception as e:
                logger.error(f"Error updating post_section for image prompts: {e}")
                return jsonify({'error': 'Failed to update section data'}), 500
            
            cursor.connection.commit()
            
            logger.info(f"[DEBUG] Generated prompt: {generated_prompt[:100]}...")
            logger.info(f"[DEBUG] Saved to database for post {post_id}, section {section_id}")
            
            # Return detailed pipeline information
            return jsonify({
                'success': True,
                'image_prompt': generated_prompt,
                'message': 'Image prompt generated and saved successfully',
                'pipeline_steps': pipeline_steps,
                'final_length': len(generated_prompt),
                'character_limit': imaging_limit,
                'compression_used': compression_used,
                'expansion_used': expansion_used,
                'actual_llm_messages': messages  # NEW: Return the actual messages sent to LLM
            })
            
    except Exception as e:
        logger.error(f"Error generating image prompt: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/sections/<section_id>/llm-prompt-details', methods=['GET'])
def api_get_llm_prompt_details(post_id, section_id):
    """Get the actual system prompt and user prompt that will be sent to the LLM"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data for context
            cursor.execute("""
                SELECT title, subtitle, summary FROM post WHERE id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get imaging model selection and character limit
            cursor.execute("""
                SELECT imaging_model_selection
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            imaging_model_row = cursor.fetchone()
            imaging_model_key = imaging_model_row['imaging_model_selection'] if imaging_model_row else 'sdxl-lora'
            
            # Get model specs for character limit
            cursor.execute("""
                SELECT api_params
                FROM llm_model
                WHERE name = %s
            """, (imaging_model_key,))
            
            model_spec_row = cursor.fetchone()
            max_chars = None
            if model_spec_row and model_spec_row['api_params']:
                api_params = model_spec_row['api_params']
                if isinstance(api_params, dict):
                    max_chars = api_params.get('max_prompt_chars')
                elif isinstance(api_params, str):
                    api_params_dict = json.loads(api_params)
                    max_chars = api_params_dict.get('max_prompt_chars')
            
            # Get section data from post_section table
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get active image style
            cursor.execute("""
                SELECT extra_settings
                FROM post
                WHERE id = %s
            """, (post_id,))
            post_row = cursor.fetchone()
            
            active_style = None
            if post_row and post_row['extra_settings']:
                extra_settings = post_row['extra_settings']
                if isinstance(extra_settings, str):
                    extra_settings = json.loads(extra_settings)
                
                imaging = extra_settings.get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]
            
            logger.info(f"[DEBUG] Active style: {active_style['name'] if active_style else 'None'}")
            
            # Set topics to empty for now (topic allocation system removed)
            topics = []
            
            # Get the user-configured image prompts prompt template
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Prompts Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'User-configured Image Prompts prompt not found. Please configure prompts in the LLM Prompts panel first.'}), 404
            
            # Build the user prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Apply model-aware substitutions if we have character limit
            if max_chars:
                prompt_text = apply_model_aware_substitutions(prompt_text, max_chars)
                system_prompt = apply_model_aware_substitutions(system_prompt, max_chars)
                logger.info(f"[DEBUG] Applied model-aware substitutions for {imaging_model_key} (max: {max_chars} chars)")
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:idea_seed]', post_data['title'] or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['subtitle'] or '')
            prompt_text = prompt_text.replace('[data:title]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:section_text]', section.get('polished') or section.get('draft') or '')
            
            # Get the selected concept for [data:selected_concept]
            selected_concept = "No concept selected"
            if section.get('image_concepts'):
                try:
                    concepts_data = json.loads(section['image_concepts'])
                    if isinstance(concepts_data, dict) and 'concepts' in concepts_data:
                        concepts = concepts_data['concepts']
                        selected_concept_id = section.get('selected_image_concept', 'CONCEPT-1')
                        for concept in concepts:
                            if concept.get('concept_id') == selected_concept_id:
                                selected_concept = concept.get('concept_description', 'No description')
                                break
                except (json.JSONDecodeError, TypeError):
                    pass
            
            prompt_text = prompt_text.replace('[data:selected_concept]', selected_concept)
            topics_text = '\n'.join([f'- {topic}' for topic in topics])
            prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
            # Add style information to prompt
            style_text = ""
            if active_style:
                style_name = active_style.get('name', '')
                style_json = active_style.get('style_json', {})
                
                # Format style information
                style_parts = []
                if style_name:
                    style_parts.append(f"Style: {style_name}")
                
                if style_json:
                    # Add key style elements
                    if style_json.get('medium'):
                        style_parts.append(f"Medium: {style_json['medium']}")
                    if style_json.get('technique'):
                        style_parts.append(f"Technique: {style_json['technique']}")
                    if style_json.get('palette'):
                        palette = ', '.join(style_json['palette'])
                        style_parts.append(f"Color Palette: {palette}")
                    if style_json.get('constraints'):
                        constraints = ', '.join(style_json['constraints'])
                        style_parts.append(f"Constraints: {constraints}")
                    if style_json.get('negatives'):
                        negatives = ', '.join(style_json['negatives'])
                        style_parts.append(f"Avoid: {negatives}")
                
                style_text = '\n'.join(style_parts)
                logger.info(f"[DEBUG] Style text: {style_text}")
            
            # Replace [data:style] placeholder with actual style information
            if '[data:style]' in prompt_text:
                if style_text:
                    prompt_text = prompt_text.replace('[data:style]', style_text)
                else:
                    prompt_text = prompt_text.replace('[data:style]', '')
            else:
                # If placeholder not found, append style information to prompt
                if style_text:
                    prompt_text += f"\n\nStyle Guidelines:\n{style_text}"
            
            # Get active style details
            style_details = "No style information available"
            cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
            post_row = cursor.fetchone()
            if post_row and post_row.get('extra_settings'):
                imaging = post_row['extra_settings'].get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]
                    style_json = active_style.get('style_json', {})
                    if style_json:
                        style_details = json.dumps(style_json, indent=2)
            
            return jsonify({
                'success': True,
                'system_prompt': system_prompt,
                'user_prompt': prompt_text,
                'style_details': style_details,
                'selected_concept': selected_concept,
                'topics': topics
            })
            
    except Exception as e:
        logger.error(f"Error getting LLM prompt details: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/save-image-prompt', methods=['POST'])
def api_save_image_prompt(post_id, section_id):
    """Save image prompt for a section"""
    try:
        data = request.get_json()
        image_prompt = data.get('image_prompt')
        
        if not image_prompt:
            return jsonify({'error': 'Image prompt is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current sections data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row:
                return jsonify({'error': 'Post development data not found'}), 404
            
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                for s in sections_list:
                    if s.get('id') == section_id:
                        s['image_prompts'] = {
                            'image_prompt': image_prompt
                        }
                        break
                
                # Update database
                cursor.execute("""
                    UPDATE post_development 
                    SET sections = %s 
                    WHERE post_id = %s
                """, (json.dumps(sections_data), post_id))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Image prompt saved successfully'
                })
            else:
                return jsonify({'error': 'Invalid sections data structure'}), 500
                
    except Exception as e:
        logger.error(f"Error saving image prompt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/generate-image-captions', methods=['POST'])
def api_generate_image_captions(post_id, section_id):
    """Generate image captions and alt text for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section data from post_section table
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get the selected concept details
            selected_concept_text = ''
            if section.get('selected_image_concept') and section.get('image_concepts'):
                try:
                    # Handle both string and object formats
                    concepts_data = section['image_concepts']
                    if isinstance(concepts_data, str):
                        concepts_data = json.loads(concepts_data)
                    
                    if concepts_data.get('concepts'):
                        selected_concept = next(
                            (c for c in concepts_data['concepts'] if c['concept_id'] == section['selected_image_concept']), 
                            None
                        )
                        if selected_concept:
                            # Exclude the concept_title as it's too metaphorical
                            selected_concept_text = f"{selected_concept['concept_description']}\nMood: {selected_concept['concept_mood']}\nKey Elements: {selected_concept['key_visual_elements']}"
                except Exception as e:
                    logger.error(f"Error parsing selected concept: {e}")
                    selected_concept_text = section.get('selected_image_concept', '')
            
            # Get the image captions prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Captions Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'Image Captions prompt not found'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:selected_concept]', selected_concept_text)
            prompt_text = prompt_text.replace('[SECTION_TITLE]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[SECTION_DESCRIPTION]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[SECTION_CONTENT]', section.get('polished') or section.get('draft') or '')
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Create intercept context for message capture
            intercept_context = {
                'post_id': post_id,
                'section_id': section_id
            }
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, intercept_context=intercept_context)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            raw_content = result['content']
            
            # Parse JSON response
            try:
                # Strip markdown code blocks if present
                content = raw_content.strip()
                if content.startswith('```') and content.endswith('```'):
                    content = content[3:-3].strip()
                elif content.startswith('```json'):
                    content = content[7:-3].strip()
                elif content.startswith('```'):
                    content = content[3:-3].strip()
                
                # Extract only the JSON part (before any additional text)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    content = content[json_start:json_end]
                
                parsed_json = json.loads(content)
                
                if not isinstance(parsed_json, dict) or 'caption' not in parsed_json or 'alt_text' not in parsed_json:
                    raise ValueError("Missing 'caption' or 'alt_text' keys")
                
                if not parsed_json['caption'] or not parsed_json['caption'].strip():
                    raise ValueError("caption field is empty")
                
                if not parsed_json['alt_text'] or not parsed_json['alt_text'].strip():
                    raise ValueError("alt_text field is empty")
                
                # Save to database
                cursor.execute("""
                    UPDATE post_section 
                    SET image_captions = %s, image_alt_text = %s
                    WHERE post_id = %s AND id = %s
                """, (parsed_json['caption'].strip(), parsed_json['alt_text'].strip(), post_id, section_id))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'caption': parsed_json['caption'].strip(),
                    'alt_text': parsed_json['alt_text'].strip(),
                    'message': 'Image captions generated successfully'
                })
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing LLM response: {e}")
                logger.error(f"Raw content: {raw_content}")
                return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
                
    except Exception as e:
        logger.error(f"Error generating image captions: {e}")
        return jsonify({'error': str(e)}), 500
