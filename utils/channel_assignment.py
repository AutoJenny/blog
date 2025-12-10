"""
Channel Assignment Utilities
Helper functions for resolving channel assignments and content formats.
"""

import logging
from typing import Optional, List, Dict, Any
from config.database import db_manager

logger = logging.getLogger(__name__)


def get_channels_for_post_type(post_type: str) -> List[Dict[str, Any]]:
    """
    Get all (channel, content_format) pairs for a post type.
    
    Args:
        post_type: Post type ('themed', 'recipe', 'weekly_word', etc.)
    
    Returns:
        list: List of dicts with 'channel', 'content_format', 'is_primary', 'is_required'
    
    Example:
        >>> get_channels_for_post_type('weekly_word')
        [
            {'channel': 'facebook', 'content_format': 'word_of_day', 'is_primary': True, 'is_required': True},
            {'channel': 'instagram', 'content_format': 'word_of_day', 'is_primary': False, 'is_required': True}
        ]
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT channel, content_format, is_primary, is_required, 
                       publication_delay_hours, publication_time
                FROM post_type_channel_config
                WHERE post_type = %s AND is_active = TRUE
                ORDER BY is_primary DESC, channel, content_format
            """, (post_type,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting channels for post type {post_type}: {e}")
        return []


def get_content_format(post_type: str, channel: str) -> Optional[str]:
    """
    Get the content format for a (post_type, channel) combination.
    
    If multiple formats exist, returns the primary format, or the first one.
    
    Args:
        post_type: Post type
        channel: Channel name
    
    Returns:
        str: Content format name, or None if not found
    
    Example:
        >>> get_content_format('weekly_word', 'facebook')
        'word_of_day'
        
        >>> get_content_format('recipe', 'blog')
        'recipe'
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT content_format
                FROM post_type_channel_config
                WHERE post_type = %s AND channel = %s AND is_active = TRUE
                ORDER BY is_primary DESC
                LIMIT 1
            """, (post_type, channel))
            
            result = cursor.fetchone()
            if result:
                return result['content_format']
            return None
    except Exception as e:
        logger.error(f"Error getting content format for {post_type}/{channel}: {e}")
        return None


def get_all_formats_for_channel(channel: str) -> List[str]:
    """
    Get all content formats available for a channel.
    
    Args:
        channel: Channel name
    
    Returns:
        list: List of format names
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT content_format
                FROM post_type_channel_config
                WHERE channel = %s AND is_active = TRUE
                ORDER BY content_format
            """, (channel,))
            
            results = cursor.fetchall()
            return [row['content_format'] for row in results]
    except Exception as e:
        logger.error(f"Error getting formats for channel {channel}: {e}")
        return []


def should_create_blog_post(post_type: str) -> bool:
    """
    Check if a post type should create a blog post.
    
    Args:
        post_type: Post type
    
    Returns:
        bool: True if blog post should be created, False otherwise
    """
    channels = get_channels_for_post_type(post_type)
    
    # Check if 'blog' channel exists
    for channel_info in channels:
        if channel_info['channel'] == 'blog':
            return True
    
    return False


def get_primary_channel(post_type: str) -> Optional[Dict[str, Any]]:
    """
    Get the primary channel for a post type.
    
    Args:
        post_type: Post type
    
    Returns:
        dict: Channel info with 'channel', 'content_format', etc., or None
    """
    channels = get_channels_for_post_type(post_type)
    
    for channel_info in channels:
        if channel_info.get('is_primary'):
            return channel_info
    
    # If no primary, return first channel
    if channels:
        return channels[0]
    
    return None


def get_social_media_channels(post_type: str) -> List[Dict[str, Any]]:
    """
    Get all social media channels (non-blog) for a post type.
    
    Args:
        post_type: Post type
    
    Returns:
        list: List of channel info dicts (excluding blog)
    """
    channels = get_channels_for_post_type(post_type)
    return [ch for ch in channels if ch['channel'] != 'blog']


def is_channel_required(post_type: str, channel: str) -> bool:
    """
    Check if a channel is required for a post type.
    
    Args:
        post_type: Post type
        channel: Channel name
    
    Returns:
        bool: True if required, False otherwise
    """
    channels = get_channels_for_post_type(post_type)
    
    for channel_info in channels:
        if channel_info['channel'] == channel:
            return channel_info.get('is_required', True)
    
    return False

