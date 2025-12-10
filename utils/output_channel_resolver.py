"""
Output Channel Resolver - Helper utilities for resolving output channel-specific pipelines

This module provides helper functions for:
- Resolving pipeline definitions for posts based on output channel
- Validating substages for output channels
- Getting available output channels for posts
"""

import logging
from typing import Optional, Dict, Any, List
from config.database import db_manager
from config.output_channel_stages import (
    get_stages_for_output,
    get_substages_for_output,
    get_all_stages_for_output,
    is_substage_valid_for_output,
    get_available_output_channels
)
from utils.taxonomy_helpers import get_post_type

logger = logging.getLogger(__name__)


def resolve_pipeline_for_output(post_id: int, output_channel: str = 'blog') -> Dict[str, Any]:
    """
    Resolve the full pipeline definition for a post based on output channel.
    
    Args:
        post_id (int): Post ID
        output_channel (str): Output channel ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')
    
    Returns:
        dict: Pipeline definition with stages and substages, or None if post not found
    
    Example:
        >>> resolve_pipeline_for_output(123, 'facebook')
        {
            'post_id': 123,
            'post_type': 'themed',
            'output_channel': 'facebook',
            'stages': ['syndication'],
            'substages': {
                'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
            }
        }
    """
    try:
        # Get post_type
        post_type = get_post_type(post_id)
        
        # Get output channel configuration
        output_config = get_stages_for_output(post_type, output_channel)
        
        # Build pipeline definition
        if output_config.get('use_post_type_config'):
            # Use post_type_substages
            from config.post_type_substages import get_substages_for_post_type
            stages_dict = get_substages_for_post_type(post_type)
            stages = list(stages_dict.keys())
            substages = stages_dict
        else:
            # Use channel-specific stages
            stages = output_config.get('stages', [])
            substages = output_config.get('substages', {})
        
        return {
            'post_id': post_id,
            'post_type': post_type,
            'output_channel': output_channel,
            'stages': stages,
            'substages': substages
        }
    except Exception as e:
        logger.error(f"Error resolving pipeline for post {post_id} output {output_channel}: {e}")
        return None


def validate_substage_for_output(post_id: int, stage: str, substage: str, output_channel: str = 'blog') -> bool:
    """
    Validate if a substage is valid for a post's output channel.
    
    Args:
        post_id (int): Post ID
        stage (str): Stage name
        substage (str): Substage key
        output_channel (str): Output channel
    
    Returns:
        bool: True if substage is valid, False otherwise
    """
    try:
        post_type = get_post_type(post_id)
        return is_substage_valid_for_output(post_type, output_channel, stage, substage)
    except Exception as e:
        logger.error(f"Error validating substage for post {post_id}: {e}")
        return False


def get_available_output_channels_for_post(post_id: int) -> List[str]:
    """
    Get list of available output channels for a post.
    
    Args:
        post_id (int): Post ID
    
    Returns:
        list: List of available output channel names
    
    Example:
        >>> get_available_output_channels_for_post(123)
        ['blog', 'facebook', 'instagram', 'newsletter', 'twitter']
    """
    try:
        post_type = get_post_type(post_id)
        return get_available_output_channels(post_type)
    except Exception as e:
        logger.error(f"Error getting available channels for post {post_id}: {e}")
        return ['blog']  # Default fallback


def get_pipeline_stages_for_output(post_id: int, output_channel: str = 'blog') -> List[str]:
    """
    Get list of stage names for a post's output channel pipeline.
    
    Args:
        post_id (int): Post ID
        output_channel (str): Output channel
    
    Returns:
        list: List of stage names in order
    
    Example:
        >>> get_pipeline_stages_for_output(123, 'facebook')
        ['syndication']
    """
    try:
        post_type = get_post_type(post_id)
        return get_all_stages_for_output(post_type, output_channel)
    except Exception as e:
        logger.error(f"Error getting pipeline stages for post {post_id}: {e}")
        return []


def get_substages_for_post_output(post_id: int, stage: str, output_channel: str = 'blog') -> List[str]:
    """
    Get list of substage keys for a specific stage in a post's output channel pipeline.
    
    Args:
        post_id (int): Post ID
        stage (str): Stage name
        output_channel (str): Output channel
    
    Returns:
        list: List of substage keys
    
    Example:
        >>> get_substages_for_post_output(123, 'syndication', 'facebook')
        ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
    """
    try:
        post_type = get_post_type(post_id)
        return get_substages_for_output(post_type, output_channel, stage)
    except Exception as e:
        logger.error(f"Error getting substages for post {post_id} stage {stage}: {e}")
        return []


def is_output_channel_supported(post_id: int, output_channel: str) -> bool:
    """
    Check if an output channel is supported for a post.
    
    Args:
        post_id (int): Post ID
        output_channel (str): Output channel
    
    Returns:
        bool: True if channel is supported, False otherwise
    """
    try:
        available_channels = get_available_output_channels_for_post(post_id)
        return output_channel.lower() in available_channels
    except Exception as e:
        logger.error(f"Error checking output channel support for post {post_id}: {e}")
        return False

