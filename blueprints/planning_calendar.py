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
        from utils.taxonomy_helpers import get_post_type
        
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        
        # Get post data with all required fields for header
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
                                      post_id=post_id, year=year, week_number=week_number,
                                      blueprint_name='planning',
                                      error='Post not found')
            
            # Get post_type for header
            post_type = get_post_type(post_id)
            
            # Get content_type_name for header
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
    except Exception as e:
        logger.error(f"Error in planning_calendar_view: {e}")
        return render_template('planning/calendar/view.html', 
                              post_id=post_id, year=2025, week_number=1,
                              blueprint_name='planning',
                              error=str(e))

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
        from flask import request
        from utils.taxonomy_helpers import get_post_type
        from utils.week_post_resolver import resolve_post_for_week
        
        # Get year/week from URL params
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        
        # Default to current week if not provided
        if not url_year or not url_week:
            year = datetime.now().year
            week_number = datetime.now().isocalendar()[1]
        else:
            year = url_year
            week_number = url_week
        
        # Resolve post for week if needed
        target_post_id = post_id
        if url_year and url_week:
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
        
        # Get post data with all required fields for header
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()
            
            if not post:
                return render_template('planning/calendar/ideas.html', 
                                      post_id=post_id, year=year, week_number=week_number,
                                      blueprint_name='planning',
                                      mode='post-based',
                                      error='Post not found')
            
            # Get post_type for header
            post_type = get_post_type(target_post_id)
            
            # Get content_type_name for header
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (target_post_id,))
            result = cursor.fetchone()
            content_type_name = result.get('content_type_name') if result else None
        
        return render_template('planning/calendar/ideas.html', 
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
                              blueprint_name='planning',
                              mode='post-based')
    except Exception as e:
        logger.error(f"Error in planning_calendar_ideas: {e}")
        year = datetime.now().year
        week_number = datetime.now().isocalendar()[1]
        return render_template('planning/calendar/ideas.html', 
                              post_id=post_id, year=year, week_number=week_number,
                              blueprint_name='planning',
                              mode='post-based',
                              error=str(e))

def planning_calendar_taxonomy(post_id, year=None, week=None):
    """Taxonomy assignment page"""
    from flask import redirect, url_for, request
    from utils.taxonomy_helpers import get_post_type
    from datetime import datetime
    
    # Get year/week from parameters or URL, or use current week
    if not year or not week:
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
    
    if not year or not week:
        now = datetime.now()
        year = now.year
        week = now.isocalendar()[1]
    
    # Check post type - redirect recipe posts away from Planning stages
    # Profile posts now have Planning stage (like themed posts)
    post_type = get_post_type(post_id)
    if post_type == 'recipe':
        return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
    
    try:
        # Get post data to check if it exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT id, title FROM post WHERE id = %s", (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return render_template('planning/calendar/taxonomy.html', 
                                      post_id=post_id,
                                      post_type=post_type,
                                      year=year,
                                      week_number=week,
                                      blueprint_name='planning',
                                      error='Post not found')
            
            # Auto-assign taxonomy for profile posts if not already assigned
            if post_type == 'profile':
                cursor.execute("""
                    SELECT content_type_id, theme_id, format_id
                    FROM post
                    WHERE id = %s
                """, (post_id,))
                post_taxonomy = cursor.fetchone()
                
                # If taxonomy not assigned, auto-assign "Products & Producers"
                if not post_taxonomy.get('content_type_id'):
                    # Get Products & Producers content type
                    cursor.execute("""
                        SELECT id, tier_id, parent_id
                        FROM taxonomy_item
                        WHERE slug = 'products-producers'
                    """)
                    content_type_result = cursor.fetchone()
                    
                    if content_type_result:
                        content_type_id = content_type_result['id']
                        theme_id = content_type_result['parent_id']  # Get parent theme
                        
                        # Get default format (Article)
                        cursor.execute("""
                            SELECT id FROM taxonomy_item WHERE slug = 'article'
                        """)
                        format_result = cursor.fetchone()
                        format_id = format_result['id'] if format_result else None
                        
                        # Update post with auto-assigned taxonomy
                        cursor.execute("""
                            UPDATE post
                            SET theme_id = %s, content_type_id = %s, format_id = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (theme_id, content_type_id, format_id, post_id))
                        logger.info(f"Auto-assigned taxonomy to profile post {post_id}: theme={theme_id}, content_type={content_type_id}, format={format_id}")
            
            # Get full post data for header
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            # Get content_type_name for header
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            content_type_name = result.get('content_type_name') if result else None
            
            return render_template('planning/calendar/taxonomy.html', 
                                  post_id=post_id,
                                  post=post,
                                  post_type=post_type,
                                  post_title=post.get('title'),
                                  post_status=post.get('status'),
                                  post_created=post.get('created_at'),
                                  post_updated=post.get('updated_at'),
                                  content_type_name=content_type_name,
                                  year=year,
                                  week_number=week,
                                  blueprint_name='planning')
    except Exception as e:
        logger.error(f"Error in planning_calendar_taxonomy: {e}")
        return render_template('planning/calendar/taxonomy.html', 
                              post_id=post_id,
                              post_type=post_type,
                              year=year,
                              week_number=week,
                              blueprint_name='planning',
                              error=str(e))