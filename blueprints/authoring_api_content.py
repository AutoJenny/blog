# Authoring Content API Blueprint
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)
bp = Blueprint('authoring_content', __name__)

# Import micro-modules
from blueprints.authoring_api_sections import api_get_sections as sections_api_func, api_get_section as section_api_func

# Import LLM service
try:
    from modules.llm_service import llm_service
except ImportError:
    # Fallback for when llm_service is not available
    llm_service = None

@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get all sections for a post"""
    return sections_api_func(post_id)

@bp.route('/api/posts/<int:post_id>/sections/<section_id>')
def api_get_section_detail(post_id, section_id):
    """Get detailed information for a specific section"""
    return section_api_func(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>', methods=['PUT'])
def api_save_section_content(post_id, section_id):
    """Save section content (draft, polished, etc.)"""
    try:
        data = request.get_json()
        
        # Extract content fields
        draft = data.get('draft', '')
        polished = data.get('polished', '')
        ideas_to_include = data.get('ideas_to_include', '')
        facts_to_include = data.get('facts_to_include', '')
        highlighting = data.get('highlighting', '')
        status = data.get('status', 'draft')
        
        with db_manager.get_cursor() as cursor:
            # Update the section
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, polished = %s, ideas_to_include = %s, 
                    facts_to_include = %s, highlighting = %s, status = %s,
                    updated_at = NOW()
                WHERE post_id = %s AND id = %s
            """, (draft, polished, ideas_to_include, facts_to_include, 
                  highlighting, status, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section content saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving section content: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate', methods=['POST'])
def api_generate_section_draft(post_id, section_id):
    """Generate section draft using LLM"""
    try:
        data = request.get_json()
        
        # Get section data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT section_heading, section_description, ideas_to_include, 
                       facts_to_include, highlighting
                FROM post_section 
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get post context
            cursor.execute("""
                SELECT title, status FROM post WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get LLM prompt template
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Section Drafting'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Section Drafting prompt not found'}), 404
            
            # Build the prompt
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Replace placeholders
            prompt_text = prompt_text.replace('[data:post_title]', post['title'] or '')
            prompt_text = prompt_text.replace('[data:section_heading]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:section_description]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:ideas_to_include]', section['ideas_to_include'] or '')
            prompt_text = prompt_text.replace('[data:facts_to_include]', section['facts_to_include'] or '')
            prompt_text = prompt_text.replace('[data:highlighting]', section['highlighting'] or '')
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            generated_content = result['content'].strip()
            
            # Save the generated content
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, status = 'draft', updated_at = NOW()
                WHERE post_id = %s AND id = %s
            """, (generated_content, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'draft': generated_content,
                'message': 'Section draft generated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error generating section draft: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-concepts', methods=['GET', 'PUT'])
def api_image_concepts_prompt():
    """Get or update the Image Concepts prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Concepts Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Concepts Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': 'Image Concepts prompt not found'}), 404
                
                return jsonify({
                    'name': prompt_data['name'],
                    'prompt_text': prompt_data['prompt_text'],
                    'system_prompt': prompt_data['system_prompt'],
                    'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                })
                
    except Exception as e:
        logger.error(f"Error with image concepts prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/section-drafting', methods=['GET', 'PUT'])
def api_section_drafting_prompt():
    """Get or update the Section Drafting prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Section Drafting'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Section Drafting'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': 'Section Drafting prompt not found'}), 404
                
                return jsonify({
                    'name': prompt_data['name'],
                    'prompt_text': prompt_data['prompt_text'],
                    'system_prompt': prompt_data['system_prompt'],
                    'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                })
                
    except Exception as e:
        logger.error(f"Error with section drafting prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-prompts', methods=['GET', 'PUT'])
def api_image_prompts_prompt():
    """Get or update the Image Prompts prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Prompts Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Prompts Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': 'Image Prompts prompt not found'}), 404
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'prompt_text': prompt_data['prompt_text'],
                        'system_prompt': prompt_data['system_prompt'],
                        'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                    }
                })
                
    except Exception as e:
        logger.error(f"Error with image prompts prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-captions', methods=['GET', 'PUT'])
def api_image_captions_prompt():
    """Get or update the Image Captions prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Captions Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Captions Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': 'Image Captions prompt not found'}), 404
                
                return jsonify({
                    'name': prompt_data['name'],
                    'prompt_text': prompt_data['prompt_text'],
                    'system_prompt': prompt_data['system_prompt'],
                    'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                })
                
    except Exception as e:
        logger.error(f"Error with image captions prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-generation', methods=['GET', 'PUT'])
def api_image_generation_prompt():
    """Get or update the Image Generation prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': 'Image Generation prompt not found'}), 404
                
                return jsonify({
                    'name': prompt_data['name'],
                    'prompt_text': prompt_data['prompt_text'],
                    'system_prompt': prompt_data['system_prompt'],
                    'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                })
                
    except Exception as e:
        logger.error(f"Error with image generation prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ui/preferences/<pref_key>', methods=['GET', 'POST'])
def authoring_ui_preferences(pref_key):
    """Handle UI preferences storage and retrieval"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'POST':
                # Save preference
                data = request.get_json()
                value = data.get('value')
                
                cursor.execute("""
                    INSERT INTO ui_user_preferences (preference_key, preference_value, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (preference_key) 
                    DO UPDATE SET preference_value = %s, updated_at = NOW()
                """, (pref_key, value, value))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Preference saved successfully'
                })
            else:
                # Get preference
                cursor.execute("""
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE preference_key = %s
                """, (pref_key,))
                result = cursor.fetchone()
                
                return jsonify({
                    'preference_key': pref_key,
                    'preference_value': result['preference_value'] if result else None
                })
                
    except Exception as e:
        logger.error(f"Error with UI preferences: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-imaging-model-selection', methods=['POST'])
def api_save_imaging_model_selection():
    """Save the selected imaging model for a post"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        model_selection = data.get('model_selection')
        
        if not post_id or not model_selection:
            return jsonify({'error': 'Missing post_id or model_selection'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update post_development table
            cursor.execute("""
                UPDATE post_development 
                SET imaging_model_selection = %s, updated_at = NOW()
                WHERE post_id = %s
            """, (model_selection, post_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Imaging model selection saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving imaging model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/imaging-model-selection', methods=['GET'])
def api_get_imaging_model_selection(post_id):
    """Get the selected imaging model for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT imaging_model_selection 
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            model_selection = result['imaging_model_selection'] if result else 'sdxl-lora'
            
            return jsonify({
                'model_selection': model_selection
            })
            
    except Exception as e:
        logger.error(f"Error getting imaging model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-system-prompt', methods=['POST'])
def api_save_system_prompt():
    """Save system prompt for LLM actions"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name')
        system_prompt = data.get('system_prompt')
        
        if not prompt_name or not system_prompt:
            return jsonify({'error': 'Missing prompt_name or system_prompt'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = %s, updated_at = NOW()
                WHERE name = %s
            """, (system_prompt, prompt_name))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'System prompt saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving system prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-style-guidelines', methods=['POST'])
def api_save_style_guidelines():
    """Save style guidelines for image generation"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name')
        style_guidelines = data.get('style_guidelines')
        
        if not prompt_name or not style_guidelines:
            return jsonify({'error': 'Missing prompt_name or style_guidelines'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE llm_prompt 
                SET prompt_text = %s, updated_at = NOW()
                WHERE name = %s
            """, (style_guidelines, prompt_name))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Style guidelines saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving style guidelines: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/generate-image-prompt-from-stored-message', methods=['POST'])
def api_generate_image_prompt_from_stored_message():
    """Generate image prompt using stored message from intercept panel"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        stored_message = data.get('stored_message')
        
        if not all([post_id, section_id, stored_message]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        if not llm_service:
            return jsonify({'error': 'LLM service not available'}), 500
        
        # Parse the stored message to extract system and user messages
        messages = []
        
        if 'SYSTEM MESSAGE:' in stored_message and 'USER MESSAGE:' in stored_message:
            parts = stored_message.split('USER MESSAGE:')
            if len(parts) == 2:
                system_part = parts[0].replace('SYSTEM MESSAGE:', '').strip()
                user_part = parts[1].strip()
                
                if system_part:
                    messages.append({'role': 'system', 'content': system_part})
                messages.append({'role': 'user', 'content': user_part})
        else:
            # Fallback: treat entire message as user message
            messages.append({'role': 'user', 'content': stored_message})
        
        # Execute LLM request with intercept context
        intercept_context = {
            'post_id': post_id,
            'section_id': section_id
        }
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, intercept_context=intercept_context)
        
        if 'error' in result:
            return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
        
        # Parse the response
        try:
            response_data = json.loads(result['content'])
            if 'image_prompt' in response_data:
                return jsonify({
                    'success': True,
                    'image_prompt': response_data['image_prompt']
                })
            else:
                return jsonify({'error': 'Invalid response format from LLM'}), 500
        except json.JSONDecodeError:
            return jsonify({'error': 'LLM returned invalid JSON'}), 500
            
    except Exception as e:
        logger.error(f"Error generating image prompt from stored message: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/intercepted-message', methods=['GET'])
def api_get_intercepted_message(post_id, section_id):
    """Get the most recent intercepted LLM message for a post/section"""
    try:
        if not llm_service:
            return jsonify({'error': 'LLM service not available'}), 500
        
        intercepted_data = llm_service.get_intercepted_message(post_id, section_id)
        
        if intercepted_data:
            return jsonify({
                'success': True,
                'message': intercepted_data['message'],
                'raw_messages': intercepted_data['raw_messages'],
                'complete_api_request': intercepted_data['complete_api_request'],
                'created_at': intercepted_data['created_at'].isoformat() if intercepted_data['created_at'] else None
            })
        else:
            return jsonify({
                'success': True,
                'message': None,
                'raw_messages': None,
                'complete_api_request': None,
                'created_at': None
            })
            
    except Exception as e:
        logger.error(f"Error getting intercepted message: {e}")
        return jsonify({'error': str(e)}), 500
