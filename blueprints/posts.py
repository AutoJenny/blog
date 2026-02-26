# blueprints/posts.py
"""
Posts Management Blueprint
Single-purpose module for post listing and status management.
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, date, timedelta
from config.database import db_manager
from utils.publication_status_resolver import normalize_post_status
import logging

bp = Blueprint('posts', __name__)
logger = logging.getLogger(__name__)


def format_time_ago(dt):
    """
    Format a datetime as 'X ago' string.
    Returns formatted string or empty string if dt is None.
    """
    if not dt:
        return ''
    
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    delta = now - dt
    
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def get_display_status(status):
    """
    Convert database status to display-friendly status.
    Maps various statuses to standard display values.
    """
    # Delegate to the shared resolver so all modules share one mapping.
    return normalize_post_status(status)


def get_week_start_end(year: int, week_number: int):
    """Return Monday and Sunday dates for ISO week."""
    try:
        # ISO week: Monday is 1
        monday = date.fromisocalendar(year, week_number, 1)
        sunday = date.fromisocalendar(year, week_number, 7)
        return monday, sunday
    except Exception:
        return None, None


@bp.route('/posts/<int:post_id>')
def post_detail(post_id):
    """Redirect to appropriate default stage based on post type"""
    from flask import redirect, url_for
    from utils.taxonomy_helpers import get_post_type
    from datetime import datetime
    
    post_type = get_post_type(post_id)
    
    # Get week context if available from query params
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # For recipe posts without week context, calculate from recipe_week_number
    if not (year and week) and post_type == 'recipe':
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT recipe_week_number FROM post WHERE id = %s
            """, (post_id,))
            result = cursor.fetchone()
            recipe_week_number = None
            if result:
                if isinstance(result, dict):
                    recipe_week_number = result.get('recipe_week_number')
                elif isinstance(result, (tuple, list)) and len(result) > 0:
                    recipe_week_number = result[0]
            
            if recipe_week_number:
                # Calculate calendar week: recipe week 1 = current week
                current_iso = datetime.now().isocalendar()
                current_year = current_iso[0]
                current_week = current_iso[1]
                
                weeks_ahead = recipe_week_number - 1
                target_week = current_week + weeks_ahead
                
                if target_week > 52:
                    year = current_year + 1
                    week = target_week - 52
                else:
                    year = current_year
                    week = target_week
    
    # Determine default route based on post type
    if post_type == 'recipe':
        # Recipe posts start at calendar week-view
        url = url_for('planning.planning_calendar_week_view', post_id=post_id)
    elif post_type == 'profile':
        # Profile posts start at calendar week-view
        url = url_for('planning.planning_calendar_week_view', post_id=post_id)
    elif post_type == 'generated':
        # Generated posts start at taxonomy (with preset values)
        url = url_for('planning.planning_calendar_taxonomy', post_id=post_id)
    else:
        # Themed posts start at calendar week-view
        url = url_for('planning.planning_calendar_week_view', post_id=post_id)
    
    # Add week context if available
    if year and week:
        url += f'?year={year}&week={week}'
    
    return redirect(url)

@bp.route('/posts')
def posts_list():
    """
    HTML page listing all posts with show/delete functionality.
    Supports ?show_deleted=1 query parameter to show deleted posts.
    """
    show_deleted = request.args.get('show_deleted', '0') == '1'
    
    try:
        with db_manager.get_cursor() as cursor:
            # Check if calendar_week_posts_v2 table exists (current table)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts_v2'
                )
            """)
            result = cursor.fetchone()
            # Handle both tuple and dict return types from psycopg
            if isinstance(result, tuple):
                has_v2_table = result[0]
            elif isinstance(result, dict):
                has_v2_table = result.get('exists', False)
            else:
                has_v2_table = False
            
            # Check if calendar_week_posts table exists (legacy)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts'
                )
            """)
            result = cursor.fetchone()
            if isinstance(result, tuple):
                has_week_posts_table = result[0]
            elif isinstance(result, dict):
                has_week_posts_table = result.get('exists', False)
            else:
                has_week_posts_table = False
            
            if has_v2_table:
                # Use calendar_week_posts_v2 table (current)
                if show_deleted:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               cwp.year AS sched_year, cwp.week_number AS sched_week, NULL AS scheduled_date, NULL AS weekday
                        FROM post p
                        LEFT JOIN LATERAL (
                            SELECT year, week_number, updated_at, created_at
                            FROM calendar_week_posts_v2
                            WHERE post_id = p.id
                            ORDER BY updated_at DESC, created_at DESC
                            LIMIT 1
                        ) cwp ON TRUE
                        WHERE p.status = 'deleted'
                        ORDER BY p.created_at DESC
                    """)
                else:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               cwp.year AS sched_year, cwp.week_number AS sched_week, NULL AS scheduled_date, NULL AS weekday
                        FROM post p
                        LEFT JOIN LATERAL (
                            SELECT year, week_number, updated_at, created_at
                            FROM calendar_week_posts_v2
                            WHERE post_id = p.id
                            ORDER BY updated_at DESC, created_at DESC
                            LIMIT 1
                        ) cwp ON TRUE
                        WHERE p.status != 'deleted'
                        ORDER BY p.updated_at DESC, p.id DESC
                    """)
            elif has_week_posts_table:
                # Use calendar_week_posts table
                if show_deleted:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               cwp.year AS sched_year, cwp.week_number AS sched_week, cwp.scheduled_date, cwp.weekday
                        FROM post p
                        LEFT JOIN LATERAL (
                            SELECT year, week_number, scheduled_date, weekday, updated_at
                            FROM calendar_week_posts
                            WHERE post_id = p.id
                            ORDER BY scheduled_date DESC NULLS LAST, updated_at DESC, created_at DESC
                            LIMIT 1
                        ) cwp ON TRUE
                        WHERE p.status = 'deleted'
                        ORDER BY p.created_at DESC
                    """)
                else:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               cwp.year AS sched_year, cwp.week_number AS sched_week, cwp.scheduled_date, cwp.weekday
                        FROM post p
                        LEFT JOIN LATERAL (
                            SELECT year, week_number, scheduled_date, weekday, updated_at
                            FROM calendar_week_posts
                            WHERE post_id = p.id
                            ORDER BY scheduled_date DESC NULLS LAST, updated_at DESC, created_at DESC
                            LIMIT 1
                        ) cwp ON TRUE
                        WHERE p.status != 'deleted'
                        ORDER BY p.updated_at DESC, p.id DESC
                    """)
            else:
                # Query posts directly without calendar table joins
                if show_deleted:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               NULL AS sched_year, NULL AS sched_week, NULL AS scheduled_date
                        FROM post p
                        WHERE p.status = 'deleted'
                        ORDER BY p.created_at DESC
                    """)
                else:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               NULL AS sched_year, NULL AS sched_week, NULL AS scheduled_date
                        FROM post p
                        WHERE p.status != 'deleted'
                        ORDER BY p.updated_at DESC, p.id DESC
                    """)
            posts = cursor.fetchall()
            
        # Helper function to determine post type
        def determine_post_type(post_row):
            """Determine post type: recipe, profile, or themed."""
            if isinstance(post_row, dict):
                recipe_week = post_row.get('recipe_week_number')
                profile_cat = post_row.get('profile_category_id')
            else:
                recipe_week = post_row[5] if len(post_row) > 5 else None
                profile_cat = post_row[6] if len(post_row) > 6 else None
            
            if recipe_week is not None:
                return 'recipe'
            elif profile_cat is not None:
                return 'profile'
            else:
                return 'themed'
        
        # Get current week for recipe mapping
        from datetime import datetime
        current_iso = datetime.now().isocalendar()
        current_year = current_iso[0]
        current_week = current_iso[1]
        
        # Format posts for template
        formatted_posts = []
        for post in posts:
            sched_year = post.get('sched_year') if isinstance(post, dict) else post['sched_year']
            sched_week = post.get('sched_week') if isinstance(post, dict) else post['sched_week']
            
            # For recipe posts, calculate calendar week from recipe_week_number if not scheduled
            post_type = determine_post_type(post)
            if post_type == 'recipe' and not (sched_year and sched_week):
                recipe_week_number = post.get('recipe_week_number') if isinstance(post, dict) else post[5] if len(post) > 5 else None
                if recipe_week_number:
                    # Calculate calendar week: recipe week 1 = current week
                    weeks_ahead = recipe_week_number - 1
                    target_week = current_week + weeks_ahead
                    
                    if target_week > 52:
                        # Wrapped to next year
                        sched_year = current_year + 1
                        sched_week = target_week - 52
                    else:
                        sched_year = current_year
                        sched_week = target_week
            
            week_label = None
            week_sort_key = None
            week_dates_small = ''
            recipe_week_label = None
            
            if sched_year and sched_week:
                week_label = f"W{int(sched_week)}"
                week_sort_key = int(sched_year) * 100 + int(sched_week)
                week_start, week_end = get_week_start_end(int(sched_year), int(sched_week))
                if week_start and week_end:
                    week_dates_small = f"{week_start.strftime('%a %d %b %Y')} – {week_end.strftime('%a %d %b %Y')}"
            
            # For recipe posts, also show recipe week number
            if post_type == 'recipe':
                recipe_week_number = post.get('recipe_week_number') if isinstance(post, dict) else post[5] if len(post) > 5 else None
                if recipe_week_number:
                    recipe_week_label = f"Recipe Week {recipe_week_number}"

            created_ts = int(post['created_at'].timestamp() * 1000) if post.get('created_at') else 0
            updated_ts = int(post['updated_at'].timestamp() * 1000) if post.get('updated_at') else 0

            formatted_posts.append({
                'id': post['id'],
                'title': post['title'] or 'Untitled',
                'status': post['status'],
                'display_status': get_display_status(post['status']),
                'created_ago': format_time_ago(post['created_at']),
                'updated_ago': format_time_ago(post['updated_at']),
                'created_ts': created_ts,
                'updated_ts': updated_ts,
                'week_label': week_label,
                'week_dates': week_dates_small,
                'recipe_week_label': recipe_week_label,  # e.g., "Recipe Week 1"
                'week_sort': week_sort_key,
                'week_number': int(sched_week) if sched_week else None,
                'year': int(sched_year) if sched_year else None,
                'post_type': post_type,
                'is_recipe': post_type == 'recipe',
                'is_profile': post_type == 'profile',
                'is_themed': post_type == 'themed'
            })
        
        return render_template('posts_list.html', 
                             posts=formatted_posts,
                             show_deleted=show_deleted,
                             current_year=current_year,
                             current_week=current_week)
        
    except Exception as e:
        logger.error(f"Error in posts_list: {e}")
        return render_template('posts_list.html', 
                             posts=[],
                             show_deleted=show_deleted)


@bp.route('/api/posts')
def api_posts():
    """
    JSON API endpoint to get all posts.
    Consolidated version - use this instead of deprecated endpoints in core.py and launchpad_old.py
    Returns: {"posts": [...]}
    """
    show_deleted = request.args.get('show_deleted', '0') == '1'
    
    try:
        with db_manager.get_cursor() as cursor:
            if show_deleted:
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                           p.clan_post_id, p.clan_last_attempt, p.clan_error, p.clan_uploaded_url,
                           pd.idea_seed, pd.provisional_title, pd.intro_blurb,
                           cs.year AS sched_year, cs.week_number AS sched_week, cs.scheduled_date
                    FROM post p
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    LEFT JOIN LATERAL (
                        SELECT year, week_number, scheduled_date, updated_at
                        FROM calendar_week_posts_v2
                        WHERE post_id = p.id
                        ORDER BY scheduled_date DESC NULLS LAST, updated_at DESC
                        LIMIT 1
                    ) cs ON TRUE
                    WHERE p.status = 'deleted'
                    ORDER BY p.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                           p.clan_post_id, p.clan_last_attempt, p.clan_error, p.clan_uploaded_url,
                           pd.idea_seed, pd.provisional_title, pd.intro_blurb,
                           cs.year AS sched_year, cs.week_number AS sched_week, cs.scheduled_date
                    FROM post p
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    LEFT JOIN LATERAL (
                        SELECT year, week_number, scheduled_date, updated_at
                        FROM calendar_week_posts_v2
                        WHERE post_id = p.id
                        ORDER BY scheduled_date DESC NULLS LAST, updated_at DESC
                        LIMIT 1
                    ) cs ON TRUE
                    WHERE p.status != 'deleted'
                    ORDER BY p.updated_at DESC, p.id DESC
                """)
            posts = cursor.fetchall()
        
        return jsonify({"posts": posts})
        
    except Exception as e:
        logger.error(f"Error in api_posts: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/posts/timeline')
def api_posts_timeline():
    """
    Get posts timeline in chronological order based on SCHEDULED OUTPUT ONLY.
    
    This endpoint uses post_type_channel_config as the source of truth to determine
    what should be displayed. It only shows posts that match the configured schedule.
    
    Architecture:
    1. Query post_type_channel_config to determine what SHOULD be scheduled
    2. For each configured post type/day/time, look up the actual post in posting_queue
    3. Only include posts that match the schedule configuration
    4. One post per day maximum (the one matching the schedule)
    """
    try:
        from datetime import date, datetime, timedelta, time as time_type
        import json
        
        limit = request.args.get('limit', type=int, default=50)
        status_filter = request.args.get('status')  # Optional: 'pending', 'ready', 'published', etc.
        show_published = request.args.get('show_published', 'false').lower() == 'true'  # Hide published by default
        
        today = date.today()
        end_date = today + timedelta(days=limit)  # Look ahead for configured limit
        
        timeline_posts = []
        
        with db_manager.get_cursor() as cursor:
            # STEP 1: Get all active schedule configurations from post_type_channel_config
            # This is the SOURCE OF TRUTH for what should be scheduled
            cursor.execute("""
                SELECT 
                    post_type,
                    channel,
                    publication_day,
                    publication_time
                FROM post_type_channel_config
                WHERE is_active = TRUE
                AND publication_day IS NOT NULL
                AND channel = 'facebook'
                ORDER BY publication_day, publication_time NULLS LAST
            """)
            schedule_configs = cursor.fetchall()
            
            # STEP 2: Get product schedules from daily_posts_schedule (recurring patterns)
            cursor.execute("""
                SELECT 
                    days,
                    time,
                    platform
                FROM daily_posts_schedule
                WHERE is_active = TRUE
                AND content_type = 'product'
                AND platform = 'facebook'
            """)
            product_schedules = cursor.fetchall()
            
            # Build a map of what should be scheduled for each date
            # Format: {(date, post_type): config}
            scheduled_items = {}
            
            # Process fixed schedule configurations (weekly_word, weekly_phrase, weekly_insult, message)
            for config in schedule_configs:
                post_type = config['post_type']
                publication_day = config['publication_day']  # 1=Monday, 7=Sunday
                publication_time = config['publication_time']
                
                # Skip product posts here - they're handled separately via daily_posts_schedule
                if post_type == 'product':
                    continue
                
                # Calculate dates for this weekday within the date range
                current_date = today
                while current_date <= end_date:
                    weekday = current_date.isoweekday()  # 1=Monday, 7=Sunday
                    if weekday == publication_day:
                        scheduled_items[(current_date, post_type)] = {
                            'post_type': post_type,
                            'scheduled_date': current_date,
                            'scheduled_time': publication_time or time_type(9, 0),  # Default 09:00
                            'from_config': True
                        }
                    current_date += timedelta(days=1)
            
            # Process product schedules (recurring weekday patterns)
            for schedule in product_schedules:
                days = schedule['days']  # JSONB array of weekday numbers
                scheduled_time = schedule['time']
                
                if not days:
                    continue
                
                # Parse days if it's a JSON string
                if isinstance(days, str):
                    days = json.loads(days)
                
                # Calculate dates for matching weekdays
                current_date = today
                while current_date <= end_date:
                    weekday = current_date.isoweekday()
                    if weekday in days:
                        # Use existing entry if present, otherwise create new
                        key = (current_date, 'product')
                        if key not in scheduled_items:
                            # Parse time if string
                            if isinstance(scheduled_time, str):
                                time_parts = scheduled_time.split(':')
                                time_obj = time_type(int(time_parts[0]), int(time_parts[1]) if len(time_parts) > 1 else 0)
                            else:
                                time_obj = scheduled_time
                            
                            scheduled_items[key] = {
                                'post_type': 'product',
                                'scheduled_date': current_date,
                                'scheduled_time': time_obj,
                                'from_config': True
                            }
                    current_date += timedelta(days=1)
            
            # STEP 3: For each scheduled item, find the actual post in posting_queue
            for (scheduled_date, post_type), schedule_info in scheduled_items.items():
                # Skip if date is in the past (only show today onwards)
                if scheduled_date < today:
                    continue
                
                # Build query to find matching post
                query = """
                    SELECT 
                        pq.id as queue_id,
                        pq.idea_id,
                        pq.product_id,
                        pq.content_type,
                        pq.platform,
                        pq.channel_type,
                        pq.generated_caption,
                        pq.generated_content,
                        pq.image_path,
                        pq.status,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.scheduled_timestamp,
                        pq.platform_post_id,
                        pq.created_at,
                        pq.updated_at,
                        -- Product details
                        cp.name as product_name,
                        cp.sku as product_sku,
                        cp.image_url as product_image,
                        -- Idea details (for language posts)
                        ci.idea_title,
                        ci.idea_description,
                        -- Display image URL
                        CASE 
                            WHEN pq.content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult') 
                                 AND pq.image_path IS NOT NULL 
                                 AND pq.image_path LIKE '/Users/%%/static/%%' 
                            THEN REPLACE(pq.image_path, '/Users/autojenny/Documents/projects/blog', '')
                            WHEN pq.content_type = 'product' AND cp.image_url IS NOT NULL
                            THEN cp.image_url
                            WHEN pq.content_type = 'product' AND pq.image_path IS NOT NULL
                            THEN pq.image_path
                            ELSE NULL
                        END as display_image_url
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    LEFT JOIN calendar_ideas ci ON pq.idea_id = ci.id
                    WHERE pq.content_type = %s
                    AND pq.platform = 'facebook'
                    AND pq.scheduled_date = %s
                """
                params = [post_type, scheduled_date]
                
                # Add status filters
                if not show_published:
                    query += " AND pq.status != 'published'"
                
                if status_filter:
                    query += " AND pq.status = %s"
                    params.append(status_filter)
                
                # For weekly content, verify weekday matches
                if post_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                    expected_weekday = {
                        'weekly_word': 1,
                        'weekly_phrase': 3,
                        'weekly_insult': 5
                    }.get(post_type)
                    query += " AND EXTRACT(ISODOW FROM pq.scheduled_date) = %s"
                    params.append(expected_weekday)
                
                # Order by created_at to get the oldest (first created) if duplicates exist
                query += " ORDER BY pq.created_at ASC LIMIT 1"
                
                cursor.execute(query, tuple(params))
                post = cursor.fetchone()
                
                if post:
                    post_dict = dict(post)
                    
                    # Format dates
                    for key in ['created_at', 'updated_at', 'scheduled_date', 'scheduled_timestamp']:
                        if post_dict.get(key) and hasattr(post_dict[key], 'isoformat'):
                            post_dict[key] = post_dict[key].isoformat()
                    if post_dict.get('scheduled_time'):
                        post_dict['scheduled_time'] = str(post_dict['scheduled_time'])
                    
                    # Determine title
                    if post_dict.get('product_name'):
                        post_dict['title'] = post_dict['product_name']
                    elif post_dict.get('idea_title'):
                        post_dict['title'] = post_dict['idea_title']
                    elif post_dict.get('content_type') == 'message' and post_dict.get('generated_content'):
                        content = post_dict['generated_content'] or ''
                        first_line = content.split('\n')[0].strip()
                        post_dict['title'] = first_line[:60] + ('...' if len(first_line) > 60 else '')
                    else:
                        post_dict['title'] = f"{post_dict.get('content_type', 'Post')} #{post_dict['queue_id']}"
                    
                    # Determine if post is due (scheduled time has passed)
                    scheduled_ts = post_dict.get('scheduled_timestamp')
                    if scheduled_ts:
                        try:
                            if isinstance(scheduled_ts, str):
                                if 'T' in scheduled_ts:
                                    scheduled_dt = datetime.fromisoformat(scheduled_ts.replace('Z', '+00:00'))
                                else:
                                    scheduled_dt = datetime.fromisoformat(scheduled_ts)
                            else:
                                scheduled_dt = scheduled_ts
                            now = datetime.now(scheduled_dt.tzinfo) if scheduled_dt.tzinfo else datetime.now()
                            post_dict['is_due'] = scheduled_dt <= now
                        except Exception as e:
                            logger.debug(f"Error parsing scheduled_timestamp {scheduled_ts}: {e}")
                            post_dict['is_due'] = False
                    else:
                        # Fallback: check scheduled_date + scheduled_time
                        try:
                            sched_date = post_dict.get('scheduled_date')
                            sched_time = post_dict.get('scheduled_time')
                            if sched_date and sched_time:
                                if isinstance(sched_date, str):
                                    sched_date = date.fromisoformat(sched_date.split('T')[0])
                                if isinstance(sched_time, str):
                                    time_parts = sched_time.split(':')
                                    sched_time = time_type(int(time_parts[0]), int(time_parts[1]) if len(time_parts) > 1 else 0)
                                scheduled_dt = datetime.combine(sched_date, sched_time)
                                post_dict['is_due'] = scheduled_dt <= datetime.now()
                            else:
                                post_dict['is_due'] = False
                        except Exception as e:
                            logger.debug(f"Error calculating is_due: {e}")
                            post_dict['is_due'] = False
                    
                    timeline_posts.append(post_dict)
            
            # Sort by scheduled date and time
            timeline_posts.sort(key=lambda p: (
                p.get('scheduled_date', ''),
                p.get('scheduled_time', '')
            ))
            
            # Limit results
            timeline_posts = timeline_posts[:limit]
            
            return jsonify({
                'success': True,
                'posts': timeline_posts,
                'total': len(timeline_posts)
            })
            
    except Exception as e:
        logger.error(f"Error in api_posts_timeline: {e}")
        logger.exception("Full exception details:")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/posts/<int:queue_id>/publish', methods=['POST'])
def api_publish_post(queue_id):
    """
    Manually publish a single post from posting_queue.

    Phase C1: Facebook publishing is only allowed through the scheduled posting executor
    so that weekday validation is enforced. This endpoint no longer calls publish_to_facebook.
    """
    try:
        # Phase C1 — Single authoritative gate: only scheduled_posting_executor may publish.
        # Manual publish would bypass weekday validation (wrong-day language, etc.).
        return jsonify({
            'success': False,
            'error': (
                'Facebook publishing must go through the scheduled posting executor. '
                'Manual publish is disabled for date safety. Use the executor (e.g. background monitor) to publish.'
            )
        }), 403
    except Exception as e:
        logger.error(f"Error in api_publish_post: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/posts/create-profile', methods=['POST'])
def api_create_profile_post():
    """Create a new profile post from a product"""
    try:
        from flask import request, jsonify
        from datetime import datetime
        import re
        
        data = request.get_json()
        product_id = data.get('product_id')
        product_name = data.get('product_name', 'Unnamed Product')
        
        if not product_id:
            return jsonify({'success': False, 'error': 'product_id is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Verify product exists and get its primary category
            cursor.execute("""
                SELECT id, name, category_ids
                FROM clan_products 
                WHERE id = %s
            """, (product_id,))
            product = cursor.fetchone()
            if not product:
                return jsonify({'success': False, 'error': 'Product not found'}), 404
            
            # Get primary category from product (first category in category_ids array)
            import json
            category_ids = product.get('category_ids')
            primary_category_id = None
            if category_ids:
                if isinstance(category_ids, list) and len(category_ids) > 0:
                    primary_category_id = category_ids[0]
                elif isinstance(category_ids, str):
                    try:
                        parsed = json.loads(category_ids)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            primary_category_id = parsed[0]
                    except:
                        pass
            
            # Generate slug from product name
            base = re.sub(r"[^a-z0-9\-]+", '-', (product_name or '').lower().strip().replace(' ', '-'))
            base = re.sub(r"-+", '-', base).strip('-') or 'profile'
            slug = base
            
            # Ensure slug uniqueness
            suffix = 1
            while True:
                cursor.execute("SELECT 1 FROM post WHERE slug = %s LIMIT 1", (slug,))
                if not cursor.fetchone():
                    break
                suffix += 1
                slug = f"{base}-{suffix}"
            
            # Create post with profile type
            # Note: post_type is determined by presence of profile_category_id (checked by get_post_type)
            # We set both profile_product_id and profile_category_id for product profiles
            cursor.execute("""
                INSERT INTO post (title, slug, status, profile_type, profile_product_id, profile_category_id, created_at, updated_at)
                VALUES (%s, %s, 'draft', 'product', %s, %s, NOW(), NOW())
                RETURNING id
            """, (product_name, slug, product_id, primary_category_id))
            
            post_id = cursor.fetchone()['id']
            
            # Create post_development entry
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed, updated_at)
                VALUES (%s, %s, NOW())
            """, (post_id, f"Profile post for {product_name}"))

            # W2-FIX-1: Ensure default sections for immediate authoring
            from utils.posts.post_factory import ensure_default_sections
            ensure_default_sections(post_id, variant='profile', template_name='default_profile')
            # W2-FIX-5: New post starts at workflow_stage=idea
            from utils.posts.workflow_stage import ensure_workflow_stage_idea
            ensure_workflow_stage_idea(post_id)
            return jsonify({
                'success': True,
                'post_id': post_id,
                'message': 'Profile post created successfully'
            })
            
    except Exception as e:
        logger.error(f"Error creating profile post: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/advance-stage', methods=['POST'])
def api_advance_workflow_stage(post_id):
    """
    W2-FIX-5: Advance post workflow stage. JSON: {"target_stage": "structured"|...}
    If target_stage=ready, also sets status=in_process (Mark Ready).
    """
    try:
        from utils.posts.workflow_stage import advance_stage, get_workflow_stage, STAGES
        data = request.get_json() or {}
        target = (data.get("target_stage") or "").strip().lower()
        if not target or target not in STAGES:
            return jsonify({
                "success": False,
                "error": f"target_stage required. Allowed: {', '.join(STAGES)}",
            }), 400
        override = data.get("override") or request.args.get("override") == "1"
        ok, err = advance_stage(post_id, target, actor="ui", override=override)
        if not ok:
            return jsonify({"success": False, "error": err or "Advance failed"}), (
                404 if "not found" in (err or "").lower() else 400
            )
        return jsonify({
            "success": True,
            "workflow_stage": get_workflow_stage(post_id, persist_if_missing=False),
        }), 200
    except Exception as e:
        logger.error(f"Error advancing workflow stage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/canonical-substages', methods=['GET'])
def api_get_canonical_substages(post_id):
    """W2 Phase 1: Canonical substage registry for post. Read-only; no execution."""
    try:
        from utils.taxonomy_helpers import get_post_type
        from utils.posts.early_stage import get_canonical_stage
        from utils.posts.stage_order import stage_index
        from utils.posts.canonical_substages import get_canonical_substages_for_post

        post_type = get_post_type(post_id)
        current_stage = get_canonical_stage(post_id)
        payload = get_canonical_substages_for_post(
            post_id=post_id,
            post_type=post_type,
            current_stage=current_stage,
            stage_index_fn=stage_index,
        )
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"Error getting canonical substages for post {post_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/early-stage', methods=['GET'])
def api_get_early_stage(post_id):
    """Instruction Set 8: Get early development stage + counts for UI (from DB)."""
    try:
        from utils.posts.early_stage import get_early_stage
        from config.database import db_manager
        stage = get_early_stage(post_id)
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS c FROM post_required_idea WHERE post_id = %s", (post_id,))
            r = cursor.fetchone()
            required_ideas_count = int(r.get("c", 0) if isinstance(r, dict) else (r[0] if r else 0))
            cursor.execute("SELECT COUNT(*) AS c FROM post_section WHERE post_id = %s", (post_id,))
            r = cursor.fetchone()
            sections_count = int(r.get("c", 0) if isinstance(r, dict) else (r[0] if r else 0))
        return jsonify({
            "success": True,
            "workflow_stage": stage,
            "required_ideas_count": required_ideas_count,
            "sections_count": sections_count,
        }), 200
    except Exception as e:
        logger.error(f"Error getting early stage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/advance-stage', methods=['POST'])
def api_advance_early_stage(post_id):
    """Instruction Set 8: Advance to next stage (explicit user action). Returns { success, new_stage } or { success: false, error }."""
    try:
        from utils.posts.early_stage import advance_post_stage
        ok, err, new_stage = advance_post_stage(post_id)
        if not ok:
            return jsonify({"success": False, "error": err or "Advance failed"}), (
                404 if err and "not found" in err.lower() else 400
            )
        return jsonify({"success": True, "new_stage": new_stage}), 200
    except Exception as e:
        logger.error(f"Error advancing early stage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/workflow-stage', methods=['GET'])
def api_get_workflow_stage(post_id):
    """
    W2-FIX-5: Get current workflow stage + next advanceable (for UI).
    Migrates legacy posts on first access.
    """
    try:
        from utils.posts.workflow_stage import get_workflow_stage, get_next_advanceable_stage
        stage = get_workflow_stage(post_id, persist_if_missing=True)
        next_stage = get_next_advanceable_stage(post_id)
        return jsonify({
            "success": True,
            "workflow_stage": stage,
            "next_advanceable": next_stage,
        }), 200
    except Exception as e:
        logger.error(f"Error getting workflow stage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/playbook', methods=['GET'])
def api_get_playbook(post_id):
    """W2 Phase 3: Get playbook and state. Idempotent init if missing. Does not mutate stage."""
    try:
        from utils.taxonomy_helpers import get_post_type
        from utils.posts.playbooks import get_playbook_and_state
        post_type = get_post_type(post_id)
        playbook, state = get_playbook_and_state(post_id, post_type)
        return jsonify({
            "success": True,
            "playbook": playbook,
            "state": state,
        }), 200
    except Exception as e:
        logger.error(f"Error getting playbook for post {post_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/playbook', methods=['PATCH'])
def api_patch_playbook(post_id):
    """W2 Phase 3: Update one task status. Does not mutate stage. Does not trigger automation."""
    try:
        from utils.posts.playbooks import update_task_state
        data = request.get_json() or {}
        stage = (data.get("stage") or "").strip()
        task_id = (data.get("task_id") or "").strip()
        status = (data.get("status") or "").strip().lower()
        note = (data.get("note") or "").strip() or None
        if not stage or not task_id or not status:
            return jsonify({
                "success": False,
                "error": "stage, task_id, and status are required",
            }), 400
        ok, err, playbook, state = update_task_state(post_id, stage=stage, task_id=task_id, status=status, note=note)
        if not ok:
            return jsonify({"success": False, "error": err or "Update failed"}), 400
        return jsonify({
            "success": True,
            "playbook": playbook,
            "state": state,
        }), 200
    except Exception as e:
        logger.error(f"Error updating playbook for post {post_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/posts/<int:post_id>/fields/status', methods=['POST'])
def api_update_post_status(post_id):
    """
    Update a post's status via canonical transitions (W2-FIX-4).
    Expected JSON: {"value": "deleted" | "draft" | "in_process" | "published" | "archived" | "restore"}
    
    - Cannot delete published posts (transition not allowed; use archive first)
    - restore: from deleted -> draft or published (based on clan_post_id)
    """
    try:
        from utils.posts.status_transitions import transition_post_status, get_post_status
        from config.database import db_manager

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        new_status = data.get('value')
        if not new_status:
            return jsonify({"error": "Status value is required"}), 400

        current = get_post_status(post_id)
        if not current:
            return jsonify({"error": "Post not found"}), 404

        target = (new_status or "").strip().lower()
        if target == "restore" and current == "deleted":
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    "SELECT clan_post_id, clan_uploaded_url FROM post WHERE id = %s",
                    (post_id,)
                )
                row = cursor.fetchone()
            target = "published" if (row and (row.get("clan_post_id") or row.get("clan_uploaded_url"))) else "draft"
        elif target == "restore":
            return jsonify({"error": "Restore only applies when status is deleted"}), 400

        override = data.get("override") or request.args.get("override") == "1"
        ok, err = transition_post_status(post_id, target, actor="posts_api", override=override)
        if not ok:
            return jsonify({"error": err or "Transition failed", "success": False}), (
                404 if "not found" in (err or "").lower() else 400
            )

        return jsonify({"success": True, "message": "Post status updated"})
    except Exception as e:
        logger.error(f"Error updating post status: {e}")
        return jsonify({"error": str(e)}), 500

