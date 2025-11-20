"""
Authoring Panel Configuration System

Defines panel sequences and output configurations for different post types.
This allows easy customization of the right-hand panel order without modifying templates.

MIGRATED: Previously used illustration_method, now uses post_type.
All post types currently use LLM-creation panels (Photo-harvesting is deprecated).
"""

# Panel configuration for each post type
POST_TYPE_PANEL_CONFIGS = {
    'themed': {
        'panels': [
            {
                'type': 'llm_settings',
                'include': 'authoring/includes/llm_settings_panel.html',
                'order': 1
            },
            {
                'type': 'llm_prompts',
                'include': 'authoring/includes/llm_prompts_panel.html',
                'order': 2
            },
            {
                'type': 'context',
                'include': 'authoring/includes/context_panel.html',
                'order': 3
            },
            {
                'type': 'batch_progress',
                'include': 'authoring/includes/batch_progress_panel.html',
                'order': 4
            },
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html',
        'output_script': 'js/authoring/image-concepts-output-panel.js'
    },
    'recipe': {
        'panels': [
            {
                'type': 'llm_settings',
                'include': 'authoring/includes/llm_settings_panel.html',
                'order': 1
            },
            {
                'type': 'llm_prompts',
                'include': 'authoring/includes/llm_prompts_panel.html',
                'order': 2
            },
            {
                'type': 'context',
                'include': 'authoring/includes/context_panel.html',
                'order': 3
            },
            {
                'type': 'batch_progress',
                'include': 'authoring/includes/batch_progress_panel.html',
                'order': 4
            },
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html',
        'output_script': 'js/authoring/image-concepts-output-panel.js'
    },
    'profile': {
        'panels': [
            {
                'type': 'llm_settings',
                'include': 'authoring/includes/llm_settings_panel.html',
                'order': 1
            },
            {
                'type': 'llm_prompts',
                'include': 'authoring/includes/llm_prompts_panel.html',
                'order': 2
            },
            {
                'type': 'context',
                'include': 'authoring/includes/context_panel.html',
                'order': 3
            },
            {
                'type': 'batch_progress',
                'include': 'authoring/includes/batch_progress_panel.html',
                'order': 4
            },
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html',
        'output_script': 'js/authoring/image-concepts-output-panel.js'
    },
    'generated': {
        'panels': [
            {
                'type': 'llm_settings',
                'include': 'authoring/includes/llm_settings_panel.html',
                'order': 1
            },
            {
                'type': 'llm_prompts',
                'include': 'authoring/includes/llm_prompts_panel.html',
                'order': 2
            },
            {
                'type': 'context',
                'include': 'authoring/includes/context_panel.html',
                'order': 3
            },
            {
                'type': 'batch_progress',
                'include': 'authoring/includes/batch_progress_panel.html',
                'order': 4
            },
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html',
        'output_script': 'js/authoring/image-concepts-output-panel.js'
    }
}

# DEPRECATED: Keep for backward compatibility
ILLUSTRATION_PANEL_CONFIGS = {
    'LLM-creation': POST_TYPE_PANEL_CONFIGS['themed'],  # Map to themed config
    'Photo-harvesting': {
        'active': False,  # DEPRECATED: Photo-harvesting is inactive
        'panels': [],
        'output_panel': None,
        'output_script': None
    }
}


def get_panel_config_by_post_type(post_type):
    """
    Get panel configuration for a post type.
    
    Args:
        post_type (str): Post type ('themed', 'recipe', 'profile', 'generated')
    
    Returns:
        dict: Panel configuration with panels list, output_panel, and output_script
    """
    return POST_TYPE_PANEL_CONFIGS.get(
        post_type,
        POST_TYPE_PANEL_CONFIGS['themed']  # Default to themed
    )


def get_sorted_panels_by_post_type(post_type):
    """
    Get sorted panel list for a post type.
    
    Args:
        post_type (str): Post type ('themed', 'recipe', 'profile', 'generated')
    
    Returns:
        list: Sorted list of panel dicts ordered by 'order' field
    """
    config = get_panel_config_by_post_type(post_type)
    return sorted(config['panels'], key=lambda p: p.get('order', 999))


# DEPRECATED: Keep for backward compatibility
def get_panel_config(illustration_method):
    """
    DEPRECATED: Use get_panel_config_by_post_type() instead.
    
    Get panel configuration for a given illustration method.
    Always returns LLM-creation config for backward compatibility.
    
    Args:
        illustration_method (str): The illustration method (ignored, always uses LLM-creation)
    
    Returns:
        dict: Panel configuration with panels list, output_panel, and output_script
    """
    # Always return LLM-creation config (which is now themed config)
    return POST_TYPE_PANEL_CONFIGS['themed']


def get_sorted_panels(illustration_method):
    """
    DEPRECATED: Use get_sorted_panels_by_post_type() instead.
    
    Get sorted panel list for a given illustration method.
    Always returns LLM-creation panels for backward compatibility.
    
    Args:
        illustration_method (str): The illustration method (ignored)
    
    Returns:
        list: Sorted list of panel dicts ordered by 'order' field
    """
    config = get_panel_config(illustration_method)
    return sorted(config['panels'], key=lambda p: p.get('order', 999))

