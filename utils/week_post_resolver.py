"""
Week/Post Resolution Utility

SINGLE SOURCE OF TRUTH for resolving post_id from year/week context.

NO FALLBACKS. Returns None if week has no scheduled post.
This forces explicit handling of missing data rather than silently using wrong posts.
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
        cursor.execute("""
            SELECT post_id
            FROM calendar_week_posts
            WHERE year = %s 
              AND week_number = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (year, week_number))
    else:
        # Fallback to old calendar_schedule table during migration
        cursor.execute("""
            SELECT post_id
            FROM calendar_schedule
            WHERE year = %s 
              AND week_number = %s
              AND post_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        """, (year, week_number))
    
    result = cursor.fetchone()
    
    if result and result['post_id']:
        logger.debug(f"Resolved post_id {result['post_id']} for week {year}/{week_number}")
        return result['post_id']
    else:
        logger.debug(f"No post_id found for week {year}/{week_number}")
        return None

