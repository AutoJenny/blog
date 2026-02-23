"""
Database-Backed Substage Configuration
Replaces config/post_type_substages.py with database-backed functions.

Maintains backward compatibility with existing function signatures.
"""

import time
import logging
from config.database import db_manager

logger = logging.getLogger(__name__)

# Cache configuration
_substage_cache = {}
_metadata_cache = {}
_cache_timestamp = None
CACHE_TTL = 300  # 5 minutes


def _refresh_cache():
    """Refresh cache from database"""
    global _substage_cache, _metadata_cache, _cache_timestamp
    
    try:
        with db_manager.get_cursor() as cursor:
            # Load substage metadata
            cursor.execute("""
                SELECT substage_key, label, route_function, display_order, stage, is_active
                FROM substage_metadata
                WHERE is_active = TRUE
                ORDER BY stage, display_order
            """)
            _metadata_cache = {}
            for row in cursor.fetchall():
                _metadata_cache[row['substage_key']] = {
                    'label': row['label'],
                    'route_function': row['route_function'],
                    'order': row['display_order'],
                    'stage': row['stage']
                }
            
            # Load post_type_substages
            cursor.execute("""
                SELECT post_type, stage, substage_key, display_order
                FROM post_type_substages
                WHERE is_active = TRUE
                ORDER BY post_type, stage, display_order
            """)
            _substage_cache = {}
            for row in cursor.fetchall():
                post_type = row['post_type']
                stage = row['stage']
                substage_key = row['substage_key']
                
                if post_type not in _substage_cache:
                    _substage_cache[post_type] = {}
                if stage not in _substage_cache[post_type]:
                    _substage_cache[post_type][stage] = []
                
                _substage_cache[post_type][stage].append(substage_key)
            
            _cache_timestamp = time.time()
            logger.debug(f"Refreshed substage cache: {len(_metadata_cache)} metadata, {len(_substage_cache)} post types")
            
    except Exception as e:
        logger.error(f"Error refreshing substage cache: {e}", exc_info=True)
        # Keep existing cache if refresh fails
        if _cache_timestamp is None:
            raise


def _ensure_cache():
    """Ensure cache is up to date"""
    if _cache_timestamp is None or (time.time() - _cache_timestamp) > CACHE_TTL:
        _refresh_cache()


def get_substages_for_post_type(post_type, stage=None):
    """
    Get substages for a post type, optionally filtered by stage.
    
    Args:
        post_type (str): Post type ('themed', 'profile', 'generated', 'recipe', 'weekly_word', 'weekly_phrase', 'weekly_insult')
        stage (str, optional): Stage name ('calendar', 'planning', 'research', 'authoring', 'imaging', 'header', 'content')
    
    Returns:
        dict or list: If stage is None, returns dict of {stage: [substages]}. 
                     If stage is provided, returns list of substage keys.
    
    Examples:
        >>> get_substages_for_post_type('themed', 'planning')
        ['ideas', 'taxonomy', 'topic_brainstorming', 'section_structure', 'topic_allocation', 'section_titling']
        
        >>> get_substages_for_post_type('profile')
        {'planning': ['taxonomy', ...], 'authoring': [...], ...}
    """
    _ensure_cache()
    
    # Normalize post_type - default to 'themed' if invalid
    if post_type not in _substage_cache:
        logger.warning(f"Unknown post_type '{post_type}', defaulting to 'themed'")
        post_type = 'themed'
    
    if post_type not in _substage_cache:
        # DB cache empty - fall back to config for legacy compatibility (W2-FIX-8)
        try:
            from config.post_type_substages import POST_TYPE_SUBSTAGES
            fallback = POST_TYPE_SUBSTAGES.get(post_type, POST_TYPE_SUBSTAGES.get('themed', {}))
            if fallback:
                logger.warning(
                    "substage_config: DB empty for post_type=%s, using config fallback. "
                    "Populate post_type_substages table for DB-backed config.",
                    post_type
                )
                if stage:
                    return fallback.get(stage, [])
                return fallback
        except ImportError:
            pass
        return [] if stage else {}
    
    substages = _substage_cache[post_type]
    
    if stage:
        return substages.get(stage, [])
    
    return substages.copy()  # Return copy to prevent mutation


def get_substage_metadata(substage_key):
    """
    Get metadata for a substage (label, route, order).
    
    Args:
        substage_key (str): Substage key (e.g., 'ideas', 'taxonomy')
    
    Returns:
        dict: Metadata dict with 'label', 'route_function', 'order', 'stage', or None if not found
    """
    _ensure_cache()
    return _metadata_cache.get(substage_key)


def get_substage_label(substage_key):
    """
    Get display label for a substage.
    
    Args:
        substage_key (str): Substage key
    
    Returns:
        str: Display label, or substage_key if not found
    """
    metadata = get_substage_metadata(substage_key)
    if metadata:
        return metadata['label']
    # Fallback: format the key
    return substage_key.replace('_', ' ').title()


def is_substage_valid_for_post_type(post_type, stage, substage_key):
    """
    Check if a substage is valid for a given post type and stage.
    
    Args:
        post_type (str): Post type
        stage (str): Stage name
        substage_key (str): Substage key
    
    Returns:
        bool: True if substage is valid for post_type/stage, False otherwise
    """
    substages = get_substages_for_post_type(post_type, stage)
    return substage_key in substages


def get_all_substages_for_stage(stage):
    """
    Get all substages that exist for a stage across all post types.
    Useful for API responses that need to include all possible substages.
    
    Args:
        stage (str): Stage name
    
    Returns:
        set: Set of all substage keys for the stage
    """
    _ensure_cache()
    all_substages = set()
    for post_type in _substage_cache:
        substages = get_substages_for_post_type(post_type, stage)
        all_substages.update(substages)
    return all_substages


def get_substages_with_metadata(post_type, stage=None):
    """
    Get substages with full metadata for a post type.
    
    Args:
        post_type (str): Post type
        stage (str, optional): Stage name
    
    Returns:
        dict or list: If stage is None, returns dict of {stage: [{substage_data}]}.
                     If stage is provided, returns list of substage data dicts.
    
    Example:
        >>> get_substages_with_metadata('themed', 'planning')
        [
            {'key': 'ideas', 'label': 'Ideas', 'route_function': '...', 'order': 1, 'stage': 'planning'},
            {'key': 'taxonomy', 'label': 'Taxonomy', 'route_function': '...', 'order': 2, 'stage': 'planning'},
            ...
        ]
    """
    substages = get_substages_for_post_type(post_type, stage)
    
    if stage:
        # Return list of substage data dicts
        result = []
        for substage_key in substages:
            metadata = get_substage_metadata(substage_key)
            if metadata:
                result.append({
                    'key': substage_key,
                    'label': metadata['label'],
                    'route_function': metadata['route_function'],
                    'order': metadata['order'],
                    'stage': metadata['stage']
                })
            else:
                result.append({
                    'key': substage_key,
                    'label': get_substage_label(substage_key),
                    'route_function': None,
                    'order': 999,
                    'stage': stage
                })
        # Sort by order
        result.sort(key=lambda x: x.get('order', 999))
        return result
    else:
        # Return dict of {stage: [substage_data]}
        result = {}
        for stage_name, substage_keys in substages.items():
            result[stage_name] = []
            for substage_key in substage_keys:
                metadata = get_substage_metadata(substage_key)
                if metadata:
                    result[stage_name].append({
                        'key': substage_key,
                        'label': metadata['label'],
                        'route_function': metadata['route_function'],
                        'order': metadata['order'],
                        'stage': metadata['stage']
                    })
                else:
                    result[stage_name].append({
                        'key': substage_key,
                        'label': get_substage_label(substage_key),
                        'route_function': None,
                        'order': 999,
                        'stage': stage_name
                    })
            # Sort by order
            result[stage_name].sort(key=lambda x: x.get('order', 999))
        return result


def invalidate_cache():
    """Invalidate the cache (force refresh on next access)"""
    global _cache_timestamp
    _cache_timestamp = None
    logger.info("Substage cache invalidated")


def get_all_post_types():
    """Get list of all post types configured in the database"""
    _ensure_cache()
    return list(_substage_cache.keys())


def get_all_stages():
    """Get list of all stages configured in the database"""
    _ensure_cache()
    stages = set()
    for post_type_config in _substage_cache.values():
        stages.update(post_type_config.keys())
    return sorted(list(stages))

