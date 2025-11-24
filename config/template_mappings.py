"""
Template Mappings Configuration
Centralized source of truth for all template paths by stage, substage, and post_type.

This ensures routes and settings system use the same template selection logic.
"""

# Template mappings organized by stage > substage > post_type
TEMPLATE_MAPPINGS = {
    'calendar': {
        'view': {
            'default': 'planning/calendar/view.html'
        },
        'week-view': {
            'default': 'planning/calendar/week_view.html'
        },
        'ideas-week': {
            'default': 'planning/calendar/ideas_week.html'
        },
        'taxonomy': {
            'default': 'planning/calendar/taxonomy.html'
        },
        'product-data-review': {
            'default': 'planning/calendar/product_data_review.html'
        }
    },
    'concept': {
        'brainstorm': {
            'default': 'planning/concept/brainstorm.html'
        },
        'section-structure': {
            'profile': 'planning/concept/section_structure_profile.html',
            'default': 'planning/concept/section_structure.html'
        },
        'topic-allocation': {
            'profile': 'planning/concept/topic_allocation_profile.html',
            'default': 'planning/concept/topic_allocation.html'
        },
        'titling': {
            'profile': 'planning/concept/titling_profile.html',
            'default': 'planning/concept/titling.html'
        },
        'outline': {
            'default': 'planning/concept/outline.html'
        },
        'section-content-mapping': {
            'default': 'planning/concept/section_content_mapping.html'
        }
    },
    'research': {
        'research': {
            'default': 'planning/research/index.html'
        },
        'sources': {
            'default': 'planning/research/sources.html'
        },
        'visuals': {
            'default': 'planning/research/visuals.html'
        },
        'prompts': {
            'default': 'planning/research/prompts.html'
        },
        'verification': {
            'default': 'planning/research/verification.html'
        }
    },
    'authoring': {
        'drafting': {
            'default': 'authoring/sections/drafting.html'
        },
        'image-concepts': {
            'default': 'authoring/sections/image_concepts.html'
        },
        'image-prompts': {
            'default': 'authoring/sections/image_prompts.html'
        },
        'image-captions': {
            'default': 'authoring/sections/image_captions.html'
        }
    },
    'imaging': {
        'image-generation': {
            'profile': 'imaging/sections/image_generation_profile.html',
            'default': 'imaging/sections/image_generation.html'
        },
        'optimise': {
            'default': 'imaging/sections/optimise.html'
        }
    },
    'header': {
        'title-summary': {
            'default': 'header/title_summary.html'
        },
        'header-image': {
            'profile': 'header/header_image_profile.html',
            'default': 'header/header_image.html'
        },
        'image-prompt': {
            'default': 'header/image_prompt.html'
        },
        'image-details': {
            'default': 'header/image_details.html'
        },
        'image-generate': {
            'default': 'header/image_generate.html'
        },
        'seo-meta': {
            'default': 'header/seo_meta.html'
        }
    }
}


def get_template_path(stage, substage, post_type='themed'):
    """
    Get template path for a given stage, substage, and post_type.
    
    Args:
        stage (str): Stage name (e.g., 'concept', 'imaging', 'authoring')
        substage (str): Substage name (e.g., 'section-structure', 'image-generation')
        post_type (str): Post type ('themed', 'profile', 'recipe', 'generated')
                        Defaults to 'themed'
    
    Returns:
        str: Template path, or None if not found
    
    Examples:
        >>> get_template_path('concept', 'section-structure', 'profile')
        'planning/concept/section_structure_profile.html'
        
        >>> get_template_path('concept', 'section-structure', 'themed')
        'planning/concept/section_structure.html'
        
        >>> get_template_path('imaging', 'image-generation', 'profile')
        'imaging/sections/image_generation_profile.html'
    """
    # Normalize post_type - use 'themed' as default
    if post_type not in ['themed', 'profile', 'recipe', 'generated']:
        post_type = 'themed'
    
    # Get stage mappings
    stage_mappings = TEMPLATE_MAPPINGS.get(stage)
    if not stage_mappings:
        return None
    
    # Get substage mappings
    substage_mappings = stage_mappings.get(substage)
    if not substage_mappings:
        return None
    
    # Try to get post_type-specific template first
    if post_type in substage_mappings:
        return substage_mappings[post_type]
    
    # Fall back to default
    return substage_mappings.get('default')


def get_all_template_mappings():
    """
    Get all template mappings (for API/settings use).
    
    Returns:
        dict: Complete template mappings structure
    """
    return TEMPLATE_MAPPINGS


def get_templates_for_substage(stage, substage):
    """
    Get all available templates for a substage (for settings display).
    
    Args:
        stage (str): Stage name
        substage (str): Substage name
    
    Returns:
        dict: Mapping of post_type -> template_path, or None if not found
    """
    stage_mappings = TEMPLATE_MAPPINGS.get(stage)
    if not stage_mappings:
        return None
    
    return stage_mappings.get(substage)

