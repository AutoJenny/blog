"""Select theme from calendar_ideas based on week number."""

from __future__ import annotations

from typing import Any, Dict, Optional
from config.database import db_manager


def parse_target_week(target_week: str) -> int:
    """Extract ISO week number from target_week string like '2025W44'."""
    try:
        if 'W' in target_week:
            week_str = target_week.split('W')[1]
            return int(week_str)
        return int(target_week)
    except Exception:
        return 0


def get_themes_for_week(week_number: int) -> list[Dict[str, Any]]:
    """Get all calendar ideas (themes) for a specific week number, ordered by priority.
    
    Excludes weekly_phrase and weekly_word entries - these are content items, not themes.
    """
    if week_number < 1 or week_number > 53:
        return []
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if item_classification column exists
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_ideas' AND column_name = 'item_classification'
                """)
                has_classification = cur.fetchone() is not None
                
                if has_classification:
                    # Filter out weekly_phrase and weekly_word - only get themes
                    cur.execute(
                        """
                        SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                               ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                               ci.is_recurring, ci.created_at, ci.updated_at
                        FROM calendar_ideas ci
                        WHERE ci.week_number = %s
                          AND (ci.item_classification = 'theme' 
                               OR ci.item_classification IS NULL 
                               OR ci.item_classification = 'idea')
                          AND ci.item_classification NOT IN ('weekly_phrase', 'weekly_word')
                        ORDER BY 
                            CASE ci.priority 
                                WHEN 'mandatory' THEN 1 
                                WHEN 'random' THEN 2 
                                ELSE 3 
                            END,
                            ci.id
                        """,
                        (week_number,),
                    )
                else:
                    # Fallback for older schema without item_classification
                    cur.execute(
                        """
                        SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                               ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                               ci.is_recurring, ci.created_at, ci.updated_at
                        FROM calendar_ideas ci
                        WHERE ci.week_number = %s
                        ORDER BY 
                            CASE ci.priority 
                                WHEN 'mandatory' THEN 1 
                                WHEN 'random' THEN 2 
                                ELSE 3 
                            END,
                            ci.id
                        """,
                        (week_number,),
                    )
                rows = cur.fetchall() or []
                return [dict(r) for r in rows]
    except Exception:
        return []


def select_default_theme(*, target_week: str) -> Optional[Dict[str, Any]]:
    """Select the default theme for a target week.
    
    Priority order:
    1. Check calendar_schedule for selected theme for this year/week
    2. Check calendar_themes for perpetual themes for this week
    3. Fallback to calendar_ideas (legacy)
    """
    # Parse year and week from target_week (e.g., "2025W48")
    iso_year, iso_week = None, None
    try:
        if 'W' in target_week:
            year_str, week_str = target_week.split('W')
            iso_year = int(year_str)
            iso_week = int(week_str)
        else:
            iso_week = int(target_week)
    except Exception:
        iso_week = parse_target_week(target_week)
    
    # First: Check calendar_schedule for selected theme (year-specific selection)
    if iso_year and iso_week:
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if calendar_schedule table exists and has theme_id column
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'calendar_schedule' AND column_name = 'theme_id'
                    """)
                    has_theme_id = cur.fetchone() is not None
                    
                    if has_theme_id:
                        # Get selected theme from calendar_schedule for this year/week
                        cur.execute("""
                            SELECT cs.theme_id, ct.id, ct.week_number, ct.theme_title, 
                                   ct.theme_description, ct.seasonal_context, ct.priority, ct.tags
                            FROM calendar_schedule cs
                            LEFT JOIN calendar_themes ct ON cs.theme_id = ct.id
                            WHERE cs.year = %s AND cs.week_number = %s AND cs.theme_id IS NOT NULL
                            ORDER BY cs.updated_at DESC
                            LIMIT 1
                        """, (iso_year, iso_week))
                        schedule_theme = cur.fetchone()
                        if schedule_theme:
                            theme_dict = dict(schedule_theme)
                            # Only return if we have a valid theme (LEFT JOIN might return None for ct fields)
                            if theme_dict.get('theme_id') and theme_dict.get('id'):
                                # Found selected theme in schedule - return it
                                # Map calendar_themes fields to expected format
                                return {
                                    'id': theme_dict.get('id'),
                                    'week_number': theme_dict.get('week_number'),
                                    'idea_title': theme_dict.get('theme_title'),  # Map theme_title to idea_title for compatibility
                                    'idea_description': theme_dict.get('theme_description'),
                                    'seasonal_context': theme_dict.get('seasonal_context'),
                                    'priority': theme_dict.get('priority'),
                                    'tags': theme_dict.get('tags'),
                                    'content_type': None,
                                    'is_recurring': True,
                                    'created_at': None,
                                    'updated_at': None
                                }
        except Exception as e:
            # Log error but continue to next check
            import logging
            logging.getLogger(__name__).warning(f"Error checking calendar_schedule for theme: {e}")
            pass  # Fall through to next check
    
    # Second: Check calendar_themes for perpetual themes for this week
    if iso_week:
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'calendar_themes'
                        )
                    """)
                    has_themes_table = cur.fetchone() is not None
                    
                    if has_themes_table:
                        cur.execute("""
                            SELECT id, week_number, theme_title, theme_description, 
                                   seasonal_context, priority, tags
                            FROM calendar_themes
                            WHERE week_number = %s
                            ORDER BY 
                                CASE priority 
                                    WHEN 'mandatory' THEN 1 
                                    WHEN 'random' THEN 2 
                                    ELSE 3 
                                END,
                                id
                            LIMIT 1
                        """, (iso_week,))
                        theme_row = cur.fetchone()
                        if theme_row:
                            theme_dict = dict(theme_row)
                            # Map calendar_themes fields to expected format
                            return {
                                'id': theme_dict.get('id'),
                                'week_number': theme_dict.get('week_number'),
                                'idea_title': theme_dict.get('theme_title'),  # Map theme_title to idea_title for compatibility
                                'idea_description': theme_dict.get('theme_description'),
                                'seasonal_context': theme_dict.get('seasonal_context'),
                                'priority': theme_dict.get('priority'),
                                'tags': theme_dict.get('tags'),
                                'content_type': None,
                                'is_recurring': True,
                                'created_at': None,
                                'updated_at': None
                            }
        except Exception:
            pass  # Fall through to legacy check
    
    # Third: Fallback to calendar_ideas (legacy)
    if iso_week:
        themes = get_themes_for_week(iso_week)
        if themes:
            return themes[0]
    
    return None


def get_theme_by_id(theme_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific theme by ID. Checks calendar_themes first, then calendar_ideas."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # First check calendar_themes
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'calendar_themes'
                    )
                """)
                has_themes_table = cur.fetchone() is not None
                
                if has_themes_table:
                    cur.execute(
                        """
                        SELECT id, week_number, theme_title, theme_description, 
                               seasonal_context, priority, tags
                        FROM calendar_themes
                        WHERE id = %s
                        """,
                        (theme_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        theme_dict = dict(row)
                        # Map calendar_themes fields to expected format
                        return {
                            'id': theme_dict.get('id'),
                            'week_number': theme_dict.get('week_number'),
                            'idea_title': theme_dict.get('theme_title'),  # Map theme_title to idea_title
                            'idea_description': theme_dict.get('theme_description'),
                            'seasonal_context': theme_dict.get('seasonal_context'),
                            'priority': theme_dict.get('priority'),
                            'tags': theme_dict.get('tags'),
                            'content_type': None,
                            'is_recurring': True,
                            'created_at': None,
                            'updated_at': None
                        }
                
                # Fallback to calendar_ideas (legacy)
                cur.execute(
                    """
                    SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                           ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                           ci.is_recurring, ci.created_at, ci.updated_at
                    FROM calendar_ideas ci
                    WHERE ci.id = %s
                    """,
                    (theme_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception:
        return None

