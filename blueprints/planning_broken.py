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
from blueprints.planning_views import planning_dashboard, planning_post_overview, planning_concept, planning_calendar, categories_manage, planning_research, planning_old_interface
from blueprints.planning_calendar import planning_calendar_view, planning_calendar_ideas_week, planning_calendar_ideas
from blueprints.planning_concept import planning_concept_brainstorm, planning_concept_section_structure, planning_concept_topic_allocation, planning_concept_titling, planning_concept_outline, planning_research_sources, planning_research_visuals, planning_research_prompts, planning_research_verification
from blueprints.planning_api import api_calendar_categories, api_get_prompt
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
    return planning_dashboard()

@bp.route('/posts/<int:post_id>')
def planning_post_overview(post_id):
    """Planning post overview"""
    return planning_post_overview(post_id)

@bp.route('/posts/<int:post_id>/concept')
def planning_concept(post_id):
    """Planning concept"""
    return planning_concept(post_id)

@bp.route('/posts/<int:post_id>/calendar')
def planning_calendar(post_id):
    """Planning calendar"""
    return planning_calendar(post_id)

@bp.route('/categories/manage')
def categories_manage():
    """Manage calendar categories"""
    return categories_manage()

@bp.route('/posts/<int:post_id>/research')
def planning_research(post_id):
    """Planning research"""
    return planning_research(post_id)

@bp.route('/posts/<int:post_id>/old-interface')
def planning_old_interface(post_id):
    """Planning old interface"""
    return planning_old_interface(post_id)

# ============================================================================
# CALENDAR FUNCTIONS (imported from planning_calendar.py)
# ============================================================================

@bp.route('/posts/<int:post_id>/calendar/view')
def planning_calendar_view(post_id):
    """Calendar view page"""
    return planning_calendar_view(post_id)

@bp.route('/calendar/ideas/week/<int:week_number>')
def planning_calendar_ideas_week(week_number):
    """Week-based idea generation"""
    return planning_calendar_ideas_week(week_number)

@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Calendar ideas page"""
    return planning_calendar_ideas(post_id)

# ============================================================================
# CONCEPT FUNCTIONS (imported from planning_concept.py)
# ============================================================================

@bp.route('/posts/<int:post_id>/concept/brainstorm')
def planning_concept_brainstorm(post_id):
    """Brainstorm page"""
    return planning_concept_brainstorm(post_id)

@bp.route('/posts/<int:post_id>/concept/section-structure')
def planning_concept_section_structure(post_id):
    """Section structure page"""
    return planning_concept_section_structure(post_id)

@bp.route('/posts/<int:post_id>/concept/topic-allocation')
def planning_concept_topic_allocation(post_id):
    """Topic allocation page"""
    return planning_concept_topic_allocation(post_id)

@bp.route('/posts/<int:post_id>/concept/titling')
def planning_concept_titling(post_id):
    """Titling page"""
    return planning_concept_titling(post_id)

@bp.route('/posts/<int:post_id>/concept/outline')
def planning_concept_outline(post_id):
    """Outline page"""
    return planning_concept_outline(post_id)

@bp.route('/posts/<int:post_id>/research/sources')
def planning_research_sources(post_id):
    """Research sources page"""
    return planning_research_sources(post_id)

@bp.route('/posts/<int:post_id>/research/visuals')
def planning_research_visuals(post_id):
    """Research visuals page"""
    return planning_research_visuals(post_id)

@bp.route('/posts/<int:post_id>/research/prompts')
def planning_research_prompts(post_id):
    """Research prompts page"""
    return planning_research_prompts(post_id)

@bp.route('/posts/<int:post_id>/research/verification')
def planning_research_verification(post_id):
    """Research verification page"""
    return planning_research_verification(post_id)

# ============================================================================
# API ENDPOINTS (imported from planning_api.py)
# ============================================================================

@bp.route('/api/calendar/categories', methods=['GET'])
def api_calendar_categories():
    """Get all calendar categories"""
    return api_calendar_categories()

@bp.route('/api/llm/prompts/<prompt_type>')
def api_get_prompt(prompt_type):
    """Get LLM prompt by type"""
    return api_get_prompt(prompt_type)

# ============================================================================
# REMAINING FUNCTIONS (still need to be moved to modules)
# ============================================================================

# TODO: Move remaining API functions to planning_api.py
# TODO: Move remaining functions to appropriate modules

# Export the main blueprint
__all__ = ['bp']
