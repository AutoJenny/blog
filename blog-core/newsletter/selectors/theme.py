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
    """Get all calendar ideas (themes) for a specific week number, ordered by priority."""
    if week_number < 1 or week_number > 53:
        return []
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
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
    """Select the default theme for a target week (first theme by priority)."""
    week_number = parse_target_week(target_week)
    themes = get_themes_for_week(week_number)
    return themes[0] if themes else None


def get_theme_by_id(theme_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific theme by ID."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
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

