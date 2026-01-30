"""
CULTURE v1.1: Culture (Mon/Thu) generator.

Library-driven selection from culture_library. No LLM.
- 90-day repeat avoidance: exclude items in posting_queue with scheduled_date >= (target_date - 90 days).
- Deterministic pick: seed (rota_year, rota_week, weekday).
- scheduled_time 15:00 for all CULTURE rails.
"""

import logging
from datetime import date, timedelta, time
from typing import Dict, Optional, List, Any

from config.database import db_manager

logger = logging.getLogger(__name__)

REPEAT_DAYS = 90
CULTURE_SCHEDULED_TIME = "15:00"


def get_eligible_culture_ids(target_date: date) -> List[int]:
    """
    Return culture_library.id values that are active and NOT in posting_queue
    with scheduled_date >= (target_date - 90 days). Planned schedule only.
    """
    cutoff = target_date - timedelta(days=REPEAT_DAYS)
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM culture_library
                WHERE active = TRUE
                AND id NOT IN (
                    SELECT culture_library_id FROM posting_queue
                    WHERE culture_library_id IS NOT NULL
                    AND scheduled_date >= %s
                )
                ORDER BY id
            """, (cutoff,))
            rows = cursor.fetchall()
            return [r["id"] for r in rows if r.get("id")]
    except Exception as e:
        logger.error("Error fetching eligible culture IDs: %s", e)
        return []


def get_culture_library_row(library_id: int) -> Optional[Dict[str, Any]]:
    """Fetch one culture_library row by id."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, category, title, body_text, source_note FROM culture_library WHERE id = %s",
                (library_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Error fetching culture_library row %s: %s", library_id, e)
        return None


def pick_culture_for_slot(
    target_date: date,
    weekday: int,
    rota_year: int,
    rota_week: int,
) -> Optional[Dict[str, Any]]:
    """
    Deterministic pick for (target_date, weekday). Seed = (rota_year, rota_week, weekday).
    Returns dict with culture_library_id, title, body_text, generated_content, etc.
    """
    eligible_ids = get_eligible_culture_ids(target_date)
    if not eligible_ids:
        logger.warning("No eligible culture items for %s (weekday=%s)", target_date, weekday)
        return None
    seed = rota_year * 53 * 10 + rota_week * 10 + weekday
    chosen_id = eligible_ids[seed % len(eligible_ids)]
    row = get_culture_library_row(chosen_id)
    if not row:
        return None
    body = (row.get("body_text") or "").strip()
    title = (row.get("title") or "").strip()
    generated_content = f"{title}\n\n{body}".strip() if title else body
    return {
        "culture_library_id": chosen_id,
        "title": title,
        "body_text": body,
        "category": row.get("category"),
        "source_note": row.get("source_note"),
        "generated_content": generated_content,
    }
