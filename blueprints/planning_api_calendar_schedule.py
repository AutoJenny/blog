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
from utils.publication_status_resolver import resolve_post_for_calendar_item
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
            theme_id = theme.get('id')
            # Fetch post status using central resolver (ID-only matching)
            status_info = resolve_post_for_calendar_item(
                "theme", theme_id, year=year, week=week_number
            ) if theme_id else {"post_id": None, "status": None, "exists": False, "raw_status": None}
            
            schedule.append({
                'type': 'theme_selection',
                'selected_theme_id': theme_id,
                'theme_id': theme_id,  # For backward compatibility
                'theme_title': theme.get('theme_title'),
                'theme_description': theme.get('theme_description'),
                'position': theme.get('position'),
                'post_id': status_info.get('post_id'),         # Include post_id if theme has a post
                'post_status': status_info.get('status'),      # Include normalized status
                '_override': theme.get('_override', False),
                '_from_cyclic_system': True  # Flag to indicate new system
            })
        
        # Recipe
        if recipe:
            recipe_id = recipe.get('id')
            status_info = resolve_post_for_calendar_item(
                "recipe", recipe_id, year=year, week=week_number
            ) if recipe_id else {"post_id": None, "status": None, "exists": False, "raw_status": None}
            
            schedule.append({
                'type': 'recipe',
                'recipe_id': recipe_id,
                'post_id': status_info.get('post_id'),  # Include post_id if recipe has a post
                'post_status': status_info.get('status'),
                'recipe_title': recipe.get('recipe_title'),
                'recipe_description': recipe.get('recipe_description'),
                'position': recipe.get('position'),
                '_from_cyclic_system': True
            })
        
        # Profiles - need to fetch title from post table
        if profile_product:
            # profile_product comes from calendar_profile_sequence (id is post_id)
            profile_post_id = profile_product.get('post_id')
            post_title = None
            if profile_post_id:
                try:
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("SELECT title FROM post WHERE id = %s", (profile_post_id,))
                        post_row = cursor.fetchone()
                        if post_row:
                            post_title = post_row.get('title')
                except Exception as e:
                    logger.warning(f"Error fetching post title for profile %s: %s", profile_post_id, e)
            
            schedule.append({
                'type': 'post',
                'item_type': 'profile',
                'profile_type': 'product',
                'post_id': profile_post_id,
                'post_title': post_title,
                'position': profile_product.get('position'),
                '_from_cyclic_system': True
            })
        
        if profile_surname:
            profile_post_id = profile_surname.get('post_id')
            post_title = None
            if profile_post_id:
                try:
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("SELECT title FROM post WHERE id = %s", (profile_post_id,))
                        post_row = cursor.fetchone()
                        if post_row:
                            post_title = post_row.get('title')
                except Exception as e:
                    logger.warning(f"Error fetching post title for profile %s: %s", profile_post_id, e)
            
            schedule.append({
                'type': 'post',
                'item_type': 'profile',
                'profile_type': 'surname',
                'post_id': profile_post_id,
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
        
        # Add product posts from posting_queue for this week
        try:
            from datetime import date, timedelta
            from utils.date_utils import iso_year_week
            
            # Calculate week start (Monday) and end (Sunday) dates
            jan4 = date(year, 1, 4)
            jan4_day = (jan4.isoweekday() + 6) % 7  # Monday = 0
            week_start = date(year, 1, 4) + timedelta(days=(week_number - 1) * 7 - jan4_day)
            week_end = week_start + timedelta(days=6)
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pq.id as posting_queue_id,
                        pq.product_id,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.status,
                        cp.name as product_name,
                        cp.sku
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    WHERE pq.content_type = 'product'
                      AND pq.scheduled_date >= %s
                      AND pq.scheduled_date <= %s
                      AND pq.scheduled_timestamp IS NOT NULL
                    ORDER BY pq.scheduled_date, pq.scheduled_time
                """, (week_start, week_end))
                product_posts = cursor.fetchall()
                
                for post in product_posts:
                    if post['scheduled_date']:
                        schedule.append({
                            'type': 'product',
                            'item_id': post['product_id'],
                            'product_id': post['product_id'],
                            'posting_queue_id': post['posting_queue_id'],
                            'title': post['product_name'] or f"Product {post['product_id']}",
                            'scheduled_date': str(post['scheduled_date']),
                            'scheduled_time': str(post['scheduled_time']) if post['scheduled_time'] else None,
                            'status': post['status'] or 'ready',
                            'position': len([s for s in schedule if s.get('type') == 'product']) + 1
                        })
        except Exception as e:
            logger.warning(f"Error loading product posts for week view: {e}")
            # Continue without product posts if there's an error
        
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
                # Check for week-persistence V2 structures:
                # - Optional legacy selection table: calendar_week_selection
                # - Required unified items table: calendar_week_items
                cursor.execute("""
                    SELECT 
                        EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                              AND table_name = 'calendar_week_selection'
                        ) AS has_selection_table,
                        EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                              AND table_name = 'calendar_week_items'
                        ) AS has_week_items
                """)
                table_check = cursor.fetchone()
                has_selection_table = table_check['has_selection_table']
                has_week_items = table_check['has_week_items']

                # Require at least calendar_week_items; legacy calendar_schedule is not used.
                if not has_week_items:
                    conn.rollback()
                    return jsonify({
                        'success': False,
                        'error': 'Week persistence V2 table calendar_week_items is required. '
                                 'Legacy calendar_schedule is no longer supported.'
                    }), 500

                # Verify theme exists
                cursor.execute("SELECT id FROM calendar_themes WHERE id = %s", (theme_id,))
                theme = cursor.fetchone()
                if not theme:
                    return jsonify({'success': False, 'error': 'Theme not found'}), 404

                # If legacy selection table exists, keep writing to it for compatibility
                if has_selection_table:
                    cursor.execute("""
                        INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (year, week_number)
                        DO UPDATE SET selected_theme_id = EXCLUDED.selected_theme_id, updated_at = NOW()
                        RETURNING year, week_number, selected_theme_id, updated_at
                    """, (year, week_number, theme_id))
                    selection_result = cursor.fetchone()
                else:
                    # Synthesize a minimal result structure for response
                    selection_result = {
                        'year': year,
                        'week_number': week_number,
                        'selected_theme_id': theme_id,
                        'updated_at': None
                    }

                # Write to calendar_week_items (new unified table) – single source of truth
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
                    'year': selection_result['year'],
                    'week_number': selection_result['week_number'],
                    'selected_theme_id': selection_result['selected_theme_id'],
                    'updated_at': selection_result['updated_at'].isoformat() if selection_result['updated_at'] else None
                })
    except Exception as e:
        logger.error(f"Error selecting theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_calendar_idea_status(theme_id: int):
    """Resolve the post creation status for a theme in a specific week/year.
    DEPRECATED: Parameter name kept as idea_id for backwards compatibility, but only theme_id is supported.
    Uses new calendar_week_selection and calendar_week_posts tables exclusively.
    Legacy calendar_schedule is no longer supported.
    """
    try:
        year = request.args.get('year', type=int)
        week_number = request.args.get('week_number', type=int)
        if not year or not week_number:
            return jsonify({'success': False, 'error': 'year and week_number are required'}), 400

        with db_manager.get_cursor() as cursor:
            # Require week-persistence selection structure (table or view).
            cursor.execute("""
                SELECT 
                    EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                          AND table_name = 'calendar_week_selection'
                    ) AS has_selection_table,
                    EXISTS (
                        SELECT FROM information_schema.views 
                        WHERE table_schema = 'public' 
                          AND table_name = 'calendar_week_selection_v2'
                    ) AS has_selection_view
            """)
            table_check = cursor.fetchone()
            has_selection = table_check['has_selection_table'] or table_check['has_selection_view']

            if not has_selection:
                return jsonify({
                    'success': False,
                    'error': 'Week persistence selection structure is required '
                             '(calendar_week_selection or calendar_week_selection_v2).'
                }), 500

            # Decide which selection source to use (table or view)
            selection_source = 'calendar_week_selection' if table_check['has_selection_table'] else 'calendar_week_selection_v2'

            # First check if the selected theme for this week matches the provided theme_id
            cursor.execute(f"""
                SELECT selected_theme_id
                FROM {selection_source}
                WHERE year = %s AND week_number = %s
            """, (year, week_number))
            week_selection = cursor.fetchone()

            # Only proceed if the week's selected theme matches (or if no theme selected yet)
            if week_selection and week_selection['selected_theme_id'] != theme_id:
                # Theme mismatch - week has different theme selected
                return jsonify({
                    'success': True,
                    'post': None,
                    'message': 'Week has different theme selected'
                })

        # At this point, the requested theme is the selected theme for the week (or no selection),
        # so resolve post status using the shared resolver.
        status_info = resolve_post_for_calendar_item("theme", theme_id, year=year, week=week_number)

        post_payload = {
            'id': status_info.get('post_id'),
            'title': None,  # Title can be fetched separately if needed
            'status': status_info.get('status'),
            'scheduled_date': None
        }

        return jsonify({'success': True, 'post': post_payload})
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
