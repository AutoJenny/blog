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
from blueprints.planning_calendar_clean import planning_calendar as calendar_func, planning_calendar_view as calendar_view_func, planning_calendar_week_view as calendar_week_view_func, planning_calendar_scheduling as scheduling_func, planning_calendar_ideas as ideas_func, planning_calendar_ideas_week as ideas_week_func
from blueprints.planning_calendar import planning_calendar_taxonomy as taxonomy_func
from blueprints.planning_calendar_product_data_review import planning_calendar_product_data_review as product_data_review_func, api_regenerate_heritage_data as regenerate_heritage_data_func
from blueprints.planning_concept import planning_concept_brainstorm as brainstorm_func, planning_concept_section_structure as section_structure_func, planning_concept_topic_allocation as topic_allocation_func, planning_concept_titling as titling_func, planning_concept_outline as outline_func, planning_research_sources as sources_func, planning_research_visuals as visuals_func, planning_research_prompts as prompts_func, planning_research_verification as verification_func
from blueprints.planning_api_calendar import api_calendar_categories as categories_api_func, api_calendar_weeks as weeks_api_func, api_calendar_ideas as ideas_api_func, api_calendar_events as events_api_func, api_calendar_schedule as schedule_api_func, api_calendar_ideas_for_week as ideas_week_api_func, api_add_calendar_idea as add_idea_api_func, api_update_calendar_idea as update_idea_api_func, api_delete_calendar_idea as delete_idea_api_func, api_calendar_idea_status as idea_status_api_func, api_get_calendar_idea as get_idea_api_func, api_convert_event_to_idea as convert_event_to_idea_api_func, api_add_calendar_event as add_event_api_func, api_update_calendar_event as update_event_api_func, api_delete_calendar_event as delete_event_api_func, api_select_theme_idea as select_theme_idea_api_func, api_update_calendar_week_item as update_calendar_week_item_api_func, api_set_calendar_week_item_primary as set_calendar_week_item_primary_api_func, api_weekly_social_focus as social_focus_api_func, api_weekly_social_focus_day as social_focus_day_api_func, api_add_weekly_social_focus as add_social_focus_api_func, api_update_weekly_social_focus as update_social_focus_api_func, api_delete_weekly_social_focus as delete_social_focus_api_func
from blueprints.planning_api_calendar_scheduling_cache import scheduling_all as scheduling_all_api_func
# OLD IMPORTS REMOVED - Use planning_api_calendar_cyclic and planning_api_calendar_overrides instead
# from blueprints.planning_api_calendar_reorder import api_reorder_item as reorder_item_api_func, api_position_for_week as position_for_week_api_func
# from blueprints.planning_api_calendar_reassign import bp as planning_api_calendar_reassign_bp
from blueprints.planning_api_themes import api_calendar_themes as themes_api_func, api_get_calendar_theme as get_theme_api_func, api_add_calendar_theme, api_update_calendar_theme, api_delete_calendar_theme
from blueprints.planning_api_posts import api_posts as posts_api_func
from blueprints.planning_api_posts import confirm_calendar_idea as confirm_calendar_idea_func
from blueprints.planning_api_post_specific import api_posts_expanded_idea as expanded_idea_api_func, api_posts_idea_seed as idea_seed_api_func, api_check_topic as check_topic_api_func, api_create_new_post as create_new_api_func, api_posts_idea_scope as idea_scope_api_func, get_post_by_theme as get_post_by_theme_func
from blueprints.planning_api_brainstorm import api_generate_brainstorm_topics as brainstorm_topics_api_func
from blueprints.planning_api_prompts import api_get_prompt as prompt_api_func
from blueprints.planning_titling import api_sections_title as sections_title_api_func, api_save_sections as sections_save_api_func
from blueprints.planning_sections import api_design_section_structure as sections_design_api_func
from blueprints.planning_api_profile import (
    api_profile_section_structure as profile_section_structure_func,
    api_get_profile_section_structure_prompt_selection as profile_prompt_selection_func,
    api_set_profile_section_structure_prompt_selection as profile_set_prompt_selection_func,
    api_get_profile_section_structure_prompt as profile_get_prompt_func,
    api_update_profile_section_structure_prompt as profile_update_prompt_func,
    api_profile_topic_allocation as profile_topic_allocation_func,
    api_profile_sections_title as profile_sections_title_func
)
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

@bp.route('/content-control-board')
def content_control_board():
    """Content Control Board - read-only planning surface for role-driven social posting"""
    from datetime import date
    # Get current ISO week
    today = date.today()
    year, week, _ = today.isocalendar()
    
    # Get year/week from query params if provided
    year = request.args.get('year', type=int) or year
    week = request.args.get('week', type=int) or week
    
    return render_template('planning/content_control_board.html', 
                         page_title='Content Control Board',
                         current_year=year,
                         current_week=week)

@bp.route('/content-roles')
def content_roles_reference():
    """Content Roles Reference - complete guide to content roles"""
    return render_template('planning/content_roles_reference.html',
                         page_title='Content Roles Reference')

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
    """Planning calendar - DEPRECATED: Redirects to ideas page"""
    from flask import redirect, url_for, request
    # Get year/week from query params if provided
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    # Redirect to ideas page with same params
    return redirect(url_for('planning.planning_calendar_ideas', post_id=post_id, year=year, week=week))

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


@bp.route('/posts/<int:post_id>/calendar/scheduling')
def planning_calendar_scheduling(post_id):
    """Calendar scheduling view - Year overview"""
    return scheduling_func(post_id)

@bp.route('/calendar')
def planning_calendar_new():
    """New unified calendar page with shared header and tabs"""
    from flask import request
    from datetime import datetime
    
    # Get year and week from URL params, default to current week
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # Calculate actual current week (for display purposes)
    now = datetime.now()
    actual_current_year = now.isocalendar()[0]
    actual_current_week = now.isocalendar()[1]
    
    # If not provided, use current week
    if not year or not week:
        year = year or actual_current_year
        week = week or actual_current_week
    
    # Determine active tab from URL path or default to week-view
    active_tab = request.args.get('tab', 'week-view')
    
    return render_template('planning/calendar/new_calendar.html',
                          year=year,
                          week=week,
                          current_year=actual_current_year,
                          current_week=actual_current_week,
                          active_tab=active_tab,
                          blueprint_name='planning')

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
    from flask import request
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    return taxonomy_func(post_id, year=year, week=week)


@bp.route('/calendar/sequence-manager')
def planning_calendar_sequence_manager():
    """
    UI for managing base cyclic sequences (themes, recipes, profiles, words, phrases).

    This page is read-only at load; all changes happen via JSON APIs.
    """
    return render_template('planning/calendar/sequence_manager.html')

@bp.route('/posts/<int:post_id>/calendar/product-data-review')
def planning_calendar_product_data_review(post_id):
    """Product Data Review page for generated posts"""
    return product_data_review_func(post_id)

@bp.route('/api/posts/<int:post_id>/regenerate-heritage-data/<int:category_id>', methods=['POST'])
def api_regenerate_heritage_data(post_id, category_id):
    """API endpoint to regenerate heritage data for a category"""
    return regenerate_heritage_data_func(post_id, category_id)

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

@bp.route('/posts/<int:post_id>/concept/section-content-mapping')
def planning_concept_section_content_mapping(post_id):
    """Section content mapping page"""
    from blueprints.planning_concept_section_content_mapping import planning_concept_section_content_mapping as handler
    return handler(post_id)

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

@bp.route('/api/calendar/ideas/<int:idea_id>', methods=['GET', 'PUT', 'PATCH'])
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
# DEPRECATED: This function uses old week_number-based theme lookup
# NEW SYSTEM: Use /planning/api/calendar/themes/week/<week_number> which now uses cyclic system
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

@bp.route('/api/calendar/profiles/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_profiles(year, week_number):
    """Get profiles scheduled for a specific year and week"""
    from blueprints.planning_api_calendar_profiles import api_calendar_profiles as profiles_func
    return profiles_func(year, week_number)

@bp.route('/api/calendar/recipes/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_recipes(year, week_number):
    """Get recipes scheduled for a specific year and week"""
    from blueprints.planning_api_calendar_recipes import api_calendar_recipes as recipes_func
    return recipes_func(year, week_number)

@bp.route('/api/calendar/content-generator/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_content_generator(year, week_number):
    """Get generated posts scheduled for a specific year and week"""
    from blueprints.planning_api_calendar_content_generator import api_calendar_content_generator as content_generator_func
    return content_generator_func(year, week_number)

@bp.route('/api/profiles', methods=['POST'])
def api_create_profile_route():
    """Create a new profile"""
    from blueprints.planning_api_profiles import api_create_profile
    return api_create_profile()

@bp.route('/api/profiles/<int:profile_id>', methods=['GET', 'PUT', 'DELETE'])
def api_profile_route(profile_id):
    """Get, update, or delete a profile"""
    from blueprints.planning_api_profiles import api_get_profile, api_update_profile, api_delete_profile
    
    if request.method == 'GET':
        return api_get_profile(profile_id)
    elif request.method == 'PUT':
        return api_update_profile(profile_id)
    elif request.method == 'DELETE':
        return api_delete_profile(profile_id)

@bp.route('/api/calendar/schedule/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_schedule(year, week_number):
    """Get schedule for a specific year and week"""
    return schedule_api_func(year, week_number)


@bp.route('/api/calendar/week-controls/<int:year>/<int:week_number>', methods=['GET', 'PUT'])
def api_week_controls(year, week_number):
    """W2-FIX-9.2: Get or set week-level automation controls (automation_enabled, locked)"""
    from utils.calendar.week_controls import get_week_controls, set_week_controls
    if request.method == 'GET':
        controls = get_week_controls(year, week_number)
        return jsonify({'success': True, 'year': year, 'week_number': week_number, **controls})
    # PUT
    data = request.get_json() or {}
    automation_enabled = data.get('automation_enabled')
    locked = data.get('locked')
    if automation_enabled is None and locked is None:
        return jsonify({'success': False, 'error': 'Provide automation_enabled and/or locked'}), 400
    if automation_enabled is not None and not isinstance(automation_enabled, bool):
        return jsonify({'success': False, 'error': 'automation_enabled must be boolean'}), 400
    if locked is not None and not isinstance(locked, bool):
        return jsonify({'success': False, 'error': 'locked must be boolean'}), 400
    ok = set_week_controls(year, week_number, automation_enabled=automation_enabled, locked=locked)
    if not ok:
        return jsonify({'success': False, 'error': 'Failed to update controls'}), 500
    controls = get_week_controls(year, week_number)
    return jsonify({'success': True, 'year': year, 'week_number': week_number, **controls})


@bp.route('/api/calendar/scheduling/all', methods=['GET'])
def api_calendar_scheduling_all():
    """Get all scheduling data for 52 weeks (cached)"""
    return scheduling_all_api_func()

# OLD ROUTES REMOVED - Use /planning/api/calendar/list/reorder instead
# @bp.route('/api/calendar/reorder', methods=['POST'])
# def api_calendar_reorder():
#     """Reorder items in sequential lists"""
#     return reorder_item_api_func()

# @bp.route('/api/calendar/position-for-week', methods=['GET'])
# def api_calendar_position_for_week():
#     """Calculate what position should appear in a specific week"""
#     return position_for_week_api_func()

# The reassign blueprint will be registered in unified_app.py

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

@bp.route('/api/calendar/week-items/<int:week_item_id>', methods=['PATCH'])
def api_update_calendar_week_item_route(week_item_id):
    """W2-OPS-6: Update calendar_week_items placement (weekday, scheduled_date, is_active)"""
    return update_calendar_week_item_api_func(week_item_id)


@bp.route('/api/calendar/week-items/<int:week_item_id>/primary', methods=['PATCH'])
def api_set_calendar_week_item_primary_route(week_item_id):
    """Set a single idea row as primary for its week."""
    return set_calendar_week_item_primary_api_func(week_item_id)

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

@bp.route('/api/posts/<int:post_id>/expanded-idea-prompt-selection', methods=['GET'])
def api_get_expanded_idea_prompt_selection(post_id):
    """Get available prompt options and current selection for expanded idea generation"""
    from blueprints.planning_api_post_specific import api_get_expanded_idea_prompt_selection as selection_func
    return selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/expanded-idea-prompt-selection', methods=['POST'])
def api_set_expanded_idea_prompt_selection(post_id):
    """Set the selected prompt for expanded idea generation"""
    from blueprints.planning_api_post_specific import api_set_expanded_idea_prompt_selection as set_selection_func
    return set_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/expanded-idea-prompt', methods=['GET'])
def api_get_expanded_idea_prompt(post_id):
    """Get the expanded idea prompt for a post, optionally filtered by prompt_name"""
    from blueprints.planning_api_post_specific import api_get_expanded_idea_prompt as prompt_func
    return prompt_func(post_id)

@bp.route('/api/posts/<int:post_id>/brainstorm-prompt-selection', methods=['GET'])
def api_get_brainstorm_prompt_selection(post_id):
    """Get available prompt options and current selection for topic brainstorming"""
    from blueprints.planning_api_post_specific import api_get_brainstorm_prompt_selection as selection_func
    return selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/brainstorm-prompt-selection', methods=['POST'])
def api_set_brainstorm_prompt_selection(post_id):
    """Set the selected prompt for topic brainstorming"""
    from blueprints.planning_api_post_specific import api_set_brainstorm_prompt_selection as set_selection_func
    return set_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/brainstorm-prompt', methods=['GET'])
def api_get_brainstorm_prompt(post_id):
    """Get the brainstorm prompt for a post, optionally filtered by prompt_name"""
    from blueprints.planning_api_post_specific import api_get_brainstorm_prompt as prompt_func
    return prompt_func(post_id)

@bp.route('/api/posts/<int:post_id>/brainstorm-prompt', methods=['PUT'])
def api_update_brainstorm_prompt(post_id):
    """Update the brainstorm prompt for a post"""
    from blueprints.planning_api_post_specific import api_update_brainstorm_prompt as update_func
    return update_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-structure-prompt-selection', methods=['GET'])
def api_get_section_structure_prompt_selection(post_id):
    """Get available prompt options and current selection for section structure design"""
    from blueprints.planning_api_post_specific import api_get_section_structure_prompt_selection as selection_func
    return selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-structure-prompt-selection', methods=['POST'])
def api_set_section_structure_prompt_selection(post_id):
    """Set the selected prompt for section structure design"""
    from blueprints.planning_api_post_specific import api_set_section_structure_prompt_selection as set_selection_func
    return set_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-structure-prompt', methods=['GET'])
def api_get_section_structure_prompt(post_id):
    """Get the section structure prompt for a post, optionally filtered by prompt_name"""
    from blueprints.planning_api_post_specific import api_get_section_structure_prompt as prompt_func
    return prompt_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-structure-prompt', methods=['PUT'])
def api_update_section_structure_prompt(post_id):
    """Update the section structure prompt for a post"""
    from blueprints.planning_api_post_specific import api_update_section_structure_prompt as update_func
    return update_func(post_id)

@bp.route('/api/posts/<int:post_id>/topic-allocation-prompt-selection', methods=['GET'])
def api_get_topic_allocation_prompt_selection(post_id):
    """Get available prompt options and current selection for topic allocation"""
    from blueprints.planning_api_post_specific import api_get_topic_allocation_prompt_selection as selection_func
    return selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/topic-allocation-prompt-selection', methods=['POST'])
def api_set_topic_allocation_prompt_selection(post_id):
    """Set the selected prompt for topic allocation"""
    from blueprints.planning_api_post_specific import api_set_topic_allocation_prompt_selection as set_selection_func
    return set_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/topic-allocation-prompt', methods=['GET'])
def api_get_topic_allocation_prompt(post_id):
    """Get the topic allocation prompt for a post, optionally filtered by prompt_name"""
    from blueprints.planning_api_post_specific import api_get_topic_allocation_prompt as prompt_func
    return prompt_func(post_id)

@bp.route('/api/posts/<int:post_id>/topic-allocation-prompt', methods=['PUT'])
def api_update_topic_allocation_prompt(post_id):
    """Update the topic allocation prompt for a post"""
    from blueprints.planning_api_post_specific import api_update_topic_allocation_prompt as update_func
    return update_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-titling-prompt-selection', methods=['GET'])
def api_get_section_titling_prompt_selection(post_id):
    """Get available prompt options and current selection for section titling"""
    from blueprints.planning_api_post_specific import api_get_section_titling_prompt_selection as selection_func
    return selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-titling-prompt-selection', methods=['POST'])
def api_set_section_titling_prompt_selection(post_id):
    """Set the selected prompt for section titling"""
    from blueprints.planning_api_post_specific import api_set_section_titling_prompt_selection as set_selection_func
    return set_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-titling-prompt', methods=['GET'])
def api_get_section_titling_prompt(post_id):
    """Get the section titling prompt for a post, optionally filtered by prompt_name"""
    from blueprints.planning_api_post_specific import api_get_section_titling_prompt as prompt_func
    return prompt_func(post_id)

@bp.route('/api/posts/<int:post_id>/section-titling-prompt', methods=['PUT'])
def api_update_section_titling_prompt(post_id):
    """Update the section titling prompt for a post"""
    from blueprints.planning_api_post_specific import api_update_section_titling_prompt as update_func
    return update_func(post_id)

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

# ============================================================================
# PROFILE API ENDPOINTS (imported from planning_api_profile.py)
# ============================================================================

@bp.route('/api/profile/section-structure', methods=['POST'])
def api_profile_section_structure():
    """Generate section structure for product profile posts"""
    return profile_section_structure_func()

@bp.route('/api/posts/<int:post_id>/profile-section-structure-prompt-selection', methods=['GET'])
def api_get_profile_section_structure_prompt_selection(post_id):
    """Get available prompt options and current selection for profile section structure design"""
    return profile_prompt_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/profile-section-structure-prompt-selection', methods=['POST'])
def api_set_profile_section_structure_prompt_selection(post_id):
    """Set the selected prompt for profile section structure design"""
    return profile_set_prompt_selection_func(post_id)

@bp.route('/api/posts/<int:post_id>/profile-section-structure-prompt', methods=['GET'])
def api_get_profile_section_structure_prompt(post_id):
    """Get the profile section structure prompt for a post"""
    return profile_get_prompt_func(post_id)

@bp.route('/api/posts/<int:post_id>/profile-section-structure-prompt', methods=['PUT'])
def api_update_profile_section_structure_prompt(post_id):
    """Update the profile section structure prompt for a post"""
    return profile_update_prompt_func(post_id)

@bp.route('/api/profile/topic-allocation', methods=['POST'])
def api_profile_topic_allocation():
    """Populate sections with raw data from product sources for profile posts"""
    return profile_topic_allocation_func()

@bp.route('/api/profile/sections/title', methods=['POST'])
def api_profile_sections_title():
    """Generate contextual section titles for profile posts"""
    return profile_sections_title_func()

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
