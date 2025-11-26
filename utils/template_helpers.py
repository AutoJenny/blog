"""
Template Helper Utilities

Provides helper functions for ensuring consistent template variables across routes.
"""

from config.database import db_manager
from utils.taxonomy_helpers import get_post_type
from config.template_mappings import get_template_path
from config.post_type_substages import get_substages_for_post_type, get_substage_metadata, get_substage_label
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
        
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at, p.content_type_id
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return {
                    'post_id': post_id,
                    'post_type': post_type,
                    'post': None,
                    'error': 'Post not found',
                    **extra_vars
                }
            
            # Format dates
            post_created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post.get('created_at') else 'Unknown'
            post_updated = post['updated_at'].strftime('%Y-%m-%d %H:%M') if post.get('updated_at') else 'Unknown'
            
            # Get content_type_name
            content_type_name = None
            if post.get('content_type_id'):
                cursor.execute("""
                    SELECT ti.display_name as content_type_name
                    FROM taxonomy_item ti
                    WHERE ti.id = %s
                """, (post['content_type_id'],))
                result = cursor.fetchone()
                content_type_name = result.get('content_type_name') if result else None
        
        return {
            'post_id': post_id,
            'post_type': post_type,
            'post': post,
            'post_title': post.get('title'),
            'post_status': post.get('status'),
            'post_created': post_created,
            'post_updated': post_updated,
            'content_type_name': content_type_name,
            'year': year,
            'week': week,
            'week_number': week,  # Alias for compatibility
            **extra_vars
        }
    except Exception as e:
        logger.error(f"Error getting standard template vars for post {post_id}: {e}", exc_info=True)
        return {
            'post_id': post_id,
            'post_type': get_post_type(post_id),
            'error': str(e),
            **extra_vars
        }


def resolve_template_for_route(stage, substage, post_id):
    """
    Resolve the correct template path for a route based on stage, substage, and post_type.
    
    This is a convenience function that combines get_post_type and get_template_path.
    
    Args:
        stage (str): Stage name (e.g., 'concept', 'imaging')
        substage (str): Substage name (e.g., 'section-structure', 'image-generation')
        post_id (int): Post ID to determine post_type
    
    Returns:
        str: Template path, or None if not found
    """
    post_type = get_post_type(post_id)
    return get_template_path(stage, substage, post_type)


def get_substages_for_navbar(post_type, stage):
    """
    Get substages for navbar display, with metadata for rendering.
    
    Args:
        post_type (str): Post type ('themed', 'profile', 'generated', 'recipe')
        stage (str): Stage name ('calendar', 'planning', 'research', 'authoring', 'imaging', 'header')
    
    Returns:
        list: List of dicts with 'key', 'label', 'route_function', 'order'
    """
    from config.post_type_substages import get_substages_with_metadata
    
    substages = get_substages_with_metadata(post_type, stage)
    return substages
