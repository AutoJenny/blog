"""
Calendar Week Items Helper Functions

Provides unified interface for working with calendar_week_items table.
All content types (themes, ideas, events, recipes, profiles, words, phrases, syndication)
are managed through this unified interface.
"""

from typing import Optional, Dict, List, Any
from datetime import date, datetime
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Item type constants
ITEM_TYPE_THEME = 'theme'
ITEM_TYPE_IDEA = 'idea'
ITEM_TYPE_ANNUAL_EVENT = 'annual_event'
ITEM_TYPE_SPECIAL_EVENT = 'special_event'
ITEM_TYPE_RECIPE = 'recipe'
ITEM_TYPE_PROFILE = 'profile'
ITEM_TYPE_WEEKLY_WORD = 'weekly_word'
ITEM_TYPE_WEEKLY_PHRASE = 'weekly_phrase'
ITEM_TYPE_SYNDICATION = 'syndication'

VALID_ITEM_TYPES = {
    ITEM_TYPE_THEME, ITEM_TYPE_IDEA, ITEM_TYPE_ANNUAL_EVENT, ITEM_TYPE_SPECIAL_EVENT,
    ITEM_TYPE_RECIPE, ITEM_TYPE_PROFILE, ITEM_TYPE_WEEKLY_WORD, ITEM_TYPE_WEEKLY_PHRASE,
    ITEM_TYPE_SYNDICATION
}

def get_item_type_from_source(source_table: str, item_classification: Optional[str] = None, 
                              recurrence_type: Optional[str] = None) -> str:
    """
    Map source table and metadata to item_type.
    
    Args:
        source_table: Name of source table (calendar_themes, calendar_ideas, etc.)
        item_classification: For calendar_ideas, the item_classification value
        recurrence_type: For calendar_events, the event_recurrence_type value
    
    Returns:
        item_type string
    """
    if source_table == 'calendar_themes':
        return ITEM_TYPE_THEME
    elif source_table == 'calendar_ideas':
        if item_classification == 'weekly_word':
            return ITEM_TYPE_WEEKLY_WORD
        elif item_classification == 'weekly_phrase':
            return ITEM_TYPE_WEEKLY_PHRASE
        else:
            return ITEM_TYPE_IDEA
    elif source_table == 'calendar_events':
        if recurrence_type == 'annual':
            return ITEM_TYPE_ANNUAL_EVENT
        else:
            return ITEM_TYPE_SPECIAL_EVENT
    elif source_table == 'post':
        # Determined by post_type or profile_type - caller must specify
        raise ValueError("For post table, specify item_type directly (recipe or profile)")
    else:
        raise ValueError(f"Unknown source table: {source_table}")


def create_week_item(item_type: str, item_id: int, year: int, week_number: int,
                     weekday: Optional[int] = None, scheduled_date: Optional[date] = None,
                     is_selected: bool = False, priority: str = 'normal',
                     position: int = 0, metadata: Optional[Dict] = None,
                     notes: Optional[str] = None, is_active: bool = True) -> int:
    """
    Create entry in calendar_week_items.
    
    Args:
        item_type: Type of item (theme, idea, etc.)
        item_id: ID of item in source table
        year: Year for the week
        week_number: ISO week number (1-52)
        weekday: Day of week (1-7, Monday=1). NULL for week-level items.
        scheduled_date: Optional specific date
        is_selected: For themes, whether this is the selected theme
        priority: Priority level (normal, mandatory, random)
        position: Ordering position for same day/type
        metadata: Type-specific JSONB data
        notes: Optional notes
        is_active: Whether item is active
    
    Returns:
        ID of created calendar_week_items entry
    """
    if item_type not in VALID_ITEM_TYPES:
        raise ValueError(f"Invalid item_type: {item_type}")
    
    # Validate weekday for week-level items
    if item_type in (ITEM_TYPE_THEME, ITEM_TYPE_WEEKLY_WORD, ITEM_TYPE_WEEKLY_PHRASE):
        if weekday is not None:
            logger.warning(f"weekday should be NULL for {item_type}, ignoring provided value")
            weekday = None
    
    metadata_json = metadata or {}
    
    # Convert dict to JSON string for JSONB column
    import json
    if isinstance(metadata_json, dict):
        metadata_json = json.dumps(metadata_json)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO calendar_week_items (
                        item_type, item_id, year, week_number, weekday, scheduled_date,
                        is_selected, priority, position, metadata, notes, is_active,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (year, week_number, item_type, item_id)
                    DO UPDATE SET
                        weekday = EXCLUDED.weekday,
                        scheduled_date = EXCLUDED.scheduled_date,
                        is_selected = EXCLUDED.is_selected,
                        priority = EXCLUDED.priority,
                        position = EXCLUDED.position,
                        metadata = EXCLUDED.metadata,
                        notes = EXCLUDED.notes,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    item_type, item_id, year, week_number, weekday, scheduled_date,
                    is_selected, priority, position, metadata_json, notes, is_active
                ))
                
                result = cursor.fetchone()
                conn.commit()
                return result['id']
    except Exception as e:
        logger.error(f"Error creating week item: {e}")
        raise


def get_week_items(year: int, week_number: int, item_type: Optional[str] = None,
                   is_active: bool = True) -> List[Dict[str, Any]]:
    """
    Get all items for a week, optionally filtered by type.
    
    Args:
        year: Year for the week
        week_number: ISO week number (1-52)
        item_type: Optional filter by item type
        is_active: Whether to filter by is_active flag
    
    Returns:
        List of calendar_week_items records
    """
    try:
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT * FROM calendar_week_items
                WHERE year = %s AND week_number = %s
            """
            params = [year, week_number]
            
            if item_type:
                query += " AND item_type = %s"
                params.append(item_type)
            
            if is_active:
                query += " AND is_active = TRUE"
            
            query += " ORDER BY item_type, position, weekday NULLS LAST, id"
            
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting week items: {e}")
        raise


def get_selected_theme(year: int, week_number: int) -> Optional[Dict[str, Any]]:
    """
    Get the selected theme for a week.
    
    Args:
        year: Year for the week
        week_number: ISO week number (1-52)
    
    Returns:
        Theme item dict or None if no theme selected
    """
    items = get_week_items(year, week_number, item_type=ITEM_TYPE_THEME, is_active=True)
    for item in items:
        if item.get('is_selected'):
            return item
    return None


def update_week_item(item_id: int, **kwargs) -> bool:
    """
    Update a calendar_week_items entry.
    
    Args:
        item_id: ID of calendar_week_items entry
        **kwargs: Fields to update (weekday, scheduled_date, is_selected, etc.)
    
    Returns:
        True if updated, False if not found
    """
    if not kwargs:
        return False
    
    # Build update clause
    set_clause = []
    params = []
    
    import json as _json
    allowed_fields = ['year', 'week_number', 'weekday', 'scheduled_date', 'is_selected', 'priority',
                     'position', 'metadata', 'notes', 'is_active']
    
    for field, value in kwargs.items():
        if field in allowed_fields:
            if field == 'metadata':
                set_clause.append("metadata = %s::jsonb")
                params.append(_json.dumps(value) if isinstance(value, dict) else value)
            else:
                set_clause.append(f"{field} = %s")
                params.append(value)
    
    if not set_clause:
        return False
    
    set_clause.append("updated_at = NOW()")
    params.append(item_id)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE calendar_week_items
                    SET {', '.join(set_clause)}
                    WHERE id = %s
                """, params)
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating week item: {e}")
        raise


def delete_week_item(item_id: int) -> bool:
    """
    Delete a calendar_week_items entry (soft delete by setting is_active=False).
    
    Args:
        item_id: ID of calendar_week_items entry
    
    Returns:
        True if deleted, False if not found
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE calendar_week_items
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE id = %s
                """, (item_id,))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting week item: {e}")
        raise


def set_selected_theme(year: int, week_number: int, theme_id: int) -> bool:
    """
    Set the selected theme for a week. Unselects any previously selected theme.
    
    Args:
        year: Year for the week
        week_number: ISO week number (1-52)
        theme_id: ID of theme in calendar_themes table
    
    Returns:
        True if successful
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # First, unselect any currently selected theme
                cursor.execute("""
                    UPDATE calendar_week_items
                    SET is_selected = FALSE, updated_at = NOW()
                    WHERE year = %s AND week_number = %s 
                      AND item_type = 'theme' AND is_selected = TRUE
                """, (year, week_number))
                
                # Then, set the new selected theme
                # First ensure the item exists
                cursor.execute("""
                    INSERT INTO calendar_week_items (
                        item_type, item_id, year, week_number, is_selected, is_active
                    ) VALUES (
                        'theme', %s, %s, %s, TRUE, TRUE
                    )
                    ON CONFLICT (year, week_number, item_type, item_id)
                    DO UPDATE SET
                        is_selected = TRUE,
                        updated_at = NOW()
                """, (theme_id, year, week_number))
                
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error setting selected theme: {e}")
        raise

