"""
Week-Level Automation Controls — W2-FIX-9.2

Persists automation_enabled and locked per (year, week).
Defaults: automation_enabled=True, locked=False when no row exists.
"""

from typing import Dict, Any, Optional
import logging
from config.database import db_manager

logger = logging.getLogger(__name__)


def get_week_controls(year: int, week_number: int) -> Dict[str, Any]:
    """
    Get automation controls for a week. Returns defaults when no row exists.
    
    Returns:
        {"automation_enabled": bool, "locked": bool}
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT automation_enabled, locked
                FROM calendar_week_controls
                WHERE year = %s AND week_number = %s
            """, (year, week_number))
            row = cursor.fetchone()
            if row:
                return {
                    "automation_enabled": bool(row.get("automation_enabled", True)),
                    "locked": bool(row.get("locked", False)),
                    "year": year,
                    "week_number": week_number,
                }
            return {
                "automation_enabled": True,
                "locked": False,
                "year": year,
                "week_number": week_number,
            }
    except Exception as e:
        logger.warning(f"get_week_controls failed for {year}/W{week_number}: {e}")
        return {"automation_enabled": True, "locked": False, "year": year, "week_number": week_number}


def set_week_controls(
    year: int,
    week_number: int,
    automation_enabled: Optional[bool] = None,
    locked: Optional[bool] = None,
) -> bool:
    """
    Set automation controls for a week. Upserts into calendar_week_controls.
    Pass None for a field to leave it unchanged; only provided fields are updated.
    
    Returns:
        True if successful
    """
    try:
        with db_manager.get_cursor() as cursor:
            if automation_enabled is not None and locked is not None:
                cursor.execute("""
                    INSERT INTO calendar_week_controls (year, week_number, automation_enabled, locked, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (year, week_number) DO UPDATE SET
                        automation_enabled = EXCLUDED.automation_enabled,
                        locked = EXCLUDED.locked,
                        updated_at = NOW()
                """, (year, week_number, automation_enabled, locked))
            elif automation_enabled is not None:
                cursor.execute("""
                    INSERT INTO calendar_week_controls (year, week_number, automation_enabled, locked, updated_at)
                    VALUES (%s, %s, %s, FALSE, NOW())
                    ON CONFLICT (year, week_number) DO UPDATE SET
                        automation_enabled = EXCLUDED.automation_enabled,
                        updated_at = NOW()
                """, (year, week_number, automation_enabled))
            elif locked is not None:
                cursor.execute("""
                    INSERT INTO calendar_week_controls (year, week_number, automation_enabled, locked, updated_at)
                    VALUES (%s, %s, TRUE, %s, NOW())
                    ON CONFLICT (year, week_number) DO UPDATE SET
                        locked = EXCLUDED.locked,
                        updated_at = NOW()
                """, (year, week_number, locked))
            else:
                return True
            cursor.connection.commit()
            return True
    except Exception as e:
        logger.error(f"set_week_controls failed for {year}/W{week_number}: {e}")
        return False


def is_week_locked(year: int, week_number: int) -> bool:
    """Convenience: True if week is locked."""
    return get_week_controls(year, week_number).get("locked", False)


def is_week_automation_enabled(year: int, week_number: int) -> bool:
    """Convenience: True if automation is enabled for the week."""
    return get_week_controls(year, week_number).get("automation_enabled", True)
