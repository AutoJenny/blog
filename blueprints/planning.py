"""
Planning Blueprint - Dedicated planning workspace
Handles Idea, Research, and Structure planning phases
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db_manager
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'name': 'OpenAI',
                'base_url': 'https://api.openai.com/v1',
                'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
            },
            'ollama': {
                'name': 'Ollama',
                'base_url': 'http://localhost:11434',
                'models': ['llama2', 'codellama', 'mistral']
            }
        }
    
    def get_available_models(self, provider='openai'):
        """Get available models for a provider."""
        try:
            if provider == 'ollama':
                response = requests.get(f"{self.providers[provider]['base_url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = [model['name'] for model in response.json().get('models', [])]
                    return models
            return self.providers.get(provider, {}).get('models', [])
        except Exception as e:
            logger.error(f"Error getting models for {provider}: {e}")
            return []
    
    def execute_llm_request(self, provider, model, messages, api_key=None):
        """Execute LLM request."""
        try:
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
            elif provider == 'ollama':
                data = {
                    'model': model,
                    'messages': messages,
                    'stream': False
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=60
                )
            else:
                return {'error': f'Unknown provider: {provider}'}
            
            if response.status_code == 200:
                result = response.json()
                if provider == 'openai':
                    return {'content': result['choices'][0]['message']['content']}
                elif provider == 'ollama':
                    return {'content': result['message']['content']}
            else:
                return {'error': f'API request failed: {response.status_code} - {response.text}'}
                
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return {'error': str(e)}

# Initialize LLM service
llm_service = LLMService()

@bp.route('/')
def planning_dashboard():
    """Main planning dashboard"""
    return render_template('planning/dashboard.html', blueprint_name='planning')

@bp.route('/posts/<int:post_id>')
def planning_post_overview(post_id):
    """Planning overview for a specific post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get planning progress
            cursor.execute("""
                SELECT stage_id, sub_stage_id, status, updated_at
                FROM post_workflow_stage 
                WHERE post_id = %s AND stage_id IN (
                    SELECT id FROM workflow_stage_entity WHERE name = 'planning'
                )
                ORDER BY stage_id, sub_stage_id
            """, (post_id,))
            progress = cursor.fetchall()
            
            return render_template('planning/post_overview.html', 
                                 post=post, progress=progress, blueprint_name='planning')
            
    except Exception as e:
        logger.error(f"Error in planning_post_overview: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/idea')
def planning_idea(post_id):
    """Idea planning phase"""
    return render_template('planning/idea.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/research')
def planning_research(post_id):
    """Research planning phase"""
    return render_template('planning/research.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/structure')
def planning_structure(post_id):
    """Structure planning phase"""
    return render_template('planning/structure.html', post_id=post_id, blueprint_name='planning')

# Content Calendar Stage
@bp.route('/posts/<int:post_id>/calendar')
def planning_calendar(post_id):
    """Content Calendar main stage"""
    return render_template('planning/calendar.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/view')
def planning_calendar_view(post_id):
    """Calendar View sub-stage"""
    return render_template('planning/calendar/view.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    return render_template('planning/calendar/ideas.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/gaps')
def planning_calendar_gaps(post_id):
    """Content Gaps sub-stage"""
    return render_template('planning/calendar/gaps.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/schedule')
def planning_calendar_schedule(post_id):
    """Schedule Management sub-stage"""
    return render_template('planning/calendar/schedule.html', post_id=post_id, blueprint_name='planning')

# Concept Development Stage
@bp.route('/posts/<int:post_id>/concept')
def planning_concept(post_id):
    """Concept Development main stage"""
    return render_template('planning/concept.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/proposal')
def planning_concept_proposal(post_id):
    """Basic Proposal sub-stage"""
    return render_template('planning/concept/proposal.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/brainstorm')
def planning_concept_brainstorm(post_id):
    """Topic Brainstorming sub-stage"""
    return render_template('planning/concept/brainstorm.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/sections')
def planning_concept_sections(post_id):
    """Section Planning sub-stage"""
    return render_template('planning/concept/sections.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/outline')
def planning_concept_outline(post_id):
    """Content Outline sub-stage"""
    return render_template('planning/concept/outline.html', post_id=post_id, blueprint_name='planning')

# Research & Resources Stage (updated)
@bp.route('/posts/<int:post_id>/research/sources')
def planning_research_sources(post_id):
    """Source Research sub-stage"""
    return render_template('planning/research/sources.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/research/visuals')
def planning_research_visuals(post_id):
    """Visual Planning sub-stage"""
    return render_template('planning/research/visuals.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/research/prompts')
def planning_research_prompts(post_id):
    """Image Prompts sub-stage"""
    return render_template('planning/research/prompts.html', post_id=post_id, blueprint_name='planning')

@bp.route('/posts/<int:post_id>/research/verification')
def planning_research_verification(post_id):
    """Fact Verification sub-stage"""
    return render_template('planning/research/verification.html', post_id=post_id, blueprint_name='planning')

# Old Interface access
@bp.route('/posts/<int:post_id>/old-interface')
def planning_old_interface(post_id):
    """Access to old workflow interface"""
    return render_template('planning/old_interface.html', post_id=post_id, blueprint_name='planning')

@bp.route('/api/posts')
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

@bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_data(post_id):
    """Get detailed post data for data tab."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.*, pd.*
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Convert to dict and separate post and development data
            data = dict(post_data)
            post_info = {k: v for k, v in data.items() if not k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions'))}
            development_info = {k: v for k, v in data.items() if k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions'))}
            
            return jsonify({
                **post_info,
                'development': development_info
            })
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/update-field', methods=['POST'])
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
        if table_type not in ['post', 'post_development']:
            return jsonify({'error': 'Invalid table_type. Must be "post" or "post_development"'}), 400
        
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

# ============================================================================
# CALENDAR API ENDPOINTS
# ============================================================================

@bp.route('/api/calendar/weeks/<int:year>', methods=['GET'])
def api_calendar_weeks(year):
    """Get all calendar weeks for a given year"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, week_number, start_date, end_date, month_name, is_current_week
                FROM calendar_weeks 
                WHERE year = %s 
                ORDER BY week_number
            """, (year,))
            
            weeks = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'weeks': weeks
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar weeks: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/ideas/<int:week_number>', methods=['GET'])
def api_calendar_ideas(week_number):
    """Get perpetual ideas for a specific week number"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ci.*, 
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'::json
                       ) as categories
                FROM calendar_ideas ci
                LEFT JOIN calendar_idea_categories cic ON ci.id = cic.idea_id
                LEFT JOIN calendar_categories cc ON cic.category_id = cc.id
                WHERE ci.week_number = %s
                GROUP BY ci.id
                ORDER BY ci.priority DESC, ci.idea_title
            """, (week_number,))
            
            ideas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'ideas': ideas
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar ideas: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/events/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_events(year, week_number):
    """Get events for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ce.*, 
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'::json
                       ) as categories
                FROM calendar_events ce
                LEFT JOIN calendar_event_categories cec ON ce.id = cec.event_id
                LEFT JOIN calendar_categories cc ON cec.category_id = cc.id
                WHERE ce.year = %s AND ce.week_number = %s
                GROUP BY ce.id
                ORDER BY ce.priority DESC, ce.event_title
            """, (year, week_number))
            
            events = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'week_number': week_number,
                'events': events
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/schedule/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_schedule(year, week_number):
    """Get scheduled items for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cs.*, 
                       ci.idea_title, ci.idea_description, ci.seasonal_context,
                       ce.event_title, ce.event_description,
                       p.title as post_title, p.status as post_status
                FROM calendar_schedule cs
                LEFT JOIN calendar_ideas ci ON cs.idea_id = ci.id
                LEFT JOIN calendar_events ce ON cs.event_id = ce.id
                LEFT JOIN post p ON cs.post_id = p.id
                WHERE cs.year = %s AND cs.week_number = %s
                ORDER BY cs.scheduled_date, cs.created_at
            """, (year, week_number))
            
            schedule = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'week_number': week_number,
                'schedule': schedule
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar schedule: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/schedule', methods=['POST'])
def api_calendar_schedule_create():
    """Create a new calendar schedule entry"""
    try:
        data = request.get_json()
        
        required_fields = ['year', 'week_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Must have either idea_id or event_id
        if not data.get('idea_id') and not data.get('event_id'):
            return jsonify({'error': 'Must provide either idea_id or event_id'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_schedule 
                (year, week_number, idea_id, event_id, post_id, status, scheduled_date, notes, is_override, original_idea_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['year'],
                data['week_number'],
                data.get('idea_id'),
                data.get('event_id'),
                data.get('post_id'),
                data.get('status', 'planned'),
                data.get('scheduled_date'),
                data.get('notes'),
                data.get('is_override', False),
                data.get('original_idea_id')
            ))
            
            schedule_id = cursor.fetchone()['id']
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Schedule entry created successfully',
                'schedule_id': schedule_id
            })
            
    except Exception as e:
        logger.error(f"Error creating calendar schedule: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/categories', methods=['GET'])
def api_calendar_categories():
    """Get all calendar categories"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, color, icon, is_active
                FROM calendar_categories 
                WHERE is_active = TRUE
                ORDER BY name
            """)
            
            categories = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'categories': categories
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar categories: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/evergreen/<int:week_number>', methods=['GET'])
def api_calendar_evergreen(week_number):
    """Get available evergreen content for a specific week"""
    try:
        year = request.args.get('year', 2025, type=int)
        frequency = request.args.get('frequency', None)
        
        with db_manager.get_cursor() as cursor:
            # Build query based on frequency
            where_clause = "ci.is_evergreen = TRUE"
            params = []
            
            if frequency:
                where_clause += " AND ci.evergreen_frequency = %s"
                params.append(frequency)
            
            # Get evergreen ideas with usage tracking
            cursor.execute(f"""
                SELECT ci.*, 
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'::json
                       ) as categories
                FROM calendar_ideas ci
                LEFT JOIN calendar_idea_categories cic ON ci.id = cic.idea_id
                LEFT JOIN calendar_categories cc ON cic.category_id = cc.id
                WHERE {where_clause}
                GROUP BY ci.id
                ORDER BY ci.usage_count ASC, ci.last_used_date ASC NULLS FIRST, ci.priority DESC
            """, params)
            
            ideas = cursor.fetchall()
            
            # Filter based on frequency rules (simplified for now)
            available_ideas = []
            for idea in ideas:
                # Simple availability check - can be enhanced later
                if idea['usage_count'] < 3:  # Allow up to 3 uses per year
                    available_ideas.append(idea)
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'year': year,
                'frequency': frequency,
                'ideas': available_ideas
            })
            
    except Exception as e:
        logger.error(f"Error fetching evergreen content: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/evergreen/usage-report', methods=['GET'])
def api_calendar_evergreen_usage_report():
    """Get evergreen content usage report"""
    try:
        year = request.args.get('year', 2025, type=int)
        
        with db_manager.get_cursor() as cursor:
            # Get frequency statistics
            cursor.execute("""
                SELECT 
                    evergreen_frequency,
                    COUNT(*) as total_ideas,
                    AVG(usage_count) as avg_usage,
                    MAX(usage_count) as max_usage,
                    COUNT(CASE WHEN usage_count > 0 THEN 1 END) as used_ideas
                FROM calendar_ideas 
                WHERE is_evergreen = TRUE
                GROUP BY evergreen_frequency
                ORDER BY evergreen_frequency
            """)
            
            frequency_stats = cursor.fetchall()
            
            # Get usage details
            cursor.execute("""
                SELECT 
                    ci.idea_title,
                    ci.evergreen_frequency,
                    ci.usage_count,
                    ci.last_used_date,
                    ci.week_number
                FROM calendar_ideas ci
                WHERE ci.is_evergreen = TRUE
                ORDER BY ci.usage_count DESC, ci.last_used_date DESC
            """)
            
            usage_details = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'frequency_stats': frequency_stats,
                'usage_details': usage_details
            })
            
    except Exception as e:
        logger.error(f"Error fetching evergreen usage report: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/progress')
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

# LLM Actions API endpoints
@bp.route('/api/step-config/<stage>/<substage>/<step>', methods=['GET'])
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

@bp.route('/api/llm/providers', methods=['GET'])
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

@bp.route('/api/llm/actions', methods=['GET'])
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

@bp.route('/api/llm/system-prompts', methods=['GET'])
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

@bp.route('/api/llm/actions/<int:action_id>/execute', methods=['POST'])
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

@bp.route('/api/run-llm', methods=['POST'])
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

@bp.route('/api/ollama/start', methods=['POST'])
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
