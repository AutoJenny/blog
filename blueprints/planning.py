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
    return render_template('planning/calendar.html', 
                         post_id=post_id, 
                         page_title='Content Calendar',
                         blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/view')
def planning_calendar_view(post_id):
    """Calendar View sub-stage"""
    return render_template('planning/calendar/view.html', 
                         post_id=post_id, 
                         page_title='Calendar View',
                         blueprint_name='planning')

@bp.route('/categories/manage')
def categories_manage():
    """Category management page"""
    return render_template('planning/categories/manage.html', blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    try:
        # Use the same week calculation as the calendar system
        from datetime import datetime
        current_date = datetime.now()
        week_number = current_date.isocalendar()[1]  # Use ISO week standard
        
        # Get week dates for display
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT start_date, end_date, month_name
                FROM calendar_weeks 
                WHERE year = %s AND week_number = %s
            """, (current_date.year, week_number))
            week_data = cursor.fetchone()
            
            if week_data:
                week_dates = f"{week_data['start_date'].strftime('%b %d')} - {week_data['end_date'].strftime('%b %d, %Y')}"
            else:
                week_dates = f"Week {week_number}, {current_date.year}"
        
        return render_template('planning/calendar/ideas.html', 
                             post_id=post_id, 
                             week_number=week_number,
                             week_dates=week_dates,
                             page_title='Idea Generation',
                             blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        # Fallback with basic week number
        from datetime import datetime
        current_date = datetime.now()
        week_number = current_date.isocalendar()[1]
        return render_template('planning/calendar/ideas.html', 
                             post_id=post_id, 
                             week_number=week_number,
                             week_dates=f"Week {week_number}, {current_date.year}",
                             page_title='Idea Generation',
                             blueprint_name='planning')


# Concept Development Stage
@bp.route('/posts/<int:post_id>/concept')
def planning_concept(post_id):
    """Concept Development main stage - redirects to Topic Brainstorming by default"""
    return redirect(url_for('planning.planning_concept_brainstorm', post_id=post_id))


@bp.route('/posts/<int:post_id>/concept/brainstorm')
def planning_concept_brainstorm(post_id):
    """Topic Brainstorming sub-stage"""
    return render_template('planning/concept/brainstorm.html', 
                         post_id=post_id, 
                         page_title='Topic Brainstorming',
                         blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/grouping')
def planning_concept_grouping(post_id):
    """Section Grouping sub-stage - groups topics into thematic clusters"""
    return render_template('planning/concept/grouping.html', 
                         post_id=post_id, 
                         page_title='Section Grouping',
                         blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/titling')
def planning_concept_titling(post_id):
    """Section Titling sub-stage - creates titles and descriptions for grouped sections"""
    return render_template('planning/concept/titling.html', 
                         post_id=post_id, 
                         page_title='Section Titling',
                         blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/sections')
def planning_concept_sections(post_id):
    """Section Planning sub-stage"""
    return render_template('planning/concept/sections.html', 
                         post_id=post_id, 
                         page_title='Section Planning',
                         blueprint_name='planning')

@bp.route('/posts/<int:post_id>/concept/outline')
def planning_concept_outline(post_id):
    """Content Outline sub-stage"""
    return render_template('planning/concept/outline.html', 
                         post_id=post_id, 
                         page_title='Content Outline',
                         blueprint_name='planning')

# TEMPORARY: Test route for Authoring template preview
@bp.route('/test-authoring/<int:post_id>')
def test_authoring_preview(post_id):
    """Temporary route to preview the Authoring template"""
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
            
            return render_template('authoring/sections/drafting.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Authoring Preview")
            
    except Exception as e:
        logger.error(f"Error in test_authoring_preview: {e}")
        return f"Error: {e}", 500

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
            post_info = {k: v for k, v in data.items() if not k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions'))}
            development_info = {k: v for k, v in data.items() if k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions'))}
            
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
                       p.title as post_title, p.status as post_status
                FROM calendar_schedule cs
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
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_schedule 
                (year, week_number, post_id, scheduled_date)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                data['year'],
                data['week_number'],
                data.get('post_id'),
                data.get('scheduled_date')
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

@bp.route('/api/calendar/categories', methods=['POST'])
def api_calendar_category_create():
    """Create a new calendar category"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'color']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_categories (name, description, color, icon, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['name'],
                data.get('description', ''),
                data['color'],
                data.get('icon', ''),
                data.get('is_active', True)
            ))
            
            category_id = cursor.fetchone()['id']
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Category created successfully',
                'category_id': category_id
            })
            
    except Exception as e:
        logger.error(f"Error creating calendar category: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/categories/<int:category_id>', methods=['PUT'])
def api_calendar_category_update(category_id):
    """Update a calendar category"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Check if category exists
            cursor.execute("SELECT id FROM calendar_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Category not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            allowed_fields = ['name', 'description', 'color', 'icon', 'is_active']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    values.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            values.append(category_id)
            query = f"UPDATE calendar_categories SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
            
            cursor.execute(query, values)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Category updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating calendar category: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/categories/<int:category_id>', methods=['DELETE'])
def api_calendar_category_delete(category_id):
    """Delete a calendar category"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if category exists
            cursor.execute("SELECT id FROM calendar_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Category not found'}), 404
            
            # Delete the category (cascade will handle related records)
            cursor.execute("DELETE FROM calendar_categories WHERE id = %s", (category_id,))
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Category deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting calendar category: {e}")
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

# ============================================================================
# CALENDAR EDITING API ENDPOINTS
# ============================================================================

@bp.route('/api/calendar/ideas', methods=['POST'])
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

@bp.route('/api/calendar/ideas/<int:idea_id>', methods=['PUT'])
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

@bp.route('/api/calendar/ideas/<int:idea_id>', methods=['DELETE'])
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

@bp.route('/api/calendar/events', methods=['POST'])
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

@bp.route('/api/calendar/events/<int:event_id>', methods=['PUT'])
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

@bp.route('/api/calendar/events/<int:event_id>', methods=['DELETE'])
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

@bp.route('/api/calendar/schedule/<int:schedule_id>', methods=['PUT'])
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

@bp.route('/api/calendar/schedule/<int:schedule_id>', methods=['DELETE'])
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

@bp.route('/api/calendar/ideas/week/<int:week_number>', methods=['GET'])
def api_calendar_ideas_for_week(week_number):
    """Get all calendar ideas for a specific week number"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, idea_title, idea_description, seasonal_context, 
                       content_type, priority, tags, is_recurring
                FROM calendar_ideas 
                WHERE week_number = %s
                ORDER BY 
                    CASE priority 
                        WHEN 'mandatory' THEN 1 
                        WHEN 'random' THEN 2 
                        ELSE 3 
                    END,
                    id
            """, (week_number,))
            
            ideas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'ideas': [dict(idea) for idea in ideas]
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar ideas for week {week_number}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/idea-seed', methods=['GET'])
def api_get_idea_seed(post_id):
    """Get the current idea seed for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT idea_seed 
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            idea_seed = result['idea_seed'] if result else None
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'idea_seed': idea_seed
            })
            
    except Exception as e:
        logger.error(f"Error fetching idea seed for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/idea-seed', methods=['POST'])
def api_update_idea_seed(post_id):
    """Update the idea seed for a post"""
    try:
        data = request.get_json()
        idea_seed = data.get('idea_seed', '')
        
        with db_manager.get_cursor() as cursor:
            # Check if post_development record exists
            cursor.execute("SELECT id FROM post_development WHERE post_id = %s", (post_id,))
            if not cursor.fetchone():
                # Create post_development record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, idea_seed)
                    VALUES (%s, %s)
                """, (post_id, idea_seed))
            else:
                # Update existing record
                cursor.execute("""
                    UPDATE post_development 
                    SET idea_seed = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s
                """, (idea_seed, post_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Idea seed updated successfully',
                'idea_seed': idea_seed
            })
            
    except Exception as e:
        logger.error(f"Error updating idea seed for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/idea-expansion', methods=['GET'])
def api_get_idea_expansion_prompt():
    """Get the LLM prompt used for idea expansion"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, system_prompt, prompt_text, description
                FROM llm_prompt 
                WHERE name = 'Scottish Idea Expansion'
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Idea expansion prompt not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'id': prompt_data['id'],
                    'name': prompt_data['name'],
                    'description': prompt_data['description'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text']
                },
                'llm_config': {
                    'provider': 'Ollama',
                    'model': 'llama3.2:latest',
                    'temperature': 0.7,
                    'max_tokens': 2000,
                    'timeout': 60
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching idea expansion prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/expanded-idea', methods=['GET'])
def api_get_expanded_idea(post_id):
    """Get the current expanded idea for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT expanded_idea 
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            expanded_idea = result['expanded_idea'] if result else None
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'expanded_idea': expanded_idea
            })
            
    except Exception as e:
        logger.error(f"Error fetching expanded idea for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/expanded-idea', methods=['POST'])
def api_generate_expanded_idea(post_id):
    """Generate expanded idea using LLM"""
    try:
        data = request.get_json()
        idea_seed = data.get('idea_seed', '')
        
        if not idea_seed:
            return jsonify({'error': 'Idea seed is required'}), 400
        
        # Get the LLM prompt
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, system_prompt, prompt_text
                FROM llm_prompt 
                WHERE name = 'Scottish Idea Expansion'
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Idea expansion prompt not found'}), 404
            
            # Build the prompt with the idea seed
            prompt_text = prompt_data['prompt_text']
            if '[data:idea_seed]' in prompt_text:
                prompt_text = prompt_text.replace('[data:idea_seed]', idea_seed)
            
            # Prepare messages for LLM
            messages = []
            if prompt_data['system_prompt']:
                messages.append({'role': 'system', 'content': prompt_data['system_prompt']})
            
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            expanded_idea = result['content']
            
            # Save to database
            cursor.execute("""
                UPDATE post_development 
                SET expanded_idea = %s, updated_at = CURRENT_TIMESTAMP
                WHERE post_id = %s
            """, (expanded_idea, post_id))
            
            if cursor.rowcount == 0:
                # Create post_development record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, expanded_idea)
                    VALUES (%s, %s)
                """, (post_id, expanded_idea))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Expanded idea generated successfully',
                'expanded_idea': expanded_idea
            })
            
    except Exception as e:
        logger.error(f"Error generating expanded idea for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/topic-brainstorming', methods=['GET'])
def api_get_topic_brainstorming_prompt():
    """Get the LLM prompt used for topic brainstorming"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, system_prompt, prompt_text, description
                FROM llm_prompt 
                WHERE name = 'Topic Brainstorming'
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Topic brainstorming prompt not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'id': prompt_data['id'],
                    'name': prompt_data['name'],
                    'description': prompt_data['description'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text']
                },
                'llm_config': {
                    'provider': 'Ollama',
                    'model': 'llama3.2:latest',
                    'temperature': 0.8,
                    'max_tokens': 3000,
                    'timeout': 90
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching topic brainstorming prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/topic-brainstorming', methods=['PUT'])
def api_update_topic_brainstorming_prompt():
    """Update the LLM prompt used for topic brainstorming"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        prompt_text = data.get('prompt_text', '')
        
        if not prompt_text:
            return jsonify({'error': 'Prompt text is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update the existing prompt
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = %s, prompt_text = %s, updated_at = CURRENT_TIMESTAMP
                WHERE name = 'Topic Brainstorming'
            """, (system_prompt, prompt_text))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Topic brainstorming prompt not found'}), 404
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Prompt updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating topic brainstorming prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/brainstorm/topics', methods=['POST'])
def api_generate_brainstorm_topics():
    """Generate brainstorming topics using LLM"""
    try:
        data = request.get_json()
        expanded_idea = data.get('expanded_idea', '')
        brainstorm_type = data.get('brainstorm_type', 'comprehensive')
        post_id = data.get('post_id')
        
        if not expanded_idea:
            return jsonify({'error': 'Expanded idea is required'}), 400
        
        # Get the LLM prompt
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, system_prompt, prompt_text
                FROM llm_prompt 
                WHERE name = 'Topic Brainstorming'
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Topic brainstorming prompt not found'}), 404
            
            # Build the prompt with the expanded idea
            prompt_text = prompt_data['prompt_text']
            if '[EXPANDED_IDEA]' in prompt_text:
                prompt_text = prompt_text.replace('[EXPANDED_IDEA]', expanded_idea)
            elif '[TOPIC]' in prompt_text:  # Fallback for old format
                prompt_text = prompt_text.replace('[TOPIC]', expanded_idea)
            
            # Add brainstorm type context
            type_context = {
                'comprehensive': 'Generate 50+ diverse topic ideas',
                'focused': 'Generate 20-30 focused topic ideas',
                'creative': 'Generate 20+ creative and unusual topic ideas',
                'practical': 'Generate 20+ practical how-to focused topic ideas'
            }
            
            prompt_text = f"{type_context.get(brainstorm_type, 'Generate diverse topic ideas')}.\n\n{prompt_text}"
            
            # Prepare messages for LLM
            messages = []
            if prompt_data['system_prompt']:
                messages.append({'role': 'system', 'content': prompt_data['system_prompt']})
            
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            # Parse the generated topics from the response
            topics = parse_brainstorm_topics(result['content'])
            
            return jsonify({
                'success': True,
                'message': 'Topics generated successfully',
                'topics': topics,
                'count': len(topics)
            })
            
    except Exception as e:
        logger.error(f"Error generating brainstorm topics: {e}")
        return jsonify({'error': str(e)}), 500

def parse_brainstorm_topics(content):
    """Enhanced topic parsing with validation and categorization"""
    topics = []
    
    # Step 1: Try JSON parsing (expected format)
    try:
        import json
        # Clean up the content to extract JSON
        content_clean = content.strip()
        
        # Find JSON array boundaries
        start_idx = content_clean.find('[')
        end_idx = content_clean.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content_clean[start_idx:end_idx + 1]
            topic_list = json.loads(json_str)
            
            if isinstance(topic_list, list):
                for topic_text in topic_list:
                    if isinstance(topic_text, str) and validate_topic(topic_text):
                        topics.append({
                            'title': topic_text.strip(),
                            'description': topic_text.strip(),
                            'category': categorize_topic(topic_text),
                            'word_count': len(topic_text.split())
                        })
                
                if topics:
                    logger.info(f"Successfully parsed {len(topics)} topics from JSON format")
                    return topics[:50]  # Limit to 50 topics
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"JSON parsing failed: {e}, falling back to text parsing")
        pass  # Fall back to text parsing
    
    # Fallback: Parse as text format (numbered, bulleted, or short lines)
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this looks like a topic (numbered, bulleted, or short line)
        if (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.', '16.', '17.', '18.', '19.', '20.', '21.', '22.', '23.', '24.', '25.', '26.', '27.', '28.', '29.', '30.', '31.', '32.', '33.', '34.', '35.', '36.', '37.', '38.', '39.', '40.', '41.', '42.', '43.', '44.', '45.', '46.', '47.', '48.', '49.', '50.')) or 
            line.startswith(('-', '*', '•')) or
            (len(line) < 100 and not line.endswith('.') and not line.startswith('SERIOUS') and not line.startswith('BALANCED') and not line.startswith('QUIRKY') and not line.startswith('Format') and not line.startswith('Ensure'))):
            
            # Clean up the line and add as topic
            clean_line = line.lstrip('1234567890.-*• ').strip()
            if clean_line and validate_topic(clean_line):
                topics.append({
                    'title': clean_line,
                    'description': clean_line,  # Same as title since it's a short summary
                    'category': categorize_topic(clean_line),
                    'word_count': len(clean_line.split())
                })
    
    # If no structured topics found, try to split by lines that look like topics
    if not topics:
        for line in lines:
            line = line.strip()
            if line and validate_topic(line):
                topics.append({
                    'title': line,
                    'description': line,
                    'category': categorize_topic(line),
                    'word_count': len(line.split())
                })
    
    return topics[:50]  # Limit to 50 topics

def validate_topic(topic):
    """Validate individual topic for length and content"""
    if not topic or not isinstance(topic, str):
        return False
    
    words = topic.strip().split()
    # Check word count (5-8 words)
    if not (5 <= len(words) <= 8):
        return False
    
    # Check minimum length
    if len(topic.strip()) < 10:
        return False
    
    # Check for common invalid patterns
    invalid_patterns = ['SERIOUS', 'BALANCED', 'QUIRKY', 'Format', 'Ensure', 'Generate', 'Here are', 'The following']
    topic_lower = topic.lower()
    if any(pattern.lower() in topic_lower for pattern in invalid_patterns):
        return False
    
    return True

def categorize_topic(topic):
    """Categorize topic by content type"""
    topic_lower = topic.lower()
    
    # Historical topics
    if any(word in topic_lower for word in ['history', 'ancient', 'traditional', 'heritage', 'origins', 'centuries', 'medieval', 'celtic']):
        return 'historical'
    
    # Cultural topics
    elif any(word in topic_lower for word in ['culture', 'festival', 'celebration', 'custom', 'tradition', 'folklore', 'mythology', 'legend']):
        return 'cultural'
    
    # Practical topics
    elif any(word in topic_lower for word in ['how', 'guide', 'tips', 'practical', 'step', 'method', 'technique', 'recipe']):
        return 'practical'
    
    # Contemporary topics
    elif any(word in topic_lower for word in ['modern', 'contemporary', 'today', 'current', 'now', 'present', 'recent', 'today\'s']):
        return 'contemporary'
    
    # Default category
    else:
        return 'general'

@bp.route('/api/posts/<int:post_id>/idea-scope', methods=['GET'])
def api_get_idea_scope(post_id):
    """Get the IDEA_SCOPE field from post_development"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT idea_scope 
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            idea_scope_raw = result['idea_scope'] if result else None
            
            # Parse the JSON string if it exists
            idea_scope = None
            if idea_scope_raw:
                try:
                    idea_scope = json.loads(idea_scope_raw)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse idea_scope JSON for post {post_id}")
                    idea_scope = None
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'idea_scope': idea_scope
            })
            
    except Exception as e:
        logger.error(f"Error fetching idea scope for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/idea-scope', methods=['POST'])
def api_update_idea_scope(post_id):
    """Update the IDEA_SCOPE field in post_development with generated topics"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        
        if not topics:
            return jsonify({'error': 'No topics provided'}), 400
        
        # Format topics as JSON for storage
        import json
        idea_scope_json = json.dumps({
            'generated_topics': topics,
            'generated_at': datetime.now().isoformat(),
            'total_count': len(topics)
        }, indent=2)
        
        with db_manager.get_cursor() as cursor:
            # Check if post_development record exists
            cursor.execute("SELECT id FROM post_development WHERE post_id = %s", (post_id,))
            if not cursor.fetchone():
                # Create post_development record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, idea_scope)
                    VALUES (%s, %s)
                """, (post_id, idea_scope_json))
            else:
                # Update existing record
                cursor.execute("""
                    UPDATE post_development 
                    SET idea_scope = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s
                """, (idea_scope_json, post_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Idea scope updated successfully',
                'topics_saved': len(topics)
            })
            
    except Exception as e:
        logger.error(f"Error updating idea scope for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/section-planning', methods=['GET'])
def api_get_section_planning_prompt():
    """Get the Section Planning prompt and LLM configuration"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get the section planning prompt
            cursor.execute("""
                SELECT id, name, prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Section Planning'
                ORDER BY id DESC
                LIMIT 1
            """)
            prompt = cursor.fetchone()
            
            if not prompt:
                return jsonify({
                    'success': False,
                    'error': 'Section Planning prompt not found'
                }), 404
            
            # Get LLM configuration
            llm_config = {
                'provider': 'Ollama',
                'model': 'llama3.2:latest',
                'temperature': 0.7,
                'max_tokens': 2000,
                'timeout': 60
            }
            
            return jsonify({
                'success': True,
                'prompt': dict(prompt),
                'llm_config': llm_config
            })
            
    except Exception as e:
        logger.error(f"Error getting section planning prompt: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/llm/prompts/section-titling', methods=['GET'])
def api_get_section_titling_prompt():
    """Get the Section Titling prompt and LLM configuration"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get the section titling prompt
            cursor.execute("""
                SELECT id, name, prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Section Titling'
                ORDER BY id DESC
                LIMIT 1
            """)
            prompt = cursor.fetchone()
            
            if not prompt:
                return jsonify({
                    'success': False,
                    'error': 'Section Titling prompt not found'
                }), 404
            
            # Get LLM configuration
            llm_config = {
                'provider': 'Ollama',
                'model': 'llama3.2:latest',
                'temperature': 0.8,  # Slightly higher for more creative titles
                'max_tokens': 2000,
                'timeout': 60
            }
            
            return jsonify({
                'success': True,
                'prompt': dict(prompt),
                'llm_config': llm_config
            })
            
    except Exception as e:
        logger.error(f"Error getting section titling prompt: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/sections/design-structure', methods=['POST'])
def api_design_section_structure():
    """Step 1: Design 7-section blog structure"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        if not topics:
            return jsonify({
                'success': False,
                'error': 'No topics provided'
            }), 400
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        # Get expanded idea if not provided
        if not expanded_idea:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT expanded_idea 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result and result['expanded_idea']:
                    expanded_idea = result['expanded_idea']
        
        # Format topics for prompt
        topics_text = '\n'.join([f"- {topic.get('title', topic) if isinstance(topic, dict) else topic}" for topic in topics])
        
        # Create structure design prompt
        structure_prompt = f"""Design a 7-section blog structure for: {expanded_idea}

TOPICS TO ENCOMPASS ({len(topics)} topics):
{topics_text}

REQUIREMENTS:
- Create exactly 7 sections that together cover all topics
- Each section should have clear thematic boundaries
- Sections should flow logically from ancient to modern
- Each section should be engaging for Scottish heritage audience
- Specify what each section includes and excludes
- Ensure comprehensive coverage without overlap

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "sections": [
    {{
      "id": "section_1",
      "theme": "Clear thematic focus",
      "boundaries": "What this section covers",
      "exclusions": "What this section does NOT cover",
      "order": 1,
      "description": "Engaging description for readers"
    }}
  ],
  "metadata": {{
    "total_sections": 7,
    "design_principles": "How sections relate to each other",
    "audience_focus": "Target audience description"
  }}
}}"""
        
        # Execute LLM request
        messages = [
            {'role': 'system', 'content': 'You are a Scottish heritage content specialist and blog structure designer. Your expertise lies in creating engaging, logical blog structures that comprehensively cover Scottish cultural topics while maintaining reader engagement.'},
            {'role': 'user', 'content': structure_prompt}
        ]
        
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        logger.info(f"LLM result: {result}")
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': f'LLM generation failed: {result["error"]}'
            }), 500
        
        # Parse the response
        try:
            import json
            import re
            
            # Remove markdown code blocks if present
            content = result['content'].strip()
            
            # Handle various markdown code block formats
            if content.startswith('```json'):
                # Remove ```json and trailing ```
                content = content[7:].strip()
                if content.endswith('```'):
                    content = content[:-3].strip()
            elif content.startswith('```') and content.endswith('```'):
                # Remove ``` and ```
                content = content[3:-3].strip()
            
            # Clean up common JSON issues
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)  # Remove control characters
            content = content.replace('\n', ' ').replace('\r', ' ')  # Replace newlines with spaces
            
            logger.info(f"Cleaned content: {content[:200]}...")
            
            structure_data = json.loads(content)
            
            # Validate the structure
            if not validate_section_structure(structure_data):
                return jsonify({
                    'success': False,
                    'error': 'Invalid section structure format'
                }), 400
            
            # Save to database
            save_section_structure(post_id, structure_data)
            
            return jsonify({
                'success': True,
                'message': 'Section structure designed successfully',
                'section_structure': structure_data
            })
            
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'Failed to parse LLM response: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in api_design_section_structure: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def validate_section_structure(structure_data):
    """Validate section structure format"""
    try:
        if not isinstance(structure_data, dict):
            return False
        
        sections = structure_data.get('sections', [])
        if len(sections) != 7:
            return False
        
        for section in sections:
            required_fields = ['id', 'theme', 'boundaries', 'exclusions', 'order', 'description']
            if not all(field in section for field in required_fields):
                return False
        
        return True
    except:
        return False

def save_section_structure(post_id, structure_data):
    """Save section structure design to database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET section_structure = %s, structure_design_at = NOW()
                WHERE post_id = %s
            """, (json.dumps(structure_data), post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, section_structure, structure_design_at, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW(), NOW())
                """, (post_id, json.dumps(structure_data)))
            
            cursor.connection.commit()
    except Exception as e:
        logger.error(f"Error saving section structure: {e}")
        raise

@bp.route('/api/sections/design-structure/<int:post_id>', methods=['GET'])
def api_get_section_structure(post_id):
    """Get section structure design for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT section_structure, structure_design_at
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if not result or not result['section_structure']:
                return jsonify({
                    'success': False,
                    'error': 'Section structure not found'
                }), 404
            
            # Handle both JSON string and dict formats
            if isinstance(result['section_structure'], str):
                structure_data = json.loads(result['section_structure'])
            else:
                structure_data = result['section_structure']
            
            return jsonify({
                'success': True,
                'section_structure': structure_data,
                'design_at': result['structure_design_at']
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_section_structure: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/sections/allocate-topics', methods=['POST'])
def api_allocate_topics():
    """Step 2: Allocate topics to sections"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        section_structure = data.get('section_structure', {})
        post_id = data.get('post_id')
        
        if not topics:
            return jsonify({
                'success': False,
                'error': 'No topics provided'
            }), 400
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        # Get section structure if not provided
        if not section_structure:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT section_structure 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result and result['section_structure']:
                    if isinstance(result['section_structure'], str):
                        section_structure = json.loads(result['section_structure'])
                    else:
                        section_structure = result['section_structure']
        
        if not section_structure or not section_structure.get('sections'):
            return jsonify({
                'success': False,
                'error': 'Section structure not found. Please complete Step 1 first.'
            }), 400
        
        # Format section structure for prompt with unique codes
        sections_text = ""
        section_codes = {}
        for section in section_structure['sections']:
            section_code = f"S{section['order']:02d}"
            section_codes[section_code] = section['theme']
            sections_text += f"\n{section_code}: {section['theme']}\n"
            sections_text += f"  Boundaries: {section['boundaries']}\n"
            sections_text += f"  Exclusions: {section['exclusions']}\n"
        
        # Format topics for prompt with explicit numbering
        topics_text = '\n'.join([f"{i+1}. {topic.get('title', topic) if isinstance(topic, dict) else topic}" for i, topic in enumerate(topics)])
        
        # Create allocation prompt
        allocation_prompt = f"""TASK: Allocate {len(topics)} topics to sections. Return each topic in the SAME ORDER as provided (1-{len(topics)}), with section code in curly braces.

SECTION STRUCTURE:
{sections_text}

TOPICS TO ALLOCATE (process these in numbered order 1-{len(topics)}):
{topics_text}

REQUIRED OUTPUT FORMAT - return exactly {len(topics)} lines like this:
Celtic Roots of Samhain Traditions {{S01}}
Crop Rotation Practices in Ancient Scotland {{S02}}
Hogmanay Traditions in Modern Scotland {{S07}}

CRITICAL RULES:
1. Return EXACTLY {len(topics)} lines
2. Keep topics in the SAME ORDER as numbered above (1-{len(topics)})
3. Each line format: Topic Title {{S01}}
4. Use section codes S01, S02, S03, S04, S05, S06, S07
5. NO JSON format, NO quotes, NO commas
6. Each topic appears exactly once
7. Process topics in order: 1, 2, 3, 4, 5... up to {len(topics)}

DO NOT return JSON format. Return simple text lines only."""
        
        # Execute LLM request
        messages = [
            {'role': 'system', 'content': 'You are a Scottish heritage content specialist and topic allocation expert. Your expertise lies in matching topics to appropriate sections based on thematic boundaries and ensuring comprehensive coverage without overlap. You MUST follow instructions exactly and return ONLY the requested text format without any additional text, explanations, or JSON.'},
            {'role': 'user', 'content': allocation_prompt}
        ]
        
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        logger.info(f"LLM allocation result: {result}")
        
        if 'error' in result:
            logger.error(f"LLM error details: {result}")
            return jsonify({
                'success': False,
                'error': f'LLM generation failed: {result["error"]}',
                'llm_response': str(result),
                'debug_info': {
                    'prompt_length': len(allocation_prompt),
                    'topics_count': len(topics),
                    'sections_count': len(section_structure.get('sections', [])),
                    'llm_service_result': result
                }
            }), 500
        
        # Parse the response
        try:
            content = result['content'].strip()
            logger.info(f"Raw LLM response: {content}")
            
            # Check if response is empty
            if not content:
                logger.error("LLM returned empty response")
                return jsonify({
                    'success': False,
                    'error': 'LLM returned empty response. Please try again.',
                    'llm_response': content
                }), 400
            
            # Debug: Log the first few lines of the response
            lines = content.split('\n')
            logger.info(f"First 5 lines of LLM response:")
            for i, line in enumerate(lines[:5]):
                logger.info(f"  Line {i+1}: '{line}'")
            
            # Parse the new format: Topic Title {S01}
            allocations = {}
            lines = content.split('\n')
            
            # Filter out empty lines and invalid lines
            valid_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Parse format: Topic Title {S01}
                if '{' in line and '}' in line:
                    # Extract section code from curly braces
                    start_brace = line.rfind('{')
                    end_brace = line.rfind('}')
                    
                    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                        section_code = line[start_brace + 1:end_brace].strip()
                        topic_title = line[:start_brace].strip()
                        
                        # Strip numbered prefixes (e.g., "1. Topic Title" -> "Topic Title")
                        if topic_title and topic_title[0].isdigit() and '. ' in topic_title:
                            topic_title = topic_title.split('. ', 1)[1]
                        
                        # Validate section code format
                        if section_code.startswith('S') and len(section_code) == 3:
                            try:
                                section_num = int(section_code[1:])
                                if 1 <= section_num <= 7:  # Valid section range
                                    if topic_title:  # Must have a topic title
                                        valid_lines.append((section_code, topic_title))
                            except ValueError:
                                continue
            
            # Check if we have the right number of allocations
            if len(valid_lines) != len(topics):
                logger.error(f"Expected {len(topics)} allocations, got {len(valid_lines)}")
                logger.error(f"Valid lines: {valid_lines}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid allocation count: expected {len(topics)}, got {len(valid_lines)}',
                    'llm_response': content
                }), 400
            
            # Convert to allocation format
            for section_code, topic_title in valid_lines:
                if section_code not in allocations:
                    allocations[section_code] = []
                allocations[section_code].append(topic_title)
            
            # Convert to expected format
            allocation_data = {
                'allocations': [],
                'metadata': {
                    'total_topics_allocated': len(topics),
                    'unallocated_topics': [],
                    'allocation_method': 'section_code_matching'
                }
            }
            
            for section_code, topic_list in allocations.items():
                section_order = int(section_code[1:])  # Extract number from S01, S02, etc.
                allocation_data['allocations'].append({
                    'section_id': f'section_{section_order}',
                    'section_theme': section_codes.get(section_code, f"Unknown Section {section_code}"),
                    'topics': topic_list,
                    'allocation_reason': f'Topics allocated to {section_codes.get(section_code, f"Unknown Section {section_code}")} based on thematic fit'
                })
            
            logger.info(f"Parsed allocation data: {allocation_data}")
            
            # Validate the allocation
            logger.info(f"Allocation data to validate: {allocation_data}")
            logger.info(f"Original topics: {topics}")
            
            validation_result = validate_topic_allocation(allocation_data, topics)
            logger.info(f"Validation result: {validation_result}")
            logger.info(f"Allocation data keys: {list(allocation_data.keys())}")
            logger.info(f"Allocations count: {len(allocation_data.get('allocations', []))}")
            if not validation_result:
                logger.error(f"Validation failed for allocation: {allocation_data}")
                logger.error(f"Valid lines found: {len(valid_lines)}")
                logger.error(f"Sample valid lines: {valid_lines[:3]}")
                
                # Get missing topics for automatic retry
                allocated_topics = []
                for allocation in allocation_data.get('allocations', []):
                    allocated_topics.extend(allocation.get('topics', []))
                original_titles = [topic.get('title', topic) if isinstance(topic, dict) else topic for topic in topics]
                missing_topics = set(original_titles) - set(allocated_topics)
                
                logger.info(f"Attempting automatic retry for {len(missing_topics)} missing topics: {list(missing_topics)}")
                
                # Automatic retry for missing topics
                try:
                    retry_result = allocate_missing_topics(list(missing_topics), section_structure, post_id)
                    if retry_result['success']:
                        # Merge the retry results with existing allocation
                        merged_allocation = merge_allocations(allocation_data, retry_result['allocations'])
                        
                        # Validate the merged result
                        if validate_topic_allocation(merged_allocation, topics):
                            logger.info(f"Automatic retry successful! All {len(original_titles)} topics now allocated.")
                            
                            # Save merged allocation to database
                            save_topic_allocation(post_id, merged_allocation)
                            
                            return jsonify({
                                'success': True,
                                'message': f'Topics allocated successfully (with automatic retry for {len(missing_topics)} missing topics)',
                                'allocations': merged_allocation
                            })
                        else:
                            logger.error("Merged allocation still failed validation")
                    else:
                        logger.error(f"Automatic retry failed: {retry_result.get('error', 'Unknown error')}")
                except Exception as retry_error:
                    logger.error(f"Automatic retry exception: {retry_error}")
                
                # If automatic retry fails, return the original error
                return jsonify({
                    'success': False,
                    'error': f'Invalid allocation count: expected {len(original_titles)}, got {len(set(allocated_topics))}. Missing topics: {list(missing_topics)}',
                    'llm_response': content,
                    'debug_info': {
                        'total_lines': len(lines),
                        'valid_lines': len(valid_lines),
                        'sample_valid_lines': valid_lines[:3],
                        'sample_raw_lines': lines[:3],
                        'allocation_data': allocation_data,
                        'missing_topics': list(missing_topics)
                    }
                }), 400
            
            # Save to database
            save_topic_allocation(post_id, allocation_data)
            
            return jsonify({
                'success': True,
                'message': 'Topics allocated successfully',
                'allocations': allocation_data
            })
            
        except Exception as e:
            logger.error(f"Error in topic allocation: {e}")
            return jsonify({
                'success': False,
                'error': f'Topic allocation failed: {str(e)}',
                'llm_response': content if 'content' in locals() else 'No response'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in api_allocate_topics: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'debug_info': {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'topics_count': len(topics) if 'topics' in locals() else 'unknown',
                'post_id': post_id if 'post_id' in locals() else 'unknown'
            }
        }), 500

def allocate_missing_topics(missing_topics, section_structure, post_id):
    """Allocate missing topics using LLM with simplified prompt"""
    try:
        # Create section codes mapping
        section_codes = {}
        for i, section in enumerate(section_structure.get('sections', []), 1):
            section_codes[f'S{i:02d}'] = section.get('theme', f'Section {i}')
        
        # Simplified prompt for missing topics only
        prompt = f"""You are a Scottish heritage content specialist. Allocate these {len(missing_topics)} missing topics to the most appropriate sections.

SECTION STRUCTURE:
{chr(10).join([f"S{i:02d}: {section.get('theme', f'Section {i}')} - {section.get('boundaries', 'No boundaries specified')}" for i, section in enumerate(section_structure.get('sections', []), 1)])}

MISSING TOPICS TO ALLOCATE:
{chr(10).join([f"{i+1}. {topic}" for i, topic in enumerate(missing_topics)])}

CRITICAL REQUIREMENTS:
- Return EXACTLY {len(missing_topics)} lines
- Use format: Topic Title {{SXX}}
- Use section codes: {', '.join(section_codes.keys())}
- Allocate each topic to its BEST FIT section
- Do NOT skip any topics

OUTPUT FORMAT:
Topic Title {{S01}}
Topic Title {{S02}}
..."""

        logger.info(f"Retry prompt for {len(missing_topics)} missing topics")
        
        # Use the same LLM service as the main function
        messages = [
            {'role': 'system', 'content': "You are a Scottish heritage content specialist and topic allocation expert. You MUST follow instructions exactly and return ONLY the requested format without any additional text."},
            {'role': 'user', 'content': prompt}
        ]
        
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if not result or not result.get('content'):
            return {'success': False, 'error': 'LLM returned empty response for retry'}
        
        # Parse the retry response
        content = result['content'].strip()
        lines = content.split('\n')
        
        retry_allocations = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse format: Topic Title {S01}
            if '{' in line and '}' in line:
                topic_part = line[:line.rfind('{')].strip()
                section_part = line[line.rfind('{')+1:line.rfind('}')].strip()
                
                if section_part in section_codes:
                    if section_part not in retry_allocations:
                        retry_allocations[section_part] = []
                    retry_allocations[section_part].append(topic_part)
        
        # Convert to allocation format
        allocation_data = {
            'allocations': [],
            'total_topics': len(missing_topics),
            'allocated_topics': sum(len(topics) for topics in retry_allocations.values()),
            'style': 'retry',
            'generated_at': datetime.now().isoformat()
        }
        
        for section_code, topics in retry_allocations.items():
            section_order = int(section_code[1:])  # Extract number from S01, S02, etc.
            allocation_data['allocations'].append({
                'section_id': f'section_{section_order}',
                'section_theme': section_codes[section_code],
                'topics': topics,
                'allocation_reason': f'Missing topics allocated to {section_codes[section_code]} via automatic retry'
            })
        
        logger.info(f"Retry allocation successful: {allocation_data}")
        return {'success': True, 'allocations': allocation_data}
        
    except Exception as e:
        logger.error(f"Error in allocate_missing_topics: {e}")
        return {'success': False, 'error': str(e)}

def merge_allocations(original_allocation, retry_allocation):
    """Merge original allocation with retry allocation"""
    try:
        merged = original_allocation.copy()
        
        # Create a map of section_id to allocation for easy lookup
        section_map = {}
        for allocation in merged['allocations']:
            section_map[allocation['section_id']] = allocation
        
        # Add retry topics to existing sections
        for retry_alloc in retry_allocation['allocations']:
            section_id = retry_alloc['section_id']
            if section_id in section_map:
                # Add topics to existing section
                section_map[section_id]['topics'].extend(retry_alloc['topics'])
            else:
                # Add new section
                merged['allocations'].append(retry_alloc)
        
        # Update totals
        merged['total_topics'] = sum(len(alloc['topics']) for alloc in merged['allocations'])
        merged['allocated_topics'] = merged['total_topics']
        merged['style'] = 'merged'
        
        logger.info(f"Merged allocation: {merged}")
        return merged
        
    except Exception as e:
        logger.error(f"Error merging allocations: {e}")
        return original_allocation

def validate_topic_allocation(allocation_data, original_topics):
    """Validate topic allocation format"""
    try:
        if not isinstance(allocation_data, dict):
            logger.error("Allocation data is not a dict")
            return False
        
        allocations = allocation_data.get('allocations', [])
        if not allocations:
            logger.error("No allocations found in data")
            return False
        
        # Check that all topics are allocated
        allocated_topics = []
        for allocation in allocations:
            if not isinstance(allocation, dict):
                logger.error(f"Allocation is not a dict: {allocation}")
                return False
            required_fields = ['section_id', 'section_theme', 'topics', 'allocation_reason']
            if not all(field in allocation for field in required_fields):
                logger.error(f"Missing required fields in allocation: {allocation}")
                return False
            allocated_topics.extend(allocation.get('topics', []))
        
        # Verify all original topics are allocated
        original_titles = [topic.get('title', topic) if isinstance(topic, dict) else topic for topic in original_topics]
        
        # Check that we have the right number of topics
        if len(set(allocated_topics)) != len(original_titles):
            logger.error(f"Topic count mismatch: allocated={len(set(allocated_topics))}, original={len(original_titles)}")
            logger.error(f"Allocated topics: {set(allocated_topics)}")
            logger.error(f"Original topics: {original_titles}")
            
            # Find missing topics
            allocated_set = set(allocated_topics)
            original_set = set(original_titles)
            missing_topics = original_set - allocated_set
            logger.error(f"Missing topics: {missing_topics}")
            return False
        
        # Check that all original topics are present in allocated topics
        allocated_set = set(allocated_topics)
        original_set = set(original_titles)
        if allocated_set != original_set:
            logger.error(f"Topic mismatch: allocated={allocated_set}, original={original_set}")
            return False
        
        return True
    except:
        return False

def save_topic_allocation(post_id, allocation_data):
    """Save topic allocation to database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET topic_allocation = %s, allocation_completed_at = NOW()
                WHERE post_id = %s
            """, (json.dumps(allocation_data), post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, topic_allocation, allocation_completed_at, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW(), NOW())
                """, (post_id, json.dumps(allocation_data)))
            
            cursor.connection.commit()
    except Exception as e:
        logger.error(f"Error saving topic allocation: {e}")
        raise

@bp.route('/api/sections/allocate-topics/<int:post_id>', methods=['GET'])
def api_get_topic_allocation(post_id):
    """Get topic allocation for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic_allocation, allocation_completed_at
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if not result or not result['topic_allocation']:
                return jsonify({
                    'success': False,
                    'error': 'Topic allocation not found'
                }), 404
            
            # Handle both JSON string and dict formats
            if isinstance(result['topic_allocation'], str):
                allocation_data = json.loads(result['topic_allocation'])
            else:
                allocation_data = result['topic_allocation']
            
            return jsonify({
                'success': True,
                'allocations': allocation_data,
                'completed_at': result['allocation_completed_at']
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_topic_allocation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/sections/refine-topics', methods=['POST'])
def api_refine_topics():
    """Step 3: Refine topics per section (optional)"""
    try:
        data = request.get_json()
        allocations = data.get('allocations', {})
        section_structure = data.get('section_structure', {})
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        # Get allocations if not provided
        if not allocations:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT topic_allocation 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result and result['topic_allocation']:
                    if isinstance(result['topic_allocation'], str):
                        allocations = json.loads(result['topic_allocation'])
                    else:
                        allocations = result['topic_allocation']
        
        if not allocations or not allocations.get('allocations'):
            return jsonify({
                'success': False,
                'error': 'Topic allocation not found. Please complete Step 2 first.'
            }), 400
        
        # Get section structure if not provided
        if not section_structure:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT section_structure 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result and result['section_structure']:
                    if isinstance(result['section_structure'], str):
                        section_structure = json.loads(result['section_structure'])
                    else:
                        section_structure = result['section_structure']
        
        # Identify sections with too many topics (>5)
        sections_to_refine = []
        for allocation in allocations['allocations']:
            topic_count = len(allocation.get('topics', []))
            if topic_count > 5:
                sections_to_refine.append({
                    'allocation': allocation,
                    'topic_count': topic_count
                })
        
        if not sections_to_refine:
            return jsonify({
                'success': True,
                'message': 'No sections need refinement (all sections have ≤5 topics)',
                'refined_sections': allocations['allocations']
            })
        
        # Refine each overloaded section
        refined_sections = []
        for section_info in sections_to_refine:
            allocation = section_info['allocation']
            section_id = allocation['section_id']
            
            # Get section context from structure
            section_context = ""
            section_order = int(section_id.replace('section_', ''))
            if section_structure and section_structure.get('sections'):
                for section in section_structure['sections']:
                    if section.get('order') == section_order:
                        section_context = f"Theme: {section.get('theme', 'Unknown')}\nBoundaries: {section.get('boundaries', 'No boundaries specified')}\nExclusions: {section.get('exclusions', 'No exclusions specified')}"
                        break
            
            # Create refinement prompt for this section
            topics_list = '\n'.join([f"- {topic}" for topic in allocation['topics']])
            
            refinement_prompt = f"""You are a Scottish heritage content specialist. Rewrite and compile topics for this section to create 5-6 comprehensive, engaging topics.

SECTION CONTEXT:
{section_context}

CURRENT TOPICS ({len(allocation['topics'])} topics - TOO MANY):
{topics_list}

CRITICAL REQUIREMENTS:
- Create EXACTLY 5-6 NEW topics (not just selecting from existing ones)
- COMPILE similar topics into comprehensive, engaging topics
- REWRITE topics to be more engaging and specific
- Ensure each new topic covers multiple aspects from the original list
- Maintain thematic coherence with section boundaries
- Make topics more specific and engaging for readers
- Avoid generic or repetitive topics

OUTPUT FORMAT:
Return exactly 5-6 lines, each with a new, comprehensive topic title:
New Comprehensive Topic Title 1
New Comprehensive Topic Title 2
New Comprehensive Topic Title 3
New Comprehensive Topic Title 4
New Comprehensive Topic Title 5
New Comprehensive Topic Title 6

EXAMPLE TRANSFORMATION:
Instead of: "Scottish Turnips as Medicine", "Scottish Turnips as Magic", "Scottish Turnips as Symbol"
Create: "The Sacred Turnip: Medicine, Magic, and Symbolism in Scottish Folk Traditions"

OUTPUT FORMAT: Return ONLY the topic titles, one per line:
New Comprehensive Topic Title 1
New Comprehensive Topic Title 2
New Comprehensive Topic Title 3
New Comprehensive Topic Title 4
New Comprehensive Topic Title 5
New Comprehensive Topic Title 6"""
            
            # Execute LLM for this section
            messages = [
                {'role': 'system', 'content': 'You are a Scottish heritage content specialist and topic refinement expert. Your expertise lies in selecting the most engaging and representative topics for blog sections while maintaining thematic coherence and reader engagement.'},
                {'role': 'user', 'content': refinement_prompt}
            ]
            
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM refinement failed for {section_id}: {result['error']}")
                # Keep original topics if refinement fails
                refined_sections.append({
                    'section_id': section_id,
                    'final_topics': allocation['topics'],
                    'refinement_notes': 'Refinement failed, keeping original topics',
                    'excluded_topics': [],
                    'refinement_criteria': 'Error fallback'
                })
                continue
            
            # Parse the refinement response
            try:
                content = result['content'].strip()
                lines = content.split('\n')
                
                # Filter out empty lines and extract topic titles
                refined_topics = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        refined_topics.append(line)
                
                # Ensure we have 5-6 topics
                if len(refined_topics) < 5 or len(refined_topics) > 6:
                    logger.warning(f"Refinement returned {len(refined_topics)} topics, expected 5-6")
                
                refined_sections.append({
                    'section_id': section_id,
                    'final_topics': refined_topics[:6],  # Limit to 6 max
                    'refinement_notes': f'Compiled {len(allocation["topics"])} original topics into {len(refined_topics)} comprehensive topics',
                    'original_topic_count': len(allocation['topics']),
                    'refined_topic_count': len(refined_topics)
                })
                
            except Exception as e:
                logger.error(f"Failed to parse refinement response for {section_id}: {e}")
                # Keep original topics if parsing fails
                refined_sections.append({
                    'section_id': section_id,
                    'final_topics': allocation['topics'],
                    'refinement_notes': 'Parsing failed, keeping original topics',
                    'original_topic_count': len(allocation['topics']),
                    'refined_topic_count': len(allocation['topics'])
                })
        
        # Create final refined allocations
        final_allocations = []
        for original_allocation in allocations['allocations']:
            section_id = original_allocation['section_id']
            
            # Check if this section was refined
            refined_section = None
            for refined in refined_sections:
                if refined['section_id'] == section_id:
                    refined_section = refined
                    break
            
            if refined_section:
                # Use refined topics
                final_allocation = original_allocation.copy()
                final_allocation['topics'] = refined_section['final_topics']
                final_allocation['refinement_notes'] = refined_section.get('refinement_notes', '')
                final_allocation['excluded_topics'] = refined_section.get('excluded_topics', [])
                final_allocations.append(final_allocation)
            else:
                # Keep original topics
                final_allocations.append(original_allocation)
        
        # Create refined data structure
        refined_data = {
            'allocations': final_allocations,
            'refined_sections': refined_sections,
            'metadata': {
                'total_sections_refined': len(sections_to_refine),
                'refinement_completed_at': 'now',
                'original_topic_count': sum(len(a.get('topics', [])) for a in allocations['allocations']),
                'refined_topic_count': sum(len(a.get('topics', [])) for a in final_allocations)
            }
        }
        
        # Save refined results
        save_refined_topics(post_id, refined_data)
        
        return jsonify({
            'success': True,
            'message': f'Refined {len(sections_to_refine)} overloaded sections',
            'refined_data': refined_data
        })
        
    except Exception as e:
        logger.error(f"Error in api_refine_topics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def save_refined_topics(post_id, refined_data):
    """Save refined topics to database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET refined_topics = %s, refinement_completed_at = NOW()
                WHERE post_id = %s
            """, (json.dumps(refined_data), post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, refined_topics, refinement_completed_at, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW(), NOW())
                """, (post_id, json.dumps(refined_data)))
            
            cursor.connection.commit()
    except Exception as e:
        logger.error(f"Error saving refined topics: {e}")
        raise

@bp.route('/api/sections/refine-topics/<int:post_id>', methods=['GET'])
def api_get_refined_topics(post_id):
    """Get refined topics for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT refined_topics, refinement_completed_at
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if not result or not result['refined_topics']:
                return jsonify({
                    'success': False,
                    'error': 'Refined topics not found'
                }), 404
            
            # Handle both JSON string and dict formats
            if isinstance(result['refined_topics'], str):
                refined_data = json.loads(result['refined_topics'])
            else:
                refined_data = result['refined_topics']
            
            return jsonify({
                'success': True,
                'refined_data': refined_data,
                'completed_at': result['refinement_completed_at']
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_refined_topics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/sections/group', methods=['POST'])
def api_sections_group():
    """Stage 1: Group topics into thematic clusters"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        group_count = data.get('group_count', 6)
        post_id = data.get('post_id')
        
        if not topics:
            return jsonify({
                'success': False,
                'error': 'No topics provided'
            }), 400
        
        # Get the expanded idea for context
        expanded_idea = ""
        if post_id:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT expanded_idea 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result and result['expanded_idea']:
                    expanded_idea = result['expanded_idea']
        
        # Create grouping prompt
        topics_text = '\n'.join([f"- {topic['title']}" for topic in topics])
        
        grouping_prompt = f"""Given these topics about {expanded_idea}, group them into exactly {group_count} thematic clusters.

TOPICS TO GROUP:
{topics_text}

REQUIREMENTS:
- Create exactly {group_count} groups
- Each topic must be in exactly one group
- Groups should be thematically related
- Balance group sizes as much as possible
+- For each group, include a concise thematic explanation (1-2 sentences) describing the unifying idea and how the topics fit together

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "groups": [
    {{
      "id": "group_1",
      "theme": "Brief theme description",
      "explanation": "1-2 sentence thematic explanation in neutral terms",
      "topics": ["Topic 1", "Topic 2", ...],
      "order": 1
    }}
  ],
  "metadata": {{
    "total_groups": {group_count},
    "total_topics": {len(topics)},
    "allocated_topics": {len(topics)}
  }}
}}"""
        
        # Call LLM
        messages = [
            {'role': 'system', 'content': 'You are an expert content organizer specializing in thematic grouping of topics.'},
            {'role': 'user', 'content': grouping_prompt}
        ]
        
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            return jsonify({
                'success': False,
                'error': f"LLM generation failed: {llm_response['error']}"
            }), 500
        
        # Parse response
        try:
            import json
            content = llm_response['content'].strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                # Find the JSON part between code blocks
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip() == '```' and not in_json:
                        in_json = True
                        continue
                    elif line.strip() == '```' and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                content = '\n'.join(json_lines)
            
            groups_data = json.loads(content)
            logger.info(f"Successfully parsed LLM response for grouping")
        except json.JSONDecodeError as e:
            logger.warning(f"LLM JSON parsing failed: {e}")
            logger.warning(f"LLM response content: {llm_response['content'][:500]}...")
            # Fallback: create simple groups
            groups_data = create_fallback_groups(topics, group_count)
        
        return jsonify({
            'success': True,
            'groups': groups_data
        })
        
    except Exception as e:
        logger.error(f"Error grouping topics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/sections/title', methods=['POST'])
def api_sections_title():
    """Stage 2: Create titles and descriptions for grouped sections"""
    try:
        data = request.get_json()
        groups = data.get('groups', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        if not groups:
            return jsonify({
                'success': False,
                'error': 'No groups provided'
            }), 400
        
        # Use hardcoded Section Titling prompt for now (to avoid database issue)
        logger.info("Using hardcoded Section Titling prompt")
        system_prompt = """You are a Scottish heritage content specialist and engaging blog writer. Your expertise lies in creating compelling, authentic titles and descriptions that resonate with audiences interested in Scottish culture, history, and traditions.

EXPERTISE:
- Scottish heritage and cultural authenticity
- Engaging title creation for heritage audiences
- Compelling descriptions that capture Scottish essence
- Historical accuracy and cultural sensitivity
- Reader engagement through evocative language

CRITICAL REQUIREMENTS:
- Create titles that evoke Scottish heritage and cultural pride
- Use authentic Scottish terminology and references where appropriate
- Ensure descriptions capture the essence and importance of each section
- Make content accessible to both Scottish and international audiences
- Focus on engagement, authenticity, and cultural significance"""
        
        # Prepare groups data for the prompt
        logger.info("Preparing groups data for prompt")
        groups_data = {
            "groups": groups,
            "metadata": {
                "total_groups": len(groups),
                "total_topics": sum(len(group.get('topics', [])) for group in groups)
            }
        }
        
        # Create the titling prompt
        logger.info("Creating titling prompt")
        groups_text = ""
        for group in groups:
            topics_list = '\n  '.join(group.get('topics', []))
            groups_text += f"\nGroup {group.get('order', 1)}: {group.get('theme', 'Untitled')}\n  {topics_list}\n"
        
        titling_prompt = f"""You are tasked with creating engaging titles and snappy subtitles for these existing thematic groups about {expanded_idea}. DO NOT reorganize, reorder, or change the topics - just add creative titles and subtitles.

EXISTING GROUPS TO TITLE (PRESERVE EXACTLY AS IS):
{groups_text}

CRITICAL REQUIREMENTS:
- Keep the EXACT same group structure, topics, and order
- Only add creative titles and snappy subtitles
- Do NOT reorganize or reallocate topics
- Do NOT change the group themes or explanations
- Do NOT modify the topic lists

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "sections": [
    {{
      "id": "group_1",
      "title": "Engaging Scottish Heritage Title",
      "subtitle": "Snappy subtitle - no fluff like 'This section delves into'",
      "description": "Brief description of what this section covers",
      "topics": ["EXACT SAME TOPICS AS INPUT"],
      "order": 1,
      "cultural_significance": "Why this theme matters to Scottish heritage"
    }}
  ],
  "metadata": {{
    "total_sections": {len(groups)},
    "total_topics": {sum(len(group.get('topics', [])) for group in groups)},
    "allocated_topics": {sum(len(group.get('topics', [])) for group in groups)},
    "audience_focus": "Scottish heritage enthusiasts and cultural readers"
  }}
}}

TITLE GUIDELINES:
- Use evocative language that captures Scottish spirit
- Include cultural references where appropriate (e.g., "Celtic", "Highland", "Ancient Scottish")
- Make titles accessible to international audiences
- Avoid overly academic or dry language
- Focus on emotional connection and cultural pride

SUBTITLE GUIDELINES:
- Keep subtitles snappy and direct
- NO fluff phrases like "This section delves into", "Join us as we explore", "Discover the fascinating", "Delving into", "Unveiling", "Exploring", "Unlocking"
- NO action verbs that add no meaning: "Discover", "Explore", "Unveil", "Delve", "Unlock", "Reveal"
- Start with concrete nouns or direct statements about the content
- Maximum 6-8 words
- Focus on WHAT the content covers, not HOW to approach it
- Examples of GOOD subtitles: "Celtic festivals and harvest traditions", "Medieval crops and farming practices"
- Examples of BAD subtitles: "Delving into the mysteries of", "Unveiling Scotland's ancient secrets", "Exploring the rich history of"

DESCRIPTION GUIDELINES:
- Brief, direct description of what readers will learn
- Highlight the cultural and historical significance
- Use engaging, accessible language
- Keep under 2 sentences"""
        
        logger.info(f"Prompt prepared, length: {len(titling_prompt)}")
        
        # Call LLM
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': titling_prompt}
        ]
        
        logger.info(f"Calling LLM for titling with {len(groups)} groups")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        logger.info(f"LLM response: {llm_response}")
        
        if 'error' in llm_response:
            return jsonify({
                'success': False,
                'error': f"LLM generation failed: {llm_response['error']}"
            }), 500
        
        # Parse response
        try:
            import json
            content = llm_response['content'].strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                # Find the JSON part between code blocks
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```') and not in_json:
                        in_json = True
                        continue
                    elif line.strip() == '```' and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                content = '\n'.join(json_lines)
            
            # Remove any text before the JSON (like "Here is the JSON output:")
            if '{' in content:
                json_start = content.find('{')
                content = content[json_start:]
            
            sections_data = json.loads(content)
            # Sanitize subtitles/descriptions and enforce constraints
            sections_data = sanitize_sections_text(sections_data)
            logger.info(f"Successfully parsed LLM response for titling")
        except json.JSONDecodeError as e:
            logger.warning(f"LLM JSON parsing failed: {e}")
            logger.warning(f"LLM response content: {llm_response['content'][:500]}...")
            # Fallback: create simple sections
            sections_data = create_fallback_sections_from_groups(groups)
        
        return jsonify({
            'success': True,
            'sections': sections_data
        })
        
    except Exception as e:
        logger.error(f"Error creating section titles: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_fallback_groups(topics, group_count):
    """Create simple fallback groups when LLM fails"""
    topic_titles = [topic['title'] for topic in topics]
    
    # Distribute topics evenly
    topics_per_group = len(topics) // group_count
    remainder = len(topics) % group_count
    
    groups = []
    topic_index = 0
    
    for i in range(group_count):
        group_topic_count = topics_per_group + (1 if i < remainder else 0)
        group_topics = topic_titles[topic_index:topic_index + group_topic_count]
        topic_index += group_topic_count
        
        groups.append({
            'id': f'group_{i+1}',
            'theme': f'Thematic Group {i+1}',
            'explanation': 'Topics grouped by broad thematic similarity for coherent coverage.',
            'topics': group_topics,
            'order': i + 1
        })
    
    return {
        'groups': groups,
        'metadata': {
            'total_groups': len(groups),
            'total_topics': len(topics),
            'allocated_topics': len(topics)
        }
    }

def create_fallback_sections_from_groups(groups):
    """Create simple fallback sections from groups"""
    sections = []
    
    for group in groups:
        sections.append({
            'id': group.get('id', f'section_{group.get("order", 1)}'),
            'title': f"Section {group.get('order', 1)}: {group.get('theme', 'Untitled')}",
            'description': f"This section covers topics related to {group.get('theme', 'the main theme').lower()}.",
            'boundaries': "Focus on the specific topics listed, avoiding overlap with other sections.",
            'topics': group.get('topics', []),
            'order': group.get('order', 1)
        })
    
    return {
        'sections': sections,
        'metadata': {
            'total_sections': len(sections),
            'total_topics': sum(len(section['topics']) for section in sections),
            'flow_type': 'logical'
        }
    }

# -----------------------------
# Sanitization helpers
# -----------------------------
def _clean_subtitle(text: str) -> str:
    if not text:
        return text
    banned_starts = [
        'delving into', 'exploring', 'unveiling', 'unlocking', 'discovering', 'discover',
        'explore', 'unveil', 'delve', 'unlock', 'reveal', 'revealing', 'learn about',
        'join us as we explore', 'here we explore', 'this section', 'in this section'
    ]
    t = text.strip()
    tl = t.lower()
    for phrase in banned_starts:
        if tl.startswith(phrase):
            t = t[len(phrase):].lstrip(' :,-')
            tl = t.lower()
            break
    words = t.split()
    max_words = 8
    if len(words) > max_words:
        t = ' '.join(words[:max_words])
    return t.strip(' .')

def _clean_description(text: str) -> str:
    if not text:
        return text
    banned_openers = [
        'this section', 'in this section', 'we will', 'join us',
        'discover how', 'explore how', 'delve into', 'unveil', 'unlock',
        # Third-person fluff verbs
        'explores', 'examines', 'investigates', 'delves', 'highlights', 'showcases', 'reveals', 'uncovers'
    ]
    t = text.strip()
    tl = t.lower()
    changed = True
    # Iteratively strip any leading banned phrases
    while changed:
        changed = False
        tl = t.lower()
        for phrase in banned_openers:
            if tl.startswith(phrase):
                t = t[len(phrase):].lstrip(' :,-')
                changed = True
                break
    return t.strip()

def sanitize_sections_text(sections_payload: dict) -> dict:
    """Sanitize subtitles/descriptions in sections payload returned by LLM or before saving.
    Expects a dict with key 'sections' which is a list.
    """
    try:
        sections_list = sections_payload.get('sections', [])
        cleaned = []
        for section in sections_list:
            sec = dict(section)
            if 'subtitle' in sec:
                sec['subtitle'] = _clean_subtitle(sec.get('subtitle') or '')
            if 'description' in sec:
                sec['description'] = _clean_description(sec.get('description') or '')
            cleaned.append(sec)
        sections_payload['sections'] = cleaned
        return sections_payload
    except Exception as e:
        logger.warning(f"sanitize_sections_text failed: {e}")
        return sections_payload

@bp.route('/api/posts/<int:post_id>/groups', methods=['GET'])
def api_get_groups(post_id):
    """Get the groups from post_development"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT groups 
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            groups_raw = result['groups'] if result else None
            
            # Parse the JSON string if it exists
            groups = None
            if groups_raw:
                try:
                    groups = json.loads(groups_raw)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse groups JSON for post {post_id}")
                    groups = None
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'groups': groups
            })
            
    except Exception as e:
        logger.error(f"Error fetching groups for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/groups', methods=['POST'])
def api_save_groups(post_id):
    """Save generated groups to post_development table"""
    try:
        data = request.get_json()
        groups_data = data.get('groups', {})
        
        if not groups_data:
            return jsonify({
                'success': False,
                'error': 'No groups data provided'
            }), 400
        
        # Convert to JSON string for database storage
        groups_json = json.dumps(groups_data)
        
        with db_manager.get_cursor() as cursor:
            # Save groups to post_development table
            cursor.execute("""
                UPDATE post_development 
                SET groups = %s, updated_at = NOW()
                WHERE post_id = %s
            """, (groups_json, post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, groups, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (post_id, groups_json))
        
            # Commit the transaction
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Groups saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving groups: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/sections/plan', methods=['POST'])
def api_sections_plan():
    """Generate sections from topics using LLM"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        section_count = data.get('section_count', 4)
        section_style = data.get('section_style', 'thematic')
        post_id = data.get('post_id')
        
        if not topics:
            return jsonify({
                'success': False,
                'error': 'No topics provided'
            }), 400
        
        # Get the section planning prompt
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Section Planning'
                ORDER BY id DESC
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': 'Section Planning prompt not found'
                }), 404
        
        # Get the expanded idea for context
        expanded_idea = ""
        if post_id:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT expanded_idea 
                    FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result and result['expanded_idea']:
                    expanded_idea = result['expanded_idea']
        
        # Prepare the prompt with topics and expanded idea
        topics_text = '\n'.join([f"- {topic['title']}" for topic in topics])
        
        prompt_text = prompt_data['prompt_text'].replace('[EXPANDED_IDEA]', expanded_idea)
        prompt_text = prompt_text.replace('[TOPICS]', topics_text)
        prompt_text = prompt_text.replace('[SECTION_COUNT]', str(section_count))
        prompt_text = prompt_text.replace('[SECTION_STYLE]', section_style)
        prompt_text = prompt_text.replace('[TOTAL_TOPICS]', str(len(topics)))
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        prompt_text = prompt_text.replace('[TIMESTAMP]', timestamp)
        
        # Call LLM
        messages = []
        if prompt_data['system_prompt']:
            messages.append({'role': 'system', 'content': prompt_data['system_prompt']})
        messages.append({'role': 'user', 'content': prompt_text})
        
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            return jsonify({
                'success': False,
                'error': f"LLM generation failed: {llm_response['error']}"
            }), 500
        
        # Parse the response to extract sections
        sections_data = parse_sections_response(llm_response['content'])
        
        # Validate the response
        validation_errors = validate_sections_response(sections_data, topics, section_count)
        logger.info(f"Validation errors: {validation_errors}")
        
        if validation_errors:
            # Try auto-correction first
            corrections = auto_correct_sections(sections_data, topics)
            if corrections:
                logger.info(f"Applied auto-corrections: {corrections}")
                # Re-validate after corrections
                validation_errors = validate_sections_response(sections_data, topics, section_count)
                logger.info(f"Validation errors after correction: {validation_errors}")
            
            # If still failing, create fallback allocation
            if validation_errors:
                logger.info("LLM validation failed even after auto-correction, creating fallback allocation")
                
                # Adjust section count based on topic count
                actual_section_count = min(section_count, max(3, len(topics) // 2 + 1))
                
                # Create simple sections with topics distributed evenly
                sections_data = create_fallback_sections(topics, actual_section_count, section_style, timestamp)
        
        return jsonify({
            'success': True,
            'sections': sections_data
        })
        
    except Exception as e:
        logger.error(f"Error generating sections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/sections', methods=['POST'])
def api_save_sections(post_id):
    """Save generated sections to post_development table"""
    try:
        data = request.get_json()
        sections_data = data.get('sections', {})
        
        if not sections_data or 'sections' not in sections_data:
            return jsonify({
                'success': False,
                'error': 'No sections data provided'
            }), 400
        
        sections = sections_data['sections']
        section_headings = sections_data.get('section_headings', [])
        metadata = sections_data.get('metadata', {})
        
        # Sanitize before saving
        try:
            sections_data = sanitize_sections_text(sections_data)
        except Exception as _e:
            logger.warning(f"Sanitization failed, proceeding without changes: {_e}")

        # Convert to JSON strings for database storage
        sections_json = json.dumps(sections_data)
        headings_json = json.dumps(section_headings)
        
        # Create section order array
        section_order = [section.get('id', f"section_{i+1}") for i, section in enumerate(sections)]
        order_json = json.dumps(section_order)
        
        with db_manager.get_cursor() as cursor:
            # Save sections to post_development table
            cursor.execute("""
                UPDATE post_development 
                SET sections = %s, section_headings = %s, section_order = %s, updated_at = NOW()
                WHERE post_id = %s
            """, (sections_json, headings_json, order_json, post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, sections, section_headings, section_order, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (post_id, sections_json, headings_json, order_json))
            
            # Commit the transaction
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sections saved successfully',
            'metadata': metadata
        })
        
    except Exception as e:
        logger.error(f"Error saving sections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/sections', methods=['GET'])
def api_get_sections(post_id):
    """Get saved sections for a post from post_development."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT sections
                FROM post_development
                WHERE post_id = %s
                """,
                (post_id,)
            )
            row = cursor.fetchone()
            if not row or not row['sections']:
                return jsonify({'success': True, 'sections': {}})

            stored = row['sections']
            try:
                if isinstance(stored, str):
                    sections = json.loads(stored)
                else:
                    sections = stored
            except Exception:
                sections = {}

            return jsonify({'success': True, 'sections': sections})
    except Exception as e:
        logger.error(f"Error fetching sections for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_sections_response(response_text):
    """Parse LLM response to extract sections"""
    # Try to parse JSON first (new format)
    try:
        import json
        parsed = json.loads(response_text)
        if isinstance(parsed, dict) and 'sections' in parsed:
            return parsed
        elif isinstance(parsed, list):
            # Convert old format to new format
            return {
                'section_headings': [section.get('title', '') for section in parsed],
                'sections': parsed,
                'metadata': {
                    'total_sections': len(parsed),
                    'total_topics': sum(len(section.get('topics', [])) for section in parsed),
                    'allocated_topics': sum(len(section.get('topics', [])) for section in parsed),
                    'style': 'thematic',
                    'generated_at': datetime.now().isoformat()
                }
            }
    except json.JSONDecodeError:
        pass
    
    # Parse text format (fallback)
    sections = []
    lines = response_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section header (e.g., "Section 1:", "## Section 1:", etc.)
        if line.startswith(('Section ', '## Section ', '### Section ')):
            if current_section:
                sections.append(current_section)
            
            # Extract section title
            title = line.replace('Section ', '').replace('## ', '').replace('### ', '')
            title = title.split(':')[0].strip()
            
            current_section = {
                'id': f"section_{len(sections) + 1}",
                'title': title,
                'description': '',
                'topics': [],
                'order': len(sections) + 1
            }
        
        # Check for description
        elif current_section and not current_section['description'] and not line.startswith('-'):
            current_section['description'] = line
        
        # Check for topics (lines starting with - or *)
        elif current_section and (line.startswith('- ') or line.startswith('* ')):
            topic = line[2:].strip()
            if topic:
                current_section['topics'].append(topic)
    
    # Add the last section
    if current_section:
        sections.append(current_section)
    
    # Convert to new format
    return {
        'section_headings': [section['title'] for section in sections],
        'sections': sections,
        'metadata': {
            'total_sections': len(sections),
            'total_topics': sum(len(section['topics']) for section in sections),
            'allocated_topics': sum(len(section['topics']) for section in sections),
            'style': 'thematic',
            'generated_at': datetime.now().isoformat()
        }
    }

def validate_sections_response(sections_data, original_topics, expected_section_count):
    """Enhanced validation with progressive levels"""
    errors = []
    
    # Level 1: Structure validation
    structure_errors = validate_structure(sections_data)
    if structure_errors:
        return structure_errors
    
    # Level 2: Count validation
    count_errors = validate_counts(sections_data, expected_section_count, len(original_topics))
    if count_errors:
        errors.extend(count_errors)
    
    # Level 3: Allocation validation
    allocation_errors = validate_allocation(sections_data, original_topics)
    if allocation_errors:
        errors.extend(allocation_errors)
    
    # Level 4: Quality validation
    quality_errors = validate_quality(sections_data)
    if quality_errors:
        errors.extend(quality_errors)
    
    return errors

def validate_structure(sections_data):
    """Level 1: Basic structure validation"""
    errors = []
    if not isinstance(sections_data, dict):
        errors.append("Response must be a JSON object")
    if 'sections' not in sections_data:
        errors.append("Response must contain 'sections' array")
    return errors

def validate_counts(sections_data, expected_count, total_topics):
    """Level 2: Count validation with flexibility"""
    errors = []
    sections = sections_data.get('sections', [])
    
    # Flexible section count (6-8 range)
    if not (6 <= len(sections) <= 8):
        errors.append(f"Must have 6-8 sections, got {len(sections)}")
    
    # Check topic allocation
    allocated_count = sum(len(section.get('topics', [])) for section in sections)
    if allocated_count != total_topics:
        errors.append(f"Topic count mismatch: {allocated_count} allocated vs {total_topics} original")
    
    return errors

def validate_allocation(sections_data, original_topics):
    """Level 3: Topic allocation validation with fuzzy matching"""
    errors = []
    sections = sections_data.get('sections', [])
    original_titles = [topic['title'] for topic in original_topics]
    allocated_topics = []
    
    for section in sections:
        for topic in section.get('topics', []):
            allocated_topics.append(topic)
    
    # Check for unallocated topics (with fuzzy matching)
    unallocated = []
    for original in original_titles:
        if not any(fuzzy_match(original, allocated) for allocated in allocated_topics):
            unallocated.append(original)
    
    if unallocated:
        errors.append(f"Unallocated topics: {', '.join(unallocated[:5])}{'...' if len(unallocated) > 5 else ''}")
    
    # Check for duplicates
    if len(set(allocated_topics)) != len(allocated_topics):
        duplicates = [topic for topic in allocated_topics if allocated_topics.count(topic) > 1]
        errors.append(f"Duplicate topics found: {', '.join(set(duplicates))}")
    
    return errors

def validate_quality(sections_data):
    """Level 4: Quality validation"""
    errors = []
    sections = sections_data.get('sections', [])
    
    for i, section in enumerate(sections):
        if not section.get('title') or len(section.get('title', '')) < 10:
            errors.append(f"Section {i+1} has inadequate title")
        if not section.get('description') or len(section.get('description', '')) < 20:
            errors.append(f"Section {i+1} has inadequate description")
        if len(section.get('topics', [])) < 3:
            errors.append(f"Section {i+1} has too few topics")
    
    return errors

def fuzzy_match(str1, str2, threshold=0.8):
    """Fuzzy string matching for topic validation"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() >= threshold

def auto_correct_sections(sections_data, original_topics):
    """Auto-correct minor issues in section data"""
    corrections = []
    
    sections = sections_data.get('sections', [])
    original_titles = [topic['title'] for topic in original_topics]
    
    # Fix empty sections
    for section in sections:
        if not section.get('topics'):
            # Find nearby topics to allocate
            nearby_topics = find_nearby_topics(section, original_topics)
            section['topics'] = nearby_topics
            corrections.append(f"Added {len(nearby_topics)} topics to empty section")
    
    # Fix duplicate topics
    all_topics = []
    for section in sections:
        unique_topics = []
        for topic in section.get('topics', []):
            if topic not in all_topics:
                unique_topics.append(topic)
                all_topics.append(topic)
        section['topics'] = unique_topics
    
    # Fix inadequate titles
    for section in sections:
        if not section.get('title') or len(section.get('title', '')) < 10:
            section['title'] = generate_section_title(section.get('topics', []))
            corrections.append("Generated section title")
    
    # Fix inadequate descriptions
    for section in sections:
        if not section.get('description') or len(section.get('description', '')) < 20:
            section['description'] = generate_section_description(section.get('topics', []))
            corrections.append("Generated section description")
    
    return corrections

def find_nearby_topics(section, original_topics):
    """Find topics that could fit in an empty section"""
    # Simple heuristic: return first few unallocated topics
    return [topic['title'] for topic in original_topics[:3]]

def generate_section_title(topics):
    """Generate a meaningful section title from topics"""
    if not topics:
        return "Untitled Section"
    
    # Extract common words from topics
    common_words = []
    for topic in topics[:3]:  # Use first 3 topics
        words = topic.lower().split()
        common_words.extend(words)
    
    # Find most common words
    from collections import Counter
    word_counts = Counter(common_words)
    common_terms = [word for word, count in word_counts.most_common(3) if count > 1]
    
    if common_terms:
        return f"Exploring {', '.join(common_terms).title()}"
    else:
        return f"Section: {topics[0][:30]}..."

def generate_section_description(topics):
    """Generate a meaningful section description from topics"""
    if not topics:
        return "This section covers various related topics."
    
    topic_count = len(topics)
    if topic_count == 1:
        return f"This section explores {topics[0].lower()}."
    elif topic_count <= 3:
        return f"This section covers {topic_count} related topics including {topics[0].lower()}."
    else:
        return f"This section explores {topic_count} interconnected topics and themes."

def create_fallback_sections(topics, section_count, section_style, timestamp):
    """Create a simple fallback section allocation when LLM fails"""
    topic_titles = [topic['title'] for topic in topics]
    
    # Distribute topics evenly across sections
    topics_per_section = len(topics) // section_count
    remainder = len(topics) % section_count
    
    sections = []
    topic_index = 0
    
    for i in range(section_count):
        # Calculate how many topics this section gets
        section_topic_count = topics_per_section + (1 if i < remainder else 0)
        
        # Get topics for this section
        section_topics = topic_titles[topic_index:topic_index + section_topic_count]
        topic_index += section_topic_count
        
        # Create section
        section = {
            'id': f'section_{i+1}',
            'title': f'Section {i+1}',
            'description': f'Topics related to {section_style} theme',
            'topics': section_topics,
            'order': i + 1
        }
        sections.append(section)
    
    return {
        'section_headings': [section['title'] for section in sections],
        'sections': sections,
        'metadata': {
            'total_sections': len(sections),
            'total_topics': len(topics),
            'allocated_topics': len(topics),
            'style': section_style,
            'generated_at': timestamp,
            'fallback': True
        }
    }
    
    sections = sections_data['sections']
    
    # Check section count
    if not (6 <= len(sections) <= 8):
        errors.append(f"Must have 6-8 sections, got {len(sections)}")
    
    # Check expected section count
    if len(sections) != expected_section_count:
        errors.append(f"Expected {expected_section_count} sections, got {len(sections)}")
    
    # Check all topics allocated
    allocated_topics = []
    original_topic_titles = [topic['title'] for topic in original_topics]
    
    for section in sections:
        if 'topics' not in section:
            errors.append(f"Section '{section.get('title', 'Unknown')}' missing topics array")
            continue
        
        for topic in section['topics']:
            allocated_topics.append(topic)
    
    # Check topic count
    if len(allocated_topics) != len(original_topic_titles):
        errors.append(f"Topic count mismatch: {len(allocated_topics)} allocated vs {len(original_topic_titles)} original")
    
    # Check for unallocated topics
    unallocated_topics = []
    for topic_title in original_topic_titles:
        if topic_title not in allocated_topics:
            unallocated_topics.append(topic_title)
    
    if unallocated_topics:
        errors.append(f"Unallocated topics: {', '.join(unallocated_topics[:5])}{'...' if len(unallocated_topics) > 5 else ''}")
    
    # Check for duplicate topics
    if len(set(allocated_topics)) != len(allocated_topics):
        duplicates = [topic for topic in allocated_topics if allocated_topics.count(topic) > 1]
        errors.append(f"Duplicate topics found: {', '.join(set(duplicates))}")
    
    # Check for invented topics (topics not in original list)
    invented_topics = []
    for topic in allocated_topics:
        if topic not in original_topic_titles:
            invented_topics.append(topic)
    
    if invented_topics:
        errors.append(f"Invented topics found: {', '.join(invented_topics[:5])}{'...' if len(invented_topics) > 5 else ''}")
    
    # Check section structure
    for i, section in enumerate(sections):
        if 'title' not in section:
            errors.append(f"Section {i+1} missing title")
        if 'topics' not in section:
            errors.append(f"Section '{section.get('title', 'Unknown')}' missing topics")
        elif len(section['topics']) == 0:
            errors.append(f"Section '{section.get('title', 'Unknown')}' has no topics")
    
    return errors

def create_fallback_sections(topics, section_count, section_style, timestamp):
    """Create a simple fallback section allocation when LLM fails"""
    topic_titles = [topic['title'] for topic in topics]
    
    # Distribute topics evenly across sections
    topics_per_section = len(topics) // section_count
    remainder = len(topics) % section_count
    
    sections = []
    topic_index = 0
    
    for i in range(section_count):
        # Calculate how many topics this section gets
        section_topic_count = topics_per_section + (1 if i < remainder else 0)
        
        # Get topics for this section
        section_topics = topic_titles[topic_index:topic_index + section_topic_count]
        topic_index += section_topic_count
        
        # Create section
        section = {
            'id': f'section_{i+1}',
            'title': f'Section {i+1}',
            'description': f'Topics related to {section_style} theme',
            'topics': section_topics,
            'order': i + 1
        }
        sections.append(section)
    
    return {
        'section_headings': [section['title'] for section in sections],
        'sections': sections,
        'metadata': {
            'total_sections': len(sections),
            'total_topics': len(topics),
            'allocated_topics': len(topics),
            'style': section_style,
            'generated_at': timestamp,
            'fallback': True
        }
    }
