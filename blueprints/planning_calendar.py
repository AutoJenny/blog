"""
Planning Calendar Module

Contains calendar-specific route functions extracted from planning.py
"""

from flask import render_template
from config.database import db_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def planning_calendar_view(post_id):
    """Calendar view page"""
    try:
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        return render_template('planning/calendar/view.html', 
                              post_id=post_id, year=year, week_number=week_number,
                              blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_view: {e}")
        return render_template('planning/calendar/view.html', 
                              post_id=post_id, year=2025, week_number=1,
                              blueprint_name='planning')

def planning_calendar_ideas_week(week_number):
    """Week-based idea generation - creates new posts as needed"""
    try:
        year = datetime.now().year
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
        year = datetime.now().year
        return render_template('planning/calendar/ideas_week.html', 
                              week_number=week_number,
                              year=year,
                              ideas=[],
                              blueprint_name='planning')

def planning_calendar_ideas(post_id):
    """Calendar ideas page (post-based)"""
    try:
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        
        # Get post data to check if it exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            post_exists = cursor.fetchone()
            
        if not post_exists:
            return render_template('planning/calendar/ideas.html', 
                                  post_id=post_id, year=year, week_number=week_number,
                                  blueprint_name='planning',
                                  mode='post-based',
                                  error='Post not found')
        
        return render_template('planning/calendar/ideas.html', 
                              post_id=post_id, year=year, week_number=week_number,
                              blueprint_name='planning',
                              mode='post-based') # Explicitly mark as post-based mode
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        return render_template('planning/calendar/ideas.html', 
                              post_id=post_id, year=year, week_number=week_number,
                              blueprint_name='planning',
                              mode='post-based')

def planning_calendar_taxonomy(post_id):
    """Taxonomy assignment page"""
    try:
        # Get post data to check if it exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT id, title FROM post WHERE id = %s", (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return render_template('planning/calendar/taxonomy.html', 
                                      post_id=post_id,
                                      blueprint_name='planning',
                                      error='Post not found')
            
            return render_template('planning/calendar/taxonomy.html', 
                                  post_id=post_id,
                                  post_title=post['title'],
                                  blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_taxonomy: {e}")
        return render_template('planning/calendar/taxonomy.html', 
                              post_id=post_id,
                              blueprint_name='planning',
                              error=str(e))