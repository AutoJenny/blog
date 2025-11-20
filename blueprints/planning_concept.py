"""
Planning Concept Module

Contains concept development route functions extracted from planning.py
"""

from flask import render_template, request
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

def _resolve_post_and_get_week_context(post_id):
    """Helper to resolve post and get week context from URL"""
    from utils.week_post_resolver import resolve_post_for_week
    
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    resolved_post_id = post_id
    if year and week:
        resolved = resolve_post_for_week(year, week)
        if resolved:
            resolved_post_id = resolved
    
    return resolved_post_id, year, week

def planning_concept_brainstorm(post_id):
    """Brainstorm page"""
    from flask import redirect, url_for
    from utils.taxonomy_helpers import get_post_type
    
    # Check post type - redirect recipe posts away from Planning stages
    # Profile posts now have Planning stage (like themed posts)
    post_type = get_post_type(post_id)
    if post_type == 'recipe':
        return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
    
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/concept/brainstorm.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        # Get content type name for category banner
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/concept/brainstorm.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_concept_section_structure(post_id):
    """Section structure page"""
    from utils.taxonomy_helpers import get_post_type
    
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/concept/section_structure.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        # Get content type name for category banner
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/concept/section_structure.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_concept_topic_allocation(post_id):
    """Topic allocation page"""
    from utils.taxonomy_helpers import get_post_type
    
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/concept/topic_allocation.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        # Get content type name for category banner
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/concept/topic_allocation.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_concept_titling(post_id):
    """Titling page"""
    from utils.taxonomy_helpers import get_post_type
    
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/concept/titling.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        # Get content type name for category banner
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/concept/titling.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_concept_outline(post_id):
    """Outline page"""
    from utils.taxonomy_helpers import get_post_type
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/concept/outline.html', 
                                  post_id=resolved_post_id, year=year, week=week, 
                                  post_type=post_type, blueprint_name='planning',
                                  error='Post not found')
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/concept/outline.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_research_sources(post_id):
    """Research sources page"""
    from utils.taxonomy_helpers import get_post_type
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/research/sources.html', 
                                  post_id=resolved_post_id, year=year, week=week,
                                  post_type=post_type, blueprint_name='planning',
                                  error='Post not found')
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/research/sources.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_research_visuals(post_id):
    """Research visuals page"""
    from utils.taxonomy_helpers import get_post_type
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/research/visuals.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/research/visuals.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_research_prompts(post_id):
    """Research prompts page"""
    from utils.taxonomy_helpers import get_post_type
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/research/prompts.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/research/prompts.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_research_verification(post_id):
    """Research verification page"""
    from utils.taxonomy_helpers import get_post_type
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    post_type = get_post_type(resolved_post_id)
    
    # Get post data with all required fields for header
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (resolved_post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/research/verification.html', 
                                  post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                                  post_type=post_type,
                                  error='Post not found')
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/research/verification.html', 
                          post_id=resolved_post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week=week,
                          blueprint_name='planning')