"""
Template Helper Utilities

Provides helper functions for ensuring consistent template variables across routes.
"""

from config.database import db_manager
from utils.taxonomy_helpers import get_post_type
import logging

logger = logging.getLogger(__name__)


def get_standard_template_vars(post_id, year=None, week=None, **extra_vars):
    """
    Get standard template variables including post_type, post data, and content_type.
    
    This ensures all routes pass consistent variables to templates, especially post_type.
    
    Args:
        post_id (int): Post ID
        year (int, optional): Year for week context
        week (int, optional): Week number for week context
        **extra_vars: Additional variables to include in the result
    
    Returns:
        dict: Dictionary of template variables including:
            - post_id
            - post_type
            - post (dict with id, title, status, created_at, updated_at, content_type_id)
            - post_title
            - post_status
            - post_created
            - post_updated
            - content_type_name (if available)
            - year (if provided)
            - week/week_number (if provided)
            - Any additional variables from **extra_vars
    """
    try:
        # Get post_type
        post_type = get_post_type(post_id)
        
        # Get post data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                logger.warning(f"Post {post_id} not found")
                post = {}
            
            # Get content_type_name
            content_type_name = None
            if post and post.get('content_type_id'):
                cursor.execute("""
                    SELECT ti.display_name as content_type_name
                    FROM taxonomy_item ti
                    WHERE ti.id = %s
                """, (post.get('content_type_id'),))
                result = cursor.fetchone()
                content_type_name = result.get('content_type_name') if result else None
        
        # Build standard vars
        template_vars = {
            'post_id': post_id,
            'post_type': post_type,
            'post': post if isinstance(post, dict) else {},
            'post_title': post.get('title') if post else None,
            'post_status': post.get('status') if post else None,
            'post_created': post.get('created_at') if post else None,
            'post_updated': post.get('updated_at') if post else None,
            'content_type_name': content_type_name,
        }
        
        # Add week context if provided
        if year is not None:
            template_vars['year'] = year
        if week is not None:
            template_vars['week'] = week
            template_vars['week_number'] = week  # Alias for consistency
        
        # Add any extra variables
        template_vars.update(extra_vars)
        
        return template_vars
        
    except Exception as e:
        logger.error(f"Error getting standard template vars for post {post_id}: {e}")
        # Return minimal vars on error
        return {
            'post_id': post_id,
            'post_type': 'themed',  # Safe default
            'post': {},
            'post_title': None,
            'post_status': None,
            'post_created': None,
            'post_updated': None,
            'content_type_name': None,
            **extra_vars
        }

