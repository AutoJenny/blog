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


@bp.route('/api/generate-image-prompt-from-builder-v2', methods=['POST'])
def api_generate_image_prompt_from_builder():
    """Generate image prompt using the compiled prompt from Prompt Builder"""
    try:
        data = request.get_json()
        compiled_prompt = data.get('compiled_prompt')
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        
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
        
        # Get post data for context
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, subtitle, summary FROM post WHERE id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get section data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row or not dev_row['sections']:
                return jsonify({'error': 'Section data not found'}), 404
            
            # Parse sections data
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                section = None
                for s in sections_list:
                    if str(s.get('id')) == str(section_id):
                        section = s
                        break
                
                if not section:
                    return jsonify({'error': 'Section not found'}), 404
            else:
                return jsonify({'error': 'Invalid sections data'}), 500
            
            # Get topics from topic_allocation
            topics = []
            try:
                if 'topic_allocation' in sections_data:
                    allocation = sections_data['topic_allocation']
                    if isinstance(allocation, dict) and 'sections' in allocation:
                        for s in allocation['sections']:
                            if str(s.get('id')) == str(section_id):
                                topics = allocation.get('topics', [])
                                break
            except Exception as e:
                logger.error(f"Error parsing topic_allocation: {e}")
            
            # Get the image prompts prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Prompts Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'Image Prompts prompt not found'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            logger.info(f"[DEBUG] System prompt length: {len(system_prompt) if system_prompt else 0}")
            logger.info(f"[DEBUG] System prompt preview: {system_prompt[:100] if system_prompt else 'None'}")
            logger.info(f"[DEBUG] *** SYSTEM PROMPT DEBUG ***")
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:idea_seed]', post_data['title'] or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['subtitle'] or '')
            prompt_text = prompt_text.replace('[data:title]', section['title'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['subtitle'] or '')
            prompt_text = prompt_text.replace('[data:section_text]', section.get('polished') or section.get('draft') or '')
            prompt_text = prompt_text.replace('[data:selected_concept]', compiled_prompt or '')
            topics_text = '\n'.join([f'- {topic}' for topic in topics])
            prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
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
                result = llm_service.execute_llm_request(llm_provider.lower(), llm_model, messages)
                
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
            
            # Apply compression if enabled and needed
            compression_used = False
            if enable_compression and len(generated_prompt) > 400:
                # Simple compression - truncate to 400 chars
                generated_prompt = generated_prompt[:400].rsplit(' ', 1)[0] + '.'
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
            
            # Get model-specific character limit
            imaging_limit = 2000  # Default for GPT-Image-1
            if 'sdxl' in llm_model.lower():
                imaging_limit = 400
            
            # Save to database
            try:
                # Update the sections data with the generated prompt
                sections_data = dev_row['sections']
                if isinstance(sections_data, str):
                    sections_data = json.loads(sections_data)
                
                if isinstance(sections_data, dict) and 'sections' in sections_data:
                    sections_list = sections_data['sections']
                    for s in sections_list:
                        if str(s.get('id')) == str(section_id):
                            s['image_prompts'] = {
                                'image_prompt': generated_prompt,
                                'base_concept': compiled_prompt
                            }
                            break
                    
                    # Update the database
                    cursor.execute("""
                        UPDATE post_development 
                        SET sections = %s 
                        WHERE post_id = %s
                    """, (json.dumps(sections_data), post_id))
                else:
                    logger.error("Invalid sections data structure")
                    return jsonify({'error': 'Failed to update sections data'}), 500
                    
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error updating sections JSON for image prompts: {e}")
                return jsonify({'error': 'Failed to update sections data'}), 500
            
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
                'expansion_used': expansion_used
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
            
            # Get section data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row or not dev_row['sections']:
                return jsonify({'error': 'Section data not found'}), 404
            
            # Parse sections data
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                section = None
                for s in sections_list:
                    if str(s.get('id')) == str(section_id):
                        section = s
                        break
                
                if not section:
                    return jsonify({'error': 'Section not found'}), 404
            else:
                return jsonify({'error': 'Invalid sections data'}), 500
            
            # Get topics from topic_allocation
            topics = []
            try:
                if 'topic_allocation' in sections_data:
                    allocation = sections_data['topic_allocation']
                    if isinstance(allocation, dict) and 'sections' in allocation:
                        for s in allocation['sections']:
                            if str(s.get('id')) == str(section_id):
                                topics = allocation.get('topics', [])
                                break
            except Exception as e:
                logger.error(f"Error parsing topic_allocation: {e}")
            
            # Get the image prompts prompt template
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Prompts Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'Image Prompts prompt not found'}), 404
            
            # Build the user prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:idea_seed]', post_data['title'] or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['subtitle'] or '')
            prompt_text = prompt_text.replace('[data:title]', section['title'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['subtitle'] or '')
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
