"""
Planning Calendar API - Reassign Items to Specific Weeks

Simple, clear system for reassigning items to specific weeks.
Uses calendar_week_items overrides to pin items to specific weeks.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Import cache invalidation
try:
    from blueprints.planning_api_calendar_scheduling_cache import invalidate_scheduling_cache
except ImportError:
    logger.warning("Could not import invalidate_scheduling_cache")
    def invalidate_scheduling_cache():
        pass

# Import calendar_week_items utility
try:
    from utils.calendar_week_items import create_week_item
except ImportError:
    logger.error("Could not import create_week_item - reassignment will not work")
    create_week_item = None

bp = Blueprint('planning_api_calendar_reassign', __name__, url_prefix='/planning')


def get_item_id_from_category(category: str, item_id: int) -> Optional[int]:
    """
    Get the actual item ID for a category.
    For profiles, item_id is a post_id. For others, it's the table ID.
    """
    # For all categories except profiles, item_id is the direct ID
    if category in ('profile_product', 'profile_category', 'profile_surname'):
        # item_id is already the post_id, which is what we need
        return item_id
    else:
        # item_id is the table ID (theme.id, recipe.id, etc.)
        return item_id


def get_item_type_from_category(category: str) -> Optional[str]:
    """Map category name to calendar_week_items item_type."""
    mapping = {
        'theme': 'theme',
        'recipe': 'recipe',
        'profile_product': 'profile',
        'profile_category': 'profile',
        'profile_surname': 'profile',
        'weekly_word': 'weekly_word',
        'weekly_phrase': 'weekly_phrase'
    }
    return mapping.get(category)


def remove_week_override(category: str, item_id: int, year: int, week_number: int) -> bool:
    """Remove an override for an item in a specific week."""
    try:
        item_type = get_item_type_from_category(category)
        if not item_type:
            return False
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE calendar_week_items
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE item_type = %s
                        AND item_id = %s
                        AND year = %s
                        AND week_number = %s
                        AND is_active = TRUE
                """, (item_type, item_id, year, week_number))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error removing week override: {e}")
        return False


@bp.route('/api/calendar/reassign', methods=['POST'])
def api_reassign_item():
    """
    Reassign an item to a specific week.
    
    This is a simple, direct operation:
    1. Create/update a calendar_week_items override for the target week
    2. Remove any override for the source week (if it was an override)
    3. That's it - the override takes precedence over the cycle formula
    
    Request JSON:
    {
        "category": "theme|recipe|profile_product|profile_surname|weekly_word|weekly_phrase",
        "item_id": 123,
        "source_week": {"year": 2025, "week": 51},
        "target_week": {"year": 2025, "week": 49}
    }
    
    Returns:
    {
        "success": true,
        "message": "Item reassigned successfully"
    }
    """
    try:
        data = request.get_json() or {}
        category = data.get('category')
        item_id = data.get('item_id')
        source_week = data.get('source_week', {})
        target_week = data.get('target_week', {})
        
        # Validate inputs
        if not category or not item_id:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: category, item_id'
            }), 400
        
        if not target_week or not target_week.get('year') or not target_week.get('week'):
            return jsonify({
                'success': False,
                'error': 'Missing required field: target_week with year and week'
            }), 400
        
        valid_categories = ['theme', 'recipe', 'profile_product', 'profile_category', 'profile_surname', 'weekly_word', 'weekly_phrase']
        if category not in valid_categories:
            return jsonify({
                'success': False,
                'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400
        
        if not create_week_item:
            return jsonify({
                'success': False,
                'error': 'Week item creation not available'
            }), 500
        
        # Get item_type
        item_type = get_item_type_from_category(category)
        if not item_type:
            return jsonify({
                'success': False,
                'error': f'Could not map category {category} to item_type'
            }), 400
        
        # Get actual item ID
        actual_item_id = get_item_id_from_category(category, item_id)
        
        target_year = target_week['year']
        target_week_num = target_week['week']
        
        # Remove override from source week if provided
        if source_week and source_week.get('year') and source_week.get('week'):
            source_year = source_week['year']
            source_week_num = source_week['week']
            remove_week_override(category, actual_item_id, source_year, source_week_num)
        
        # Create/update override for target week
        try:
            # create_week_item expects metadata_json to be a dict that gets converted to JSONB
            # But we need to pass it properly - let's use an empty dict
            import json as json_lib
            metadata_json = {}  # Will be converted to JSONB by create_week_item
            
            create_week_item(
                item_type=item_type,
                item_id=actual_item_id,
                year=target_year,
                week_number=target_week_num,
                weekday=None,
                scheduled_date=None,
                is_selected=(category == 'theme'),
                priority='normal',
                position=0,
                metadata=metadata_json,
                notes=None,
                is_active=True
            )
        except Exception as e:
            logger.error(f"Error creating week item override: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to create override: {str(e)}'
            }), 500
        
        # Invalidate cache
        invalidate_scheduling_cache()
        
        return jsonify({
            'success': True,
            'message': f'Item reassigned to week {target_year}-W{target_week_num:02d}',
            'target_week': f'{target_year}-W{target_week_num:02d}'
        })
    
    except Exception as e:
        logger.error(f"Error in api_reassign_item: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

