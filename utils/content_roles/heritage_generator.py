"""
Phase H1: HERITAGE (Thursday) generator.

Library-driven selection from heritage_library. No LLM.
- 90-day repeat avoidance: exclude items in posting_queue with scheduled_date >= (target_date - 90 days).
- Deterministic pick: seed = f"{year}-W{week}-THU-HERITAGE".
- Thursday only; scheduled_time 15:00.
"""

import hashlib
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Any

from config.database import db_manager

logger = logging.getLogger(__name__)

REPEAT_DAYS = 90
HERITAGE_SCHEDULED_TIME = "15:00"


def get_eligible_heritage_ids(target_date: date) -> List[int]:
    """
    Return heritage_library.id values that are active and NOT in posting_queue
    with scheduled_date >= (target_date - 90 days). Planned schedule only.
    """
    cutoff = target_date - timedelta(days=REPEAT_DAYS)
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM heritage_library
                WHERE active = TRUE
                AND id NOT IN (
                    SELECT heritage_library_id FROM posting_queue
                    WHERE heritage_library_id IS NOT NULL
                    AND scheduled_date >= %s
                )
                ORDER BY id
            """, (cutoff,))
            rows = cursor.fetchall()
            return [r["id"] for r in rows if r.get("id")]
    except Exception as e:
        logger.error("Error fetching eligible heritage IDs: %s", e)
        return []


def get_heritage_library_row(library_id: int) -> Optional[Dict[str, Any]]:
    """Fetch one heritage_library row by id."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, category, title, body_text, source_note FROM heritage_library WHERE id = %s",
                (library_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Error fetching heritage_library row %s: %s", library_id, e)
        return None


def pick_heritage_for_thursday(
    target_date: date,
    year: int,
    week: int,
) -> Optional[Dict[str, Any]]:
    """
    Deterministic pick for Thursday. Seed = f"{year}-W{week}-THU-HERITAGE".
    Returns dict with heritage_library_id, title, body_text, category, source_note, generated_content.
    """
    eligible_ids = get_eligible_heritage_ids(target_date)
    if not eligible_ids:
        logger.warning("No eligible heritage items for %s (Thursday)", target_date)
        return None
    seed_str = f"{year}-W{week}-THU-HERITAGE"
    seed_hash = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    chosen_id = eligible_ids[seed_hash % len(eligible_ids)]
    row = get_heritage_library_row(chosen_id)
    if not row:
        return None
    body = (row.get("body_text") or "").strip()
    title = (row.get("title") or "").strip()
    generated_content = f"{title}\n\n{body}".strip() if title else body
    return {
        "heritage_library_id": chosen_id,
        "title": title,
        "body_text": body,
        "category": row.get("category"),
        "source_note": row.get("source_note"),
        "generated_content": generated_content,
    }
