"""
Planning Calendar Module - Clean Version

Contains the original calendar function with correct template reference
"""

from flask import render_template
import logging

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
