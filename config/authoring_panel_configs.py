"""
Authoring Panel Configuration System

Defines panel sequences and output configurations for different illustration routes.
This allows easy customization of the right-hand panel order without modifying templates.
"""

# Panel configuration for each illustration method
ILLUSTRATION_PANEL_CONFIGS = {
    'LLM-creation': {
        'active': True,  # LLM-creation is the active illustration method
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
    'Photo-harvesting': {
        'active': False,  # DEPRECATED: Photo-harvesting is inactive
        'panels': [
            {
                'type': 'photo_settings',
                'include': 'authoring/includes/photo_settings_panel.html',
                'order': 1
            },
            {
                'type': 'photo_prompts',
                'include': 'authoring/includes/photo_prompts_panel.html',
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
        'output_panel': 'authoring/includes/output_panel_photo_harvesting.html',
        'output_script': 'js/authoring/photo-harvesting-output-panel.js'
    }
}


def get_panel_config(illustration_method):
    """
    Get panel configuration for a given illustration method.
    
    Args:
        illustration_method (str): The illustration method ('LLM-creation', 'Photo-harvesting', etc.)
    
    Returns:
        dict: Panel configuration with panels list, output_panel, and output_script
    """
    # Default to LLM-creation if method not found
    return ILLUSTRATION_PANEL_CONFIGS.get(
        illustration_method,
        ILLUSTRATION_PANEL_CONFIGS['LLM-creation']
    )


def get_sorted_panels(illustration_method):
    """
    Get sorted panel list for a given illustration method.
    
    Args:
        illustration_method (str): The illustration method
    
    Returns:
        list: Sorted list of panel dicts ordered by 'order' field
    """
    config = get_panel_config(illustration_method)
    return sorted(config['panels'], key=lambda p: p.get('order', 999))

