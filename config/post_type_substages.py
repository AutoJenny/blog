"""
Post Type Substages Configuration
Single source of truth for which substages belong to which post types and stages.

This ensures consistency across:
- Navbar navigation
- 1-click blog page
- Settings modal
- Pipeline status API
- Any other location that displays substages
"""

# Substage metadata: key -> {label, route_function, order}
SUBSTAGE_METADATA = {
    # Calendar substages
    'view': {
        'label': 'Calendar View',
        'route_function': 'planning.planning_calendar_view',
        'order': 1
    },
    'week-view': {
        'label': 'Week View',
        'route_function': 'planning.planning_calendar_week_view',
        'order': 2
    },
    'ideas-week': {
        'label': 'Week Themes',
        'route_function': None,  # Special case - handled by JavaScript
        'order': 3
    },
    
    # Planning substages
    'ideas': {
        'label': 'Ideas',
        'route_function': 'planning.planning_calendar_ideas',
        'order': 1
    },
    'taxonomy': {
        'label': 'Taxonomy',
        'route_function': 'planning.planning_calendar_taxonomy',
        'order': 2
    },
    'topic_brainstorming': {
        'label': 'Topic Brainstorming',
        'route_function': 'planning.planning_concept_brainstorm',
        'order': 3
    },
    'section_structure': {
        'label': 'Section Structure Design',
        'route_function': 'planning.planning_concept_section_structure',
        'order': 4
    },
    'topic_allocation': {
        'label': 'Section Ideas',
        'route_function': 'planning.planning_concept_topic_allocation',
        'order': 5
    },
    'section_titling': {
        'label': 'Section Titling',
        'route_function': 'planning.planning_concept_titling',
        'order': 6
    },
    'product_data_review': {
        'label': 'Product Data Review',
        'route_function': 'planning.planning_calendar_product_data_review',
        'order': 2  # After taxonomy for generated posts
    },
    'section_content_mapping': {
        'label': 'Section Content Mapping',
        'route_function': 'planning.planning_concept_section_content_mapping',
        'order': 3  # After product_data_review for generated posts
    },
    
    # Research substages
    'research': {
        'label': 'Research Overview',
        'route_function': 'planning.planning_research',
        'order': 1
    },
    'sources': {
        'label': 'Sources',
        'route_function': 'planning.planning_research_sources',
        'order': 2
    },
    'visuals': {
        'label': 'Visuals',
        'route_function': 'planning.planning_research_visuals',
        'order': 3
    },
    'prompts': {
        'label': 'Prompts',
        'route_function': 'planning.planning_research_prompts',
        'order': 4
    },
    'verification': {
        'label': 'Verification',
        'route_function': 'planning.planning_research_verification',
        'order': 5
    },
    'background_research': {
        'label': 'Background Research',
        'route_function': 'research.background_research',
        'order': 1
    },
    
    # Authoring substages
    'drafting': {
        'label': 'Drafting',
        'route_function': 'authoring.authoring_sections_drafting',
        'order': 1
    },
    'image_concepts': {
        'label': 'Image Concepts',
        'route_function': 'authoring_imaging.authoring_sections_image_concepts',
        'order': 2
    },
    'image_prompts': {
        'label': 'Image Prompts',
        'route_function': 'authoring_imaging.authoring_sections_image_prompts',
        'order': 3
    },
    'image_captions': {
        'label': 'Image Captions',
        'route_function': 'authoring_imaging.authoring_sections_image_captions',
        'order': 4
    },
    'recipe_image_style_prompt': {
        'label': 'Image Style & Prompts',
        'route_function': 'recipes_imaging.recipe_image_style_prompt',
        'order': 2  # After drafting for recipe posts
    },
    
    # Content substages (for weekly content types)
    'format_content': {
        'label': 'Format Content',
        'route_function': None,  # May be handled by JavaScript or future route
        'order': 1
    },
    
    # Imaging substages
    'image_generation': {
        'label': 'Image Generation',
        'route_function': 'imaging.imaging_sections_image_generation',
        'order': 1
    },
    'optimise': {
        'label': 'Optimise',
        'route_function': 'imaging.imaging_sections_optimise',
        'order': 2
    },
    
    # Header substages
    'title_summary': {
        'label': 'Title & Summary',
        'route_function': 'header.header_title_summary',
        'order': 1
    },
    'header_image': {
        'label': 'Header Image',
        'route_function': 'header.header_header_image',
        'order': 2
    },
    'seo_meta': {
        'label': 'SEO Meta',
        'route_function': 'header.header_seo_meta',
        'order': 3
    },
    'product_match': {
        'label': 'Product Match',
        'route_function': 'header.header_product_match',
        'order': 4
    },
    'final_review': {
        'label': 'Final Review',
        'route_function': None,  # May not have a route
        'order': 5
    }
}

# Post type substage definitions
# Format: post_type -> stage -> [substage_keys in order]
POST_TYPE_SUBSTAGES = {
    'themed': {
        'calendar': ['view', 'week-view', 'ideas-week'],
        'planning': ['ideas', 'taxonomy', 'topic_brainstorming', 'section_structure', 'topic_allocation', 'section_titling'],
        'research': ['research', 'sources', 'visuals', 'prompts', 'verification'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'product_match', 'final_review']
    },
    'profile': {
        'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
    },
    'generated': {
        'calendar': ['view', 'week-view', 'ideas-week'],
        'planning': ['taxonomy', 'product_data_review', 'section_content_mapping', 'section_titling'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
    },
    'recipe': {
        'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
        'research': ['background_research'],
        'authoring': ['drafting', 'recipe_image_style_prompt', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
    },
    'weekly_word': {
        'calendar': ['view'],
        'content': ['format_content'],
        'header': ['title_summary']
    },
    'weekly_phrase': {
        'calendar': ['view'],
        'content': ['format_content'],
        'header': ['title_summary']
    },
    'weekly_insult': {
        'calendar': ['view'],
        'content': ['format_content'],
        'header': ['title_summary']
    }
}


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
    # Normalize post_type - default to 'themed' if invalid
    if post_type not in POST_TYPE_SUBSTAGES:
        post_type = 'themed'
    
    substages = POST_TYPE_SUBSTAGES[post_type]
    
    if stage:
        return substages.get(stage, [])
    
    return substages


def get_substage_metadata(substage_key):
    """
    Get metadata for a substage (label, route, order).
    
    Args:
        substage_key (str): Substage key (e.g., 'ideas', 'taxonomy')
    
    Returns:
        dict: Metadata dict with 'label', 'route_function', 'order', or None if not found
    """
    return SUBSTAGE_METADATA.get(substage_key)


def get_substage_label(substage_key):
    """
    Get display label for a substage.
    
    Args:
        substage_key (str): Substage key
    
    Returns:
        str: Display label, or substage_key if not found
    """
    metadata = get_substage_metadata(substage_key)
    return metadata['label'] if metadata else substage_key.replace('_', ' ').title()


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
    all_substages = set()
    for post_type in POST_TYPE_SUBSTAGES:
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
            {'key': 'ideas', 'label': 'Ideas', 'route_function': '...', 'order': 1},
            {'key': 'taxonomy', 'label': 'Taxonomy', 'route_function': '...', 'order': 2},
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
                    **metadata
                })
            else:
                result.append({
                    'key': substage_key,
                    'label': get_substage_label(substage_key),
                    'route_function': None,
                    'order': 999
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
                        **metadata
                    })
                else:
                    result[stage_name].append({
                        'key': substage_key,
                        'label': get_substage_label(substage_key),
                        'route_function': None,
                        'order': 999
                    })
            # Sort by order
            result[stage_name].sort(key=lambda x: x.get('order', 999))
        return result


