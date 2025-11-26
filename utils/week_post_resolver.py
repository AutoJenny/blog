"""
Week/Post Resolution Utility

SINGLE SOURCE OF TRUTH for resolving post_id from year/week context.

NO FALLBACKS. Returns None if week has no scheduled post.
This forces explicit handling of missing data rather than silently using wrong posts.

⚠️ CRITICAL WARNING ⚠️
=====================

DO NOT USE THIS FUNCTION WHEN post_id IS PROVIDED IN THE URL!

This function is ONLY for:
- Displaying which post is scheduled for a week (calendar view)
- Publishing/scheduling operations
- Finding posts by week context when post_id is NOT in URL

NEVER use this function in routes that have post_id in the URL parameter.
When post_id is in the URL, it is the DEFINITIVE identifier.
Week parameters (?year=X&week=Y) are CONTEXT ONLY, not identifiers.

Example of WRONG usage:
    @bp.route('/posts/<int:post_id>/taxonomy')
    def taxonomy(post_id):
        resolved = resolve_post_for_week(year, week)  # ❌ WRONG!
        # This changes post_id from URL, causing data to go to wrong post

Example of CORRECT usage:
    @bp.route('/posts/<int:post_id>/taxonomy')
    def taxonomy(post_id):
        target_post_id = post_id  # ✅ CORRECT - use URL post_id
        # Week is only for context/display, not for changing post_id
"""

from config.database import db_manager
import logging

logger = logging.getLogger(__name__)


def resolve_post_for_week(year, week_number, cursor=None):
    """
    Resolve the post_id scheduled for a specific week.
    
    Args:
        year: Integer year
        week_number: Integer week number (1-52)
        cursor: Optional database cursor (if None, creates new one)
    
    Returns:
        int|None: post_id if found, None if no post scheduled for this week
        
    NO FALLBACKS. If week has no post_id, returns None.
    This ensures callers handle missing data explicitly rather than using wrong posts.
    """
    if not year or not week_number:
        logger.warning(f"resolve_post_for_week called with invalid params: year={year}, week={week_number}")
        return None
    
    # Use provided cursor or create new one
    if cursor:
        return _resolve_with_cursor(cursor, year, week_number)
    else:
        with db_manager.get_cursor() as cursor:
            return _resolve_with_cursor(cursor, year, week_number)


def _resolve_with_cursor(cursor, year, week_number):
    """Internal implementation using provided cursor"""
    # SINGLE SOURCE OF TRUTH: Query calendar_week_posts for this specific week
    # Check if new table exists first (for migration period)
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'calendar_week_posts'
        )
    """)
    has_new_table = cursor.fetchone()['exists']
    
    if has_new_table:
        # Use new calendar_week_posts table
        # FIX: Join with post table to filter out deleted posts
        cursor.execute("""
            SELECT cwp.post_id
            FROM calendar_week_posts cwp
            JOIN post p ON cwp.post_id = p.id
            WHERE cwp.year = %s 
              AND cwp.week_number = %s
              AND p.status != 'deleted'
            ORDER BY cwp.created_at DESC
            LIMIT 1
        """, (year, week_number))
    else:
        # Fallback to old calendar_schedule table during migration
        # FIX: Join with post table to filter out deleted posts
        cursor.execute("""
            SELECT cs.post_id
            FROM calendar_schedule cs
            JOIN post p ON cs.post_id = p.id
            WHERE cs.year = %s 
              AND cs.week_number = %s
              AND cs.post_id IS NOT NULL
              AND p.status != 'deleted'
            ORDER BY cs.created_at DESC
            LIMIT 1
        """, (year, week_number))
    
    result = cursor.fetchone()
    
    if result and result['post_id']:
        logger.debug(f"Resolved post_id {result['post_id']} for week {year}/{week_number}")
        return result['post_id']
    else:
        logger.debug(f"No active post_id found for week {year}/{week_number}")
        return None

