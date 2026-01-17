"""
Output Channel Stage Configuration
Defines stages/substages per (post_type, output_channel) combination.

This enables different production pipelines for the same post type
depending on the target output channel (blog, Facebook, Instagram, etc.).

For example:
- weekly_word → blog: Full pipeline with SEO, metadata, etc.
- weekly_word → facebook: Minimal pipeline (format → image → publish)
- themed → blog: Full pipeline
- themed → facebook: Syndication pipeline (reuse blog content)
"""

from utils.substage_config import get_substages_for_post_type

# Output channel stage definitions
# Format: (post_type, output_channel) -> {stages: [...], substages: {...}}
OUTPUT_CHANNEL_STAGES = {
    # Blog outputs - use post_type_substages.py (full pipelines)
    ('themed', 'blog'): {
        'use_post_type_config': True,  # Fallback to post_type_substages.py
        'stages': None,
        'substages': None
    },
    ('recipe', 'blog'): {
        'use_post_type_config': True
    },
    ('profile', 'blog'): {
        'use_post_type_config': True
    },
    ('generated', 'blog'): {
        'use_post_type_config': True
    },
    ('weekly_word', 'blog'): {
        'use_post_type_config': True
    },
    ('weekly_phrase', 'blog'): {
        'use_post_type_config': True
    },
    ('weekly_insult', 'blog'): {
        'use_post_type_config': True
    },
    
    # Facebook outputs - minimal pipelines for weekly content
    ('weekly_word', 'facebook'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_facebook', 'generate_caption', 'add_hashtags'],
            'imaging': ['optimize_for_facebook'],
            'publish': ['publish_to_facebook']
        }
    },
    ('weekly_phrase', 'facebook'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_facebook', 'generate_caption', 'add_translation', 'add_hashtags'],
            'imaging': ['optimize_for_facebook'],
            'publish': ['publish_to_facebook']
        }
    },
    ('weekly_insult', 'facebook'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_facebook', 'generate_caption', 'add_translation', 'add_hashtags'],
            'imaging': ['optimize_for_facebook'],
            'publish': ['publish_to_facebook']
        }
    },
    
    # Facebook outputs - syndication for blog posts
    ('themed', 'facebook'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
        }
    },
    ('recipe', 'facebook'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
        }
    },
    ('profile', 'facebook'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
        }
    },
    ('generated', 'facebook'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
        }
    },
    
    # Instagram outputs - minimal pipelines for weekly content
    ('weekly_word', 'instagram'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_instagram', 'create_caption'],
            'imaging': ['optimize_for_instagram', 'create_carousel'],
            'publish': ['publish_to_instagram']
        }
    },
    ('weekly_phrase', 'instagram'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_instagram', 'add_translation', 'create_caption'],
            'imaging': ['optimize_for_instagram', 'create_carousel'],
            'publish': ['publish_to_instagram']
        }
    },
    ('weekly_insult', 'instagram'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_instagram', 'add_translation', 'create_caption'],
            'imaging': ['optimize_for_instagram', 'create_carousel'],
            'publish': ['publish_to_instagram']
        }
    },
    
    # Instagram outputs - syndication for blog posts
    ('themed', 'instagram'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_instagram', 'create_caption', 'publish_to_instagram']
        }
    },
    ('recipe', 'instagram'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_instagram', 'create_caption', 'publish_to_instagram']
        }
    },
    ('profile', 'instagram'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_instagram', 'create_caption', 'publish_to_instagram']
        }
    },
    
    # Twitter outputs - minimal pipelines
    ('weekly_word', 'twitter'): {
        'stages': ['content', 'publish'],
        'substages': {
            'content': ['format_for_twitter', 'add_hashtags'],
            'publish': ['publish_to_twitter']
        }
    },
    ('weekly_phrase', 'twitter'): {
        'stages': ['content', 'publish'],
        'substages': {
            'content': ['format_for_twitter', 'add_translation', 'add_hashtags'],
            'publish': ['publish_to_twitter']
        }
    },
    ('weekly_insult', 'twitter'): {
        'stages': ['content', 'publish'],
        'substages': {
            'content': ['format_for_twitter', 'add_translation', 'add_hashtags'],
            'publish': ['publish_to_twitter']
        }
    },
    ('themed', 'twitter'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_twitter', 'publish_to_twitter']
        }
    },
    
    # Newsletter outputs - syndication only
    ('themed', 'newsletter'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_newsletter', 'add_to_newsletter']
        }
    },
    ('recipe', 'newsletter'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_newsletter', 'add_to_newsletter']
        }
    },
    ('profile', 'newsletter'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_newsletter', 'add_to_newsletter']
        }
    }
}


def get_stages_for_output(post_type: str, output_channel: str, content_format: str = None) -> dict:
    """
    Get stages/substages for a (post_type, output_channel) combination.
    
    Optionally considers content_format for more specific resolution.
    If content_format is not provided, resolves it from post_type_channel_config.
    
    Args:
        post_type (str): Post type ('themed', 'recipe', 'weekly_word', etc.)
        output_channel (str): Output channel ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')
        content_format (str, optional): Content format ('recipe', 'word_of_day', 'syndication', etc.)
    
    Returns:
        dict: Configuration dict with 'stages' and 'substages' keys, or None if not found
    
    Examples:
        >>> get_stages_for_output('weekly_word', 'facebook')
        {
            'stages': ['content', 'imaging', 'publish'],
            'substages': {
                'content': ['format_for_facebook', 'add_hashtags'],
                ...
            }
        }
        
        >>> get_stages_for_output('themed', 'blog')
        {
            'use_post_type_config': True,
            'stages': None,
            'substages': None
        }
    """
    # If content_format not provided, try to resolve it
    if not content_format:
        try:
            from utils.channel_assignment import get_content_format
            content_format = get_content_format(post_type, output_channel)
        except Exception:
            pass  # Continue without format
    
    # Try exact match first: (post_type, output_channel)
    key = (post_type, output_channel)
    
    if key in OUTPUT_CHANNEL_STAGES:
        config = OUTPUT_CHANNEL_STAGES[key]
        
        # If this config uses post_type_substages, return it as-is
        # The caller should handle the fallback
        if config.get('use_post_type_config'):
            return config
        
        # Otherwise return the channel-specific config
        return {
            'stages': config.get('stages', []),
            'substages': config.get('substages', {}),
            'content_format': content_format  # Include format in response
        }
    
    # Fallback: use post_type config for blog, minimal for social media
    if output_channel == 'blog':
        # Return config indicating to use post_type_substages
        return {
            'use_post_type_config': True,
            'stages': None,
            'substages': None,
            'content_format': content_format or 'article'
        }
    
    # For unknown combinations, return minimal default
    result = get_minimal_social_media_pipeline(post_type, output_channel)
    result['content_format'] = content_format
    return result


def get_minimal_social_media_pipeline(post_type: str, output_channel: str) -> dict:
    """
    Get a minimal default pipeline for social media outputs.
    Used as fallback for unknown (post_type, output_channel) combinations.
    
    Args:
        post_type (str): Post type
        output_channel (str): Output channel
    
    Returns:
        dict: Minimal pipeline configuration
    """
    # Default minimal pipeline for social media
    return {
        'stages': ['content', 'publish'],
        'substages': {
            'content': [f'format_for_{output_channel}'],
            'publish': [f'publish_to_{output_channel}']
        }
    }


def get_substages_for_output(post_type: str, output_channel: str, stage: str) -> list:
    """
    Get substages for a specific stage in an output pipeline.
    
    Args:
        post_type (str): Post type
        output_channel (str): Output channel
        stage (str): Stage name
    
    Returns:
        list: List of substage keys for the stage
    
    Examples:
        >>> get_substages_for_output('weekly_word', 'facebook', 'content')
        ['format_for_facebook', 'add_hashtags']
    """
    config = get_stages_for_output(post_type, output_channel)
    
    # If using post_type config, fall back to post_type_substages
    if config.get('use_post_type_config'):
        return get_substages_for_post_type(post_type, stage)
    
    # Otherwise return from channel-specific config
    return config.get('substages', {}).get(stage, [])


def get_all_stages_for_output(post_type: str, output_channel: str) -> list:
    """
    Get all stage names for an output pipeline.
    
    Args:
        post_type (str): Post type
        output_channel (str): Output channel
    
    Returns:
        list: List of stage names in order
    
    Examples:
        >>> get_all_stages_for_output('weekly_word', 'facebook')
        ['content', 'imaging', 'publish']
    """
    config = get_stages_for_output(post_type, output_channel)
    
    # If using post_type config, get stages from post_type_substages
    if config.get('use_post_type_config'):
        post_type_config = get_substages_for_post_type(post_type)
        return list(post_type_config.keys())
    
    # Otherwise return from channel-specific config
    return config.get('stages', [])


def is_substage_valid_for_output(post_type: str, output_channel: str, stage: str, substage_key: str) -> bool:
    """
    Check if a substage is valid for a given (post_type, output_channel, stage) combination.
    
    Args:
        post_type (str): Post type
        output_channel (str): Output channel
        stage (str): Stage name
        substage_key (str): Substage key
    
    Returns:
        bool: True if substage is valid, False otherwise
    """
    substages = get_substages_for_output(post_type, output_channel, stage)
    return substage_key in substages


def get_available_output_channels(post_type: str) -> list:
    """
    Get list of output channels that have configurations for a post type.
    
    Args:
        post_type (str): Post type
    
    Returns:
        list: List of output channel names
    
    Examples:
        >>> get_available_output_channels('weekly_word')
        ['blog', 'facebook', 'instagram', 'twitter']
    """
    channels = set()
    
    # Check all configured combinations
    for (pt, channel) in OUTPUT_CHANNEL_STAGES.keys():
        if pt == post_type:
            channels.add(channel)
    
    # Always include 'blog' as it's the default
    channels.add('blog')
    
    return sorted(list(channels))

