"""
Planning Calendar API - Reordering Sequential Lists

Provides API endpoints for reordering items within category sequential lists.
Supports insertion and swapping modes for drag-and-drop functionality.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import cache invalidation function
try:
    from blueprints.planning_api_calendar_scheduling_cache import invalidate_scheduling_cache
except ImportError:
    logger.warning("Could not import invalidate_scheduling_cache - cache invalidation will be skipped")
    def invalidate_scheduling_cache():
        return False

# Import calendar_week_items utility
try:
    from utils.calendar_week_items import create_week_item, get_week_items
except ImportError:
    logger.warning("Could not import calendar_week_items utilities")
    create_week_item = None
    get_week_items = None

bp = Blueprint('planning_api_calendar_reorder', __name__)


def get_item_position(category: str, item_id: int) -> Optional[int]:
    """Get current position of an item in its category."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("SELECT position FROM calendar_themes WHERE id = %s", (item_id,))
            elif category == 'recipe':
                cursor.execute("SELECT position FROM calendar_recipes WHERE id = %s", (item_id,))
            elif category in ('profile_product', 'profile_category', 'profile_surname'):
                if category == 'profile_product':
                    profile_type = 'product'
                elif category == 'profile_category':
                    profile_type = 'category'
                else:  # profile_surname
                    profile_type = 'surname'
                cursor.execute("""
                    SELECT position FROM calendar_profile_sequence 
                    WHERE post_id = %s AND profile_type = %s
                """, (item_id, profile_type))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT position FROM calendar_ideas 
                    WHERE id = %s AND item_classification = 'weekly_word'
                """, (item_id,))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT position FROM calendar_ideas 
                    WHERE id = %s AND item_classification = 'weekly_phrase'
                """, (item_id,))
            else:
                return None
            
            result = cursor.fetchone()
            return result['position'] if result else None
    except Exception as e:
        logger.error(f"Error getting position for {category} item {item_id}: {e}")
        return None


def update_item_position(category: str, item_id: int, new_position: int, cursor=None) -> bool:
    """
    Update position of a specific item.
    
    Args:
        category: Category name
        item_id: Item ID to update
        new_position: New position value
        cursor: Optional database cursor (if provided, uses it; otherwise creates new connection)
    
    Returns:
        True if update succeeded, False otherwise
    """
    try:
        if cursor is not None:
            # Use provided cursor (part of existing transaction)
            if category == 'theme':
                cursor.execute("""
                    UPDATE calendar_themes 
                    SET position = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_position, item_id))
            elif category == 'recipe':
                cursor.execute("""
                    UPDATE calendar_recipes 
                    SET position = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_position, item_id))
            elif category in ('profile_product', 'profile_category', 'profile_surname'):
                if category == 'profile_product':
                    profile_type = 'product'
                elif category == 'profile_category':
                    profile_type = 'category'
                else:  # profile_surname
                    profile_type = 'surname'
                cursor.execute("""
                    UPDATE calendar_profile_sequence 
                    SET position = %s, updated_at = NOW()
                    WHERE post_id = %s AND profile_type = %s
                """, (new_position, item_id, profile_type))
            elif category == 'weekly_word':
                cursor.execute("""
                    UPDATE calendar_ideas 
                    SET position = %s, updated_at = NOW()
                    WHERE id = %s AND item_classification = 'weekly_word'
                """, (new_position, item_id))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    UPDATE calendar_ideas 
                    SET position = %s, updated_at = NOW()
                    WHERE id = %s AND item_classification = 'weekly_phrase'
                """, (new_position, item_id))
            else:
                return False
            
            return cursor.rowcount > 0
        else:
            # Create new connection (for standalone calls)
            with db_manager.get_connection() as conn:
                with conn.cursor() as new_cursor:
                    if category == 'theme':
                        new_cursor.execute("""
                            UPDATE calendar_themes 
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (new_position, item_id))
                    elif category == 'recipe':
                        new_cursor.execute("""
                            UPDATE calendar_recipes 
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (new_position, item_id))
                    elif category in ('profile_product', 'profile_category', 'profile_surname'):
                        if category == 'profile_product':
                            profile_type = 'product'
                        elif category == 'profile_category':
                            profile_type = 'category'
                        else:  # profile_surname
                            profile_type = 'surname'
                        new_cursor.execute("""
                            UPDATE calendar_profile_sequence 
                            SET position = %s, updated_at = NOW()
                            WHERE post_id = %s AND profile_type = %s
                        """, (new_position, item_id, profile_type))
                    elif category == 'weekly_word':
                        new_cursor.execute("""
                            UPDATE calendar_ideas 
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s AND item_classification = 'weekly_word'
                        """, (new_position, item_id))
                    elif category == 'weekly_phrase':
                        new_cursor.execute("""
                            UPDATE calendar_ideas 
                            SET position = %s, updated_at = NOW()
                            WHERE id = %s AND item_classification = 'weekly_phrase'
                        """, (new_position, item_id))
                    else:
                        return False
                    
                    conn.commit()
                    return new_cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating position for {category} item {item_id}: {e}")
        return False


def increment_positions(category: str, start_pos: int, end_pos: int, amount: int) -> bool:
    """Increment positions in range [start_pos, end_pos] by amount."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                if category == 'theme':
                    cursor.execute("""
                        UPDATE calendar_themes 
                        SET position = position + %s, updated_at = NOW()
                        WHERE position >= %s AND position <= %s
                    """, (amount, start_pos, end_pos))
                elif category == 'recipe':
                    cursor.execute("""
                        UPDATE calendar_recipes 
                        SET position = position + %s, updated_at = NOW()
                        WHERE position >= %s AND position <= %s
                    """, (amount, start_pos, end_pos))
                elif category in ('profile_product', 'profile_category', 'profile_surname'):
                    if category == 'profile_product':
                        profile_type = 'product'
                    elif category == 'profile_category':
                        profile_type = 'category'
                    else:  # profile_surname
                        profile_type = 'surname'
                    cursor.execute("""
                        UPDATE calendar_profile_sequence 
                        SET position = position + %s, updated_at = NOW()
                        WHERE position >= %s AND position <= %s AND profile_type = %s
                    """, (amount, start_pos, end_pos, profile_type))
                elif category == 'weekly_word':
                    cursor.execute("""
                        UPDATE calendar_ideas 
                        SET position = position + %s, updated_at = NOW()
                        WHERE position >= %s AND position <= %s 
                            AND item_classification = 'weekly_word'
                    """, (amount, start_pos, end_pos))
                elif category == 'weekly_phrase':
                    cursor.execute("""
                        UPDATE calendar_ideas 
                        SET position = position + %s, updated_at = NOW()
                        WHERE position >= %s AND position <= %s 
                            AND item_classification = 'weekly_phrase'
                    """, (amount, start_pos, end_pos))
                else:
                    return False
                
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error incrementing positions for {category}: {e}")
        return False


def get_item_at_position(category: str, position: int) -> Optional[int]:
    """Get item ID at a specific position."""
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                cursor.execute("SELECT id FROM calendar_themes WHERE position = %s", (position,))
            elif category == 'recipe':
                cursor.execute("SELECT id FROM calendar_recipes WHERE position = %s", (position,))
            elif category in ('profile_product', 'profile_category', 'profile_surname'):
                if category == 'profile_product':
                    profile_type = 'product'
                elif category == 'profile_category':
                    profile_type = 'category'
                else:  # profile_surname
                    profile_type = 'surname'
                cursor.execute("""
                    SELECT post_id as id FROM calendar_profile_sequence 
                    WHERE position = %s AND profile_type = %s
                """, (position, profile_type))
            elif category == 'weekly_word':
                cursor.execute("""
                    SELECT id FROM calendar_ideas 
                    WHERE position = %s AND item_classification = 'weekly_word'
                """, (position,))
            elif category == 'weekly_phrase':
                cursor.execute("""
                    SELECT id FROM calendar_ideas 
                    WHERE position = %s AND item_classification = 'weekly_phrase'
                """, (position,))
            else:
                return None
            
            result = cursor.fetchone()
            return result['id'] if result else None
    except Exception as e:
        logger.error(f"Error getting item at position {position} for {category}: {e}")
        return None


@bp.route('/api/calendar/reorder', methods=['POST'])
def api_reorder_item():
    """
    Reorder items within a category's sequential list.
    
    IMPORTANT: This endpoint uses SWAP mode to preserve the sequential cycle.
    When moving an item to a week, we swap it with the item currently in that week's position.
    This ensures all weeks remain filled and the cycle formula continues to work.
    
    Request JSON:
    {
        "category": "theme|recipe|profile_product|profile_category|weekly_word|weekly_phrase",
        "item_id": 123,
        "new_position": 5,
        "target_week": {"year": 2025, "week": 49}  // Optional: for logging/debugging
    }
    
    Returns:
    {
        "success": true,
        "message": "Item swapped successfully",
        "old_position": 52,
        "new_position": 5,
        "swapped_with_item_id": 456
    }
    """
    try:
        data = request.get_json() or {}
        category = data.get('category')
        item_id = data.get('item_id')
        new_position = data.get('new_position')
        target_week = data.get('target_week')  # For logging only
        
        # Validate inputs
        if not category or not item_id or new_position is None:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: category, item_id, new_position'
            }), 400
        
        if new_position < 1:
            return jsonify({
                'success': False,
                'error': 'new_position must be >= 1'
            }), 400
        
        valid_categories = ['theme', 'recipe', 'profile_product', 'profile_category', 'profile_surname', 'weekly_word', 'weekly_phrase']
        if category not in valid_categories:
            return jsonify({
                'success': False,
                'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400
        
        # Get current position
        current_position = get_item_position(category, item_id)
        if current_position is None:
            return jsonify({
                'success': False,
                'error': f'Item {item_id} not found in category {category}'
            }), 404
        
        # If already at target position, no-op
        if current_position == new_position:
            return jsonify({
                'success': True,
                'message': 'Item already at target position',
                'old_position': current_position,
                'new_position': new_position
            })
        
        # Get target week info
        target_year = target_week.get('year') if target_week else None
        target_week_num = target_week.get('week') if target_week else None
        
        # Map category to item_type for calendar_week_items
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
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # If target week is specified, create/update a calendar_week_items override
                # This ensures the item appears in that specific week, not just in all weeks where its position cycles
                if target_year and target_week_num and item_type and create_week_item:
                    # Deactivate any existing override for this item in other weeks (optional cleanup)
                    # We'll just create/update the override for the target week
                    
                    # Create or update the override
                    try:
                        create_week_item(
                            item_type=item_type,
                            item_id=item_id,
                            year=target_year,
                            week_number=target_week_num,
                            weekday=None,  # Week-level items don't have weekday
                            scheduled_date=None,
                            is_selected=(category == 'theme'),  # Themes can be selected
                            priority='normal',
                            position=0,
                            metadata=None,
                            notes=None,
                            is_active=True
                        )
                        logger.info(f"Created override for {category} item {item_id} in week {target_year}-W{target_week_num}")
                    except Exception as e:
                        logger.error(f"Error creating week item override: {e}")
                        # Continue with position swap as fallback
                
                # Also swap positions to maintain the sequential list order
                # This ensures the item's position in the list is correct for cycling
                other_item_id = get_item_at_position(category, new_position)
                
                if other_item_id:
                    # Swap: move our item to target position, move other item to our old position
                    # This preserves the cycle - the position still appears in the same week, just with different items
                    # We need to use a temporary position to avoid unique constraint violations
                    temp_position = 99999  # Temporary position that shouldn't conflict
                    
                    # Step 1: Move our item to temporary position
                    update_item_position(category, item_id, temp_position, cursor)
                    
                    # Step 2: Move other item to our old position
                    update_item_position(category, other_item_id, current_position, cursor)
                    
                    # Step 3: Move our item to target position
                    update_item_position(category, item_id, new_position, cursor)
                    
                    swapped_with = other_item_id
                else:
                    # No item at target position (shouldn't happen in a properly filled list, but handle gracefully)
                    logger.warning(f"No item found at position {new_position} for category {category} - just moving item")
                    update_item_position(category, item_id, new_position, cursor)
                    swapped_with = None
                
                conn.commit()
        
        # Invalidate the scheduling cache so fresh data is loaded
        invalidate_scheduling_cache()
        
        message = f'Item assigned to week {target_year}-W{target_week_num}' if (target_year and target_week_num) else f'Item moved to position {new_position}'
        if swapped_with:
            message += f' (swapped position with item {swapped_with})'
        
        return jsonify({
            'success': True,
            'message': message,
            'old_position': current_position,
            'new_position': new_position,
            'swapped_with_item_id': swapped_with,
            'target_week': f'{target_year}-W{target_week_num}' if (target_year and target_week_num) else None
        })
    
    except Exception as e:
        logger.error(f"Error in api_reorder_item: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/calendar/position-for-week', methods=['GET'])
def api_position_for_week():
    """
    Calculate what position should appear in a specific week for a category.
    
    Query params:
    - category: Category name (theme, recipe, etc.)
    - year: Year (e.g., 2025)
    - week: Week number (1-52)
    
    Returns:
    {
        "success": true,
        "position": 5
    }
    """
    try:
        from utils.calendar_sequential_resolver import calculate_position_for_week
        
        category = request.args.get('category')
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        if not category or not year or not week:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: category, year, week'
            }), 400
        
        position = calculate_position_for_week(category, year, week)
        
        if position is None:
            return jsonify({
                'success': False,
                'error': 'Could not calculate position (no items in category?)'
            }), 404
        
        return jsonify({
            'success': True,
            'position': position,
            'category': category,
            'year': year,
            'week': week
        })
    
    except Exception as e:
        logger.error(f"Error in api_position_for_week: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

