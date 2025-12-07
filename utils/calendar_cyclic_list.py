"""
Cyclic Calendar List Operations

Implements add, delete, and reorder operations for cyclic lists.
All operations maintain contiguous positions (1, 2, 3, ... N) with no gaps.
"""

import logging
from typing import Optional, List, Dict, Any
from config.database import db_manager

logger = logging.getLogger(__name__)


def get_table_and_id_column(category: str) -> tuple[Optional[str], Optional[str], Optional[Dict]]:
    """
    Get table name, ID column, and any additional filters for a category.
    
    Returns:
        (table_name, id_column, filters_dict) or (None, None, None) if invalid
    """
    mapping = {
        'theme': ('calendar_themes', 'id', {}),
        'recipe': ('calendar_recipes', 'id', {}),
        'profile_product': ('calendar_profile_sequence', 'post_id', {'profile_type': 'product'}),
        'profile_category': ('calendar_profile_sequence', 'post_id', {'profile_type': 'category'}),
        'profile_surname': ('calendar_profile_sequence', 'post_id', {'profile_type': 'surname'}),
        'weekly_word': ('calendar_ideas', 'id', {'item_classification': 'weekly_word'}),
        'weekly_phrase': ('calendar_ideas', 'id', {'item_classification': 'weekly_phrase'}),
    }
    return mapping.get(category, (None, None, None))


def get_max_position(category: str) -> int:
    """Get the maximum position in a category's list."""
    table_name, _, filters = get_table_and_id_column(category)
    if not table_name:
        return 0
    
    try:
        with db_manager.get_cursor() as cursor:
            query = f"SELECT COALESCE(MAX(position), 0) as max_pos FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = %s")
                    params.append(value)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
            return result['max_pos'] if result else 0
    except Exception as e:
        logger.error(f"Error getting max position for {category}: {e}")
        return 0


def reorder_item(category: str, item_id: int, new_pos: int) -> bool:
    """
    Move an item from its current position to a new position.
    Automatically shifts other items to maintain contiguous positions.
    
    Args:
        category: Category name
        item_id: Item ID to move
        new_pos: Target position (1-based)
    
    Returns:
        True if successful, False otherwise
    """
    table_name, id_column, filters = get_table_and_id_column(category)
    if not table_name:
        logger.error(f"Invalid category: {category}")
        return False
    
    if new_pos < 1:
        logger.error(f"Invalid position: {new_pos} (must be >= 1)")
        return False
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get current position
                query = f"SELECT position FROM {table_name} WHERE {id_column} = %s"
                params = [item_id]
                
                if filters:
                    for key, value in filters.items():
                        query += f" AND {key} = %s"
                        params.append(value)
                
                cursor.execute(query, tuple(params))
                result = cursor.fetchone()
                
                if not result:
                    logger.error(f"Item {item_id} not found in {category}")
                    return False
                
                old_pos = result['position']
                
                if old_pos == new_pos:
                    logger.info(f"Item already at position {new_pos}")
                    return True
                
                # Build WHERE clause for filters
                filter_where = ""
                filter_params = []
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        conditions.append(f"{key} = %s")
                        filter_params.append(value)
                    if conditions:
                        filter_where = " AND " + " AND ".join(conditions)
                
                # Move item
                if new_pos > old_pos:
                    # Moving down: shift items between old_pos and new_pos up
                    shift_query = f"""
                        UPDATE {table_name}
                        SET position = position - 1, updated_at = NOW()
                        WHERE position > %s AND position <= %s {filter_where}
                    """
                    cursor.execute(shift_query, (old_pos, new_pos) + tuple(filter_params))
                else:
                    # Moving up: shift items between new_pos and old_pos down
                    shift_query = f"""
                        UPDATE {table_name}
                        SET position = position + 1, updated_at = NOW()
                        WHERE position >= %s AND position < %s {filter_where}
                    """
                    cursor.execute(shift_query, (new_pos, old_pos) + tuple(filter_params))
                
                # Update item to new position
                update_query = f"""
                    UPDATE {table_name}
                    SET position = %s, updated_at = NOW()
                    WHERE {id_column} = %s {filter_where}
                """
                cursor.execute(update_query, (new_pos, item_id) + tuple(filter_params))
                
                conn.commit()
                logger.info(f"Moved {category} item {item_id} from position {old_pos} to {new_pos}")
                return True
                
    except Exception as e:
        logger.error(f"Error reordering {category} item {item_id}: {e}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return False


def add_item(category: str, item_id: int, insert_pos: Optional[int] = None) -> bool:
    """
    Add an item to the list.
    
    Args:
        category: Category name
        item_id: Item ID to add
        insert_pos: Position to insert at (None = append at end)
    
    Returns:
        True if successful, False otherwise
    """
    table_name, id_column, filters = get_table_and_id_column(category)
    if not table_name:
        logger.error(f"Invalid category: {category}")
        return False
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if item already exists
                check_query = f"SELECT position FROM {table_name} WHERE {id_column} = %s"
                params = [item_id]
                
                if filters:
                    for key, value in filters.items():
                        check_query += f" AND {key} = %s"
                        params.append(value)
                
                cursor.execute(check_query, tuple(params))
                if cursor.fetchone():
                    logger.warning(f"Item {item_id} already exists in {category}")
                    return False
                
                # Determine insert position
                if insert_pos is None:
                    # Append at end
                    max_pos = get_max_position(category)
                    insert_pos = max_pos + 1
                else:
                    if insert_pos < 1:
                        logger.error(f"Invalid position: {insert_pos}")
                        return False
                    
                    # Shift existing items
                    filter_where = ""
                    filter_params = []
                    if filters:
                        conditions = []
                        for key, value in filters.items():
                            conditions.append(f"{key} = %s")
                            filter_params.append(value)
                        if conditions:
                            filter_where = " AND " + " AND ".join(conditions)
                    
                    shift_query = f"""
                        UPDATE {table_name}
                        SET position = position + 1, updated_at = NOW()
                        WHERE position >= %s {filter_where}
                    """
                    cursor.execute(shift_query, (insert_pos,) + tuple(filter_params))
                
                # Insert item
                # For calendar_themes and calendar_recipes, we need to insert with position
                # For calendar_profile_sequence, we need to insert with profile_type
                # For calendar_ideas, we need to insert with item_classification
                
                if category in ('theme', 'recipe'):
                    insert_query = f"""
                        UPDATE {table_name}
                        SET position = %s, updated_at = NOW()
                        WHERE {id_column} = %s
                    """
                    cursor.execute(insert_query, (insert_pos, item_id))
                elif category in ('profile_product', 'profile_category', 'profile_surname'):
                    # Check if entry exists, if not create it
                    check_query = f"SELECT post_id FROM {table_name} WHERE post_id = %s AND profile_type = %s"
                    cursor.execute(check_query, (item_id, filters['profile_type']))
                    if cursor.fetchone():
                        update_query = f"""
                            UPDATE {table_name}
                            SET position = %s, updated_at = NOW()
                            WHERE post_id = %s AND profile_type = %s
                        """
                        cursor.execute(update_query, (insert_pos, item_id, filters['profile_type']))
                    else:
                        insert_query = f"""
                            INSERT INTO {table_name} (post_id, profile_type, position, created_at, updated_at)
                            VALUES (%s, %s, %s, NOW(), NOW())
                        """
                        cursor.execute(insert_query, (item_id, filters['profile_type'], insert_pos))
                elif category in ('weekly_word', 'weekly_phrase'):
                    update_query = f"""
                        UPDATE {table_name}
                        SET position = %s, updated_at = NOW()
                        WHERE id = %s AND item_classification = %s
                    """
                    cursor.execute(update_query, (insert_pos, item_id, filters['item_classification']))
                
                conn.commit()
                logger.info(f"Added {category} item {item_id} at position {insert_pos}")
                return True
                
    except Exception as e:
        logger.error(f"Error adding {category} item {item_id}: {e}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return False


def delete_item(category: str, item_id: int) -> bool:
    """
    Delete an item from the list and shift remaining items.
    
    Args:
        category: Category name
        item_id: Item ID to delete
    
    Returns:
        True if successful, False otherwise
    """
    table_name, id_column, filters = get_table_and_id_column(category)
    if not table_name:
        logger.error(f"Invalid category: {category}")
        return False
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get current position
                query = f"SELECT position FROM {table_name} WHERE {id_column} = %s"
                params = [item_id]
                
                if filters:
                    for key, value in filters.items():
                        query += f" AND {key} = %s"
                        params.append(value)
                
                cursor.execute(query, tuple(params))
                result = cursor.fetchone()
                
                if not result:
                    logger.warning(f"Item {item_id} not found in {category}")
                    return False
                
                old_pos = result['position']
                
                # Build filter WHERE clause
                filter_where = ""
                filter_params = []
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        conditions.append(f"{key} = %s")
                        filter_params.append(value)
                    if conditions:
                        filter_where = " AND " + " AND ".join(conditions)
                
                # Delete item
                delete_query = f"DELETE FROM {table_name} WHERE {id_column} = %s {filter_where}"
                cursor.execute(delete_query, (item_id,) + tuple(filter_params))
                
                # Shift remaining items
                shift_query = f"""
                    UPDATE {table_name}
                    SET position = position - 1, updated_at = NOW()
                    WHERE position > %s {filter_where}
                """
                cursor.execute(shift_query, (old_pos,) + tuple(filter_params))
                
                conn.commit()
                logger.info(f"Deleted {category} item {item_id} from position {old_pos}")
                return True
                
    except Exception as e:
        logger.error(f"Error deleting {category} item {item_id}: {e}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return False


def get_ordered_list(category: str) -> List[Dict[str, Any]]:
    """
    Get all items in a category ordered by position.
    
    Returns:
        List of item dictionaries with id, position, and title fields
    """
    table_name, id_column, filters = get_table_and_id_column(category)
    if not table_name:
        return []
    
    try:
        with db_manager.get_cursor() as cursor:
            if category == 'theme':
                query = """
                    SELECT id, position, theme_title as title
                    FROM calendar_themes
                    WHERE position IS NOT NULL
                    ORDER BY position
                """
            elif category == 'recipe':
                query = """
                    SELECT id, position, recipe_title as title
                    FROM calendar_recipes
                    WHERE position IS NOT NULL
                    ORDER BY position
                """
            elif category in ('profile_product', 'profile_category', 'profile_surname'):
                profile_type = filters['profile_type']
                query = f"""
                    SELECT cps.post_id as id, cps.position, p.title
                    FROM calendar_profile_sequence cps
                    JOIN post p ON cps.post_id = p.id
                    WHERE cps.profile_type = %s
                    ORDER BY cps.position
                """
                cursor.execute(query, (profile_type,))
                return [dict(row) for row in cursor.fetchall()]
            elif category in ('weekly_word', 'weekly_phrase'):
                item_class = filters['item_classification']
                query = f"""
                    SELECT id, position, idea_title as title
                    FROM calendar_ideas
                    WHERE item_classification = %s AND position IS NOT NULL
                    ORDER BY position
                """
                cursor.execute(query, (item_class,))
                return [dict(row) for row in cursor.fetchall()]
            else:
                return []
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Error getting ordered list for {category}: {e}")
        return []

