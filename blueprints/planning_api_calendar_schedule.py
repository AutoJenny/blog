"""
Planning Calendar API - Schedule

Calendar schedule and selection endpoints

DEPRECATED: Old week-specific assignment tables (calendar_week_items, calendar_week_selection)
NEW SYSTEM: Uses JSON-backed cyclic system via resolve_item_for_week() from utils.calendar_resolver

This endpoint now uses the new cyclic system to align with the scheduling calendar.
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
from utils.calendar_resolver import resolve_item_for_week
import logging

logger = logging.getLogger(__name__)

def api_calendar_schedule(year, week_number):
    """
    Get schedule for a specific year and week.
    
    NOW USES: New JSON-backed cyclic system (same as scheduling calendar)
    DEPRECATED: Old calendar_week_items and calendar_week_selection tables
    
    Returns theme, recipes, profiles, words, phrases, insults using cyclic logic.
    """
    try:
        # NEW SYSTEM: Use cyclic resolver for all categories
        # This ensures week-view aligns with the scheduling calendar
        theme = resolve_item_for_week("theme", year, week_number)
        
        # Also get recipes, profiles, words, phrases, insults from cyclic system
        recipe = resolve_item_for_week("recipe", year, week_number)
        profile_product = resolve_item_for_week("profile_product", year, week_number)
        profile_surname = resolve_item_for_week("profile_surname", year, week_number)
        weekly_word = resolve_item_for_week("weekly_word", year, week_number, classification="weekly_word")
        weekly_phrase = resolve_item_for_week("weekly_phrase", year, week_number, classification="weekly_phrase")
        weekly_insult = resolve_item_for_week("weekly_insult", year, week_number, classification="weekly_insult")
        
        # Build schedule response using new system
        schedule = []
        
        # Theme
        if theme:
            schedule.append({
                'type': 'theme_selection',
                'selected_theme_id': theme.get('id'),
                'theme_id': theme.get('id'),  # For backward compatibility
                'theme_title': theme.get('theme_title'),
                'theme_description': theme.get('theme_description'),
                'position': theme.get('position'),
                '_override': theme.get('_override', False),
                '_from_cyclic_system': True  # Flag to indicate new system
            })
        
        # Recipe
        if recipe:
            schedule.append({
                'type': 'recipe',
                'recipe_id': recipe.get('id'),
                'recipe_title': recipe.get('recipe_title'),
                'recipe_description': recipe.get('recipe_description'),
                'position': recipe.get('position'),
                '_from_cyclic_system': True
            })
        
        # Profiles - need to fetch title from post table
        if profile_product:
            post_id = profile_product.get('post_id')
            # Fetch post title if we have post_id
            post_title = None
            if post_id:
                try:
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                        post_row = cursor.fetchone()
                        if post_row:
                            post_title = post_row.get('title')
                except Exception as e:
                    logger.warning(f"Error fetching post title for profile {post_id}: {e}")
            
            schedule.append({
                'type': 'post',
                'item_type': 'profile',
                'profile_type': 'product',
                'post_id': post_id,
                'post_title': post_title,
                'position': profile_product.get('position'),
                '_from_cyclic_system': True
            })
        
        if profile_surname:
            post_id = profile_surname.get('post_id')
            # Fetch post title if we have post_id
            post_title = None
            if post_id:
                try:
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("SELECT title FROM post WHERE id = %s", (post_id,))
                        post_row = cursor.fetchone()
                        if post_row:
                            post_title = post_row.get('title')
                except Exception as e:
                    logger.warning(f"Error fetching post title for profile {post_id}: {e}")
            
            schedule.append({
                'type': 'post',
                'item_type': 'profile',
                'profile_type': 'surname',
                'post_id': post_id,
                'post_title': post_title,
                'position': profile_surname.get('position'),
                '_from_cyclic_system': True
            })
        
        # Weekly content
        if weekly_word:
            schedule.append({
                'type': 'weekly_word',
                'item_id': weekly_word.get('id'),
                'title': weekly_word.get('idea_title'),
                'description': weekly_word.get('idea_description'),
                'position': weekly_word.get('position'),
                '_from_cyclic_system': True
            })
        
        if weekly_phrase:
            schedule.append({
                'type': 'weekly_phrase',
                'item_id': weekly_phrase.get('id'),
                'title': weekly_phrase.get('idea_title'),
                'description': weekly_phrase.get('idea_description'),
                'position': weekly_phrase.get('position'),
                '_from_cyclic_system': True
            })
        
        if weekly_insult:
            schedule.append({
                'type': 'weekly_insult',
                'item_id': weekly_insult.get('id'),
                'title': weekly_insult.get('idea_title'),
                'description': weekly_insult.get('idea_description'),
                'position': weekly_insult.get('position'),
                '_from_cyclic_system': True
            })
        
        # Return response with new cyclic system data
        selected_theme_id = theme.get('id') if theme else None
        
        return jsonify({
            'success': True,
            'year': year,
            'week_number': week_number,
            'schedule': schedule,
            'selected_theme_id': selected_theme_id,
            '_from_cyclic_system': True  # Flag to indicate new system
        })
            
    except Exception as e:
        logger.error(f"Error fetching calendar schedule: {e}")
        return jsonify({'error': str(e)}), 500

# DEPRECATED: Old fallback code removed - now uses cyclic system only
# The old week-specific assignment logic (calendar_week_items, calendar_week_selection, calendar_schedule)
# is no longer used for theme/recipe/profile/weekly content.
# The new system uses cyclic position-based logic via resolve_item_for_week().

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
                    
                    # DUAL-WRITE: Write to both old and new tables
                    # 1. Write to calendar_week_selection (old table)
                    cursor.execute("""
                        INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (year, week_number)
                        DO UPDATE SET selected_theme_id = EXCLUDED.selected_theme_id, updated_at = NOW()
                        RETURNING year, week_number, selected_theme_id, updated_at
                    """, (year, week_number, theme_id))
                    
                    result = cursor.fetchone()
                    
                    # 2. Write to calendar_week_items (new unified table)
                    # Check if calendar_week_items table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'calendar_week_items'
                        )
                    """)
                    has_week_items = cursor.fetchone()['exists']
                    
                    if has_week_items:
                        # First, unselect any currently selected theme for this week
                        cursor.execute("""
                            UPDATE calendar_week_items
                            SET is_selected = FALSE, updated_at = NOW()
                            WHERE year = %s AND week_number = %s 
                              AND item_type = 'theme' AND is_selected = TRUE
                        """, (year, week_number))
                        
                        # Then, insert/update the selected theme
                        cursor.execute("""
                            INSERT INTO calendar_week_items (
                                item_type, item_id, year, week_number, is_selected, is_active, created_at, updated_at
                            ) VALUES (
                                'theme', %s, %s, %s, TRUE, TRUE, NOW(), NOW()
                            )
                            ON CONFLICT (year, week_number, item_type, item_id)
                            DO UPDATE SET
                                is_selected = TRUE,
                                updated_at = NOW()
                        """, (theme_id, year, week_number))
                    
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
