"""
Calendar Cycle Resolver

Resolves which item appears in a specific week using:
1. Manual overrides (calendar_week_overrides) - highest priority
2. Cycle formula based on sequential list positions
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
            return 1  # Default
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


def get_override(category: str, year: int, week_number: int) -> Optional[int]:
    """
    Check for manual override for a specific week.
    
    Returns:
        item_id if override exists, None otherwise
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT item_id
                FROM calendar_week_overrides
                WHERE category = %s AND year = %s AND week_number = %s
            """, (category, year, week_number))
            result = cursor.fetchone()
            return result['item_id'] if result else None
    except Exception as e:
        logger.error(f"Error getting override for {category} week {year}-W{week_number}: {e}")
        return None


def get_item_by_position(category: str, position: int) -> Optional[Dict[str, Any]]:
    """Get item at specific position in category's list."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("""
                    SELECT id, theme_title as title, theme_description as description,
                           position, seasonal_context, priority, tags
                    FROM calendar_themes
                    WHERE position = %s
                    LIMIT 1
                """, (position,))
            elif category == 'recipe':
                cursor.execute("""
                    SELECT id, recipe_title as title, recipe_description as description,
                           position, seasonal_context, priority, tags
                    FROM calendar_recipes
                    WHERE position = %s
                    LIMIT 1
                """, (position,))
            elif category == 'profile_product':
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title,
                           p.profile_type, p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.position = %s AND cps.profile_type = 'product'
                    LIMIT 1
                """, (position,))
            elif category == 'profile_category':
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title,
                           p.profile_type, p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.position = %s AND cps.profile_type = 'category'
                    LIMIT 1
                """, (position,))
            elif category == 'profile_surname':
                cursor.execute("""
                    SELECT cps.post_id as id, cps.position, p.title,
                           p.profile_type, p.profile_product_id, p.profile_category_id
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.position = %s AND cps.profile_type = 'surname'
                    LIMIT 1
                """, (position,))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT id, position, idea_title as title, idea_description as description,
                           tags
                    FROM calendar_ideas
                    WHERE position = %s AND item_classification = 'weekly_word'
                    LIMIT 1
                """, (position,))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT id, position, idea_title as title, idea_description as description,
                           tags
                    FROM calendar_ideas
                    WHERE position = %s AND item_classification = 'weekly_phrase'
                    LIMIT 1
                """, (position,))
            else:
                return None
            
            result = cursor.fetchone()
            if result:
                item = dict(result)
                item['category'] = category
                return item
            
            return None
    except Exception as e:
        logger.error(f"Error getting item by position for {category} position {position}: {e}")
        return None


def get_item_by_id(category: str, item_id: int) -> Optional[Dict[str, Any]]:
    """Get item by ID (for overrides)."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("""
                    SELECT id, theme_title as title, theme_description as description,
                           position, seasonal_context, priority, tags
                    FROM calendar_themes
                    WHERE id = %s
                    LIMIT 1
                """, (item_id,))
            elif category == 'recipe':
                cursor.execute("""
                    SELECT id, recipe_title as title, recipe_description as description,
                           position, seasonal_context, priority, tags
                    FROM calendar_recipes
                    WHERE id = %s
                    LIMIT 1
                """, (item_id,))
            elif category in ('profile_product', 'profile_category', 'profile_surname'):
                cursor.execute("""
                    SELECT p.id, p.title, cps.position,
                           p.profile_type, p.profile_product_id, p.profile_category_id
                    FROM post p
                    LEFT JOIN calendar_profile_sequence cps ON p.id = cps.post_id
                    WHERE p.id = %s
                    LIMIT 1
                """, (item_id,))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT id, idea_title as title, idea_description as description,
                           position, tags
                    FROM calendar_ideas
                    WHERE id = %s AND item_classification = 'weekly_word'
                    LIMIT 1
                """, (item_id,))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT id, idea_title as title, idea_description as description,
                           position, tags
                    FROM calendar_ideas
                    WHERE id = %s AND item_classification = 'weekly_phrase'
                    LIMIT 1
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
        logger.error(f"Error getting item by ID for {category} item {item_id}: {e}")
        return None


def resolve_item_for_week(category: str, year: int, week_number: int) -> Optional[Dict[str, Any]]:
    """
    Resolve which item appears in a specific week.
    
    Priority:
    1. Check calendar_week_overrides for manual override
    2. Calculate position using cycle formula
    3. Return item at that position
    
    Args:
        category: Category name
        year: Year (e.g., 2025)
        week_number: ISO week number (1-52)
    
    Returns:
        Item dictionary with all relevant fields, or None if no item found
    """
    # Check for manual override first
    override_item_id = get_override(category, year, week_number)
    if override_item_id:
        item = get_item_by_id(category, override_item_id)
        if item:
            item['_override'] = True
            return item
    
    # Calculate position using cycle formula
    item_count = get_item_count(category)
    if item_count == 0:
        return None
    
    cycle_start = get_cycle_start_week(category)
    
    # Calculate absolute week number (handles year boundaries)
    absolute_week = (year - BASE_YEAR) * 52 + week_number
    
    # Calculate position using modular arithmetic
    position = ((absolute_week - cycle_start) % item_count) + 1
    
    # Get item at this position
    item = get_item_by_position(category, position)
    if item:
        item['_override'] = False
        item['_position'] = position
    return item

