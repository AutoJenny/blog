"""
Taxonomy Helper Utilities

Centralized functions for retrieving taxonomy-related data, particularly
illustration_method and category-based prompt selection.

Supports two types of category variance:
1. Process-level variance: Different workflows (e.g., Photo-harvesting)
2. Prompt-level variance: Same process, different prompts (e.g., Landscapes & Seasons)
"""

from config.database import db_manager
import logging

logger = logging.getLogger(__name__)


def get_illustration_method(post_id, default='LLM-creation'):
    """
    Get illustration_method for a post from taxonomy.
    
    Standardizes retrieval across all blueprints. Uses LEFT JOIN to handle
    cases where content_type_id might be NULL.
    
    Args:
        post_id (int): The post ID to look up
        default (str): Default value if not found or NULL. Defaults to 'LLM-creation'
    
    Returns:
        str: The illustration_method value or default
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT content_type.illustration_method
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result.get('illustration_method'):
                return result['illustration_method']
            
            logger.debug(f"Post {post_id} has no illustration_method, using default: {default}")
            return default
    except Exception as e:
        logger.error(f"Error retrieving illustration_method for post {post_id}: {e}")
        return default


def get_content_type_name(post_id):
    """
    Get content_type_name for a post from taxonomy.
    
    Used for prompt-level variance (category-specific prompts).
    
    Args:
        post_id (int): The post ID to look up
    
    Returns:
        str: The content_type name or None
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT content_type.name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result.get('content_type_name'):
                return result['content_type_name']
            
            return None
    except Exception as e:
        logger.error(f"Error retrieving content_type_name for post {post_id}: {e}")
        return None


def get_category_prompt_name(base_name, illustration_method, content_type_name=None):
    """
    Get prompt name based on variance type.
    
    Supports two variance types:
    1. Process-level variance: Uses illustration_method (e.g., Photo-harvesting)
    2. Prompt-level variance: Uses content_type_name (e.g., Landscapes & Seasons)
    
    Args:
        base_name (str): Base prompt name (e.g., 'Image Concepts Generation')
        illustration_method (str): Illustration method from taxonomy
        content_type_name (str, optional): Content type name for prompt-level variance
    
    Returns:
        str: Category-specific prompt name or base name
    
    Examples:
        # Process-level variance
        get_category_prompt_name('Image Concepts Generation', 'Photo-harvesting')
        # Returns: 'Image Concepts Generation (Photo-harvesting)'
        
        # Prompt-level variance
        get_category_prompt_name('Image Concepts Generation', 'LLM-creation', 'Landscapes & Seasons')
        # Returns: 'Image Concepts Generation (Landscapes & Seasons)'
        
        # Default
        get_category_prompt_name('Image Concepts Generation', 'LLM-creation')
        # Returns: 'Image Concepts Generation'
    """
    # Process-level variance: Photo-harvesting uses different prompts
    if illustration_method == 'Photo-harvesting':
        prompt_name = f"{base_name} (Photo-harvesting)"
        logger.debug(f"Using process-level variance prompt: {prompt_name}")
        return prompt_name
    
    # Prompt-level variance: Use content_type_name if provided
    if content_type_name:
        prompt_name = f"{base_name} ({content_type_name})"
        logger.debug(f"Using prompt-level variance prompt: {prompt_name}")
        return prompt_name
    
    # Default: return base name
    logger.debug(f"Using default prompt: {base_name}")
    return base_name


def get_illustration_method_with_post(post_id, year=None, week=None, default='LLM-creation'):
    """
    Get illustration_method with optional week context resolution.
    
    If year and week are provided, resolves the target post_id first using
    week context, then retrieves illustration_method.
    
    Args:
        post_id (int): Initial post ID from URL
        year (int, optional): Year for week context
        week (int, optional): Week number for week context
        default (str): Default value if not found
    
    Returns:
        tuple: (target_post_id, illustration_method)
    """
    target_post_id = post_id
    
    # Resolve week context if provided
    if year and week:
        try:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(year, week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.debug(f"Week {year}/{week} resolved to post_id {target_post_id}")
            else:
                logger.warning(f"Week {year}/{week} has no scheduled post - using URL post_id {post_id}")
        except Exception as e:
            logger.error(f"Error resolving week context: {e}")
    
    illustration_method = get_illustration_method(target_post_id, default)
    return target_post_id, illustration_method

