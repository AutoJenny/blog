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
    from utils.taxonomy_helpers import get_post_type
    
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/calendar.html', 
                                  post_id=post_id,
                                  blueprint_name='planning',
                                  error='Post not found')
        
        post_type = get_post_type(post_id)
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/calendar.html', 
                          post_id=post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          blueprint_name='planning')

def planning_calendar_view(post_id):
    """Calendar View sub-stage"""
    from utils.taxonomy_helpers import get_post_type
    from datetime import datetime
    
    year = datetime.now().year
    week_number = datetime.now().isocalendar()[1]
    
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                   p.content_type_id
            FROM post p
            WHERE p.id = %s
        """, (post_id,))
        post = cursor.fetchone()
        
        if not post:
            return render_template('planning/calendar/view.html',
                                  post_id=post_id,
                                  year=year,
                                  week_number=week_number,
                                  blueprint_name='planning',
                                  error='Post not found')
        
        post_type = get_post_type(post_id)
        
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (post_id,))
        result = cursor.fetchone()
        content_type_name = result.get('content_type_name') if result else None
    
    return render_template('planning/calendar/view.html',
                          post_id=post_id,
                          post=post,
                          post_type=post_type,
                          post_title=post.get('title'),
                          post_status=post.get('status'),
                          post_created=post.get('created_at'),
                          post_updated=post.get('updated_at'),
                          content_type_name=content_type_name,
                          year=year,
                          week_number=week_number,
                          blueprint_name='planning')

def planning_calendar_week_view(post_id):
    """Calendar Week View sub-stage (week-per-view)
    
    IMPORTANT: Calendar week view is WEEK-CENTRIC, not post-centric.
    The post_id is only used for navigation through pipeline stages.
    We do NOT treat any post as "active" in calendar view - it's about the week.
    """
    from flask import request
    from utils.taxonomy_helpers import get_post_type
    
    # Read week context from URL (required for week view)
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # Get post type for the original post_id first (for UI purposes only)
    original_post_type = get_post_type(post_id)
    
    # CRITICAL: Always use post_id from URL - it's the definitive identifier
    # Week parameters are context only, not for changing post_id
    # This applies to ALL post types (themed, recipe, profile, generated)
    resolved_post_id = post_id
    
    # CRITICAL: Calendar week view is WEEK-CENTRIC, not post-centric
    # We do NOT pass any post-related data to the template
    # post_id is ONLY used for navigation through pipeline stages (in URLs)
    # No post_type, no post data, nothing - just week context
    
    # Verify post exists (for error handling)
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT id FROM post WHERE id = %s", (post_id,))
        if not cursor.fetchone():
            return render_template('planning/calendar/week_view.html',
                                  post_id=post_id,  # Use original for navigation
                                  year=year,
                                  week=week,
                                  blueprint_name='planning',
                                  error='Post not found')
    
    # Render template with NO post data - only post_id for navigation
    return render_template('planning/calendar/week_view.html',
                          post_id=post_id,  # Only for navigation links
                          year=year,
                          week=week,
                          blueprint_name='planning')

def planning_calendar_scheduling(post_id):
    """Calendar Scheduling View - Year overview of weeks with Themes, Recipes, Profiles"""
    from flask import request
    from datetime import datetime, date
    
    # Get current week to start from
    now = datetime.now()
    current_year = now.year
    current_week = now.isocalendar()[1]
    
    # Simple render - no post verification needed for scheduling view
    return render_template('planning/calendar/scheduling.html',
                          post_id=post_id,
                          current_year=current_year,
                          current_week=current_week,
                          blueprint_name='planning')

def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    try:
        from flask import request, redirect, url_for
        from datetime import datetime
        from utils.taxonomy_helpers import get_post_type
        
        # Check post type - redirect recipe posts away from Planning stages
        # Profile posts now have Planning stage (like themed posts)
        post_type = get_post_type(post_id)
        if post_type == 'recipe':
            # Redirect recipe posts to authoring (drafting) stage
            return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
        elif post_type == 'generated':
            # Redirect generated posts to taxonomy (they start there, not at ideas)
            return redirect(url_for('planning.planning_calendar_taxonomy', post_id=post_id))
        
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
        
        # CRITICAL: Always use post_id from URL - it's the definitive identifier
        # Week parameters are context only, not for changing post_id
        target_post_id = post_id
        
        # Get post data with all required fields for header and body
        content_type_name = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.summary, p.subtitle, p.created_at, p.updated_at,
                       p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()

            if not post:
                return render_template('planning/calendar/ideas.html', 
                                      post_id=post_id,
                                      year=year,
                                      week_number=week_number,
                                      blueprint_name='planning',
                                      mode='post-based',
                                      error='Post not found')

            # Get content type name for category banner
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (target_post_id,))
            result = cursor.fetchone()
            if result:
                content_type_name = result.get('content_type_name')

        # Post-authoritative context: no week/theme overwrite; theme + subtitle from post only
        post_derived_theme = None
        post_context = None
        if post_type == 'themed' and post.get('id'):
            # Theme description: post.summary first, fallback post.subtitle (canonical mapping 7.1)
            theme_desc = (post.get('summary') or post.get('subtitle') or '')
            post_derived_theme = {
                'post_id': post_id,
                'theme_title': post.get('title'),
                'theme_description': theme_desc,
                'priority': 'normal',
            }
            post_context = {
                'post_id': post_id,
                'title': post.get('title') or '',
                'summary': post.get('summary') or '',
                'subtitle': post.get('subtitle') or '',
            }

        return render_template('planning/calendar/ideas.html', 
                               post_id=post_id,
                               post=post,
                               post_type=post_type,
                               post_title=post.get('title'),
                               post_status=post.get('status'),
                               post_created=post.get('created_at'),
                               post_updated=post.get('updated_at'),
                               content_type_name=content_type_name,
                               post_derived_theme=post_derived_theme,
                               post_context=post_context,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        from datetime import datetime
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        
        # Get post data with all required fields for header
        content_type_name = None
        post = None
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.summary, p.subtitle, p.created_at, p.updated_at,
                           p.content_type_id
                    FROM post p
                    WHERE p.id = %s
                """, (post_id,))
                post = cursor.fetchone()
                
                if post:
                    # Get content type name for category banner
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
        
        # Get post_type for header
        try:
            post_type = get_post_type(post_id)
        except:
            post_type = None

        post_derived_theme = None
        post_context = None
        if post and post_type == 'themed' and post.get('title'):
            theme_desc = (post.get('summary') or post.get('subtitle') or '')
            post_derived_theme = {
                'post_id': post_id,
                'theme_title': post.get('title'),
                'theme_description': theme_desc,
                'priority': 'normal',
            }
            post_context = {
                'post_id': post_id,
                'title': post.get('title') or '',
                'summary': post.get('summary') or '',
                'subtitle': post.get('subtitle') or '',
            }
        
        return render_template('planning/calendar/ideas.html',
                               post_id=post_id,
                               post=post,
                               post_type=post_type,
                               post_title=post.get('title') if post else None,
                               post_status=post.get('status') if post else None,
                               post_created=post.get('created_at') if post else None,
                               post_updated=post.get('updated_at') if post else None,
                               content_type_name=content_type_name,
                               post_derived_theme=post_derived_theme,
                               post_context=post_context,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based',
                               error=str(e) if 'e' in locals() else None)

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
