"""
Section Headings Utility Module

Provides utilities for managing section headings across different post types.
Ensures headings are always populated, especially for recipe posts.
"""

import logging

logger = logging.getLogger(__name__)

# Standard recipe section headings mapping
RECIPE_SECTION_HEADINGS = {
    'recipe_background': 'Background',
    'recipe_ingredients': 'Ingredients',
    'recipe_method': 'Method',
    'recipe_variants': 'Variations',
    'recipe_serving': 'Serving Suggestions',
    'recipe_further_reading': 'Further Reading',
    'recipe_gallery': 'Making Process',  # If this section type exists
}

# Standard recipe section descriptions
RECIPE_SECTION_DESCRIPTIONS = {
    'recipe_background': 'The historic and cultural background of this recipe. Write 2-3 paragraphs (150-200 words) covering the origin story, regional associations, and occasions when traditionally eaten. Use a warm, storytelling voice that evokes place, people, and time.',
    'recipe_ingredients': 'List of ingredients needed for this recipe. Format clearly for home cooks, with amounts and any preparation notes. May include regional variations or historical notes.',
    'recipe_method': 'Step-by-step cooking instructions. Use numbered steps with clear instructions. Aimed at home cooks, not professional chefs.',
    'recipe_variants': 'Optional twists and regional variations (e.g., "Hebridean version uses smoked haddock only", "Modern twist: add whisky cream"). Not every recipe needs variants - this section is optional.',
    'recipe_serving': 'How Scots traditionally serve this dish. Include drinks, sides, or traditional accompaniments. Optional mention of related products available on clan.com.',
    'recipe_further_reading': 'Search for 2-5 authoritative sources for background information about this recipe. Focus on: cultural/heritage sites, Wikipedia articles, historical sources, ingredient provenance sites, and tourism/heritage organizations. AVOID competing recipe sites or cooking blogs. For each source, provide: Title & Link, Why It\'s Good (brief explanation of the source\'s value), and Use Case in Your Content (how to reference this source in the recipe sections above). Sources should support the Background, Ingredients, Variations, and Serving Suggestions sections.',
    'recipe_gallery': 'Making process image showing one step of the recipe preparation.',
}

# Standard recipe sections in order
STANDARD_RECIPE_SECTIONS = [
    ('recipe_background', RECIPE_SECTION_HEADINGS['recipe_background'], RECIPE_SECTION_DESCRIPTIONS['recipe_background']),
    ('recipe_ingredients', RECIPE_SECTION_HEADINGS['recipe_ingredients'], RECIPE_SECTION_DESCRIPTIONS['recipe_ingredients']),
    ('recipe_method', RECIPE_SECTION_HEADINGS['recipe_method'], RECIPE_SECTION_DESCRIPTIONS['recipe_method']),
    ('recipe_variants', RECIPE_SECTION_HEADINGS['recipe_variants'], RECIPE_SECTION_DESCRIPTIONS['recipe_variants']),
    ('recipe_serving', RECIPE_SECTION_HEADINGS['recipe_serving'], RECIPE_SECTION_DESCRIPTIONS['recipe_serving']),
    ('recipe_further_reading', RECIPE_SECTION_HEADINGS['recipe_further_reading'], RECIPE_SECTION_DESCRIPTIONS['recipe_further_reading']),
]


def get_standard_recipe_heading(section_type: str) -> str:
    """
    Get the standard heading for a recipe section type.
    
    Args:
        section_type: The section type (e.g., 'recipe_background')
    
    Returns:
        The standard heading string, or None if not a recognized recipe section type
    """
    return RECIPE_SECTION_HEADINGS.get(section_type)


def get_standard_recipe_description(section_type: str) -> str:
    """
    Get the standard description for a recipe section type.
    
    Args:
        section_type: The section type (e.g., 'recipe_background')
    
    Returns:
        The standard description string, or empty string if not recognized
    """
    return RECIPE_SECTION_DESCRIPTIONS.get(section_type, '')


def is_recipe_section_type(section_type: str) -> bool:
    """
    Check if a section type is a recipe section.
    
    Args:
        section_type: The section type to check
    
    Returns:
        True if it's a recipe section type, False otherwise
    """
    if not section_type:
        return False
    return section_type.startswith('recipe_')


def ensure_section_heading(section_type: str, current_heading: str = None) -> str:
    """
    Ensure a section has a heading. For recipe sections, use standard headings.
    For other sections, return the current heading or None.
    
    Args:
        section_type: The section type
        current_heading: The current heading (may be None or empty)
    
    Returns:
        A heading string (standard recipe heading if recipe section, otherwise current_heading)
    """
    # If we already have a heading, use it
    if current_heading and current_heading.strip():
        return current_heading
    
    # For recipe sections, use standard headings
    if is_recipe_section_type(section_type):
        standard_heading = get_standard_recipe_heading(section_type)
        if standard_heading:
            logger.debug(f"Using standard heading '{standard_heading}' for recipe section type '{section_type}'")
            return standard_heading
    
    # For other sections, return None (they should come from titling endpoint)
    return None


def get_standard_recipe_sections() -> list:
    """
    Get the list of standard recipe sections in order.
    
    Returns:
        List of tuples: (section_type, section_heading, section_description)
    """
    return STANDARD_RECIPE_SECTIONS.copy()

