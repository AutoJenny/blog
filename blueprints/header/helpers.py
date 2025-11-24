"""Helper functions for header blueprint"""
import logging

logger = logging.getLogger(__name__)


def resolve_target_post_id_with_auto_week_check(post_id, year=None, week=None):
    """
    Resolve target_post_id with automatic week requirement check based on post type.
    Non-themed posts (recipe, profile, generated) don't require week context.
    
    Args:
        post_id: Original post_id from URL
        year: Year from query params (optional)
        week: Week from query params (optional)
    
    Returns:
        tuple: (target_post_id, error_message)
        If error_message is not None, target_post_id should be ignored
    """
    from utils.taxonomy_helpers import get_post_type
    
    post_type = get_post_type(post_id)
    non_themed_types = ('recipe', 'profile', 'generated')
    require_week = post_type not in non_themed_types
    
    return resolve_target_post_id(post_id, year, week, require_week=require_week)


def resolve_target_post_id(post_id, year=None, week=None, require_week=False):
    """
    Resolve target_post_id from week context, preserving post_id for non-themed posts.
    
    Args:
        post_id: Original post_id from URL
        year: Year from query params (optional)
        week: Week from query params (optional)
        require_week: If True, return error if year/week not provided (only for themed posts)
    
    Returns:
        tuple: (target_post_id, error_message)
        If error_message is not None, target_post_id should be ignored
    """
    from utils.taxonomy_helpers import get_post_type
    from utils.week_post_resolver import resolve_post_for_week
    
    # Get post type for the original post_id first
    original_post_type = get_post_type(post_id)
    
    # Non-themed post types don't require week context
    non_themed_types = ('recipe', 'profile', 'generated')
    
    # For non-themed posts, always preserve original post_id (no week context needed)
    if original_post_type in non_themed_types:
        return (post_id, None)
    
    # For themed posts, resolve from week context
    if require_week and (not year or not week):
        return (None, 'Week context (year and week) is required for themed posts')
    
    if year and week:
        target_post_id = resolve_post_for_week(year, week)
        if not target_post_id:
            return (None, f'No post scheduled for week {week}, {year}')
        return (target_post_id, None)
    
    # No week context and not required - use provided post_id
    return (post_id, None)

