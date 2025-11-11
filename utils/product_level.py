"""
Product Level Parser

Determines product level (Classic, Luxury, Essential) based on product title.
"""

import re
from typing import Literal

ProductLevel = Literal['classic', 'luxury', 'essential']


def parse_product_level(product_name: str) -> ProductLevel:
    """
    Parse product level from product name.
    
    Rules:
    - Default: 'classic'
    - Contains "luxury" (case-insensitive) → 'luxury'
    - Contains "essential" (case-insensitive) → 'essential'
    - If both keywords present, "luxury" takes precedence
    
    Args:
        product_name: Product title/name
        
    Returns:
        Product level: 'classic', 'luxury', or 'essential'
    """
    if not product_name:
        return 'classic'
    
    name_lower = product_name.lower()
    
    # Check for luxury first (takes precedence)
    if 'luxury' in name_lower:
        return 'luxury'
    
    # Check for essential
    if 'essential' in name_lower:
        return 'essential'
    
    # Default to classic
    return 'classic'


def get_product_level_display_name(level: ProductLevel) -> str:
    """
    Get display name for product level.
    
    Args:
        level: Product level ('classic', 'luxury', or 'essential')
        
    Returns:
        Display name (capitalized)
    """
    return level.capitalize()


def get_product_level_description(level: ProductLevel) -> str:
    """
    Get description for product level.
    
    Args:
        level: Product level ('classic', 'luxury', or 'essential')
        
    Returns:
        Description text
    """
    descriptions = {
        'classic': 'Standard quality products made to traditional standards',
        'luxury': 'Premium quality products with enhanced features and materials',
        'essential': 'Budget-friendly options made to proper traditional standards, may have limited choices'
    }
    return descriptions.get(level, descriptions['classic'])

