"""
Planning Post-Specific API Module

Micro-file for post-specific API endpoints that aren't basic CRUD
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def get_post_by_theme(theme_id):
    """Get a post assigned to a week that has this theme selected.
    DEPRECATED: Parameter name kept as theme_idea_id for backwards compatibility, but only theme_id is supported.
    Uses new calendar_week_selection and calendar_week_posts tables.
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Check if new tables exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_selection'
                ) as has_selection,
                EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts'
                ) as has_posts
            """)
            table_check = cursor.fetchone()
            has_new_tables = table_check['has_selection'] and table_check['has_posts']
            
            if has_new_tables:
                # Use new V2 architecture - find post in week with selected theme matching theme_id
                cursor.execute("""
                    SELECT cwp.post_id
                    FROM calendar_week_selection cws
                    JOIN calendar_week_posts cwp ON cws.year = cwp.year AND cws.week_number = cwp.week_number
                    WHERE cws.selected_theme_id = %s
                      AND cwp.post_id IS NOT NULL
                    ORDER BY cwp.created_at DESC
                    LIMIT 1
                """, (theme_id,))
            else:
                # Use calendar_week_posts_v2 to find post with this theme
                cursor.execute("""
                    SELECT cwp.post_id
                    FROM calendar_week_selection_v2 cws
                    JOIN calendar_week_posts_v2 cwp ON cws.year = cwp.year AND cws.week_number = cwp.week_number
                    WHERE cws.selected_theme_id = %s
                      AND cwp.post_id IS NOT NULL
                    ORDER BY cwp.created_at DESC
                    LIMIT 1
                """, (theme_id,))
            
            result = cursor.fetchone()
            
            if result and result['post_id']:
                return jsonify({
                    'success': True,
                    'post_id': result['post_id']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No post found with this theme'
                }), 404
    except Exception as e:
        logger.error(f"Error finding post by theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_get_expanded_idea_prompt_selection(post_id):
    """Get available prompt options and current selection for expanded idea generation"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get taxonomy for the post
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            taxonomy_result = cursor.fetchone()
            content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
            
            # Get available prompts
            available_prompts = []
            
            # Default prompt
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Expanded Idea Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            default_prompt = cursor.fetchone()
            if default_prompt:
                available_prompts.append({
                    'name': default_prompt['name'],
                    'id': default_prompt['id'],
                    'is_default': True
                })
            
            # Category-specific prompt (if category exists)
            if content_type_name:
                category_prompt_name = f'Expanded Idea Generation ({content_type_name})'
                cursor.execute("""
                    SELECT name, id FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (category_prompt_name,))
                category_prompt = cursor.fetchone()
                if category_prompt:
                    available_prompts.append({
                        'name': category_prompt['name'],
                        'id': category_prompt['id'],
                        'is_default': False,
                        'category': content_type_name
                    })
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('expanded_idea_prompt_name')
            
            # LEGACY POSTS: If no selection exists, explicitly set to default prompt
            # This is an explicit initial selection, not a fallback
            # We save it to the post so it's persistent
            if not current_selection and available_prompts:
                # Find the default prompt (marked with is_default: true)
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this explicit selection to the post for legacy posts
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['expanded_idea_prompt_name'] = current_selection
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
                else:
                    # No default prompt available - this is a system error
                    return jsonify({
                        'error': 'Default prompt "Expanded Idea Generation" not found. Please create it in the database.'
                    }), 500
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection,
                'content_type_name': content_type_name
            })
    except Exception as e:
        logger.error(f"Error getting prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_set_expanded_idea_prompt_selection(post_id):
    """Set the selected prompt for expanded idea generation"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name') if data else None
        
        if not prompt_name:
            return jsonify({'error': 'prompt_name is required'}), 400
        
        # Verify prompt exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM llm_prompt WHERE name = %s
            """, (prompt_name,))
            if not cursor.fetchone():
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            # Save selection to post.extra_settings - PERSIST TO DATABASE
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['expanded_idea_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_expanded_idea_prompt(post_id):
    """Get the expanded idea prompt for a post, optionally filtered by prompt_name query parameter"""
    try:
        # Get prompt_name from query parameter (passed from frontend)
        prompt_name = request.args.get('prompt_name')
        
        with db_manager.get_cursor() as cursor:
            # If prompt_name not provided, get from post.extra_settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('expanded_idea_prompt_name')
                
                # LEGACY: If still no prompt_name, use default
                if not prompt_name:
                    prompt_name = 'Expanded Idea Generation'
            
            # Get the prompt by exact name - NO FALLBACKS
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            # Extract parameters from JSONB if they exist
            parameters = prompt_data['parameters'] or {}
            model = parameters.get('model', 'llama3.2:latest')
            temperature = parameters.get('temperature', 0.7)
            max_tokens = parameters.get('max_tokens', 2000)
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': prompt_data['name'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text'],
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            })
    except Exception as e:
        logger.error(f"Error fetching expanded idea prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_brainstorm_prompt_selection(post_id):
    """Get available prompt options and current selection for topic brainstorming"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get taxonomy for the post
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            taxonomy_result = cursor.fetchone()
            content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
            
            # Get available prompts
            available_prompts = []
            
            # Default prompt (look for "Topic Brainstorming" first, then "brainstorm_topics")
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Topic Brainstorming' OR name = 'brainstorm_topics'
                ORDER BY CASE 
                    WHEN name = 'Topic Brainstorming' THEN 1
                    WHEN name = 'brainstorm_topics' THEN 2
                    ELSE 3
                END, updated_at DESC 
                LIMIT 1
            """)
            default_prompt = cursor.fetchone()
            if default_prompt:
                available_prompts.append({
                    'name': default_prompt['name'],
                    'id': default_prompt['id'],
                    'is_default': True
                })
            
            # Category-specific prompt (if category exists)
            if content_type_name:
                category_prompt_name = f'Topic Brainstorming ({content_type_name})'
                cursor.execute("""
                    SELECT name, id FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (category_prompt_name,))
                category_prompt = cursor.fetchone()
                if category_prompt:
                    available_prompts.append({
                        'name': category_prompt['name'],
                        'id': category_prompt['id'],
                        'is_default': False,
                        'category': content_type_name
                    })
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('brainstorm_prompt_name')
            
            # LEGACY POSTS: If no selection exists, explicitly set to default prompt
            if not current_selection and available_prompts:
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this explicit selection to the post for legacy posts
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['brainstorm_prompt_name'] = current_selection
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
                else:
                    return jsonify({
                        'error': 'Default prompt "Topic Brainstorming" or "brainstorm_topics" not found. Please create it in the database.'
                    }), 500
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection,
                'content_type_name': content_type_name
            })
    except Exception as e:
        logger.error(f"Error getting brainstorm prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_set_brainstorm_prompt_selection(post_id):
    """Set the selected prompt for topic brainstorming"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name') if data else None
        
        if not prompt_name:
            return jsonify({'error': 'prompt_name is required'}), 400
        
        # Verify prompt exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM llm_prompt WHERE name = %s
            """, (prompt_name,))
            if not cursor.fetchone():
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            # Save selection to post.extra_settings - PERSIST TO DATABASE
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['brainstorm_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting brainstorm prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_brainstorm_prompt(post_id):
    """Get the brainstorm prompt for a post, optionally filtered by prompt_name query parameter"""
    try:
        # Get prompt_name from query parameter (passed from frontend)
        prompt_name = request.args.get('prompt_name')
        
        with db_manager.get_cursor() as cursor:
            # If prompt_name not provided, get from post.extra_settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('brainstorm_prompt_name')
                
                # LEGACY: If still no prompt_name, try defaults
                if not prompt_name:
                    # Try old name first, then new name
                    cursor.execute("""
                        SELECT name FROM llm_prompt WHERE name = 'brainstorm_topics'
                    """)
                    if cursor.fetchone():
                        prompt_name = 'brainstorm_topics'
                    else:
                        prompt_name = 'Topic Brainstorming'
            
            # Get the prompt by exact name - NO FALLBACKS
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            # Extract parameters from JSONB if they exist
            parameters = prompt_data['parameters'] or {}
            model = parameters.get('model', 'llama3.2:latest')
            temperature = parameters.get('temperature', 0.7)
            max_tokens = parameters.get('max_tokens', 2000)
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': prompt_data['name'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text'],
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            })
    except Exception as e:
        logger.error(f"Error fetching brainstorm prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_update_brainstorm_prompt(post_id):
    """Update the brainstorm prompt for a post"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        prompt_text = data.get('prompt_text', '')
        
        if not system_prompt and not prompt_text:
            return jsonify({'error': 'system_prompt or prompt_text is required'}), 400
        
        # Get the prompt name from post settings
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            prompt_name = None
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                prompt_name = settings.get('brainstorm_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                cursor.execute("""
                    SELECT id FROM llm_prompt WHERE name = 'brainstorm_topics'
                """)
                if cursor.fetchone():
                    prompt_name = 'brainstorm_topics'
                else:
                    prompt_name = 'Topic Brainstorming'
            
            # Update the prompt in the database
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = COALESCE(%s, system_prompt),
                    prompt_text = COALESCE(%s, prompt_text),
                    updated_at = NOW()
                WHERE name = %s
                RETURNING name, system_prompt, prompt_text
            """, (system_prompt if system_prompt else None, 
                  prompt_text if prompt_text else None, 
                  prompt_name))
            
            updated_prompt = cursor.fetchone()
            cursor.connection.commit()
            
            if not updated_prompt:
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': updated_prompt['name'],
                    'system_prompt': updated_prompt['system_prompt'],
                    'prompt_text': updated_prompt['prompt_text']
                }
            })
    except Exception as e:
        logger.error(f"Error updating brainstorm prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_section_structure_prompt_selection(post_id):
    """Get available prompt options and current selection for section structure design"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get taxonomy for the post
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            taxonomy_result = cursor.fetchone()
            content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
            
            # Get available prompts
            available_prompts = []
            
            # Default prompt
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Section Structure Design'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            default_prompt = cursor.fetchone()
            if default_prompt:
                available_prompts.append({
                    'name': default_prompt['name'],
                    'id': default_prompt['id'],
                    'is_default': True
                })
            
            # Category-specific prompt (if category exists)
            if content_type_name:
                cursor.execute("""
                    SELECT name, id FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (f'Section Structure Design ({content_type_name})',))
                category_prompt = cursor.fetchone()
                if category_prompt:
                    available_prompts.append({
                        'name': category_prompt['name'],
                        'id': category_prompt['id'],
                        'is_default': False
                    })
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('section_structure_prompt_name')
            
            # LEGACY POSTS: If no selection exists, explicitly set to default prompt
            if not current_selection and available_prompts:
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this explicit selection to the post for legacy posts
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['section_structure_prompt_name'] = current_selection
                    
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection,
                'content_type_name': content_type_name
            })
    except Exception as e:
        logger.error(f"Error fetching section structure prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_set_section_structure_prompt_selection(post_id):
    """Set the selected prompt for section structure design"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name') if data else None
        
        if not prompt_name:
            return jsonify({'error': 'prompt_name is required'}), 400
        
        # Verify prompt exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM llm_prompt WHERE name = %s
            """, (prompt_name,))
            if not cursor.fetchone():
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            # Save selection to post.extra_settings - PERSIST TO DATABASE
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['section_structure_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting section structure prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_section_structure_prompt(post_id):
    """Get the section structure prompt for a post, optionally filtered by prompt_name query parameter"""
    try:
        # Get prompt_name from query parameter (passed from frontend)
        prompt_name = request.args.get('prompt_name')
        
        with db_manager.get_cursor() as cursor:
            # If prompt_name not provided, get from post.extra_settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('section_structure_prompt_name')
                
                # LEGACY: If still no prompt_name, use default
                if not prompt_name:
                    prompt_name = 'Section Structure Design'
            
            # Get the prompt by exact name - NO FALLBACKS
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            # Extract parameters from JSONB if they exist
            parameters = prompt_data['parameters'] or {}
            model = parameters.get('model', 'llama3.2:latest')
            temperature = parameters.get('temperature', 0.7)
            max_tokens = parameters.get('max_tokens', 2000)
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': prompt_data['name'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text'],
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            })
    except Exception as e:
        logger.error(f"Error fetching section structure prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_update_section_structure_prompt(post_id):
    """Update the section structure prompt for a post"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        prompt_text = data.get('prompt_text', '')
        
        if not system_prompt and not prompt_text:
            return jsonify({'error': 'system_prompt or prompt_text is required'}), 400
        
        # Get the prompt name from post settings
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            prompt_name = None
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                prompt_name = settings.get('section_structure_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                prompt_name = 'Section Structure Design'
            
            # Update the prompt in the database
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = COALESCE(%s, system_prompt),
                    prompt_text = COALESCE(%s, prompt_text),
                    updated_at = NOW()
                WHERE name = %s
                RETURNING name, system_prompt, prompt_text
            """, (system_prompt if system_prompt else None, 
                  prompt_text if prompt_text else None, 
                  prompt_name))
            
            updated_prompt = cursor.fetchone()
            cursor.connection.commit()
            
            if not updated_prompt:
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': updated_prompt['name'],
                    'system_prompt': updated_prompt['system_prompt'],
                    'prompt_text': updated_prompt['prompt_text']
                }
            })
    except Exception as e:
        logger.error(f"Error updating section structure prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_topic_allocation_prompt_selection(post_id):
    """Get available prompt options and current selection for topic allocation"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get taxonomy for the post
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            taxonomy_result = cursor.fetchone()
            content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
            
            # Get available prompts
            available_prompts = []
            
            # Default prompt
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Topic Allocation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            default_prompt = cursor.fetchone()
            if default_prompt:
                available_prompts.append({
                    'name': default_prompt['name'],
                    'id': default_prompt['id'],
                    'is_default': True
                })
            
            # Category-specific prompt (if category exists)
            if content_type_name:
                cursor.execute("""
                    SELECT name, id FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (f'Topic Allocation ({content_type_name})',))
                category_prompt = cursor.fetchone()
                if category_prompt:
                    available_prompts.append({
                        'name': category_prompt['name'],
                        'id': category_prompt['id'],
                        'is_default': False
                    })
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('topic_allocation_prompt_name')
            
            # LEGACY POSTS: If no selection exists, explicitly set to default prompt
            if not current_selection and available_prompts:
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this explicit selection to the post for legacy posts
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['topic_allocation_prompt_name'] = current_selection
                    
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection,
                'content_type_name': content_type_name
            })
    except Exception as e:
        logger.error(f"Error fetching topic allocation prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_set_topic_allocation_prompt_selection(post_id):
    """Set the selected prompt for topic allocation"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name') if data else None
        
        if not prompt_name:
            return jsonify({'error': 'prompt_name is required'}), 400
        
        # Verify prompt exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM llm_prompt WHERE name = %s
            """, (prompt_name,))
            if not cursor.fetchone():
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            # Save selection to post.extra_settings - PERSIST TO DATABASE
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['topic_allocation_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting topic allocation prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_topic_allocation_prompt(post_id):
    """Get the topic allocation prompt for a post, optionally filtered by prompt_name query parameter"""
    try:
        # Get prompt_name from query parameter (passed from frontend)
        prompt_name = request.args.get('prompt_name')
        
        with db_manager.get_cursor() as cursor:
            # If prompt_name not provided, get from post.extra_settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('topic_allocation_prompt_name')
                
                # LEGACY: If still no prompt_name, use default
                if not prompt_name:
                    prompt_name = 'Topic Allocation'
            
            # Get the prompt by exact name - NO FALLBACKS
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            # Extract parameters from JSONB if they exist
            parameters = prompt_data['parameters'] or {}
            model = parameters.get('model', 'llama3.2:latest')
            temperature = parameters.get('temperature', 0.7)
            max_tokens = parameters.get('max_tokens', 2000)
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': prompt_data['name'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text'],
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            })
    except Exception as e:
        logger.error(f"Error fetching topic allocation prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_update_topic_allocation_prompt(post_id):
    """Update the topic allocation prompt for a post"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        prompt_text = data.get('prompt_text', '')
        
        if not system_prompt and not prompt_text:
            return jsonify({'error': 'system_prompt or prompt_text is required'}), 400
        
        # Get the prompt name from post settings
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            prompt_name = None
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                prompt_name = settings.get('topic_allocation_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                prompt_name = 'Topic Allocation'
            
            # Update the prompt in the database
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = COALESCE(%s, system_prompt),
                    prompt_text = COALESCE(%s, prompt_text),
                    updated_at = NOW()
                WHERE name = %s
                RETURNING name, system_prompt, prompt_text
            """, (system_prompt if system_prompt else None, 
                  prompt_text if prompt_text else None, 
                  prompt_name))
            
            updated_prompt = cursor.fetchone()
            cursor.connection.commit()
            
            if not updated_prompt:
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': updated_prompt['name'],
                    'system_prompt': updated_prompt['system_prompt'],
                    'prompt_text': updated_prompt['prompt_text']
                }
            })
    except Exception as e:
        logger.error(f"Error updating topic allocation prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_section_titling_prompt_selection(post_id):
    """Get available prompt options and current selection for section titling"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get taxonomy for the post
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            taxonomy_result = cursor.fetchone()
            content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
            
            # Get available prompts
            available_prompts = []
            
            # Default prompt
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Section Titling'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            default_prompt = cursor.fetchone()
            if default_prompt:
                available_prompts.append({
                    'name': default_prompt['name'],
                    'id': default_prompt['id'],
                    'is_default': True
                })
            
            # Category-specific prompt (if category exists)
            if content_type_name:
                cursor.execute("""
                    SELECT name, id FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (f'Section Titling ({content_type_name})',))
                category_prompt = cursor.fetchone()
                if category_prompt:
                    available_prompts.append({
                        'name': category_prompt['name'],
                        'id': category_prompt['id'],
                        'is_default': False
                    })
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('section_titling_prompt_name')
            
            # LEGACY POSTS: If no selection exists, explicitly set to default prompt
            if not current_selection and available_prompts:
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this explicit selection to the post for legacy posts
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['section_titling_prompt_name'] = current_selection
                    
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection,
                'content_type_name': content_type_name
            })
    except Exception as e:
        logger.error(f"Error fetching section titling prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_set_section_titling_prompt_selection(post_id):
    """Set the selected prompt for section titling"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name') if data else None
        
        if not prompt_name:
            return jsonify({'error': 'prompt_name is required'}), 400
        
        # Verify prompt exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM llm_prompt WHERE name = %s
            """, (prompt_name,))
            if not cursor.fetchone():
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            # Save selection to post.extra_settings - PERSIST TO DATABASE
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['section_titling_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting section titling prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_section_titling_prompt(post_id):
    """Get the section titling prompt for a post, optionally filtered by prompt_name query parameter"""
    try:
        # Get prompt_name from query parameter (passed from frontend)
        prompt_name = request.args.get('prompt_name')
        
        with db_manager.get_cursor() as cursor:
            # If prompt_name not provided, get from post.extra_settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('section_titling_prompt_name')
                
                # LEGACY: If still no prompt_name, use default
                if not prompt_name:
                    prompt_name = 'Section Titling'
            
            # Get the prompt by exact name - NO FALLBACKS
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            # Extract parameters from JSONB if they exist
            parameters = prompt_data['parameters'] or {}
            model = parameters.get('model', 'llama3.2:latest')
            temperature = parameters.get('temperature', 0.7)
            max_tokens = parameters.get('max_tokens', 2000)
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': prompt_data['name'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text'],
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            })
    except Exception as e:
        logger.error(f"Error fetching section titling prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_update_section_titling_prompt(post_id):
    """Update the section titling prompt for a post"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        prompt_text = data.get('prompt_text', '')
        
        if not system_prompt and not prompt_text:
            return jsonify({'error': 'system_prompt or prompt_text is required'}), 400
        
        # Get the prompt name from post settings
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            prompt_name = None
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                prompt_name = settings.get('section_titling_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                prompt_name = 'Section Titling'
            
            # Update the prompt in the database
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = COALESCE(%s, system_prompt),
                    prompt_text = COALESCE(%s, prompt_text),
                    updated_at = NOW()
                WHERE name = %s
                RETURNING name, system_prompt, prompt_text
            """, (system_prompt if system_prompt else None, 
                  prompt_text if prompt_text else None, 
                  prompt_name))
            
            updated_prompt = cursor.fetchone()
            cursor.connection.commit()
            
            if not updated_prompt:
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': updated_prompt['name'],
                    'system_prompt': updated_prompt['system_prompt'],
                    'prompt_text': updated_prompt['prompt_text']
                }
            })
    except Exception as e:
        logger.error(f"Error updating section titling prompt: {e}")
        return jsonify({'error': str(e)}), 500

def api_posts_expanded_idea(post_id):
    """Get or create expanded idea for a post"""
    if request.method == 'GET':
        try:
            # CRITICAL: Read year/week from query parameters to get expanded idea for the CORRECT week
            url_year = request.args.get('year', type=int)
            url_week = request.args.get('week', type=int)
            
            # If week context is provided, try to fetch expanded idea for that week's post
            if url_year and url_week:
                with db_manager.get_cursor() as cursor:
                    # Check for calendar_week_posts_v2 table
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'calendar_week_posts_v2'
                        )
                    """)
                    has_v2_table = cursor.fetchone()['exists']
                    
                    if has_v2_table:
                        # Use V2 architecture - find post in THIS week only
                        cursor.execute("""
                            SELECT cwp.post_id, pd.expanded_idea, 
                                   cws.selected_theme_id, ct.theme_title
                            FROM calendar_week_posts_v2 cwp
                            LEFT JOIN post_development pd ON cwp.post_id = pd.post_id
                            LEFT JOIN calendar_week_selection_v2 cws ON cwp.year = cws.year AND cwp.week_number = cws.week_number
                            LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                            WHERE cwp.year = %s 
                              AND cwp.week_number = %s
                              AND pd.expanded_idea IS NOT NULL
                              AND pd.expanded_idea != ''
                            ORDER BY cwp.created_at DESC
                            LIMIT 1
                        """, (url_year, url_week))
                        
                        week_result = cursor.fetchone()
                        
                        if week_result and week_result['expanded_idea']:
                            logger.info(f"Found expanded idea for week {url_year}/{url_week}: post {week_result['post_id']}, theme: {week_result.get('theme_title', 'Unknown')}")
                            return jsonify({
                                'success': True,
                                'expanded_idea': week_result['expanded_idea']
                            })
                    
                    # If week lookup failed or no result, query post_development directly by post_id
                    logger.info(f"No expanded idea found for week {url_year}/{url_week}, trying direct post lookup for post_id {post_id}")
                    cursor.execute("""
                        SELECT expanded_idea
                        FROM post_development 
                        WHERE post_id = %s
                          AND expanded_idea IS NOT NULL
                          AND expanded_idea != ''
                    """, (post_id,))
                    
                    direct_result = cursor.fetchone()
                    
                    if direct_result and direct_result['expanded_idea']:
                        logger.info(f"Found expanded idea directly for post_id {post_id}")
                        return jsonify({
                            'success': True,
                            'expanded_idea': direct_result['expanded_idea']
                        })
                    
                    logger.warn(f"No expanded idea found for post_id {post_id} (week {url_year}/{url_week})")
                    return jsonify({
                        'success': True,
                        'expanded_idea': None
                    })
            
            # If no week context in URL, fetch expanded idea for the requested post_id
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT expanded_idea
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                
                if result and result['expanded_idea']:
                    return jsonify({
                        'success': True,
                        'expanded_idea': result['expanded_idea']
                    })
                else:
                    return jsonify({
                        'success': True,
                        'expanded_idea': None
                    })
                    
        except Exception as e:
            logger.error(f"Error fetching expanded idea: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # REQUIRED: Get year/week from request body or query params
            data = request.get_json() or {}
            url_year = request.args.get('year', type=int) or data.get('year')
            url_week = request.args.get('week', type=int) or data.get('week')
            
            if not url_year or not url_week:
                return jsonify({
                    'error': 'year and week are required. Please provide week context to get the selected theme.'
                }), 400
            
            # Get selected theme with full details from calendar_week_selection
            selected_theme = None
            with db_manager.get_cursor() as cursor:
                # Check for calendar_week_selection_v2 table (current table)
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_selection_v2'
                    )
                """)
                has_v2_table = cursor.fetchone()['exists']
                
                theme_id = None
                
                if has_v2_table:
                    # Use V2 architecture - get selected theme from calendar_week_selection_v2
                    cursor.execute("""
                        SELECT selected_theme_id
                        FROM calendar_week_selection_v2
                        WHERE year = %s AND week_number = %s
                    """, (url_year, url_week))
                    week_selection = cursor.fetchone()
                    
                    if not week_selection or not week_selection.get('selected_theme_id'):
                        # Fallback: Use cyclic system resolver to get theme (same as schedule API)
                        try:
                            from utils.calendar_resolver import resolve_item_for_week
                            theme = resolve_item_for_week("theme", url_year, url_week)
                            if theme and theme.get('id'):
                                theme_id = theme['id']
                            else:
                                return jsonify({
                                    'error': f'No theme selected for week {url_year}/{url_week}. Please select a theme in the calendar week view.'
                                }), 400
                        except Exception as e:
                            logger.error(f"Error resolving theme from cyclic system: {e}")
                            return jsonify({
                                'error': f'No theme selected for week {url_year}/{url_week}. Please select a theme in the calendar week view.'
                            }), 400
                    else:
                        theme_id = week_selection['selected_theme_id']
                    
                    # theme_id is now set from either calendar_week_selection_v2 or cyclic system resolver above
                    # No need to check schedule or assign post to week
                
                theme_data = None
                
                # Try to fetch from calendar_themes first (if theme_id exists)
                if theme_id:
                    cursor.execute("""
                        SELECT ct.theme_title, ct.theme_description, ct.important_notes
                        FROM calendar_themes ct
                        WHERE ct.id = %s
                    """, (theme_id,))
                    theme_data = cursor.fetchone()
                    
                    if theme_data:
                        selected_theme = {
                            'title': theme_data.get('theme_title') or '',
                            'description': theme_data.get('theme_description') or '',
                            'important_notes': theme_data.get('important_notes') or []
                        }
                
                # Fallback to calendar_ideas if theme_id didn't work (backwards compatibility)
                if not theme_data and idea_id:
                    # Check if important_notes column exists
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'calendar_ideas' AND column_name = 'important_notes'
                    """)
                    has_important_notes = cursor.fetchone() is not None
                    
                    # Fetch full idea data (for backwards compatibility)
                    important_notes_field = 'ci.important_notes' if has_important_notes else "'[]'::jsonb as important_notes"
                    cursor.execute(f"""
                        SELECT ci.idea_title, ci.idea_description, {important_notes_field}
                        FROM calendar_ideas ci
                        WHERE ci.id = %s
                    """, (idea_id,))
                    theme_data = cursor.fetchone()
                    
                    if theme_data:
                        selected_theme = {
                            'title': theme_data.get('idea_title') or '',
                            'description': theme_data.get('idea_description') or '',
                            'important_notes': []
                        }
                        
                        if has_important_notes and theme_data.get('important_notes'):
                            import json
                            notes_data = theme_data['important_notes']
                            if isinstance(notes_data, (list, dict)):
                                selected_theme['important_notes'] = notes_data if isinstance(notes_data, list) else [notes_data]
                            elif isinstance(notes_data, str):
                                selected_theme['important_notes'] = json.loads(notes_data)
                
                if not selected_theme:
                    return jsonify({'error': 'Selected theme not found in database'}), 404
            
            # Generate expanded idea using LLM
            llm_service = LLMService()
            
            # Load prompt from database using explicit selection
            with db_manager.get_cursor() as cursor:
                # Get selected prompt name from post settings
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                prompt_name = None
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('expanded_idea_prompt_name')
                
                # LEGACY POSTS: If no selection exists, use default prompt
                # This should only happen if the selection endpoint hasn't been called yet
                # (which would have set the selection). This is an explicit default, not a fallback.
                if not prompt_name:
                    prompt_name = 'Expanded Idea Generation'
                
                # Get the selected prompt - NO FALLBACKS
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (prompt_name,))
                prompt_data = cursor.fetchone()
                
                # FAIL CLEARLY if prompt not found
                if not prompt_data:
                    return jsonify({
                        'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                    }), 404
                
                system_prompt = prompt_data['system_prompt']
                prompt_text = prompt_data['prompt_text']
            
            # Build theme content string to replace [data:idea_seed] or [theme_data]
            theme_content = f"Title: {selected_theme['title']}\n\n"
            if selected_theme['description']:
                theme_content += f"Description: {selected_theme['description']}\n\n"
            
            # Add Important Notes if they exist - HIGHLIGHTED as CRITICAL AND MANDATORY
            if selected_theme['important_notes'] and len(selected_theme['important_notes']) > 0:
                theme_content += "\n\n"
                theme_content += "=" * 70 + "\n"
                theme_content += "⚠️  CRITICAL: IMPORTANT NOTES - MANDATORY REQUIREMENTS ⚠️\n"
                theme_content += "=" * 70 + "\n"
                theme_content += "\n"
                theme_content += "EACH OF THE FOLLOWING NOTES REPRESENTS A MANDATORY TOPIC THAT MUST BE EXPLICITLY INCLUDED.\n"
                theme_content += "YOU CANNOT SKIP, OMIT, OR GLOSS OVER ANY OF THESE - EACH MUST BE EXPLICITLY MENTIONED.\n"
                theme_content += "IF A NOTE SAYS 'Mention X', YOU MUST EXPLICITLY MENTION X IN YOUR RESPONSE.\n"
                theme_content += "\n"
                for i, note in enumerate(selected_theme['important_notes'], 1):
                    note_text = note.get('text', '') if isinstance(note, dict) else str(note)
                    if note_text:
                        theme_content += f"⚠️  MANDATORY NOTE #{i}: {note_text}\n"
                        theme_content += f"   → THIS TOPIC/POINT MUST BE EXPLICITLY AND CLEARLY MENTIONED IN YOUR EXPANDED IDEA\n"
                        theme_content += f"   → DO NOT ALLUDE TO IT - YOU MUST EXPLICITLY INCLUDE IT\n\n"
                theme_content += "=" * 70 + "\n"
                theme_content += "⚠️  FINAL REMINDER: Every single Important Note above is MANDATORY.\n"
                theme_content += "⚠️  You must explicitly address each one - no exceptions.\n"
                theme_content += "⚠️  If you fail to explicitly mention all Important Notes, your response is incomplete.\n"
                theme_content += "=" * 70 + "\n\n"
            
            # Replace placeholder in prompt (handle both old and new formats)
            user_prompt = prompt_text.replace('[data:idea_seed]', theme_content).replace('{idea_seed}', theme_content).replace('[theme_data]', theme_content)
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
            
            if response and 'content' in response:
                expanded_idea = response['content']
                
                # Save to database
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE post_development 
                        SET expanded_idea = %s, updated_at = %s
                        WHERE post_id = %s
                    """, (expanded_idea, datetime.now(), post_id))
                
                return jsonify({
                    'success': True,
                    'expanded_idea': expanded_idea
                })
            else:
                return jsonify({'error': 'Failed to generate expanded idea'}), 500
                
        except Exception as e:
            logger.error(f"Error generating expanded idea: {e}")
            return jsonify({'error': str(e)}), 500

def api_posts_idea_seed(post_id):
    """Get or set idea seed for a post"""
    if request.method == 'GET':
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT idea_seed
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return jsonify({
                        'success': True,
                        'idea_seed': result['idea_seed']
                    })
                else:
                    return jsonify({
                        'success': True,
                        'idea_seed': None
                    })
                    
        except Exception as e:
            logger.error(f"Error fetching idea seed: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            idea_seed = data.get('idea_seed', '')
            
            if not idea_seed:
                return jsonify({'error': 'Idea seed is required'}), 400
            
            # Save to database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post_development 
                    SET idea_seed = %s, updated_at = %s
                    WHERE post_id = %s
                """, (idea_seed, datetime.now(), post_id))
            
            return jsonify({
                'success': True,
                'idea_seed': idea_seed
            })
                
        except Exception as e:
            logger.error(f"Error saving idea seed: {e}")
            return jsonify({'error': str(e)}), 500

def api_check_topic():
    """Check if a topic has already been used this year"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        year = data.get('year', datetime.now().year)
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Check if this topic exists in post_development for this year
            cursor.execute("""
                SELECT pd.post_id, pd.idea_seed, p.created_at
                FROM post_development pd
                JOIN post p ON pd.post_id = p.id
                WHERE pd.idea_seed ILIKE %s 
                AND EXTRACT(YEAR FROM p.created_at) = %s
                ORDER BY p.created_at DESC
                LIMIT 1
            """, (f'%{topic}%', year))
            
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'topic_exists': True,
                    'existing_post_id': result['post_id'],
                    'idea_seed': result['idea_seed']
                })
            else:
                return jsonify({
                    'success': True,
                    'topic_exists': False
                })
                
    except Exception as e:
        logger.error(f"Error checking topic: {e}")
        return jsonify({'error': str(e)}), 500

def api_create_new_post():
    """Create a new post"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Generate unique slug from topic
            base_slug = topic.lower().replace(' ', '-').replace('_', '-')
            base_slug = ''.join(c for c in base_slug if c.isalnum() or c == '-')
            
            # Make slug unique by adding timestamp
            import time
            unique_slug = f"{base_slug}-{int(time.time())}"
            
            # Insert new post
            cursor.execute("""
                INSERT INTO post (title, slug, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (topic, unique_slug, datetime.now(), datetime.now()))
            
            post_id = cursor.fetchone()['id']
            
            # Insert post_development record
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed)
                VALUES (%s, %s)
            """, (post_id, topic))
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'topic': topic
            })
            
    except Exception as e:
        logger.error(f"Error creating new post: {e}")
        return jsonify({'error': str(e)}), 500

def api_posts_idea_scope(post_id):
    """Get or set idea scope for a post"""
    if request.method == 'GET':
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT idea_scope
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                
                if result:
                    # Parse JSON string if it exists
                    idea_scope = result['idea_scope']
                    if idea_scope and isinstance(idea_scope, str):
                        try:
                            idea_scope = json.loads(idea_scope)
                        except json.JSONDecodeError:
                            # If parsing fails, return as string
                            pass
                    
                    return jsonify({
                        'success': True,
                        'idea_scope': idea_scope
                    })
                else:
                    return jsonify({
                        'success': True,
                        'idea_scope': None
                    })
                    
        except Exception as e:
            logger.error(f"Error fetching idea scope: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Handle both 'topics' and 'idea_scope' formats for backward compatibility
            if 'topics' in data:
                # Format topics as JSON for storage (brainstorm page format)
                topics = data.get('topics', [])
                if not topics:
                    return jsonify({'error': 'No topics provided'}), 400
                
                idea_scope_data = {
                    'generated_topics': topics,
                    'generated_at': datetime.now().isoformat(),
                    'total_count': len(topics)
                }
                idea_scope_json = json.dumps(idea_scope_data)
                
            elif 'idea_scope' in data:
                # Direct idea_scope format
                idea_scope_json = data.get('idea_scope', '')
                if not idea_scope_json:
                    return jsonify({'error': 'Idea scope is required'}), 400
            else:
                return jsonify({'error': 'Either topics or idea_scope is required'}), 400
            
            # Save to database
            with db_manager.get_cursor() as cursor:
                # Check if post_development record exists
                cursor.execute("SELECT id FROM post_development WHERE post_id = %s", (post_id,))
                if not cursor.fetchone():
                    # Create post_development record if it doesn't exist
                    cursor.execute("""
                        INSERT INTO post_development (post_id, idea_scope, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW())
                    """, (post_id, idea_scope_json))
                else:
                    # Update existing record
                    cursor.execute("""
                        UPDATE post_development 
                        SET idea_scope = %s, updated_at = NOW()
                        WHERE post_id = %s
                    """, (idea_scope_json, post_id))
            
            return jsonify({
                'success': True,
                'message': 'Topics saved successfully' if 'topics' in data else 'Idea scope updated successfully'
            })
                
        except Exception as e:
            logger.error(f"Error saving idea scope: {e}")
            return jsonify({'error': str(e)}), 500
