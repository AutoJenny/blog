"""Helper functions for header blueprint"""
import logging

logger = logging.getLogger(__name__)


def resolve_target_post_id(post_id, year=None, week=None, require_week=False):
    """
    Resolve target_post_id from week context, preserving post_id for recipe/profile posts.
    
    Args:
        post_id: Original post_id from URL
        year: Year from query params (optional)
        week: Week from query params (optional)
        require_week: If True, return error if year/week not provided
    
    Returns:
        tuple: (target_post_id, error_message)
        If error_message is not None, target_post_id should be ignored
    """
    from utils.taxonomy_helpers import get_post_type
    from utils.week_post_resolver import resolve_post_for_week
    
    # Get post type for the original post_id first
    original_post_type = get_post_type(post_id)
    
    # For recipe/profile posts, always preserve original post_id
    if original_post_type in ('recipe', 'profile'):
        return (post_id, None)
    
    # For themed posts, resolve from week context
    if require_week and (not year or not week):
        return (None, 'Week context (year and week) is required')
    
    if year and week:
        target_post_id = resolve_post_for_week(year, week)
        if not target_post_id:
            return (None, f'No post scheduled for week {week}, {year}')
        return (target_post_id, None)
    
    # No week context and not required - use provided post_id
    return (post_id, None)

