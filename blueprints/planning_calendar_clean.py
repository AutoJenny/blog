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
    from flask import request
    from utils.week_post_resolver import resolve_post_for_week
    from utils.taxonomy_helpers import get_post_type
    
    # Read week context from URL (required for week view)
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # Get post type for the original post_id first
    original_post_type = get_post_type(post_id)
    
    # Resolve post if week context provided
    # BUT: For recipe/profile posts, preserve the original post_id to maintain recipe/profile association
    resolved_post_id = post_id
    if year and week and original_post_type not in ('recipe', 'profile'):
        # Only resolve for themed posts - recipe/profile posts should keep their original post_id
        resolved = resolve_post_for_week(year, week)
        if resolved:
            resolved_post_id = resolved
    
    # Get post type for template (use original if recipe/profile, otherwise use resolved)
    post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(resolved_post_id)
    
    return render_template('planning/calendar/week_view.html',
                          post_id=resolved_post_id,
                          year=year,
                          week=week,
                          post_type=post_type,
                          blueprint_name='planning')

def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    try:
        from flask import request
        from datetime import datetime
        
        # SINGLE SOURCE OF TRUTH: Read ONLY from URL query parameters
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        
        # If URL params missing, default to current week (only for initial page load)
        if url_year and url_week:
            year = url_year
            week_number = url_week
        else:
            # Default to current week if URL doesn't have params
            now = datetime.now()
            year = now.year
            week_number = now.isocalendar()[1]
        
        # Get content type name for category banner
        content_type_name = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            if result:
                content_type_name = result.get('content_type_name')
        
        return render_template('planning/calendar/ideas.html', 
                               post_id=post_id,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based',
                               content_type_name=content_type_name)
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        from datetime import datetime
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        
        # Get content type name for category banner
        content_type_name = None
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT ti.display_name as content_type_name
                    FROM post p
                    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                    WHERE p.id = %s
                """, (post_id,))
                result = cursor.fetchone()
                if result:
                    content_type_name = result.get('content_type_name')
        except:
            pass
        
        return render_template('planning/calendar/ideas.html', 
                               post_id=post_id,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based',
                               content_type_name=content_type_name)

def planning_calendar_ideas_week(week_number):
    """Week-based idea generation - creates new posts as needed"""
    try:
        # Get optional post_id from query parameter for context (from one-click blog selection)
        post_id = request.args.get('post_id', type=int, default=0)
        
        # SINGLE SOURCE OF TRUTH: Read year from URL query parameters
        url_year = request.args.get('year', type=int)
        if url_year:
            year = url_year
        else:
            year = datetime.now().year
        
        with db_manager.get_cursor() as cursor:
            # Check if calendar_themes table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_themes'
                )
            """)
            has_themes_table = cursor.fetchone()['exists']
            
            # Load themes from calendar_themes table
            themes = []
            if has_themes_table:
                cursor.execute("""
                    SELECT id, week_number, theme_title, theme_description, seasonal_context, 
                           priority, tags, is_recurring
                    FROM calendar_themes 
                    WHERE week_number = %s
                    ORDER BY 
                        CASE priority 
                            WHEN 'mandatory' THEN 1 
                            WHEN 'random' THEN 2 
                            ELSE 3 
                        END,
                        id
                """, (week_number,))
                themes = cursor.fetchall()
            
            # Load ideas from calendar_ideas (excluding themes)
            cursor.execute("""
                SELECT id, idea_title, idea_description, seasonal_context, 
                       content_type, priority, tags, is_recurring
                FROM calendar_ideas 
                WHERE week_number = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM calendar_themes WHERE calendar_themes.id = calendar_ideas.id
                  )
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
                              themes=themes,
                              ideas=ideas,
                              post_id=post_id,
                              blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas_week: {e}")
        post_id = request.args.get('post_id', type=int, default=0)
        # SINGLE SOURCE OF TRUTH: Read year from URL query parameters
        url_year = request.args.get('year', type=int)
        if url_year:
            year = url_year
        else:
            year = datetime.now().year
        return render_template('planning/calendar/ideas_week.html', 
                              week_number=week_number,
                              year=year,
                              themes=[],
                              ideas=[],
                              post_id=post_id,
                              blueprint_name='planning')
