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

logger = logging.getLogger(__name__)

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
                               blueprint_name='planning')
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
                               blueprint_name='planning')

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
                       pd.refined_topics, pd.expanded_idea
                FROM posts p
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
                SELECT id, section_order, section_heading, section_description, 
                       ideas_to_include, facts_to_include, highlighting,
                       image_concepts, image_prompts, image_meta_descriptions,
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
                WHERE prompt_type = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_type,))
            
            result = cursor.fetchone()
            if result:
                return jsonify({
                    'success': True,
                    'prompt_text': result['prompt_text'],
                    'system_prompt': result['system_prompt'],
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                    'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                })
            else:
                return jsonify({'error': 'Prompt not found'}), 404
                
    except Exception as e:
        logger.error(f"Error fetching prompt: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# IMPORT REMAINING FUNCTIONS FROM ORIGINAL FILE
# ============================================================================

# For now, we'll import the rest from the original file
# This allows us to gradually migrate functions one by one

# Import all other functions from the original file
import sys
import importlib.util

# Load the original planning module
spec = importlib.util.spec_from_file_location("planning_original", "blueprints/planning_original_backup.py")
planning_original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planning_original)

# Add all other functions to this module's namespace
for name in dir(planning_original):
    if not name.startswith('_') and callable(getattr(planning_original, name)):
        if name not in globals():
            globals()[name] = getattr(planning_original, name)

# Export the main blueprint
__all__ = ['bp']
