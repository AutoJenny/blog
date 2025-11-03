"""
Planning Calendar API Utilities

Shared utility functions for calendar API endpoints
"""

from flask import request
import logging

logger = logging.getLogger(__name__)

def _safe_parse_json_request():
    """Parse JSON body without triggering 'Body is disturbed or locked' errors.
    Uses Flask's get_json which handles stream caching internally - safest approach.
    """
    # Use get_json with silent=True (without force=True to avoid stream issues)
    # silent=True returns None on error instead of raising
    # Content-Type: application/json is set by the client, so force shouldn't be needed
    try:
        data = request.get_json(silent=True)
        if data is not None and isinstance(data, dict):
            return data
        # If we got something but it's not a dict, return empty dict
        return {}
    except RuntimeError as e:
        # "Body is disturbed or locked" is a RuntimeError from Flask
        # If this happens, log it and try to access cached data
        if 'disturbed' in str(e).lower() or 'locked' in str(e).lower():
            logger.warning(f"Request body already consumed, trying cached JSON: {e}")
            # Try to access Flask's internal cache
            if hasattr(request, '_cached_json') and request._cached_json:
                return request._cached_json if isinstance(request._cached_json, dict) else {}
        logger.error(f"Error parsing JSON request: {e}", exc_info=True)
        return {}
    except Exception as e:
        # Any other error
        logger.error(f"Error parsing JSON request: {e}", exc_info=True)
        return {}

def _current_iso_week():
    from datetime import datetime
    return datetime.utcnow().isocalendar().week


def resolve_post_for_route(post_id, require_week_context=False):
    """
    Helper function for route handlers to resolve correct post_id based on week context.
    
    Args:
        post_id: Post ID from URL parameter
        require_week_context: If True, return None if week context missing
    
    Returns:
        tuple: (resolved_post_id, year, week) or (post_id, None, None) if no week context
    """
    from flask import request
    from utils.week_post_resolver import resolve_post_for_week
    
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    if require_week_context and (not year or not week):
        return None, None, None
    
    # If week context provided, resolve correct post
    if year and week:
        resolved_post_id = resolve_post_for_week(year, week)
        if resolved_post_id:
            return resolved_post_id, year, week
    
    # No week context or no resolved post, return original post_id
    return post_id, year, week
