"""
Planning Blueprint - Modular Version
Imports functions from separate modules
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db_manager
import logging
import json
import requests
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# Import functions from new modules
from blueprints.planning_views import planning_dashboard as dashboard_func, planning_post_overview as post_overview_func, planning_concept as concept_func, categories_manage as categories_func, planning_research as research_func
from blueprints.planning_calendar_clean import planning_calendar as calendar_func, planning_calendar_view as calendar_view_func, planning_calendar_week_view as calendar_week_view_func, planning_calendar_ideas as ideas_func, planning_calendar_ideas_week as ideas_week_func
from blueprints.planning_calendar import planning_calendar_taxonomy as taxonomy_func
from blueprints.planning_concept import planning_concept_brainstorm as brainstorm_func, planning_concept_section_structure as section_structure_func, planning_concept_topic_allocation as topic_allocation_func, planning_concept_titling as titling_func, planning_concept_outline as outline_func, planning_research_sources as sources_func, planning_research_visuals as visuals_func, planning_research_prompts as prompts_func, planning_research_verification as verification_func
from blueprints.planning_api_calendar import api_calendar_categories as categories_api_func, api_calendar_weeks as weeks_api_func, api_calendar_ideas as ideas_api_func, api_calendar_events as events_api_func, api_calendar_schedule as schedule_api_func, api_calendar_ideas_for_week as ideas_week_api_func, api_add_calendar_idea as add_idea_api_func, api_update_calendar_idea as update_idea_api_func, api_delete_calendar_idea as delete_idea_api_func, api_calendar_idea_status as idea_status_api_func, api_get_calendar_idea as get_idea_api_func, api_convert_event_to_idea as convert_event_to_idea_api_func, api_add_calendar_event as add_event_api_func, api_update_calendar_event as update_event_api_func, api_delete_calendar_event as delete_event_api_func, api_select_theme_idea as select_theme_idea_api_func, api_weekly_social_focus as social_focus_api_func, api_weekly_social_focus_day as social_focus_day_api_func, api_add_weekly_social_focus as add_social_focus_api_func, api_update_weekly_social_focus as update_social_focus_api_func, api_delete_weekly_social_focus as delete_social_focus_api_func
from blueprints.planning_api_themes import api_calendar_themes as themes_api_func, api_get_calendar_theme as get_theme_api_func, api_add_calendar_theme, api_update_calendar_theme, api_delete_calendar_theme
from blueprints.planning_api_posts import api_posts as posts_api_func
from blueprints.planning_api_posts import confirm_calendar_idea as confirm_calendar_idea_func
from blueprints.planning_api_post_specific import api_posts_expanded_idea as expanded_idea_api_func, api_posts_idea_seed as idea_seed_api_func, api_check_topic as check_topic_api_func, api_create_new_post as create_new_api_func, api_posts_idea_scope as idea_scope_api_func, get_post_by_theme as get_post_by_theme_func
from blueprints.planning_api_brainstorm import api_generate_brainstorm_topics as brainstorm_topics_api_func
from blueprints.planning_api_prompts import api_get_prompt as prompt_api_func
from blueprints.planning_sections import api_sections_title as sections_title_api_func, api_save_sections as sections_save_api_func, api_design_section_structure as sections_design_api_func
from blueprints.planning_api_topic_allocation import api_generate_section_specific_topics as generate_topics_func, api_get_topic_allocation as get_allocation_func
from blueprints.planning_llm import LLMService, parse_brainstorm_topics

# Initialize LLM service
llm_service = LLMService()

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

# ============================================================================
# PLANNING VIEWS (imported from planning_views.py)
# ============================================================================

@bp.route('/')
def planning_dashboard():
    """Planning dashboard"""
    return dashboard_func()

@bp.route('/posts/<int:post_id>')
def planning_post_overview(post_id):
    """Planning post overview"""
    return post_overview_func(post_id)

@bp.route('/posts/<int:post_id>/concept')
def planning_concept(post_id):
    """Planning concept"""
    return concept_func(post_id)

@bp.route('/posts/<int:post_id>/calendar')
def planning_calendar(post_id):
    """Planning calendar"""
    return calendar_func(post_id)

@bp.route('/categories/manage')
def categories_manage():
    """Manage calendar categories"""
    return categories_func()

@bp.route('/posts/<int:post_id>/research')
def planning_research(post_id):
    """Planning research"""
    return research_func(post_id)

# ARCHIVED: planning_old_interface route removed - old interface system has been archived
# See ARCHIVED_OLD_WORKFLOW/ for archived code

# ============================================================================
# CALENDAR FUNCTIONS (imported from planning_calendar.py)
# ============================================================================

@bp.route('/posts/<int:post_id>/calendar/view')
def planning_calendar_view(post_id):
    """Calendar view page"""
    return calendar_view_func(post_id)

@bp.route('/posts/<int:post_id>/calendar/week-view')
def planning_calendar_week_view(post_id):
    """Calendar week (week-per-view) page"""
    return calendar_week_view_func(post_id)

@bp.route('/calendar/ideas/week/<int:week_number>')
def planning_calendar_ideas_week(week_number):
    """Week-based idea generation"""
    return ideas_week_func(week_number)

@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Calendar ideas page"""
    return ideas_func(post_id)

@bp.route('/posts/<int:post_id>/calendar/taxonomy')
def planning_calendar_taxonomy(post_id):
    """Taxonomy assignment page"""
    return taxonomy_func(post_id)

# ============================================================================
# CONCEPT FUNCTIONS (imported from planning_concept.py)
# ============================================================================

@bp.route('/posts/<int:post_id>/concept/brainstorm')
def planning_concept_brainstorm(post_id):
    """Brainstorm page"""
    return brainstorm_func(post_id)

@bp.route('/posts/<int:post_id>/concept/section-structure')
def planning_concept_section_structure(post_id):
    """Section structure page"""
    return section_structure_func(post_id)

@bp.route('/posts/<int:post_id>/concept/topic-allocation')
def planning_concept_topic_allocation(post_id):
    """Topic allocation page"""
    return topic_allocation_func(post_id)

@bp.route('/posts/<int:post_id>/concept/titling')
def planning_concept_titling(post_id):
    """Titling page"""
    return titling_func(post_id)

@bp.route('/posts/<int:post_id>/concept/outline')
def planning_concept_outline(post_id):
    """Outline page"""
    return outline_func(post_id)

@bp.route('/posts/<int:post_id>/research/sources')
def planning_research_sources(post_id):
    """Research sources page"""
    return sources_func(post_id)

@bp.route('/posts/<int:post_id>/research/visuals')
def planning_research_visuals(post_id):
    """Research visuals page"""
    return visuals_func(post_id)

@bp.route('/posts/<int:post_id>/research/prompts')
def planning_research_prompts(post_id):
    """Research prompts page"""
    return prompts_func(post_id)

@bp.route('/posts/<int:post_id>/research/verification')
def planning_research_verification(post_id):
    """Research verification page"""
    return verification_func(post_id)

# ============================================================================
# API ENDPOINTS (imported from planning_api.py)
# ============================================================================

@bp.route('/api/calendar/categories', methods=['GET'])
def api_calendar_categories():
    """Get all calendar categories"""
    return categories_api_func()

@bp.route('/api/llm/prompts/<prompt_type>')
def api_get_prompt(prompt_type):
    """Get LLM prompt by type"""
    return prompt_api_func(prompt_type)

@bp.route('/api/calendar/weeks/<int:year>', methods=['GET'])
def api_calendar_weeks(year):
    """Get all calendar weeks for a given year"""
    return weeks_api_func(year)

@bp.route('/api/calendar/ideas/<int:idea_id>', methods=['GET', 'PUT'])
def api_calendar_idea(idea_id):
    """Get or update an idea - must come before week_number route"""
    if request.method == 'GET':
        return get_idea_api_func(idea_id)
    else:
        return update_idea_api_func(idea_id)

@bp.route('/api/calendar/ideas/week/<int:week_number>', methods=['GET'])
def api_calendar_ideas_for_week(week_number):
    """Get ideas for a specific week"""
    return ideas_week_api_func(week_number)

@bp.route('/api/calendar/ideas/<int:week_number>', methods=['GET'])
def api_calendar_ideas(week_number):
    """Get perpetual ideas for a specific week number"""
    return ideas_api_func(week_number)

@bp.route('/api/calendar/themes/week/<int:week_number>', methods=['GET'])
def api_calendar_themes(week_number):
    """Get perpetual themes for a specific week number"""
    return themes_api_func(week_number)

@bp.route('/api/calendar/themes/<int:theme_id>', methods=['GET', 'PUT', 'DELETE'])
def api_calendar_theme(theme_id):
    """Get, update, or delete a single calendar theme"""
    if request.method == 'GET':
        return get_theme_api_func(theme_id)
    elif request.method == 'PUT':
        return api_update_calendar_theme(theme_id)
    elif request.method == 'DELETE':
        return api_delete_calendar_theme(theme_id)

@bp.route('/api/calendar/themes', methods=['POST'])
def api_add_calendar_theme_route():
    """Create a new calendar theme"""
    return api_add_calendar_theme()

@bp.route('/api/calendar/events/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_events(year, week_number):
    """Get events for a specific year and week"""
    return events_api_func(year, week_number)

@bp.route('/api/calendar/schedule/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_schedule(year, week_number):
    """Get schedule for a specific year and week"""
    return schedule_api_func(year, week_number)

@bp.route('/api/calendar/schedule/update-theme-to-idea', methods=['POST'])
def api_schedule_update_theme_to_idea():
    """Update schedule entries to convert theme_id to idea_id"""
    from blueprints.planning_api_calendar import api_schedule_update_theme_to_idea
    return api_schedule_update_theme_to_idea()

@bp.route('/api/calendar/ideas', methods=['POST'])
def api_calendar_add_idea():
    """Create a new idea for a week"""
    return add_idea_api_func()

@bp.route('/api/calendar/events', methods=['POST'])
def api_add_event():
    """Create a new calendar event"""
    return add_event_api_func()

@bp.route('/api/calendar/events/<int:event_id>', methods=['PUT', 'DELETE'])
def api_event(event_id):
    """Update or delete an existing calendar event"""
    if request.method == 'DELETE':
        return delete_event_api_func(event_id)
    return update_event_api_func(event_id)

@bp.route('/api/calendar/events/<int:event_id>/convert-to-idea', methods=['POST'])
def api_convert_event_to_idea(event_id):
    """Convert an event to an idea (atomic operation)"""
    return convert_event_to_idea_api_func(event_id)

@bp.route('/api/calendar/ideas/<int:idea_id>', methods=['DELETE'])
def api_calendar_delete_idea(idea_id):
    """Delete an idea"""
    return delete_idea_api_func(idea_id)

@bp.route('/api/calendar/ideas/<int:idea_id>/status', methods=['GET'])
def api_calendar_idea_status(idea_id):
    """Get post creation status for an idea in a week"""
    return idea_status_api_func(idea_id)

@bp.route('/api/calendar/select-theme', methods=['POST'])
def api_select_theme():
    """Select a theme/idea for a specific week/year"""
    return select_theme_idea_api_func()

# ============================================================================
# WEEKLY SOCIAL FOCUS API ENDPOINTS
# ============================================================================

@bp.route('/api/social-focus/week', methods=['GET'])
def api_social_focus_week():
    """Get all weekly social focus entries"""
    return social_focus_api_func()

@bp.route('/api/social-focus/day/<int:day_of_week>', methods=['GET'])
def api_social_focus_day(day_of_week):
    """Get social focus for a specific day (1-7)"""
    return social_focus_day_api_func(day_of_week)

@bp.route('/api/social-focus', methods=['POST'])
def api_add_social_focus():
    """Create a new weekly social focus"""
    return add_social_focus_api_func()

@bp.route('/api/social-focus/<int:focus_id>', methods=['PUT'])
def api_update_social_focus(focus_id):
    """Update an existing weekly social focus"""
    return update_social_focus_api_func(focus_id)

@bp.route('/api/social-focus/<int:focus_id>', methods=['DELETE'])
def api_delete_social_focus(focus_id):
    """Delete (deactivate) a weekly social focus"""
    return delete_social_focus_api_func(focus_id)

@bp.route('/api/posts/<int:post_id>', methods=['GET'])
def api_posts(post_id):
    """Get post data for planning"""
    return posts_api_func(post_id)

@bp.route('/api/calendar/confirm-idea', methods=['POST'])
def api_calendar_confirm_idea():
    """Confirm calendar idea and produce/reuse post"""
    return confirm_calendar_idea_func()

@bp.route('/api/posts/by-theme/<int:theme_idea_id>', methods=['GET'])
def api_get_post_by_theme(theme_idea_id):
    """Get a post that has a specific theme idea_id in its schedule"""
    return get_post_by_theme_func(theme_idea_id)

@bp.route('/api/posts/<int:post_id>/expanded-idea', methods=['GET', 'POST'])
def api_posts_expanded_idea(post_id):
    """Get or create expanded idea for a post"""
    return expanded_idea_api_func(post_id)

@bp.route('/api/posts/<int:post_id>/idea-seed', methods=['GET', 'POST'])
def api_posts_idea_seed(post_id):
    """Get or set idea seed for a post"""
    return idea_seed_api_func(post_id)

@bp.route('/api/posts/check-topic', methods=['POST'])
def api_check_topic():
    """Check if a topic has already been used this year"""
    return check_topic_api_func()

@bp.route('/api/posts/create-new', methods=['POST'])
def api_create_new_post():
    """Create a new post"""
    return create_new_api_func()

@bp.route('/api/posts/<int:post_id>/idea-scope', methods=['GET', 'POST'])
def api_posts_idea_scope(post_id):
    """Get or set idea scope for a post"""
    return idea_scope_api_func(post_id)

@bp.route('/api/brainstorm/topics', methods=['POST'])
def api_generate_brainstorm_topics():
    """Generate brainstorming topics using LLM"""
    return brainstorm_topics_api_func()

# ============================================================================
# SECTION API ENDPOINTS (imported from planning_sections.py)
# ============================================================================

@bp.route('/api/sections/design-structure', methods=['POST'])
def api_design_section_structure():
    """Design section structure based on topics"""
    return sections_design_api_func()

@bp.route('/api/sections/design-structure/<int:post_id>', methods=['GET'])
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

@bp.route('/api/sections/title', methods=['POST'])
def api_sections_title():
    """Generate section titles"""
    return sections_title_api_func()

@bp.route('/api/sections/save', methods=['POST'])
def api_save_sections():
    """Save sections to database"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        if not post_id:
            return jsonify({'error': 'post_id is required'}), 400
        return sections_save_api_func(post_id)
    except Exception as e:
        logger.error(f"Error in api_save_sections route: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/allocate-topics', methods=['POST'])
def api_allocate_topics():
    """Allocate topics to sections"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        topics = data.get('topics', [])
        sections = data.get('sections', [])
        
        if not post_id or not topics or not sections:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Simple topic allocation logic - distribute topics evenly across sections
        topics_per_section = len(topics) // len(sections)
        remainder = len(topics) % len(sections)
        
        allocations = []
        topic_index = 0
        
        for i, section in enumerate(sections):
            section_topics = []
            topics_for_this_section = topics_per_section + (1 if i < remainder else 0)
            
            for j in range(topics_for_this_section):
                if topic_index < len(topics):
                    section_topics.append(topics[topic_index])
                    topic_index += 1
            
            allocations.append({
                'section_id': section.get('id', f'section_{i+1}'),
                'section_title': section.get('title', f'Section {i+1}'),
                'topics': section_topics
            })
        
        # Save to database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET topic_allocation = %s, allocation_completed_at = %s, updated_at = %s
                WHERE post_id = %s
            """, (json.dumps(allocations), datetime.now(), datetime.now(), post_id))
        
        return jsonify({
            'success': True,
            'allocations': allocations
        })
        
    except Exception as e:
        logger.error(f"Error allocating topics: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/sections/generate-section-specific-topics', methods=['POST'])
def api_generate_section_specific_topics():
    """Generate section-specific topics instead of forcing existing ideas into sections"""
    return generate_topics_func()

@bp.route('/api/sections/allocate-topics/<int:post_id>', methods=['GET'])
def api_get_topic_allocation(post_id):
    """Get existing topic allocation for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result['topic_allocation']:
                allocations = result['topic_allocation']
                if isinstance(allocations, str):
                    allocations = json.loads(allocations)
                
                return jsonify({
                    'success': True,
                    'allocations': allocations
                })
            else:
                return jsonify({'success': True, 'allocations': None})
                
    except Exception as e:
        logger.error(f"Error fetching topic allocation: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# REMAINING FUNCTIONS (still need to be moved to modules)
# ============================================================================

# TODO: Move remaining API functions to planning_api.py
# TODO: Move remaining functions to appropriate modules

# Export the main blueprint
__all__ = ['bp']
