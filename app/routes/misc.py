"""
Miscellaneous Api Routes module
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from config.database import db_manager
import logging
from datetime import datetime, date
import json
import requests

logger = logging.getLogger(__name__)

# Create misc_bp blueprint
misc_bp = Blueprint('misc_bp', __name__, url_prefix='/api')

"""

# Auto-generated from blueprints/planning.py
# Module: routes/misc.py

@misc_bp.route('/posts')
def api_posts():
    """API endpoint to get posts for planning"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE status IN ('draft', 'in_process')
                ORDER BY updated_at DESC
                LIMIT 20
            """)
            posts = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'posts': [dict(post) for post in posts]
            })
            
    except Exception as e:
        logger.error(f"Error in api_posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@misc_bp.route('/get-post-data')
def get_post_data(post_id):
    """Get detailed post data for data tab."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id as post_id, p.*, pd.*
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Convert to dict and separate post and development data
            data = dict(post_data)
            
            # Ensure we use the correct post ID
            if 'post_id' in data:
                data['id'] = data['post_id']
            
            # Separate post info from development info
            post_info = {k: v for k, v in data.items() if not k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions', 'section_structure', 'topic_allocation', 'refined_topics'))}
            development_info = {k: v for k, v in data.items() if k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions', 'section_structure', 'topic_allocation', 'refined_topics'))}
            
            # Get calendar schedule data for this post
            cursor.execute("""
                SELECT cs.*
                FROM calendar_schedule cs
                WHERE cs.post_id = %s
            """, (post_id,))
            calendar_schedule_data = cursor.fetchall()
            
            # Debug logging
            logger.info(f"Calendar schedule query for post_id={post_id} returned {len(calendar_schedule_data)} results")
            
            # Convert calendar schedule data to list of dicts
            calendar_schedule_list = []
            for row in calendar_schedule_data:
                schedule_dict = dict(row)
                calendar_schedule_list.append(schedule_dict)
                logger.info(f"Calendar schedule entry: {schedule_dict}")
            
            # Get post sections data
            cursor.execute("""
                SELECT ps.*
                FROM post_section ps
                WHERE ps.post_id = %s
                ORDER BY ps.section_order
            """, (post_id,))
            post_sections_data = cursor.fetchall()
            
            # Debug logging
            logger.info(f"Post sections query for post_id={post_id} returned {len(post_sections_data)} results")
            
            # Convert post sections data to list of dicts
            post_sections_list = []
            for row in post_sections_data:
                section_dict = dict(row)
                post_sections_list.append(section_dict)
                logger.info(f"Post section entry: {section_dict}")
            
            return jsonify({
                **post_info,
                'development': development_info,
                'calendar_schedule': calendar_schedule_list,
                'post_sections': post_sections_list
            })
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/update-field')
def api_update_field(post_id):
    """API endpoint to update a field in post or post_development table"""
    try:
        data = request.get_json()
        field_name = data.get('field_name')
        table_type = data.get('table_type')
        new_value = data.get('new_value')
        
        if not field_name or not table_type:
            return jsonify({'error': 'Missing field_name or table_type'}), 400
        
        # Validate table type
        if table_type not in ['post', 'post_development', 'post_section']:
            return jsonify({'error': 'Invalid table_type. Must be "post", "post_development", or "post_section"'}), 400
        
        # Convert empty string to None for database
        if new_value == '':
            new_value = None
        
        with db_manager.get_cursor() as cursor:
            # Update the field
            if table_type == 'post':
                cursor.execute(f"""
                    UPDATE post 
                    SET {field_name} = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_value, post_id))
            else:  # post_development
                cursor.execute(f"""
                    UPDATE post_development 
                    SET {field_name} = %s, updated_at = NOW()
                    WHERE post_id = %s
                """, (new_value, post_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'No rows updated. Post may not exist.'}), 404
            
            # Commit the transaction
            cursor.connection.commit()
            
            logger.info(f"Updated {table_type}.{field_name} for post {post_id} to: {new_value}")
            
            return jsonify({
                'success': True,
                'message': f'Field {field_name} updated successfully',
                'field_name': field_name,
                'table_type': table_type,
                'new_value': new_value
            })
            
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/post-progress')
def api_post_progress(post_id):
    """API endpoint to get planning progress for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    wse.name as stage_name,
                    wsse.name as sub_stage_name,
                    pws.status,
                    pws.updated_at
                FROM post_workflow_stage pws
                JOIN workflow_stage_entity wse ON pws.stage_id = wse.id
                LEFT JOIN workflow_sub_stage_entity wsse ON pws.sub_stage_id = wsse.id
                WHERE pws.post_id = %s AND wse.name = 'planning'
                ORDER BY wse.stage_order, wsse.sub_stage_order
            """, (post_id,))
            progress = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'progress': [dict(p) for p in progress]
            })
            
    except Exception as e:
        logger.error(f"Error in api_post_progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@misc_bp.route('/get-step-config')
def get_step_config(stage, substage, step):
    """Get step configuration for LLM actions."""
    try:
        with db_manager.get_cursor() as cursor:
            # Convert step name from URL format to database format
            db_step_name = step.replace('_', ' ').title()
            
            cursor.execute("""
                SELECT ws.id, ws.name, ws.description, ws.config
                FROM workflow_stage_entity s
                JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
                WHERE s.name ILIKE %s
                AND ss.name ILIKE %s
                AND ws.name ILIKE %s
            """, (stage, substage, db_step_name))
            result = cursor.fetchone()
            
            if result:
                # Handle config - it might already be a dict or a JSON string
                if isinstance(result['config'], dict):
                    config = result['config']
                elif isinstance(result['config'], str):
                    try:
                        config = json.loads(result['config'])
                    except json.JSONDecodeError:
                        config = {}
                else:
                    config = {}
                
                return jsonify({
                    'step_id': result['id'],
                    'step_name': result['name'],
                    'description': result['description'],
                    'config': config
                })
            else:
                return jsonify({'error': 'Step not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting step config: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/get-providers')
def get_providers():
    """Get available LLM providers."""
    try:
        providers = []
        for key, provider in llm_service.providers.items():
            providers.append({
                'id': key,
                'name': provider['name'],
                'base_url': provider['base_url'],
                'models': llm_service.get_available_models(key)
            })
        return jsonify(providers)
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/get-actions')
def get_actions():
    """Get all LLM actions/prompts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT lp.id, lp.name, lp.description, 
                       COALESCE(lp.system_prompt, '') as system_prompt,
                       COALESCE(lp.prompt_text, '') as prompt_text
                FROM llm_prompt lp
                WHERE lp.system_prompt IS NULL OR lp.system_prompt = ''
                ORDER BY lp.name
            """)
            task_prompts = cursor.fetchall()

            return jsonify({
                'task_prompts': [dict(prompt) for prompt in task_prompts]
            })
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/get-system-prompts')
def get_system_prompts():
    """Get all system prompts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT lp.id, lp.name, lp.description, 
                       COALESCE(lp.system_prompt, '') as system_prompt,
                       COALESCE(lp.prompt_text, '') as prompt_text
                FROM llm_prompt lp
                WHERE lp.system_prompt IS NOT NULL AND lp.system_prompt != ''
                ORDER BY lp.name
            """)
            system_prompts = cursor.fetchall()

            return jsonify({
                'system_prompts': [dict(prompt) for prompt in system_prompts]
            })
    except Exception as e:
        logger.error(f"Error getting system prompts: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/execute-action')
def execute_action(action_id):
    """Execute a specific LLM action."""
    try:
        data = request.get_json()
        input_data = data.get('input_data', {})
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'llama2')
        
        # Get action details
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT name, description, prompt_text, system_prompt
                FROM llm_prompt
                WHERE id = %s
            """, (action_id,))
            action = cursor.fetchone()
            
            if not action:
                return jsonify({'error': 'Action not found'}), 404
            
            # Build messages
            messages = []
            if action['system_prompt']:
                messages.append({'role': 'system', 'content': action['system_prompt']})
            
            # Process prompt template with input data
            prompt = action['prompt_text']
            for key, value in input_data.items():
                # Handle both {key} and [key] formats
                prompt = prompt.replace(f'{{{key}}}', str(value))
                prompt = prompt.replace(f'[{key}]', str(value))
            
            messages.append({'role': 'user', 'content': prompt})
            
            # Execute LLM request
            result = llm_service.execute_llm_request(provider, model, messages)
            
            return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/run-llm')
def run_llm():
    """Execute LLM processing for planning steps."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        stage = data.get('stage', 'planning')
        substage = data.get('substage', 'idea')
        step = data.get('step', 'initial_concept')
        task = data.get('task', '')
        output_field = data.get('output_field', 'basic_idea')
        
        if not post_id or not task:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get step configuration
        with db_manager.get_cursor() as cursor:
            # Get system and task prompts for this step
            cursor.execute("""
                SELECT lp.system_prompt, lp.prompt_text
                FROM llm_prompt lp
                JOIN workflow_step_entity ws ON ws.name = lp.name
                JOIN workflow_sub_stage_entity ss ON ss.id = ws.sub_stage_id
                JOIN workflow_stage_entity s ON s.id = ss.stage_id
                WHERE s.name ILIKE %s AND ss.name ILIKE %s AND ws.name ILIKE %s
                ORDER BY lp.id DESC
                LIMIT 1
            """, (stage, substage, step.replace('_', ' ').title()))
            
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'No prompts found for this step'}), 404
            
            # Build messages
            messages = []
            if prompt_data['system_prompt']:
                messages.append({'role': 'system', 'content': prompt_data['system_prompt']})
            
            # Use task prompt or user input
            user_content = prompt_data['prompt_text'] if prompt_data['prompt_text'] else task
            messages.append({'role': 'user', 'content': user_content})
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.1:8b', messages)
            
            if 'error' in result:
                return jsonify({'error': result['error']}), 500
            
            # Save result to database
            cursor.execute("""
                INSERT INTO post_development (post_id, {})
                VALUES (%s, %s)
                ON CONFLICT (post_id) 
                DO UPDATE SET {} = %s, updated_at = NOW()
            """.format(output_field, output_field), 
            (post_id, result['content'], result['content']))
            
            return jsonify({
                'success': True,
                'result': result['content'],
                'output_field': output_field
            })
    
    except Exception as e:
        logger.error(f"Error running LLM: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/start-ollama')
def start_ollama():
    """Start Ollama service."""
    try:
        # Check if Ollama is already running
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Ollama is already running'})
        
        # Try to start Ollama (this would require system integration)
        return jsonify({'success': False, 'error': 'Ollama is not running. Please start it manually with "ollama serve"'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': 'Ollama is not running. Please start it manually with "ollama serve"'})


@misc_bp.route('/calendar-idea-create')
def api_calendar_idea_create():
    """Create a new calendar idea"""
    try:
        data = request.get_json()
        
        required_fields = ['idea_title', 'week_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_ideas 
                (week_number, idea_title, idea_description, seasonal_context, content_type, 
                 priority, tags, is_recurring, can_span_weeks, max_weeks, is_evergreen, evergreen_frequency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['week_number'],
                data['idea_title'],
                data.get('idea_description', ''),
                data.get('seasonal_context', ''),
                data.get('content_type', 'guide'),
                data.get('priority', 1),
                json.dumps(data.get('tags', [])),
                data.get('is_recurring', True),
                data.get('can_span_weeks', False),
                data.get('max_weeks', 1),
                data.get('is_evergreen', False),
                data.get('evergreen_frequency', 'low-frequency')
            ))
            
            idea_id = cursor.fetchone()['id']
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Calendar idea created successfully',
                'idea_id': idea_id
            })
            
    except Exception as e:
        logger.error(f"Error creating calendar idea: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-idea-update')
def api_calendar_idea_update(idea_id):
    """Update a calendar idea"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Check if idea exists
            cursor.execute("SELECT id FROM calendar_ideas WHERE id = %s", (idea_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Idea not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            allowed_fields = [
                'idea_title', 'idea_description', 'seasonal_context', 'content_type',
                'priority', 'week_number', 'is_recurring', 'can_span_weeks', 'max_weeks',
                'is_evergreen', 'evergreen_frequency', 'evergreen_notes', 'tags'
            ]
            
            for field in allowed_fields:
                if field in data:
                    if field == 'tags':
                        update_fields.append(f"{field} = %s")
                        values.append(json.dumps(data[field]))
                    else:
                        update_fields.append(f"{field} = %s")
                        values.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            update_fields.append("updated_at = NOW()")
            values.append(idea_id)
            
            query = f"UPDATE calendar_ideas SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Calendar idea updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating calendar idea: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-idea-delete')
def api_calendar_idea_delete(idea_id):
    """Delete a calendar idea"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if idea exists
            cursor.execute("SELECT id FROM calendar_ideas WHERE id = %s", (idea_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Idea not found'}), 404
            
            # Delete the idea (cascade will handle related records)
            cursor.execute("DELETE FROM calendar_ideas WHERE id = %s", (idea_id,))
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Calendar idea deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting calendar idea: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-event-create')
def api_calendar_event_create():
    """Create a new calendar event"""
    try:
        data = request.get_json()
        
        required_fields = ['event_title', 'start_date', 'end_date', 'year']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_events 
                (event_title, event_description, start_date, end_date, week_number, year,
                 content_type, priority, tags, is_recurring, can_span_weeks, max_weeks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['event_title'],
                data.get('event_description', ''),
                data['start_date'],
                data['end_date'],
                data.get('week_number'),
                data['year'],
                data.get('content_type', 'guide'),
                data.get('priority', 1),
                json.dumps(data.get('tags', [])),
                data.get('is_recurring', False),
                data.get('can_span_weeks', False),
                data.get('max_weeks', 1)
            ))
            
            event_id = cursor.fetchone()['id']
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Calendar event created successfully',
                'event_id': event_id
            })
            
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-event-update')
def api_calendar_event_update(event_id):
    """Update a calendar event"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Check if event exists
            cursor.execute("SELECT id FROM calendar_events WHERE id = %s", (event_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Event not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            allowed_fields = [
                'event_title', 'event_description', 'start_date', 'end_date',
                'week_number', 'year', 'content_type', 'priority', 'is_recurring',
                'can_span_weeks', 'max_weeks', 'tags'
            ]
            
            for field in allowed_fields:
                if field in data:
                    if field == 'tags':
                        update_fields.append(f"{field} = %s")
                        values.append(json.dumps(data[field]))
                    else:
                        update_fields.append(f"{field} = %s")
                        values.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            update_fields.append("updated_at = NOW()")
            values.append(event_id)
            
            query = f"UPDATE calendar_events SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Calendar event updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-event-delete')
def api_calendar_event_delete(event_id):
    """Delete a calendar event"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if event exists
            cursor.execute("SELECT id FROM calendar_events WHERE id = %s", (event_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Event not found'}), 404
            
            # Delete the event (cascade will handle related records)
            cursor.execute("DELETE FROM calendar_events WHERE id = %s", (event_id,))
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Calendar event deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-schedule-update')
def api_calendar_schedule_update(schedule_id):
    """Update a calendar schedule entry"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Check if schedule exists
            cursor.execute("SELECT id FROM calendar_schedule WHERE id = %s", (schedule_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Schedule entry not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            allowed_fields = [
                'year', 'week_number', 'idea_id', 'event_id', 'post_id',
                'status', 'priority', 'scheduled_date', 'notes', 'is_override', 'original_idea_id'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    values.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            update_fields.append("updated_at = NOW()")
            values.append(schedule_id)
            
            query = f"UPDATE calendar_schedule SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Schedule entry updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating schedule entry: {e}")
        return jsonify({'error': str(e)}), 500


@misc_bp.route('/calendar-schedule-delete')
def api_calendar_schedule_delete(schedule_id):
    """Delete a calendar schedule entry"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if schedule exists
            cursor.execute("SELECT id FROM calendar_schedule WHERE id = %s", (schedule_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Schedule entry not found'}), 404
            
            # Delete the schedule entry
            cursor.execute("DELETE FROM calendar_schedule WHERE id = %s", (schedule_id,))
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Schedule entry deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting schedule entry: {e}")
        return jsonify({'error': str(e)}), 500


