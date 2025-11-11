"""
Post Type Pipeline Configuration
Defines which pipeline steps are used for each post type.
"""

POST_TYPE_PIPELINE_CONFIGS = {
    'themed': {
        'active': True,
        'steps': [
            'week-ideas',           # Calendar selection
            'taxonomy',             # Assign taxonomy
            'idea-generation',      # Expand idea
            'topic-brainstorming',  # Generate topics
            'section-structure-design', # Design structure
            'section-ideas',        # Section ideas
            'section-titling',      # Section titles
            'drafting',             # Author drafts
            'image-concepts',       # Image concepts
            'image-prompts',        # Image prompts
            'image-captions',       # Image captions
            'image-generation',     # Generate images
            'optimise',             # Optimize images
            'header-title-summary', # Header title/summary
            'header-image-prompt',  # Header image prompt
            'header-image-details', # Header image details
            'header-image-generate', # Header image generation
            'header-image-optimise', # Header image optimization
            'header-seo-meta',      # SEO metadata
            'final-review'          # Final review
        ]
    },
    'recipe': {
        'active': True,
        'steps': [
            'recipe-selection',     # Select recipe (replaces week-ideas)
            'recipe-research',      # Optional: Web research for historical context
            'drafting',             # Authoring — Drafting (all recipe sections via existing workflow)
            'recipe-image-style-prompt',  # Combined: Style guidelines + prompts for all 3 images (hero, ingredients, method)
            'image-captions',       # Authoring — Image Captions
            'image-generation',     # Imaging — Image Generation (hero + ingredients + method)
            'optimise',             # Imaging — Optimise
            'header-title-summary', # Header — Title & Summary
            'header-image-prompt',  # Header Image — Prompt
            'header-image-details', # Header Image — Captions/Alt
            'header-image-generate', # Header Image — Image
            'header-image-optimise', # Header Image — Optimise
            'header-seo-meta',      # Header — SEO & Meta
            'final-review'          # Final Review — Preview
        ]
    },
    'profile': {
        'active': True,
        'steps': [
            'profile-selection',    # Select product/category (replaces week-ideas)
            'profile-data-sync',    # NEW: Sync product data from clan_products
            'profile-sections',     # Profile sections generation
            'profile-image-concepts', # Profile image concepts
            'profile-image-prompts', # Profile image prompts
            'profile-image-generation', # Profile images
            'profile-image-optimise', # Optimize profile images
            'header-title-summary', # Header title/summary
            'header-image-prompt',  # Header image prompt
            'header-image-details', # Header image details
            'header-image-generate', # Header image generation
            'header-image-optimise', # Header image optimization
            'header-seo-meta',      # SEO metadata
            'final-review'          # Final review
        ]
    },
    'generated': {
        'active': True,
        'steps': [
            'taxonomy',                    # Already preset, allow refinement
            'product-data-review',        # Review CLAN product data
            'section-content-mapping',    # Visual data-to-section mapping
            'section-titling',            # Finalize section titles
            'drafting',                   # Author drafts
            'image-concepts',             # Image concepts
            'image-prompts',              # Image prompts
            'image-captions',             # Image captions
            'image-generation',           # Generate images
            'optimise',                   # Optimize images
            'header-title-summary',       # Header title/summary
            'header-image-prompt',        # Header image prompt
            'header-image-details',       # Header image details
            'header-image-generate',      # Header image generation
            'header-image-optimise',      # Header image optimization
            'header-seo-meta',            # SEO metadata
            'final-review'               # Final review
        ]
    }
}

# Step function mappings (for reference - actual implementation in JavaScript)
STEP_FUNCTION_MAPPINGS = {
    'themed': {
        'week-ideas': 'runWeekIdeas',
        'taxonomy': 'runTaxonomy',
        'idea-generation': 'runIdeaGeneration',
        'topic-brainstorming': 'runTopicBrainstorming',
        'section-structure-design': 'runSectionStructure',
        'section-ideas': 'runSectionIdeas',
        'section-titling': 'runSectionTitling',
        'drafting': 'runDrafting',
        'image-concepts': 'runImageConcepts',
        'image-prompts': 'runImagePrompts',
        'image-captions': 'runImageCaptions',
        'image-generation': 'runImageGeneration',
        'optimise': 'runImageOptimise',
        'header-title-summary': 'runHeaderTitleSummary',
        'header-image-prompt': 'runHeaderImagePrompt',
        'header-image-details': 'runHeaderImageDetails',
        'header-image-generate': 'runHeaderImageGenerate',
        'header-image-optimise': 'runHeaderImageOptimize',
        'header-seo-meta': 'runHeaderSeoMeta',
        'final-review': 'runFinalReview'
    },
    'recipe': {
        'recipe-selection': 'runRecipeSelection',
        'recipe-research': 'runRecipeResearch',
        'drafting': 'runDrafting',  # Uses existing authoring workflow
        'recipe-image-style-prompt': 'runRecipeImageStylePrompt',  # Combined style + prompts
        'image-captions': 'runImageCaptions',
        'image-generation': 'runImageGeneration',
        'optimise': 'runImageOptimise',
        'header-title-summary': 'runHeaderTitleSummary',
        'header-image-prompt': 'runHeaderImagePrompt',
        'header-image-details': 'runHeaderImageDetails',
        'header-image-generate': 'runHeaderImageGenerate',
        'header-image-optimise': 'runHeaderImageOptimize',
        'header-seo-meta': 'runHeaderSeoMeta',
        'final-review': 'runFinalReview'
    },
    'profile': {
        'profile-selection': 'runProfileSelection',
        'profile-data-sync': 'runProfileDataSync',
        'profile-sections': 'runProfileSections',
        'profile-image-concepts': 'runProfileImageConcepts',
        'profile-image-prompts': 'runProfileImagePrompts',
        'profile-image-generation': 'runProfileImageGeneration',
        'profile-image-optimise': 'runProfileImageOptimise',
        'header-title-summary': 'runHeaderTitleSummary',
        'header-image-prompt': 'runHeaderImagePrompt',
        'header-image-details': 'runHeaderImageDetails',
        'header-image-generate': 'runHeaderImageGenerate',
        'header-image-optimise': 'runHeaderImageOptimize',
        'header-seo-meta': 'runHeaderSeoMeta',
        'final-review': 'runFinalReview'
    },
    'generated': {
        'taxonomy': 'runTaxonomy',
        'product-data-review': 'runProductDataReview',
        'section-content-mapping': 'runSectionContentMapping',
        'section-titling': 'runSectionTitling',
        'drafting': 'runDrafting',
        'image-concepts': 'runImageConcepts',
        'image-prompts': 'runImagePrompts',
        'image-captions': 'runImageCaptions',
        'image-generation': 'runImageGeneration',
        'optimise': 'runImageOptimise',
        'header-title-summary': 'runHeaderTitleSummary',
        'header-image-prompt': 'runHeaderImagePrompt',
        'header-image-details': 'runHeaderImageDetails',
        'header-image-generate': 'runHeaderImageGenerate',
        'header-image-optimise': 'runHeaderImageOptimize',
        'header-seo-meta': 'runHeaderSeoMeta',
        'final-review': 'runFinalReview'
    }
}

# Step labels (for UI display)
STEP_LABELS = {
    'week-ideas': 'Calendar — Week Ideas',
    'taxonomy': 'Planning — Taxonomy',
    'idea-generation': 'Planning — Idea Generation',
    'topic-brainstorming': 'Planning — Topic Brainstorming',
    'section-structure-design': 'Planning — Section Structure',
    'section-ideas': 'Planning — Section Ideas',
    'section-titling': 'Planning — Section Titling',
    'drafting': 'Authoring — Drafting',
    'image-concepts': 'Authoring — Image Concepts',
    'image-prompts': 'Authoring — Image Prompts',
    'image-captions': 'Authoring — Image Captions',
    'image-generation': 'Imaging — Image Generation',
    'optimise': 'Imaging — Optimise',
    'header-title-summary': 'Header — Title & Summary',
    'header-image-prompt': 'Header Image — Prompt',
    'header-image-details': 'Header Image — Captions/Alt',
    'header-image-generate': 'Header Image — Image',
    'header-image-optimise': 'Header Image — Optimise',
    'header-seo-meta': 'Header — SEO & Meta',
    'final-review': 'Final Review — Preview',
    'recipe-selection': 'Recipe — Selection',
    'recipe-research': 'Research — Recipe Context',
    'recipe-image-style-prompt': 'Imaging — Style & Prompts',
    'profile-selection': 'Profile — Selection',
    'profile-data-sync': 'Data Sync — Product Information',
    'profile-sections': 'Profile — Sections',
    'profile-image-concepts': 'Profile — Image Concepts',
    'profile-image-prompts': 'Profile — Image Prompts',
    'profile-image-generation': 'Profile — Image Generation',
    'profile-image-optimise': 'Profile — Image Optimise',
    'product-data-review': 'Planning — Product Data Review',
    'section-content-mapping': 'Planning — Section Content Mapping'
}

def get_pipeline_steps(post_type):
    """
    Get pipeline steps for a post type.
    
    Args:
        post_type (str): Post type ('themed', 'recipe', 'profile')
    
    Returns:
        list: List of step IDs for the pipeline
    """
    config = POST_TYPE_PIPELINE_CONFIGS.get(
        post_type,
        POST_TYPE_PIPELINE_CONFIGS['themed']  # Default to themed
    )
    
    if not config.get('active', True):
        # Fallback to themed if post type is inactive
        return POST_TYPE_PIPELINE_CONFIGS['themed']['steps']
    
    return config['steps']


def get_step_label(step_id):
    """
    Get display label for a step.
    
    Args:
        step_id (str): Step ID
    
    Returns:
        str: Display label or step_id if not found
    """
    return STEP_LABELS.get(step_id, step_id)


def get_step_function(step_id, post_type):
    """
    Get JavaScript function name for a step.
    
    Args:
        step_id (str): Step ID
        post_type (str): Post type
    
    Returns:
        str: Function name or None
    """
    mappings = STEP_FUNCTION_MAPPINGS.get(post_type, {})
    return mappings.get(step_id)

