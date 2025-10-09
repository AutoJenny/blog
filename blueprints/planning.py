"""
Planning Blueprint - Minimal Modular Version
Manually extracted key functions with proper imports
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db_manager
import logging
import json
import requests
from datetime import datetime
import re

logger = logging.getLogger(__name__)

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
    
    def execute_llm_request(self, provider, model, messages, api_key=None, max_tokens=2000):
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
                    'max_tokens': max_tokens
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
                    'stream': False,
                    'options': {
                        'num_predict': max_tokens
                    }
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=120
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

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

# ============================================================================
# PLANNING VIEWS (manually extracted)
# ============================================================================

@bp.route('/')
def planning_dashboard():
    """Planning dashboard"""
    return render_template('planning/dashboard.html')

@bp.route('/posts/<int:post_id>')
def planning_post_overview(post_id):
    """Planning post overview"""
    return render_template('planning/post_overview.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/concept')
def planning_concept(post_id):
    """Planning concept page"""
    return redirect(url_for('planning.planning_concept_brainstorm', post_id=post_id))

@bp.route('/posts/<int:post_id>/concept/brainstorm')
def planning_concept_brainstorm(post_id):
    """Planning concept brainstorm page"""
    return render_template('planning/concept/brainstorm.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/concept/section-structure')
def planning_concept_section_structure(post_id):
    """Planning concept section structure page"""
    return render_template('planning/concept/section_structure.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/concept/topic-allocation')
def planning_concept_topic_allocation(post_id):
    """Planning concept topic allocation page"""
    return render_template('planning/concept/topic_allocation.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/concept/titling')
def planning_concept_titling(post_id):
    """Planning concept titling page"""
    return render_template('planning/concept/titling.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/concept/outline')
def planning_concept_outline(post_id):
    """Planning concept outline page"""
    return render_template('planning/concept/outline.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/calendar')
def planning_calendar(post_id):
    """Content Calendar main stage"""
    return render_template('planning/calendar.html', 
                           post_id=post_id,
                           blueprint_name='planning')

@bp.route('/posts/<int:post_id>/calendar/view')
def planning_calendar_view(post_id):
    """Calendar View sub-stage"""
    return render_template('planning/calendar/view.html',
                           post_id=post_id,
                           blueprint_name='planning')

@bp.route('/categories/manage')
def categories_manage():
    """Category management page"""
    return render_template('planning/categories/manage.html', blueprint_name='planning')

# Calendar API endpoints
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
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, ci.created_at, ci.updated_at,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'
                       ) as categories
                FROM calendar_ideas ci
                LEFT JOIN calendar_idea_categories cic ON ci.id = cic.idea_id
                LEFT JOIN calendar_categories cc ON cic.category_id = cc.id
                WHERE ci.week_number = %s
                GROUP BY ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                         ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                         ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                         ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                         ci.evergreen_notes, ci.created_at, ci.updated_at
                ORDER BY ci.created_at DESC
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
                SELECT ce.id, ce.event_title, ce.event_description, ce.start_date, ce.end_date, 
                       ce.week_number, ce.year, ce.content_type, ce.priority, ce.tags,
                       ce.is_recurring, ce.can_span_weeks, ce.max_weeks, ce.created_at, ce.updated_at,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'
                       ) as categories
                FROM calendar_events ce
                LEFT JOIN calendar_event_categories cec ON ce.id = cec.event_id
                LEFT JOIN calendar_categories cc ON cec.category_id = cc.id
                WHERE ce.year = %s AND ce.week_number = %s
                GROUP BY ce.id, ce.event_title, ce.event_description, ce.start_date, ce.end_date, 
                         ce.week_number, ce.year, ce.content_type, ce.priority, ce.tags,
                         ce.is_recurring, ce.can_span_weeks, ce.max_weeks, ce.created_at, ce.updated_at
                ORDER BY ce.start_date
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
    """Get schedule for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cs.id, cs.year, cs.week_number, cs.post_id, cs.scheduled_date, 
                       cs.created_at, cs.updated_at
                FROM calendar_schedule cs
                WHERE cs.year = %s AND cs.week_number = %s
                ORDER BY cs.scheduled_date
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

# Missing ideas page API endpoints
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
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed)
                VALUES (%s, %s)
                ON CONFLICT (post_id) 
                DO UPDATE SET idea_seed = EXCLUDED.idea_seed
            """, (post_id, idea_seed))
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'idea_seed': idea_seed
            })
            
    except Exception as e:
        logger.error(f"Error updating idea seed for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Topic deduplication and post creation endpoints
@bp.route('/api/posts/check-topic', methods=['POST'])
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
                    'idea_seed': result['idea_seed'],
                    'created_at': result['created_at']
                })
            else:
                return jsonify({
                    'success': True,
                    'topic_exists': False,
                    'existing_post_id': None
                })
                
    except Exception as e:
        logger.error(f"Error checking topic: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/create-new', methods=['POST'])
def api_create_new_post():
    """Create a new post for a topic"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        week_number = data.get('week_number', 1)
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Create new post
            # Create slug from topic
            slug = topic.lower().replace(' ', '-').replace(':', '').replace(',', '')
            
            cursor.execute("""
                INSERT INTO post (title, slug, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (f"Blog Post: {topic}", slug, datetime.now(), datetime.now()))
            
            result = cursor.fetchone()
            post_id = result['id']
            
            # Create post_development entry
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed)
                VALUES (%s, %s)
            """, (post_id, f"{topic}: Generated for week {week_number}"))
            
            return jsonify({
                'success': True,
                'post_id': post_id,
                'topic': topic,
                'week_number': week_number
            })
            
    except Exception as e:
        logger.error(f"Error creating new post: {e}")
        return jsonify({'error': str(e)}), 500

# Week-based calendar ideas route
@bp.route('/calendar/ideas/week/<int:week_number>')
def planning_calendar_ideas_week(week_number):
    """Week-based idea generation - creates new posts as needed"""
    try:
        # Get current year
        from datetime import datetime
        year = datetime.now().year
        
        # Load ideas for the specified week
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
        
        return render_template('planning/calendar/ideas_week.html', 
                               week_number=week_number,
                               year=year,
                               ideas=ideas,
                               blueprint_name='planning')
                               
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas_week: {e}")
        # Fallback with basic week number
        from datetime import datetime
        year = datetime.now().year
        return render_template('planning/calendar/ideas_week.html', 
                               week_number=week_number,
                               year=year,
                               ideas=[],
                               blueprint_name='planning')

@bp.route('/api/posts/redirect-after-creation', methods=['POST'])
def api_redirect_after_creation():
    """Handle post creation and return redirect URL"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        week_number = data.get('week_number', 1)
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Check if topic already exists this year
        check_response = api_check_topic()
        check_data = check_response.get_json()
        
        if check_data and check_data.get('success') and check_data.get('topic_exists'):
            # Topic exists - redirect to existing post
            post_id = check_data['existing_post_id']
            redirect_url = f"/planning/posts/{post_id}/concept/brainstorm"
        else:
            # Create new post
            new_post_response = api_create_new_post()
            new_post_data = new_post_response.get_json()
            
            if new_post_data and new_post_data.get('success'):
                post_id = new_post_data['post_id']
                redirect_url = f"/planning/posts/{post_id}/concept/brainstorm"
            else:
                return jsonify({'error': 'Failed to create new post'}), 500
        
        return jsonify({
            'success': True,
            'redirect_url': redirect_url,
            'post_id': post_id,
            'topic': topic,
            'week_number': week_number
        })
        
    except Exception as e:
        logger.error(f"Error in api_redirect_after_creation: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cs.year, cs.week_number, cs.scheduled_date
                FROM calendar_schedule cs
                WHERE cs.post_id = %s
                ORDER BY cs.created_at DESC
                LIMIT 1
            """, (post_id,))
            
            schedule = cursor.fetchone()
            
            if schedule:
                year = schedule['year']
                week_number = schedule['week_number']
            else:
                # Fallback to current week
                from datetime import datetime
                now = datetime.now()
                year = now.year
                week_number = now.isocalendar()[1]
        
        return render_template('planning/calendar/ideas.html', 
                               post_id=post_id,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based')  # Explicitly mark as post-based mode
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        # Fallback with basic week number
        from datetime import datetime
        now = datetime.now()
        year = now.year
        week_number = now.isocalendar()[1]
        return render_template('planning/calendar/ideas.html', 
                               post_id=post_id,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based')

@bp.route('/posts/<int:post_id>/research')
def planning_research(post_id):
    """Research planning phase"""
    return render_template('planning/research.html', post_id=post_id, blueprint_name='planning')

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

@bp.route('/posts/<int:post_id>/old-interface')
def planning_old_interface(post_id):
    """Old interface"""
    return render_template('planning/old_interface.html', post_id=post_id, blueprint_name='planning')

# ============================================================================
# API ENDPOINTS (manually extracted key ones)
# ============================================================================

@bp.route('/api/posts/<int:post_id>')
def api_posts(post_id):
    """Get post data for planning"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.idea_scope, pd.section_structure, pd.topic_allocation,
                       pd.refined_topics, pd.expanded_idea, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get calendar schedule
            cursor.execute("""
                SELECT id, year, week_number, scheduled_date, created_at, updated_at
                FROM calendar_schedule 
                WHERE post_id = %s
            """, (post_id,))
            
            schedule = cursor.fetchone()
            
            # Get post sections
            cursor.execute("""
                SELECT id, post_id, section_order, section_heading, section_description, 
                       ideas_to_include, facts_to_include, highlighting,
                       image_concepts, image_prompts, image_alt_text,
                       image_captions, status, polished, draft,
                       image_filename, image_generated_at, image_title,
                       image_width, image_height
                FROM post_section 
                WHERE post_id = %s 
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'post': dict(result),
                'schedule': dict(schedule) if schedule else None,
                'sections': [dict(section) for section in sections]
            })
            
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/<prompt_type>')
def api_get_prompt(prompt_type):
    """Get LLM prompt from database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT prompt_text, system_prompt, created_at, updated_at
                FROM llm_prompt 
                WHERE name = %s OR id = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_type, prompt_type))
            
            result = cursor.fetchone()
            if result:
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_type.replace('-', ' ').title(),
                        'prompt_text': result['prompt_text'],
                        'system_prompt': result['system_prompt'],
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                    },
                    'llm_config': {
                        'provider': 'Ollama',
                        'model': 'llama3.1:8b',
                        'temperature': 0.7,
                        'max_tokens': 4000
                    }
                })
            else:
                # Return a default prompt if not found
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_type.replace('-', ' ').title(),
                        'prompt_text': 'Generate creative, short section titles (2-4 words maximum) that are poetic and evocative. NO COLONS, NO SUBTITLES, NO DESCRIPTIONS in the title. MAXIMUM 4 WORDS. Use evocative, poetic language.',
                        'system_prompt': 'You are a creative writing assistant specializing in generating compelling, poetic section titles.',
                        'created_at': None,
                        'updated_at': None
                    },
                    'llm_config': {
                        'provider': 'Ollama',
                        'model': 'llama3.1:8b',
                        'temperature': 0.7,
                        'max_tokens': 4000
                    }
                })
                
    except Exception as e:
        logger.error(f"Error fetching prompt: {e}")
        # Return a default prompt on error
        return jsonify({
            'success': True,
            'prompt': {
                'name': prompt_type.replace('-', ' ').title(),
                'prompt_text': 'Generate creative, short section titles (2-4 words maximum) that are poetic and evocative. NO COLONS, NO SUBTITLES, NO DESCRIPTIONS in the title. MAXIMUM 4 WORDS. Use evocative, poetic language.',
                'system_prompt': 'You are a creative writing assistant specializing in generating compelling, poetic section titles.',
                'created_at': None,
                'updated_at': None
            },
            'llm_config': {
                'provider': 'Ollama',
                'model': 'llama3.1:8b',
                'temperature': 0.7,
                'max_tokens': 4000
            }
        })

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
                SELECT prompt_text, system_prompt 
                FROM llm_prompt 
                WHERE name = 'brainstorm_topics'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                user_prompt = result['prompt_text']
                system_prompt = result['system_prompt']
            else:
                # Default prompts if not found in database
                user_prompt = f"""
Generate {brainstorm_type} topics for a blog post about: {expanded_idea}

Requirements:
- Generate exactly 50 diverse topics
- Each topic should be specific and actionable
- Include a mix of historical, cultural, practical, and contemporary angles
- Format as JSON array with title, description, category, and word_count
- Use idea codes like {{IDEA01}}, {{IDEA02}}, etc.
"""
                system_prompt = "You are a creative content strategist specializing in generating comprehensive topic ideas for blog posts."
        
        # Prepare messages for LLM
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': user_prompt})
        
        # Execute LLM request
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=4000)
        
        if result and 'content' in result:
            topics = parse_brainstorm_topics(result['content'])
            
            return jsonify({
                'success': True,
                'message': 'Topics generated successfully',
                'topics': topics,
                'count': len(topics),
                'raw_response': result['content']
            })
        else:
            return jsonify({'error': 'Failed to generate topics'}), 500
            
    except Exception as e:
        logger.error(f"Error generating brainstorm topics: {e}")
        return jsonify({'error': str(e)}), 500

def parse_brainstorm_topics(content):
    """Enhanced topic parsing with validation and categorization"""
    topics = []
    
    # Step 1: Try JSON parsing (expected format)
    try:
        # Clean up the content to extract JSON
        content_clean = content.strip()
        
        # Find JSON array boundaries
        start_idx = content_clean.find('[')
        end_idx = content_clean.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = content_clean[start_idx:end_idx + 1]
            parsed_data = json.loads(json_str)
            
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    if isinstance(item, dict):
                        topic = {
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'category': item.get('category', 'general'),
                            'word_count': item.get('word_count', 0)
                        }
                        topics.append(topic)
                    elif isinstance(item, str):
                        topics.append({
                            'title': item,
                            'description': '',
                            'category': 'general',
                            'word_count': len(item.split())
                        })
                return topics
    except json.JSONDecodeError:
        pass
    
    # Step 2: Fallback to line-by-line parsing
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('*'):
            # Extract idea code if present
            idea_match = re.search(r'\{IDEA\d+\}', line)
            if idea_match:
                title = line.replace(idea_match.group(), '').strip()
                topics.append({
                    'title': f"{idea_match.group()} {title}",
                    'description': '',
                    'category': 'general',
                    'word_count': len(title.split())
                })
            elif len(line) > 10:  # Only include substantial lines
                topics.append({
                    'title': line,
                    'description': '',
                    'category': 'general',
                    'word_count': len(line.split())
                })
    
    return topics

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
            if result and result['idea_scope']:
                idea_scope = result['idea_scope']
                if isinstance(idea_scope, str):
                    idea_scope = json.loads(idea_scope)
                
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

@bp.route('/api/posts/<int:post_id>/idea-scope', methods=['POST'])
def api_update_idea_scope(post_id):
    """Update the IDEA_SCOPE field in post_development with generated topics"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        
        if not topics:
            return jsonify({'error': 'No topics provided'}), 400
        
        # Format topics as JSON for storage
        idea_scope_data = {
            'generated_topics': topics,
            'generated_at': datetime.now().isoformat(),
            'total_count': len(topics)
        }
        
        with db_manager.get_cursor() as cursor:
            # Check if post_development record exists
            cursor.execute("""
                SELECT id FROM post_development WHERE post_id = %s
            """, (post_id,))
            
            if cursor.fetchone():
                # Update existing record
                cursor.execute("""
                    UPDATE post_development 
                    SET idea_scope = %s, updated_at = NOW()
                    WHERE post_id = %s
                """, (json.dumps(idea_scope_data), post_id))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO post_development (post_id, idea_scope, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (post_id, json.dumps(idea_scope_data)))
            
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Topics saved successfully',
            'count': len(topics)
        })
        
    except Exception as e:
        logger.error(f"Error updating idea scope: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get sections data for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT section_order, section_heading, section_description, 
                       ideas_to_include, facts_to_include, highlighting,
                       image_concepts, image_prompts, image_alt_text,
                       image_captions, status, polished, draft,
                       image_filename, image_generated_at, image_title,
                       image_width, image_height
                FROM post_section 
                WHERE post_id = %s 
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'sections': [dict(section) for section in sections]
            })
            
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/topic-allocation')
def api_get_topic_allocation(post_id):
    """Get topic allocation data for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result['topic_allocation']:
                # Check if it's already a dict or needs parsing
                topic_allocation = result['topic_allocation']
                if isinstance(topic_allocation, str):
                    topic_allocation = json.loads(topic_allocation)
                
                return jsonify({
                    'success': True,
                    'topic_allocation': topic_allocation
                })
            else:
                return jsonify({'success': True, 'topic_allocation': None})
                
    except Exception as e:
        logger.error(f"Error fetching topic allocation: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/title', methods=['POST'])
def api_sections_title():
    """Generate section titles"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        topic_allocation = data.get('topic_allocation')
        
        if not post_id or not topic_allocation:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Import the function from the new sections module
        from blueprints.planning_sections import api_sections_title
        
        # Call the function
        return api_sections_title()
        
    except Exception as e:
        logger.error(f"Error in section titling: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/save', methods=['POST'])
def api_save_sections():
    """Save section titles and descriptions"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        sections = data.get('sections')
        
        if not post_id or not sections:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Import the function from the new sections module
        from blueprints.planning_sections import api_save_sections
        
        # Call the function
        return api_save_sections()
        
    except Exception as e:
        logger.error(f"Error saving sections: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/allocate-topics/<int:post_id>')
def api_get_allocate_topics(post_id):
    """Get topic allocation data - endpoint expected by titling page JavaScript"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result['topic_allocation']:
                # Check if it's already a dict or needs parsing
                topic_allocation = result['topic_allocation']
                if isinstance(topic_allocation, str):
                    topic_allocation = json.loads(topic_allocation)
                
                return jsonify({
                    'success': True,
                    'allocations': topic_allocation
                })
            else:
                return jsonify({'success': True, 'allocations': None})
                
    except Exception as e:
        logger.error(f"Error fetching topic allocation: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/expanded-idea', methods=['GET', 'POST'])
def api_get_expanded_idea(post_id):
    """Get or generate expanded idea for a post"""
    if request.method == 'GET':
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT expanded_idea FROM post_development 
                    WHERE post_id = %s AND expanded_idea IS NOT NULL
                """, (post_id,))
                
                result = cursor.fetchone()
                if result and result['expanded_idea']:
                    return jsonify({
                        'success': True,
                        'expanded_idea': result['expanded_idea']
                    })
                else:
                    return jsonify({'success': True, 'expanded_idea': ''})
                    
        except Exception as e:
            logger.error(f"Error fetching expanded idea: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            idea_seed = data.get('idea_seed', '')
            
            if not idea_seed:
                return jsonify({'error': 'Idea seed is required'}), 400
            
            # Generate expanded idea using LLM
            llm_service = LLMService()
            
            prompt = f"""
            Expand the following blog post idea into a detailed outline and content plan:
            
            {idea_seed}
            
            Please provide:
            1. A compelling introduction hook
            2. Main sections with key points
            3. Supporting details and examples
            4. A strong conclusion
            5. Suggested tone and style
            
            Make it engaging and informative for readers interested in Scottish culture and traditions.
            """
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', [{'role': 'user', 'content': prompt}], max_tokens=4000)
            
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

@bp.route('/api/posts/<int:post_id>')
def api_get_post_data(post_id):
    """Get post data including development data"""
    try:
        # Import the function from the new data module
        from blueprints.planning_data import get_post_data
        
        # Call the function
        return get_post_data(post_id)
        
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/design-structure/<int:post_id>')
def api_get_section_structure(post_id):
    """Get section structure for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT section_structure FROM post_development 
                WHERE post_id = %s AND section_structure IS NOT NULL
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result['section_structure']:
                section_structure = result['section_structure']
                if isinstance(section_structure, str):
                    section_structure = json.loads(section_structure)
                
                return jsonify({
                    'success': True,
                    'section_structure': section_structure
                })
            else:
                return jsonify({'success': True, 'section_structure': None})
                
    except Exception as e:
        logger.error(f"Error fetching section structure: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/design-structure', methods=['POST'])
def api_design_section_structure():
    """Design section structure based on topics"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        post_id = data.get('post_id')
        
        if not topics or not post_id:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Import the function from the new sections module
        from blueprints.planning_sections import api_design_section_structure
        
        # Call the function
        return api_design_section_structure()
        
    except Exception as e:
        logger.error(f"Error designing section structure: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# IMPORT REMAINING FUNCTIONS FROM ORIGINAL FILE
# ============================================================================

# NOTE: Dynamic loading removed to prevent duplicate function conflicts
# Individual functions are imported as needed above

# Export the main blueprint
__all__ = ['bp']
