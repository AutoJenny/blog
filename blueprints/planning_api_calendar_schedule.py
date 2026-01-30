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
_db_target_logged = False


def api_calendar_schedule(year, week_number):
    """
    Get schedule for a specific year and week.
    
    NOW USES: New JSON-backed cyclic system (same as scheduling calendar)
    DEPRECATED: Old calendar_week_items and calendar_week_selection tables
    
    Returns theme, recipes, profiles, words, phrases, insults using cyclic logic.
    """
    global _db_target_logged
    if not _db_target_logged:
        try:
            from config.unified_config import get_database_target_for_logging
            logger.info("DB target (schedule API): %s", get_database_target_for_logging())
        except Exception:
            logger.info("DB target (schedule API): (config unavailable)")
        _db_target_logged = True
    try:
        # NEW SYSTEM: Use cyclic resolver for all categories
        # This ensures week-view aligns with the scheduling calendar
        theme = resolve_item_for_week("theme", year, week_number)
        
        # Also get recipes, profiles from cyclic system
        recipe = resolve_item_for_week("recipe", year, week_number)
        profile_product = resolve_item_for_week("profile_product", year, week_number)
        profile_surname = resolve_item_for_week("profile_surname", year, week_number)
        # CULTURE v1.1: Tuesday only — one language type per week, rotating word → phrase → insult
        language_types = ['weekly_word', 'weekly_phrase', 'weekly_insult']
        language_type = language_types[(week_number - 1) % 3]
        tuesday_language = resolve_item_for_week(language_type, year, week_number, classification=language_type)
        
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
        
        # Weekly content — CULTURE v1.1: Tuesday only (one language type per week, rotating)
        # Prefer posting_queue for this week's Tuesday if present; else resolver
        from datetime import date, timedelta
        jan4 = date(year, 1, 4)
        jan4_day = (jan4.isoweekday() + 6) % 7
        week_start = date(year, 1, 4) + timedelta(days=(week_number - 1) * 7 - jan4_day)
        tuesday_date = week_start + timedelta(days=1)
        tuesday_from_queue = None
        try:
            with db_manager.get_cursor() as cursor:
                # Tuesday language: platform=facebook, scheduled_date=that Tuesday, content_type in weekly_*,
                # status in ready/pending/generated/published/scheduled (visible); pick one (prefer ready, else newest).
                cursor.execute("""
                    SELECT pq.id, pq.idea_id, pq.content_type, pq.status, pq.scheduled_date, pq.scheduled_time
                    FROM posting_queue pq
                    WHERE pq.platform = 'facebook'
                    AND pq.content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
                    AND pq.scheduled_date = %s
                    AND pq.status IN ('ready', 'pending', 'generated', 'published', 'scheduled')
                    ORDER BY CASE WHEN pq.status = 'ready' THEN 0 WHEN pq.status = 'published' THEN 1 ELSE 2 END, pq.id DESC
                    LIMIT 1
                """, (tuesday_date,))
                row = cursor.fetchone()
                if row and row.get('idea_id'):
                    cursor.execute(
                        "SELECT id, idea_title, idea_description, position FROM calendar_ideas WHERE id = %s",
                        (row['idea_id'],)
                    )
                    idea_row = cursor.fetchone()
                    if idea_row:
                        tuesday_from_queue = {
                            'type': row['content_type'],
                            'item_id': idea_row['id'],
                            'title': idea_row.get('idea_title'),
                            'description': idea_row.get('idea_description'),
                            'position': idea_row.get('position'),
                            'posting_queue_id': row['id'],
                            'post_status': row.get('status'),
                            'scheduled_date': row.get('scheduled_date'),
                            'scheduled_time': row.get('scheduled_time'),
                        }
                elif row:
                    # No calendar_ideas row: still surface the queue item with generated content as title
                    tuesday_from_queue = {
                        'type': row['content_type'],
                        'item_id': row['id'],
                        'title': f"Language ({row['content_type']})",
                        'description': None,
                        'position': None,
                        'posting_queue_id': row['id'],
                        'post_status': row.get('status'),
                        'scheduled_date': row.get('scheduled_date'),
                        'scheduled_time': row.get('scheduled_time'),
                    }
        except Exception as e:
            logger.warning("Error loading Tuesday language from posting_queue: %s", e)
        if tuesday_from_queue:
            schedule.append({
                'type': tuesday_from_queue['type'],
                'item_id': tuesday_from_queue['item_id'],
                'title': tuesday_from_queue['title'],
                'description': tuesday_from_queue.get('description'),
                'position': tuesday_from_queue.get('position'),
                'role': 'CULTURE',
                'posting_queue_id': tuesday_from_queue.get('posting_queue_id'),
                'post_status': tuesday_from_queue.get('post_status'),
                'scheduled_date': str(tuesday_from_queue['scheduled_date']) if tuesday_from_queue.get('scheduled_date') else None,
                'scheduled_time': str(tuesday_from_queue['scheduled_time']) if tuesday_from_queue.get('scheduled_time') else None,
                '_from_posting_queue': True,
                '_tuesday_language': True
            })
        elif tuesday_language:
            schedule.append({
                'type': language_type,
                'item_id': tuesday_language.get('id'),
                'title': tuesday_language.get('idea_title'),
                'description': tuesday_language.get('idea_description'),
                'position': tuesday_language.get('position'),
                'role': 'CULTURE',
                'scheduled_date': str(tuesday_date) if tuesday_date else None,
                'scheduled_time': '09:00:00',
                '_from_cyclic_system': True,
                '_tuesday_language': True
            })
        
        # Add automated Facebook posts (products and messages) from posting_queue for this week
        # CRITICAL: Use post_type_channel_config as authoritative source to determine what should be displayed
        # - Products: Exclude Saturday (day 6) - Messages replace Saturday product posts
        # - Messages: Only Saturday (day 6)
        try:
            from datetime import date, timedelta
            
            # Calculate week start (Monday) and end (Sunday) dates
            jan4 = date(year, 1, 4)
            jan4_day = (jan4.isoweekday() + 6) % 7  # Monday = 0
            week_start = date(year, 1, 4) + timedelta(days=(week_number - 1) * 7 - jan4_day)
            week_end = week_start + timedelta(days=6)
            
            logger.info(f"Loading automated Facebook posts for week {year}-W{week_number:02d}: {week_start} to {week_end}")
            
            with db_manager.get_cursor() as cursor:
                # First, check post_type_channel_config to see what should be displayed
                # This is the authoritative source - same as publication schedule view
                cursor.execute("""
                    SELECT 
                        post_type,
                        channel,
                        publication_day
                    FROM post_type_channel_config
                    WHERE is_active = TRUE
                    AND publication_day IS NOT NULL
                    AND channel = 'facebook'
                    AND post_type IN ('product', 'message')
                """)
                configs = cursor.fetchall()
                
                # Determine which days should show products vs messages
                product_days = set()
                message_days = set()
                for config in configs:
                    day = config['publication_day']
                    if config['post_type'] == 'product':
                        product_days.add(day)
                    elif config['post_type'] == 'message':
                        message_days.add(day)
                
                logger.info(f"Product days from config: {sorted(product_days)}, Message days: {sorted(message_days)}")
                
                # Query product posts - Matrix v1: COMMERCE/product on Saturday (day 6) only
                # Use ISODOW for ISO weekday (1=Monday, 7=Sunday)
                cursor.execute("""
                    SELECT 
                        pq.id as posting_queue_id,
                        pq.product_id,
                        pq.role,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.status,
                        EXTRACT(ISODOW FROM pq.scheduled_date) as weekday,
                        cp.name as product_name,
                        cp.sku
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    WHERE pq.content_type = 'product'
                      AND pq.platform = 'facebook'
                      AND pq.scheduled_date >= %s
                      AND pq.scheduled_date <= %s
                      AND pq.scheduled_timestamp IS NOT NULL
                      AND EXTRACT(ISODOW FROM pq.scheduled_date) = 6  -- Matrix v1: Saturday only
                    ORDER BY pq.scheduled_date, pq.scheduled_time
                """, (week_start, week_end))
                product_posts = cursor.fetchall()
                # Option A: Cap Saturday to 1 visible card in week-view grid; rest remain in queue/detail
                filtered_product_posts = product_posts[:1]
                logger.info(f"Found {len(product_posts)} product posts (Matrix v1: Saturday only); showing 1 in grid")
                
                # Add product posts (one card per Saturday in grid)
                for idx, post in enumerate(filtered_product_posts):
                    if post['scheduled_date']:
                        # Map posting_queue status to post_status for frontend
                        queue_status = post['status'] or 'draft'
                        post_status_map = {
                            'draft': 'draft',
                            'ready': 'ready',
                            'published': 'published',
                            'failed': 'failed'
                        }
                        post_status = post_status_map.get(queue_status, 'draft')
                        
                        schedule.append({
                            'type': 'product',
                            'item_id': post['product_id'],
                            'product_id': post['product_id'],
                            'posting_queue_id': post['posting_queue_id'],
                            'role': post.get('role'),  # Matrix v1: COMMERCE; surface for UI
                            'title': post['product_name'] or f"Product {post['product_id']}",
                            'scheduled_date': str(post['scheduled_date']),
                            'scheduled_time': str(post['scheduled_time']) if post['scheduled_time'] else None,
                            'status': queue_status,  # Keep original status field
                            'post_status': post_status,  # Add post_status for frontend compatibility
                            'post_exists': True,  # Product post exists in posting_queue
                            'position': idx + 1
                        })
                
                # Query message posts - Matrix v1: REASSURANCE/message on Wednesday (day 3) only
                # Use ISODOW for ISO weekday (1=Monday, 7=Sunday)
                cursor.execute("""
                    SELECT 
                        pq.id as posting_queue_id,
                        pq.role,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.status,
                        pq.generated_content,
                        EXTRACT(ISODOW FROM pq.scheduled_date) as weekday
                    FROM posting_queue pq
                    WHERE pq.content_type = 'message'
                      AND pq.platform = 'facebook'
                      AND pq.scheduled_date >= %s
                      AND pq.scheduled_date <= %s
                      AND pq.scheduled_timestamp IS NOT NULL
                      AND EXTRACT(ISODOW FROM pq.scheduled_date) = 3  -- Matrix v1: Wednesday only
                    ORDER BY pq.scheduled_date, pq.scheduled_time
                """, (week_start, week_end))
                message_posts = cursor.fetchall()
                wednesday_messages = message_posts
                logger.info(f"Found {len(message_posts)} message posts (Matrix v1: Wednesday only)")
                
                # Add message posts (Matrix v1: Wednesday only)
                for idx, post in enumerate(wednesday_messages):
                    if post['scheduled_date']:
                        # Extract first line of message for title
                        content = post['generated_content'] or ''
                        title = content.split('\n')[0][:50] if content else 'Message'
                        
                        # Map posting_queue status to post_status for frontend
                        queue_status = post['status'] or 'draft'
                        # posting_queue status: draft -> ready -> published
                        # Map to post_status format expected by frontend
                        post_status_map = {
                            'draft': 'draft',
                            'ready': 'ready',
                            'published': 'published',
                            'failed': 'failed'
                        }
                        post_status = post_status_map.get(queue_status, 'draft')
                        
                        schedule.append({
                            'type': 'message',
                            'item_id': post['posting_queue_id'],
                            'posting_queue_id': post['posting_queue_id'],
                            'role': post.get('role'),  # Matrix v1: REASSURANCE; surface for UI
                            'title': title,
                            'scheduled_date': str(post['scheduled_date']),
                            'scheduled_time': str(post['scheduled_time']) if post['scheduled_time'] else None,
                            'status': queue_status,  # Keep original status field
                            'post_status': post_status,  # Add post_status for frontend compatibility
                            'post_exists': True,  # Message post exists in posting_queue
                            'position': idx + 1
                        })
                
                logger.info(f"Added {len([s for s in schedule if s.get('type') == 'product'])} product posts and {len([s for s in schedule if s.get('type') == 'message'])} message posts to schedule")
                
                # Query role-based posts (e.g. DEPTH_LONG Sunday, AUTHORITY_SHORT Friday, CULTURE Mon, HERITAGE Thu)
                # CULTURE v1.1: Monday CULTURE (culture_fact). Phase H1: Thursday HERITAGE (heritage_fact). Both appear here via role rail.
                # Exclude:
                #   - 'product' and 'message' (already returned by the product/message queries above)
                #   - weekly language types ('weekly_word','weekly_phrase','weekly_insult')
                #     which are Tuesday only and already added via tuesday_language above.
                cursor.execute("""
                    SELECT 
                        pq.id as posting_queue_id,
                        pq.role,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.status,
                        pq.generated_content,
                        pq.generated_caption,
                        EXTRACT(ISODOW FROM pq.scheduled_date) as weekday
                    FROM posting_queue pq
                    WHERE pq.role IS NOT NULL
                      AND pq.platform = 'facebook'
                      AND pq.scheduled_date >= %s
                      AND pq.scheduled_date <= %s
                      AND pq.scheduled_timestamp IS NOT NULL
                      AND pq.content_type NOT IN ('product', 'message', 'weekly_word', 'weekly_phrase', 'weekly_insult')
                    ORDER BY pq.scheduled_date, pq.scheduled_time
                """, (week_start, week_end))
                role_posts = cursor.fetchall()
                
                logger.info(f"Found {len(role_posts)} role-based posts")
                
                # Add role-based posts to schedule
                for idx, post in enumerate(role_posts):
                    if post['scheduled_date']:
                        # Extract title from content; avoid surfacing placeholder text
                        content = post['generated_content'] or post['generated_caption'] or ''
                        first_line = (content.split('\n')[0][:50].strip() if content else '') or ''
                        if first_line and ('placeholder' in first_line.lower() or 'short factual context' in first_line.lower()):
                            title = f"{post['role']} post"
                        else:
                            title = first_line if first_line else f"{post['role']} Post"
                        
                        # Map posting_queue status to post_status for frontend
                        queue_status = post['status'] or 'draft'
                        post_status_map = {
                            'draft': 'draft',
                            'generated': 'draft',
                            'validated_pass': 'draft',
                            'approved': 'ready',
                            'scheduled': 'ready',
                            'ready': 'ready',
                            'published': 'published',
                            'failed': 'failed'
                        }
                        post_status = post_status_map.get(queue_status, 'draft')
                        
                        # Determine type based on role
                        schedule_type = post['role'].lower() if post['role'] else 'role_post'
                        
                        schedule.append({
                            'type': schedule_type,
                            'item_id': post['posting_queue_id'],
                            'posting_queue_id': post['posting_queue_id'],
                            'role': post['role'],
                            'title': title,
                            'generated_content': (post.get('generated_content') or post.get('generated_caption') or '')[:500],
                            'scheduled_date': str(post['scheduled_date']),
                            'scheduled_time': str(post['scheduled_time']) if post['scheduled_time'] else None,
                            'status': queue_status,  # Keep original status field
                            'post_status': post_status,  # Add post_status for frontend compatibility
                            'post_exists': True,  # Role-based post exists in posting_queue
                            'position': idx + 1
                        })
                
                logger.info(f"Added {len([s for s in schedule if s.get('role')])} role-based posts to schedule")
        except Exception as e:
            logger.error(f"Error loading automated Facebook posts for week view: {e}", exc_info=True)
            # Continue without posts if there's an error
        
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
