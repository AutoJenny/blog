"""
Calendar Sequential List Resolver

Resolves which item appears in a specific week using sequential list cycling.
Each category maintains an independent ordered list with positions (1, 2, 3, ... N).
Items cycle through weeks using modular arithmetic.

Formula: position = ((absolute_week - cycle_start_week) % item_count) + 1
"""

import logging
from typing import Optional, Dict, Any
from config.database import db_manager

logger = logging.getLogger(__name__)

# Base year for absolute week calculation
BASE_YEAR = 2025


def get_cycle_start_week(category: str) -> int:
    """Get the cycle start week for a category."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cycle_start_week
                FROM calendar_category_cycles
                WHERE category = %s
            """, (category,))
            result = cursor.fetchone()
            if result:
                return result['cycle_start_week']
            # Default to 1 if not configured
            return 1
    except Exception as e:
        logger.error(f"Error getting cycle start week for {category}: {e}")
        return 1


def get_item_count(category: str) -> int:
    """Get total number of items in category's sequential list."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("SELECT COUNT(*) as count FROM calendar_themes WHERE position IS NOT NULL")
            elif category == 'recipe':
                cursor.execute("SELECT COUNT(*) as count FROM calendar_recipes WHERE position IS NOT NULL")
            elif category == 'profile_product':
                cursor.execute("SELECT COUNT(*) as count FROM calendar_profile_sequence WHERE profile_type = 'product'")
            elif category == 'profile_category':
                cursor.execute("SELECT COUNT(*) as count FROM calendar_profile_sequence WHERE profile_type = 'category'")
            elif category == 'profile_surname':
                cursor.execute("SELECT COUNT(*) as count FROM calendar_profile_sequence WHERE profile_type = 'surname'")
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT COUNT(*) as count FROM calendar_ideas 
                    WHERE item_classification = 'weekly_word' AND position IS NOT NULL
                """)
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT COUNT(*) as count FROM calendar_ideas 
                    WHERE item_classification = 'weekly_phrase' AND position IS NOT NULL
                """)
            else:
                return 0
            
            result = cursor.fetchone()
            return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Error getting item count for {category}: {e}")
        return 0


def calculate_position_for_week(category: str, year: int, week_number: int) -> Optional[int]:
    """
    Calculate which position in the sequential list should appear in a specific week.
    
    Args:
        category: Category name (theme, recipe, profile_product, etc.)
        year: Year (e.g., 2025)
        week_number: ISO week number (1-52)
    
    Returns:
        Position number (1, 2, 3, ...) or None if no items exist
    """
    item_count = get_item_count(category)
    if item_count == 0:
        return None
    
    cycle_start = get_cycle_start_week(category)
    
    # Calculate absolute week number (handles year boundaries)
    absolute_week = (year - BASE_YEAR) * 52 + week_number
    
    # Calculate position using modular arithmetic
    position = ((absolute_week - cycle_start) % item_count) + 1
    
    return position


def resolve_item_for_week(category: str, year: int, week_number: int) -> Optional[Dict[str, Any]]:
    """
    Resolve which item appears in a specific week using sequential list cycling.
    
    Priority:
    1. Check calendar_week_items for year-specific override
    2. Calculate position using cycle formula
    3. Return item at that position
    
    Args:
        category: Category name (theme, recipe, profile_product, profile_category, weekly_word, weekly_phrase)
        year: Year (e.g., 2025)
        week_number: ISO week number (1-52)
    
    Returns:
        Item dictionary with all relevant fields, or None if no item found
    """
    # Check for year-specific override first
    override = get_calendar_week_item_override(category, year, week_number)
    if override:
        return override
    
    # Calculate position
    position = calculate_position_for_week(category, year, week_number)
    if position is None:
        return None
    
    # Get item at this position
    return get_item_by_position(category, position)


def get_calendar_week_item_override(category: str, year: int, week_number: int) -> Optional[Dict[str, Any]]:
    """Check for year-specific override in calendar_week_items."""
    try:
        with db_manager.get_cursor() as cursor:
            # Map category to item_type
            item_type_map = {
                'theme': 'theme',
                'recipe': 'recipe',
                'profile_product': 'profile',
                'profile_category': 'profile',
                'profile_surname': 'profile',
                'weekly_word': 'weekly_word',
                'weekly_phrase': 'weekly_phrase'
            }
            item_type = item_type_map.get(category)
            if not item_type:
                return None
            
            cursor.execute("""
                SELECT cwi.*, cwi.item_id
                FROM calendar_week_items cwi
                WHERE cwi.item_type = %s
                    AND cwi.year = %s
                    AND cwi.week_number = %s
                    AND cwi.is_active = TRUE
                LIMIT 1
            """, (item_type, year, week_number))
            
            result = cursor.fetchone()
            if result:
                # Get full item details based on category
                return get_item_details(category, result['item_id'])
            
            return None
    except Exception as e:
        logger.error(f"Error checking override for {category} week {year}-{week_number}: {e}")
        return None


def get_item_by_position(category: str, position: int) -> Optional[Dict[str, Any]]:
    """Get item at specific position in category's list."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("""
                    SELECT id, week_number, theme_title as title, theme_description as description,
                           seasonal_context, priority, tags, position
                    FROM calendar_themes
                    WHERE position = %s
                    LIMIT 1
                """, (position,))
            elif category == 'recipe':
                cursor.execute("""
                    SELECT id, week_number, recipe_title as title, recipe_description as description,
                           seasonal_context, priority, tags, position
                    FROM calendar_recipes
                    WHERE position = %s
                    LIMIT 1
                """, (position,))
            elif category == 'profile_product':
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title, p.profile_type,
                           p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.position = %s AND cps.profile_type = 'product'
                    LIMIT 1
                """, (position,))
            elif category == 'profile_category':
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title, p.profile_type,
                           p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.position = %s AND cps.profile_type = 'category'
                    LIMIT 1
                """, (position,))
            elif category == 'profile_surname':
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title, p.profile_type,
                           p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.position = %s AND cps.profile_type = 'surname'
                    LIMIT 1
                """, (position,))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT id, week_number, idea_title as title, idea_description as description,
                           tags, position
                    FROM calendar_ideas
                    WHERE position = %s AND item_classification = 'weekly_word'
                    LIMIT 1
                """, (position,))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT id, week_number, idea_title as title, idea_description as description,
                           tags, position
                    FROM calendar_ideas
                    WHERE position = %s AND item_classification = 'weekly_phrase'
                    LIMIT 1
                """, (position,))
            else:
                return None
            
            result = cursor.fetchone()
            if result:
                # Convert to dict and add category info
                item = dict(result)
                item['category'] = category
                return item
            
            return None
    except Exception as e:
        logger.error(f"Error getting item by position for {category} position {position}: {e}")
        return None


def get_item_details(category: str, item_id: int) -> Optional[Dict[str, Any]]:
    """Get full details for an item by ID."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("""
                    SELECT id, week_number, theme_title as title, theme_description as description,
                           seasonal_context, priority, tags, position
                    FROM calendar_themes
                    WHERE id = %s
                """, (item_id,))
            elif category == 'recipe':
                cursor.execute("""
                    SELECT id, week_number, recipe_title as title, recipe_description as description,
                           seasonal_context, priority, tags, position
                    FROM calendar_recipes
                    WHERE id = %s
                """, (item_id,))
            elif category in ('profile_product', 'profile_category', 'profile_surname'):
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title, p.profile_type,
                           p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.post_id = %s
                    LIMIT 1
                """, (item_id,))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT id, week_number, idea_title as title, idea_description as description,
                           tags, position
                    FROM calendar_ideas
                    WHERE id = %s AND item_classification = 'weekly_word'
                """, (item_id,))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT id, week_number, idea_title as title, idea_description as description,
                           tags, position
                    FROM calendar_ideas
                    WHERE id = %s AND item_classification = 'weekly_phrase'
                """, (item_id,))
            else:
                return None
            
            result = cursor.fetchone()
            if result:
                item = dict(result)
                item['category'] = category
                return item
            
            return None
    except Exception as e:
        logger.error(f"Error getting item details for {category} ID {item_id}: {e}")
        return None

