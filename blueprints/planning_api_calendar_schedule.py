"""
Planning Calendar API - Schedule

Calendar schedule and selection endpoints
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging

logger = logging.getLogger(__name__)

def api_calendar_schedule(year, week_number):
    """Get schedule for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if new tables exist (for migration period)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_selection'
                ) as has_selection,
                EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts'
                ) as has_posts
            """)
            table_check = cursor.fetchone()
            has_new_tables = table_check['has_selection'] and table_check['has_posts']
            
            if has_new_tables:
                # Use new V2 architecture tables
                # Get selected theme
                cursor.execute("""
                    SELECT cws.selected_theme_id, cws.updated_at,
                           ct.theme_title, ct.theme_description
                    FROM calendar_week_selection cws
                    LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                    WHERE cws.year = %s AND cws.week_number = %s
                """, (year, week_number))
                theme_selection = cursor.fetchone()
                
                # Get all posts for this week
                cursor.execute("""
                    SELECT cwp.id, cwp.post_id, cwp.scheduled_date, cwp.created_at, cwp.updated_at,
                           p.title as post_title, p.status as post_status,
                           pd.idea_seed as post_idea_seed
                    FROM calendar_week_posts cwp
                    LEFT JOIN post p ON cwp.post_id = p.id
                    LEFT JOIN post_development pd ON cwp.post_id = pd.post_id
                    WHERE cwp.year = %s AND cwp.week_number = %s
                    ORDER BY cwp.scheduled_date NULLS LAST, cwp.created_at DESC
                """, (year, week_number))
                posts = cursor.fetchall()
                
                # Build unified schedule response
                schedule = []
                if theme_selection:
                    schedule.append({
                        'type': 'theme_selection',
                        'selected_theme_id': theme_selection['selected_theme_id'],
                        'theme_title': theme_selection['theme_title'],
                        'theme_description': theme_selection['theme_description'],
                        'updated_at': theme_selection['updated_at'].isoformat() if theme_selection['updated_at'] else None
                    })
                
                for post in posts:
                    schedule.append({
                        'type': 'post',
                        'id': post['id'],
                        'post_id': post['post_id'],
                        'post_title': post['post_title'],
                        'post_status': post['post_status'],
                        'post_idea_seed': post['post_idea_seed'],
                        'scheduled_date': post['scheduled_date'].isoformat() if post['scheduled_date'] else None,
                        'created_at': post['created_at'].isoformat() if post['created_at'] else None,
                        'updated_at': post['updated_at'].isoformat() if post['updated_at'] else None
                    })
                
                return jsonify({
                    'success': True,
                    'year': year,
                    'week_number': week_number,
                    'schedule': schedule,
                    'selected_theme_id': theme_selection['selected_theme_id'] if theme_selection else None
                })
            else:
                # Fallback to old calendar_schedule table during migration
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_themes'
                    )
                """)
                has_themes_table = cursor.fetchone()['exists']
                
                if has_themes_table:
                    cursor.execute("""
                        SELECT cs.id, cs.post_id, cs.idea_id, cs.theme_id, cs.year, cs.week_number, cs.scheduled_date,
                               cs.created_at, cs.updated_at,
                               p.title as post_title, p.status as post_status,
                               pd.idea_seed as post_idea_seed,
                               ct.theme_title, ct.id as calendar_theme_id
                        FROM calendar_schedule cs
                        LEFT JOIN post p ON cs.post_id = p.id
                        LEFT JOIN post_development pd ON p.id = pd.post_id
                        LEFT JOIN calendar_themes ct ON cs.theme_id = ct.id
                        WHERE cs.year = %s AND cs.week_number = %s
                        ORDER BY cs.scheduled_date
                    """, (year, week_number))
                else:
                    cursor.execute("""
                        SELECT cs.id, cs.post_id, cs.idea_id, cs.year, cs.week_number, cs.scheduled_date,
                               cs.created_at, cs.updated_at,
                               p.title as post_title, p.status as post_status,
                               pd.idea_seed as post_idea_seed
                        FROM calendar_schedule cs
                        LEFT JOIN post p ON cs.post_id = p.id
                        LEFT JOIN post_development pd ON p.id = pd.post_id
                        WHERE cs.year = %s AND cs.week_number = %s
                        ORDER BY cs.scheduled_date
                    """, (year, week_number))
                
                schedule = cursor.fetchall()
                
                return jsonify({
                    'success': True,
                    'year': year,
                    'week_number': week_number,
                    'schedule': schedule
                })
            
    except Exception as e:
        logger.error(f"Error fetching calendar schedule: {e}")
        return jsonify({'error': str(e)}), 500

def api_select_theme_idea():
    """Select a theme for a specific week/year using calendar_week_selection.
    DEPRECATED: idea_id support removed. Only theme_id is accepted.
    This allows themes to persist their selection before a post is created.
    """
    try:
        from flask import request
        data = _safe_parse_json_request() or {}
        theme_id = data.get('theme_id')
        idea_id = data.get('idea_id')  # Deprecated - kept for backwards compatibility warning
        year = data.get('year')
        week_number = data.get('week_number')
        
        # Require theme_id (idea_id deprecated)
        if not theme_id:
            if idea_id:
                # Reject idea_id - must use theme_id
                return jsonify({
                    'success': False, 
                    'error': 'idea_id is deprecated. Please use theme_id instead.'
                }), 400
            return jsonify({'success': False, 'error': 'theme_id is required'}), 400
        
        if not year or not week_number:
            return jsonify({'success': False, 'error': 'year and week_number are required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if new table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_selection'
                    )
                """)
                has_new_table = cursor.fetchone()['exists']
                
                if has_new_table:
                    # Verify theme exists
                    cursor.execute("SELECT id FROM calendar_themes WHERE id = %s", (theme_id,))
                    theme = cursor.fetchone()
                    if not theme:
                        return jsonify({'success': False, 'error': 'Theme not found'}), 404
                    
                    # UPSERT into calendar_week_selection (one theme per week, enforced by PRIMARY KEY)
                    cursor.execute("""
                        INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (year, week_number)
                        DO UPDATE SET selected_theme_id = EXCLUDED.selected_theme_id, updated_at = NOW()
                        RETURNING year, week_number, selected_theme_id, updated_at
                    """, (year, week_number, theme_id))
                    
                    result = cursor.fetchone()
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'year': result['year'],
                        'week_number': result['week_number'],
                        'selected_theme_id': result['selected_theme_id'],
                        'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                    })
                else:
                    # Fallback to old calendar_schedule table during migration
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'calendar_themes'
                        )
                    """)
                    has_themes_table = cursor.fetchone()['exists']
                    
                    if not has_themes_table:
                        return jsonify({'success': False, 'error': 'calendar_themes table not found'}), 500
                    
                    # Verify theme exists
                    cursor.execute("SELECT id FROM calendar_themes WHERE id = %s", (theme_id,))
                    theme = cursor.fetchone()
                    if not theme:
                        return jsonify({'success': False, 'error': 'Theme not found'}), 404
                    
                    # Check if there's already a schedule entry for this week/year
                    cursor.execute("""
                        SELECT id, theme_id, post_id 
                        FROM calendar_schedule 
                        WHERE year = %s AND week_number = %s
                        LIMIT 1
                    """, (year, week_number))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing schedule entry
                        cursor.execute("""
                            UPDATE calendar_schedule 
                            SET theme_id = %s, idea_id = NULL, updated_at = NOW()
                            WHERE id = %s
                            RETURNING id, theme_id, idea_id, post_id
                        """, (theme_id, existing['id']))
                    else:
                        # Create new schedule entry
                        cursor.execute("""
                            INSERT INTO calendar_schedule (year, week_number, theme_id, created_at, updated_at)
                            VALUES (%s, %s, %s, NOW(), NOW())
                            RETURNING id, theme_id, idea_id, post_id
                        """, (year, week_number, theme_id))
                    
                    result = cursor.fetchone()
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'schedule_id': result['id'],
                        'theme_id': result['theme_id'],
                        'post_id': result['post_id']
                    })
    except Exception as e:
        logger.error(f"Error selecting theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_calendar_idea_status(theme_id: int):
    """Resolve the post creation status for a theme in a specific week/year.
    DEPRECATED: Parameter name kept as idea_id for backwards compatibility, but only theme_id is supported.
    Uses new calendar_week_selection and calendar_week_posts tables.
    """
    try:
        year = request.args.get('year', type=int)
        week_number = request.args.get('week_number', type=int)
        if not year or not week_number:
            return jsonify({'success': False, 'error': 'year and week_number are required'}), 400

        with db_manager.get_cursor() as cursor:
            # Check if new tables exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_selection'
                ) as has_selection,
                EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts'
                ) as has_posts
            """)
            table_check = cursor.fetchone()
            has_new_tables = table_check['has_selection'] and table_check['has_posts']
            
            post = None
            
            if has_new_tables:
                # Use new V2 architecture
                # First check if the selected theme for this week matches the provided theme_id
                cursor.execute("""
                    SELECT selected_theme_id
                    FROM calendar_week_selection
                    WHERE year = %s AND week_number = %s
                """, (year, week_number))
                week_selection = cursor.fetchone()
                
                # Only proceed if the week's selected theme matches (or if no theme selected yet)
                if week_selection:
                    if week_selection['selected_theme_id'] != theme_id:
                        # Theme mismatch - week has different theme selected
                        return jsonify({
                            'success': True, 
                            'post': None,
                            'message': 'Week has different theme selected'
                        })
                
                # Get first post for this week (if multiple, return first created)
                cursor.execute("""
                    SELECT p.id, p.title, p.status, cwp.scheduled_date
                    FROM calendar_week_posts cwp
                    LEFT JOIN post p ON cwp.post_id = p.id
                    WHERE cwp.year = %s AND cwp.week_number = %s
                    ORDER BY cwp.created_at DESC
                    LIMIT 1
                """, (year, week_number))
                post = cursor.fetchone()
            else:
                # Fallback to old calendar_schedule table during migration
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_themes'
                    )
                """)
                has_themes_table = cursor.fetchone()['exists']
                
                if has_themes_table:
                    # Verify it's a theme
                    cursor.execute("SELECT id FROM calendar_themes WHERE id = %s", (theme_id,))
                    if cursor.fetchone():
                        # Handle theme: find post by theme_id in schedule
                        cursor.execute("""
                            SELECT p.id, p.title, p.status, cs.scheduled_date
                            FROM calendar_schedule cs
                            LEFT JOIN post p ON cs.post_id = p.id
                            WHERE cs.year = %s AND cs.week_number = %s AND cs.theme_id = %s
                            ORDER BY cs.scheduled_date DESC NULLS LAST, p.updated_at DESC NULLS LAST
                            LIMIT 1
                        """, (year, week_number, theme_id))
                        post = cursor.fetchone()

        status = None
        post_id = None
        title = None
        scheduled_date = None
        if post:
            post_id = post['id']
            title = post['title']
            status = post['status']
            scheduled_date = post['scheduled_date'].isoformat() if post['scheduled_date'] else None

        return jsonify({'success': True, 'post': {'id': post_id, 'title': title, 'status': status, 'scheduled_date': scheduled_date}})
    except Exception as e:
        logger.error(f"Error getting theme status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_schedule_update_theme_to_idea():
    """DEPRECATED: This endpoint is no longer needed.
    idea_id is deprecated from week persistence. Only theme_id is supported.
    This endpoint is kept for backwards compatibility but returns an error.
    """
    return jsonify({
        'success': False,
        'error': 'This endpoint is deprecated. idea_id is no longer supported in week persistence. Use theme_id instead.'
    }), 410  # 410 Gone
