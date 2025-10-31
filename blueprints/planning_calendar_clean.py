"""
Planning Calendar Module - Clean Version

Contains the original calendar function with correct template reference
"""

from flask import render_template, request
from config.database import db_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def planning_calendar(post_id):
    """Content Calendar main stage"""
    return render_template('planning/calendar.html', 
                          post_id=post_id,
                          blueprint_name='planning')

def planning_calendar_view(post_id):
    """Calendar View sub-stage"""
    return render_template('planning/calendar/view.html',
                          post_id=post_id,
                          blueprint_name='planning')

def planning_calendar_week_view(post_id):
    """Calendar Week View sub-stage (week-per-view)"""
    return render_template('planning/calendar/week_view.html',
                          post_id=post_id,
                          blueprint_name='planning')

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
                # Default to current week if no schedule found
                from datetime import datetime
                year = datetime.now().year
                week_number = datetime.now().isocalendar()[1]
            
            return render_template('planning/calendar/ideas.html', 
                                   post_id=post_id,
                                   year=year,
                                   week_number=week_number,
                                   blueprint_name='planning',
                                   mode='post-based')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        from datetime import datetime
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        return render_template('planning/calendar/ideas.html', 
                               post_id=post_id,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based')

def planning_calendar_ideas_week(week_number):
    """Week-based idea generation - creates new posts as needed"""
    try:
        # Get optional post_id from query parameter for context (from one-click blog selection)
        post_id = request.args.get('post_id', type=int, default=0)
        
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
                              post_id=post_id,
                              blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas_week: {e}")
        post_id = request.args.get('post_id', type=int, default=0)
        year = datetime.now().year
        return render_template('planning/calendar/ideas_week.html', 
                              week_number=week_number,
                              year=year,
                              ideas=[],
                              post_id=post_id,
                              blueprint_name='planning')
