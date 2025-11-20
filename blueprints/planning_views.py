"""
Planning Views Module

Contains user-facing page route functions extracted from planning.py
"""

from flask import render_template
import logging

logger = logging.getLogger(__name__)

def planning_dashboard():
    """Planning dashboard"""
    return render_template('planning/dashboard.html', blueprint_name='planning')

def planning_post_overview(post_id):
    """Post overview page"""
    from flask import request
    from utils.week_post_resolver import resolve_post_for_week
    
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    resolved_post_id = post_id
    if year and week:
        resolved = resolve_post_for_week(year, week)
        if resolved:
            resolved_post_id = resolved
    
    return render_template('planning/posts/overview.html', 
                          post_id=resolved_post_id, year=year, week=week, blueprint_name='planning')

def planning_concept(post_id):
    """Concept development page - redirects to Idea Generation (first planning substage)"""
    from flask import redirect, url_for, request
    from utils.taxonomy_helpers import get_post_type
    
    # Check post type - redirect recipe posts away from Planning stages
    # Profile posts now have Planning stage (like themed posts)
    post_type = get_post_type(post_id)
    if post_type == 'recipe':
        return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
    
    # CRITICAL: Preserve year/week query parameters from URL (canonical source)
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    url = url_for('planning.planning_calendar_ideas', post_id=post_id)
    if year and week:
        url += f'?year={year}&week={week}'
    return redirect(url)

def planning_calendar(post_id):
    """Calendar page"""
    from flask import request
    from utils.week_post_resolver import resolve_post_for_week
    
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    resolved_post_id = post_id
    if year and week:
        resolved = resolve_post_for_week(year, week)
        if resolved:
            resolved_post_id = resolved
    
    return render_template('planning/calendar/index.html', 
                          post_id=resolved_post_id, year=year, week=week, blueprint_name='planning')

def categories_manage():
    """Manage calendar categories"""
    return render_template('planning/categories/manage.html', blueprint_name='planning')

def planning_research(post_id):
    """Research page"""
    from flask import request, redirect, url_for
    from utils.week_post_resolver import resolve_post_for_week
    from utils.taxonomy_helpers import get_post_type
    
    # Check post type - redirect recipe posts away from Planning stages
    # Profile posts now have Research stage (like themed posts)
    post_type = get_post_type(post_id)
    if post_type == 'recipe':
        return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
    
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    resolved_post_id = post_id
    if year and week:
        resolved = resolve_post_for_week(year, week)
        if resolved:
            resolved_post_id = resolved
    
    return render_template('planning/research/index.html', 
                          post_id=resolved_post_id, year=year, week=week, 
                          post_type=post_type,
                          blueprint_name='planning')

# ARCHIVED: planning_old_interface function removed - old interface system has been archived
# See ARCHIVED_OLD_WORKFLOW/ for archived code