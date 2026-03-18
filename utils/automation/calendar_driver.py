"""
Calendar-Driven Automation Work Selection — W2-FIX-9.2

Returns posts to process for a given (year, week), ordered by workflow stage.
W2 Phase 2: Uses utils.posts.stage_order (single source) for ordering.
Sources: calendar_week_items (item_type recipe/profile) and post.extra_settings.calendar_seed.
"""

from typing import List, Dict, Any
from datetime import date
import logging
from config.database import db_manager
from utils.posts.stage_order import STAGE_ORDER, stage_index

logger = logging.getLogger(__name__)


def get_posts_for_week(
    year: int,
    week_number: int,
    only_automation_enabled: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get posts seeded to the given week, ordered by workflow stage (earliest first).
    
    Sources:
    1. calendar_week_items where item_type IN ('recipe','profile') — item_id = post_id
    2. post.extra_settings.calendar_seed where year/week_number match
    
    Filters:
    - status IN ('draft','in_process') — not deleted, not published
    - If only_automation_enabled: post.extra_settings.automation.enabled != false
    
    Returns:
        List of {"post_id": int, "workflow_stage": str, "stage_order": int, ...}
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Union: posts from calendar_week_items + posts from calendar_seed
            cursor.execute("""
                WITH week_posts AS (
                    SELECT cwi.item_id AS post_id
                    FROM calendar_week_items cwi
                    WHERE cwi.year = %s AND cwi.week_number = %s
                      AND cwi.item_type IN ('recipe', 'profile')
                      AND cwi.is_active = TRUE
                    UNION
                    SELECT p.id AS post_id
                    FROM post p
                    WHERE p.status IN ('draft', 'in_process')
                      AND p.extra_settings IS NOT NULL
                      AND p.extra_settings->'calendar_seed' IS NOT NULL
                      AND p.extra_settings->'calendar_seed'->>'year' IS NOT NULL
                      AND p.extra_settings->'calendar_seed'->>'week_number' IS NOT NULL
                      AND (p.extra_settings->'calendar_seed'->>'year')::int = %s
                      AND (p.extra_settings->'calendar_seed'->>'week_number')::int = %s
                )
                SELECT DISTINCT wp.post_id
                FROM week_posts wp
                JOIN post p ON p.id = wp.post_id
                WHERE p.status IN ('draft', 'in_process')
            """, (year, week_number, year, week_number))

            post_ids = [r["post_id"] for r in (cursor.fetchall() or [])]
            if not post_ids:
                return []

            # Filter by automation.enabled if requested
            if only_automation_enabled:
                allowed = set()
                for pid in post_ids:
                    cursor.execute("""
                        SELECT COALESCE(
                            (extra_settings->'automation'->>'enabled') IS DISTINCT FROM 'false',
                            TRUE
                        ) AS enabled
                        FROM post WHERE id = %s
                    """, (pid,))
                    row = cursor.fetchone()
                    if row and row.get("enabled", True):
                        allowed.add(pid)
                post_ids = [p for p in post_ids if p in allowed]

            if not post_ids:
                return []

            # Get workflow_stage for each (canonical column only). W2 Phase 1.
            placeholders = ",".join(["%s"] * len(post_ids))
            cursor.execute(f"""
                SELECT p.id AS post_id,
                       COALESCE(p.workflow_stage, 'metadata')::text AS workflow_stage
                FROM post p
                WHERE p.id IN ({placeholders})
            """, tuple(post_ids))

            rows = cursor.fetchall() or []
            result = []
            for r in rows:
                stage = (r.get("workflow_stage") or "metadata").strip()
                order = stage_index(stage)
                result.append({
                    "post_id": r["post_id"],
                    "workflow_stage": stage,
                    "stage_order": order,
                })
            result.sort(key=lambda x: (x["stage_order"], x["post_id"]))
            return result

    except Exception as e:
        logger.error(f"get_posts_for_week failed for {year}/W{week_number}: {e}")
        return []
