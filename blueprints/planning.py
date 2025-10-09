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
from blueprints.planning_views import planning_dashboard as dashboard_func, planning_post_overview as post_overview_func, planning_concept as concept_func, categories_manage as categories_func, planning_research as research_func, planning_old_interface as old_interface_func
from blueprints.planning_calendar_clean import planning_calendar as calendar_func, planning_calendar_view as calendar_view_func, planning_calendar_ideas as ideas_func
from blueprints.planning_concept import planning_concept_brainstorm as brainstorm_func, planning_concept_section_structure as section_structure_func, planning_concept_topic_allocation as topic_allocation_func, planning_concept_titling as titling_func, planning_concept_outline as outline_func, planning_research_sources as sources_func, planning_research_visuals as visuals_func, planning_research_prompts as prompts_func, planning_research_verification as verification_func
from blueprints.planning_api_calendar import api_calendar_categories as categories_api_func, api_calendar_weeks as weeks_api_func, api_calendar_ideas as ideas_api_func, api_calendar_events as events_api_func, api_calendar_schedule as schedule_api_func, api_calendar_ideas_for_week as ideas_week_api_func
from blueprints.planning_api_posts import api_posts as posts_api_func
from blueprints.planning_api_post_specific import api_posts_expanded_idea as expanded_idea_api_func, api_posts_idea_seed as idea_seed_api_func, api_check_topic as check_topic_api_func, api_create_new_post as create_new_api_func, api_posts_idea_scope as idea_scope_api_func
from blueprints.planning_api_brainstorm import api_generate_brainstorm_topics as brainstorm_topics_api_func
from blueprints.planning_api_prompts import api_get_prompt as prompt_api_func
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

@bp.route('/posts/<int:post_id>/old-interface')
def planning_old_interface(post_id):
    """Planning old interface"""
    return old_interface_func(post_id)

# ============================================================================
# CALENDAR FUNCTIONS (imported from planning_calendar.py)
# ============================================================================

@bp.route('/posts/<int:post_id>/calendar/view')
def planning_calendar_view(post_id):
    """Calendar view page"""
    return calendar_view_func(post_id)

@bp.route('/calendar/ideas/week/<int:week_number>')
def planning_calendar_ideas_week(week_number):
    """Week-based idea generation"""
    return ideas_week_func(week_number)

@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Calendar ideas page"""
    return ideas_func(post_id)

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

@bp.route('/api/calendar/ideas/<int:week_number>', methods=['GET'])
def api_calendar_ideas(week_number):
    """Get perpetual ideas for a specific week number"""
    return ideas_api_func(week_number)

@bp.route('/api/calendar/ideas/week/<int:week_number>', methods=['GET'])
def api_calendar_ideas_for_week(week_number):
    """Get ideas for a specific week"""
    return ideas_week_api_func(week_number)

@bp.route('/api/calendar/events/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_events(year, week_number):
    """Get events for a specific year and week"""
    return events_api_func(year, week_number)

@bp.route('/api/calendar/schedule/<int:year>/<int:week_number>', methods=['GET'])
def api_calendar_schedule(year, week_number):
    """Get schedule for a specific year and week"""
    return schedule_api_func(year, week_number)

@bp.route('/api/posts/<int:post_id>', methods=['GET'])
def api_posts(post_id):
    """Get post data for planning"""
    return posts_api_func(post_id)

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
# REMAINING FUNCTIONS (still need to be moved to modules)
# ============================================================================

# TODO: Move remaining API functions to planning_api.py
# TODO: Move remaining functions to appropriate modules

# Export the main blueprint
__all__ = ['bp']
