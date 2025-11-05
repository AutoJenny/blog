# blueprints/posts.py
"""
Posts Management Blueprint
Single-purpose module for post listing and status management.
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, date, timedelta
from config.database import db_manager
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
    status_lower = (status or '').lower()
    
    if status_lower in ['published', 'live']:
        return 'published'
    elif status_lower == 'error':
        return 'error'
    elif status_lower == 'publishing':
        return 'publishing'
    elif status_lower == 'deleted':
        return 'deleted'
    else:
        return status_lower or 'draft'


def get_week_start_end(year: int, week_number: int):
    """Return Monday and Sunday dates for ISO week."""
    try:
        # ISO week: Monday is 1
        monday = date.fromisocalendar(year, week_number, 1)
        sunday = date.fromisocalendar(year, week_number, 7)
        return monday, sunday
    except Exception:
        return None, None


@bp.route('/posts')
def posts_list():
    """
    HTML page listing all posts with show/delete functionality.
    Supports ?show_deleted=1 query parameter to show deleted posts.
    """
    show_deleted = request.args.get('show_deleted', '0') == '1'
    
    try:
        with db_manager.get_cursor() as cursor:
            # Check if calendar_week_posts table exists, otherwise use calendar_schedule
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts'
                )
            """)
            result = cursor.fetchone()
            # Handle both tuple and dict return types from psycopg
            if isinstance(result, tuple):
                has_week_posts_table = result[0]
            elif isinstance(result, dict):
                has_week_posts_table = result.get('exists', False)
            else:
                has_week_posts_table = False
            
            if has_week_posts_table:
                # Use new calendar_week_posts table (V2 architecture)
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
                # Fallback to calendar_schedule (legacy)
                if show_deleted:
                    cursor.execute("""
                        SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                               p.recipe_week_number, p.profile_category_id,
                               cs.year AS sched_year, cs.week_number AS sched_week, cs.scheduled_date
                        FROM post p
                        LEFT JOIN LATERAL (
                            SELECT year, week_number, scheduled_date, updated_at
                            FROM calendar_schedule
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
                               p.recipe_week_number, p.profile_category_id,
                               cs.year AS sched_year, cs.week_number AS sched_week, cs.scheduled_date
                        FROM post p
                        LEFT JOIN LATERAL (
                            SELECT year, week_number, scheduled_date, updated_at
                            FROM calendar_schedule
                            WHERE post_id = p.id
                            ORDER BY scheduled_date DESC NULLS LAST, updated_at DESC
                            LIMIT 1
                        ) cs ON TRUE
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
        
        # Format posts for template
        formatted_posts = []
        for post in posts:
            sched_year = post.get('sched_year') if isinstance(post, dict) else post['sched_year']
            sched_week = post.get('sched_week') if isinstance(post, dict) else post['sched_week']
            week_label = None
            week_sort_key = None
            week_dates_small = ''
            if sched_year and sched_week:
                week_label = f"W{int(sched_week)}"
                week_sort_key = int(sched_year) * 100 + int(sched_week)
                week_start, week_end = get_week_start_end(int(sched_year), int(sched_week))
                if week_start and week_end:
                    week_dates_small = f"{week_start.strftime('%a %d %b %Y')} – {week_end.strftime('%a %d %b %Y')}"

            created_ts = int(post['created_at'].timestamp() * 1000) if post.get('created_at') else 0
            updated_ts = int(post['updated_at'].timestamp() * 1000) if post.get('updated_at') else 0
            
            post_type = determine_post_type(post)

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
                             show_deleted=show_deleted)
        
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
                        FROM calendar_schedule
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
                        FROM calendar_schedule
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


@bp.route('/api/posts/<int:post_id>/fields/status', methods=['POST'])
def api_update_post_status(post_id):
    """
    Update a post's status.
    Used by posts_list.html template for delete/restore operations.
    
    Expected JSON: {"value": "deleted" | "draft" | "published" | "restore" | etc.}
    
    - Cannot delete published posts (returns error)
    - When restoring from deleted, restores to 'published' if it was published before
    - Otherwise normal status update
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        new_status = data.get('value')
        if not new_status:
            return jsonify({"error": "Status value is required"}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get current status
                cursor.execute("SELECT status FROM post WHERE id = %s", (post_id,))
                current = cursor.fetchone()
                
                if not current:
                    return jsonify({"error": "Post not found"}), 404
                
                current_status = current['status']
                
                # Prevent deletion of published posts
                if new_status == 'deleted' and current_status == 'published':
                    return jsonify({
                        "error": "Cannot delete published posts. Please unpublish first.",
                        "success": False
                    }), 400
                
                # When restoring from deleted, check if it should be restored to published
                # We'll check if there's a clan_post_id or other indicators it was published
                if current_status == 'deleted' and new_status == 'restore':
                    # Check if post was published by looking for indicators
                    cursor.execute("""
                        SELECT clan_post_id, clan_uploaded_url 
                        FROM post 
                        WHERE id = %s
                    """, (post_id,))
                    post_info = cursor.fetchone()
                    
                    # If it has clan_post_id or uploaded_url, it was likely published
                    if post_info and (post_info.get('clan_post_id') or post_info.get('clan_uploaded_url')):
                        restore_to = 'published'
                    else:
                        restore_to = 'draft'
                    
                    cursor.execute("""
                        UPDATE post 
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (restore_to, post_id))
                else:
                    # Normal status update
                    cursor.execute("""
                        UPDATE post 
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_status, post_id))
                
                conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"Post status updated"
        })
        
    except Exception as e:
        logger.error(f"Error updating post status: {e}")
        return jsonify({"error": str(e)}), 500

