"""
Calendar Seed Traceability — W2-FIX-9.1

Stores and verifies post.extra_settings.calendar_seed for calendar-driven traceability.
All posts created via calendar or automation should have a seed. Manual posts get type="manual".

Seed schema:
{
    "type": "theme" | "recipe" | "weekly_word" | "weekly_phrase" | "weekly_insult" | "profile" | "manual",
    "year": int (optional),
    "week_number": int (optional),
    "item_id": int (optional, theme_id/recipe_id/idea_id),
    "category": str (optional),
    "created_at": str (iso),
    "actor": str (optional)
}
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from config.database import db_manager

logger = logging.getLogger(__name__)


def set_calendar_seed(post_id: int, seed_data: Dict[str, Any], actor: str = "unknown", cursor=None) -> bool:
    """
    Set post.extra_settings.calendar_seed. Merges into existing extra_settings.

    Args:
        post_id: Post ID
        seed_data: Must include "type". For calendar types: year, week_number, item_id, category.
        actor: Who set it (e.g. "confirm_idea", "recipe_create", "create_post_from_item", "manual")
        cursor: Optional cursor to use (participates in caller's transaction). If None, gets own cursor and commits.

    Returns:
        True if successful
    """
    if not seed_data or "type" not in seed_data:
        logger.warning("set_calendar_seed: seed_data must include 'type'")
        return False

    seed = dict(seed_data)
    seed["created_at"] = datetime.utcnow().isoformat() + "Z"
    seed["actor"] = actor

    def _do_set(c):
        c.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
        row = c.fetchone()
        if not row:
            return False

        extra = row.get("extra_settings") or {}
        if isinstance(extra, str):
            import json
            try:
                extra = json.loads(extra) if extra else {}
            except (json.JSONDecodeError, TypeError):
                extra = {}

        extra["calendar_seed"] = seed
        c.execute(
            "UPDATE post SET extra_settings = %s::jsonb, updated_at = NOW() WHERE id = %s",
            (extra, post_id),
        )
        return c.rowcount > 0

    try:
        if cursor:
            return _do_set(cursor)
        with db_manager.get_cursor() as c:
            ok = _do_set(c)
            c.connection.commit()
            return ok
    except Exception as e:
        logger.error(f"set_calendar_seed failed for post {post_id}: {e}")
        return False


def get_calendar_seed(post_id: int) -> Optional[Dict[str, Any]]:
    """Get calendar_seed from post.extra_settings. Returns None if missing."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
            row = cursor.fetchone()
            if not row:
                return None

            extra = row.get("extra_settings") or {}
            if isinstance(extra, str):
                import json
                try:
                    extra = json.loads(extra) if extra else {}
                except (json.JSONDecodeError, TypeError):
                    return None

            return extra.get("calendar_seed")
    except Exception as e:
        logger.error(f"get_calendar_seed failed for post {post_id}: {e}")
        return None


def verify_calendar_seed_for_automation(
    post_id: int,
    target_year: Optional[int] = None,
    target_week: Optional[int] = None,
    backfill_missing: bool = True,
) -> Tuple[bool, Optional[Dict[str, Any]], int]:
    """
    Verify post has calendar_seed before automation advances.
    If target_year/target_week provided, verifies seed matches (for week-driven automation).

    Args:
        post_id: Post ID
        target_year: Optional target year for week-driven run
        target_week: Optional target week for week-driven run
        backfill_missing: If True, set type=manual when seed missing (backward compat for pre-W2-FIX-9.1 posts)

    Returns:
        (ok, error_dict, status_code)
        ok=True → proceed. ok=False → error_dict and status_code (409)
    """
    seed = get_calendar_seed(post_id)
    if not seed:
        if backfill_missing:
            ensure_manual_seed(post_id, actor="automation_verify_backfill")
            return True, None, 0
        return False, {
            "calendar_mismatch": True,
            "error": "Post has no calendar_seed. Ensure post was created from calendar or set calendar_seed.",
            "post_id": post_id,
        }, 409

    if target_year is not None and target_week is not None:
        seed_year = seed.get("year")
        seed_week = seed.get("week_number")
        # Only enforce match for calendar-driven types (not manual)
        if seed.get("type") != "manual" and (seed_year is None or seed_week is None):
            return False, {
                "calendar_mismatch": True,
                "error": "Post calendar_seed lacks year/week for week-driven automation.",
                "post_id": post_id,
                "seed": seed,
            }, 409
        if seed_year != target_year or seed_week != target_week:
            return False, {
                "calendar_mismatch": True,
                "error": f"Post calendar_seed ({seed_year}/W{seed_week}) does not match target week ({target_year}/W{target_week}).",
                "post_id": post_id,
                "seed_year": seed_year,
                "seed_week": seed_week,
                "target_year": target_year,
                "target_week": target_week,
            }, 409

    return True, None, 0


def ensure_manual_seed(post_id: int, actor: str = "migration") -> bool:
    """Set calendar_seed to manual for posts created without calendar context. Used by creation paths."""
    return set_calendar_seed(post_id, {"type": "manual"}, actor=actor)
