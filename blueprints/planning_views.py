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
    return render_template('planning/posts/overview.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_concept(post_id):
    """Concept development page - redirects to Idea Generation (first planning substage)"""
    from flask import redirect, url_for
    return redirect(url_for('planning.planning_calendar_ideas', post_id=post_id))

def planning_calendar(post_id):
    """Calendar page"""
    return render_template('planning/calendar/index.html', 
                          post_id=post_id, blueprint_name='planning')

def categories_manage():
    """Manage calendar categories"""
    return render_template('planning/categories/manage.html', blueprint_name='planning')

def planning_research(post_id):
    """Research page"""
    return render_template('planning/research/index.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_old_interface(post_id):
    """Old interface page"""
    return render_template('planning/old_interface.html', 
                          post_id=post_id, blueprint_name='planning')