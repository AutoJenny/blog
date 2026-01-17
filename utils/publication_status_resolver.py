"""
Publication Status Resolver
---------------------------

Single-purpose module that resolves creation / publication status for
calendar-driven content and posting-queue items.

Rules:
- For categories with a **direct foreign key** into `post` (e.g. recipes,
  profile posts), matching uses that ID only.
- For week-driven items like **themes**, matching uses the canonical
  week→post mapping view (`calendar_week_posts_v2`) keyed by `(year, week)`,
  never by titles or fuzzy heuristics.
- No title- or text-based fallbacks are allowed.
- If relationships are missing or inconsistent, the resolver reports
  `exists = False` so that data issues can be fixed at source.
"""

from __future__ import annotations

from typing import TypedDict, Optional, Tuple
import logging

from config.database import db_manager

logger = logging.getLogger(__name__)


class PostStatusInfo(TypedDict):
    """Normalized status information for a blog-style post."""

    exists: bool
    status: Optional[str]
    post_id: Optional[int]
    raw_status: Optional[str]


class QueueStatusInfo(TypedDict):
    """Normalized status information for a posting_queue item."""

    exists: bool
    status: Optional[str]
    queue_id: Optional[int]
    raw_status: Optional[str]


def normalize_post_status(status: Optional[str]) -> Optional[str]:
    """
    Normalize raw post.status into a small display enum.

    This mirrors the behaviour of blueprints.posts.get_display_status
    so that posts list, dashboards and calendar views stay consistent.
    """
    status_lower = (status or "").lower()

    if status_lower in ("published", "live"):
        return "published"
    if status_lower == "error":
        return "error"
    if status_lower == "publishing":
        return "publishing"
    if status_lower == "deleted":
        return "deleted"

    # For anything else (including empty / None), treat as draft-like.
    return status_lower or "draft"


def normalize_queue_status(status: Optional[str]) -> Optional[str]:
    """
    Normalize posting_queue.status into the same display enum space.

    Expected raw values (see posting_queue_schema.md):
      - pending, ready, published, failed, cancelled
    """
    s = (status or "").lower()

    if s in ("pending", "ready"):
        return "scheduled"
    if s == "published":
        return "published"
    if s in ("failed", "error"):
        return "error"
    if s == "cancelled":
        return "deleted"

    # Unknown values: surface as-is for diagnostics
    return s or None


def _extract_id_and_status(row) -> Tuple[Optional[int], Optional[str]]:
    """Helper to read id/status from either dict_row or tuple."""
    if not row:
        return None, None
    if isinstance(row, dict):
        return row.get("id"), row.get("status")
    if isinstance(row, (tuple, list)) and row:
        # Expect (id, status) ordering in all resolver queries.
        post_id = row[0]
        raw_status = row[1] if len(row) > 1 else None
        return post_id, raw_status
    return None, None


def resolve_post_for_calendar_item(
    category: str,
    item_id: Optional[int],
    *,
    year: Optional[int] = None,
    week: Optional[int] = None,
) -> PostStatusInfo:
    """
    Resolve post existence/status for a calendar item.

    Parameters
    ----------
    category:
        Logical category: 'theme', 'recipe', 'profile_product',
        'profile_surname', 'weekly_word', 'weekly_phrase',
        'weekly_insult'.

    item_id:
        Identifier from the calendar / cyclic tables. Matching is
        strictly by ID; if there is no appropriate ID column on post
        for a category, this resolver will not attempt to guess.

    year, week:
        Optional context. Currently unused for matching (to preserve
        the ID-only rule) but accepted for future diagnostics or
        disambiguation strategies that still respect IDs.
    """
    info: PostStatusInfo = {
        "exists": False,
        "status": None,
        "post_id": None,
        "raw_status": None,
    }

    category_norm = (category or "").strip().lower()
    try:
        with db_manager.get_cursor() as cursor:
            # Themes are resolved via the canonical week→post mapping, not theme_id.
            if category_norm == "theme":
                post_id, raw_status = _resolve_theme_post_by_week(cursor, year, week)
            # Recipes have a direct recipe_id → post.recipe_id relationship.
            elif category_norm == "recipe" and item_id:
                cursor.execute(
                    """
                    SELECT id, status
                    FROM post
                    WHERE recipe_id = %s
                      AND status != 'deleted'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (item_id,),
                )
                row = cursor.fetchone()
                post_id, raw_status = _extract_id_and_status(row)
            # Profiles use post.id directly as their schedule ID.
            elif category_norm in ("profile_product", "profile_surname") and item_id:
                cursor.execute(
                    """
                    SELECT id, status
                    FROM post
                    WHERE id = %s
                      AND status != 'deleted'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (item_id,),
                )
                row = cursor.fetchone()
                post_id, raw_status = _extract_id_and_status(row)
            else:
                # Weekly content and unsupported categories currently have no
                # dedicated ID link into post or week→post mapping.
                logger.debug(
                    "resolve_post_for_calendar_item: no mapping for category %s "
                    "(item_id=%s, year=%s, week=%s)",
                    category_norm,
                    item_id,
                    year,
                    week,
                )
                return info
    except Exception as exc:
        logger.warning(
            "Error resolving post for category %s, item_id=%s, year=%s, week=%s: %s",
            category_norm,
            item_id,
            year,
            week,
            exc,
        )
        return info

    # post_id/raw_status populated by the category-specific branches above.
    if not post_id:
        return info

    info["exists"] = True
    info["post_id"] = post_id
    info["raw_status"] = raw_status
    info["status"] = normalize_post_status(raw_status)
    return info


def _resolve_theme_post_by_week(cursor, year: Optional[int], week: Optional[int]) -> Tuple[Optional[int], Optional[str]]:
    """
    Resolve the primary themed blog post for a given ISO (year, week).

    Uses the canonical week→post mapping view `calendar_week_posts_v2`,
    filtered to exclude recipe posts and product/surname profiles so that
    only the main weekly article is considered.
    """
    if not (year and week):
        return None, None

    cursor.execute(
        """
        SELECT p.id, p.status
        FROM calendar_week_posts_v2 cwp
        JOIN post p ON cwp.post_id = p.id
        WHERE cwp.year = %s
          AND cwp.week_number = %s
          AND p.status != 'deleted'
          AND p.recipe_id IS NULL
          AND p.profile_category_id IS NULL
          AND (p.generated_source_type IS NULL OR p.generated_source_type = '')
        ORDER BY cwp.created_at DESC
        LIMIT 1
        """,
        (year, week),
    )
    row = cursor.fetchone()
    return _extract_id_and_status(row)


def resolve_product_output(queue_id: Optional[int]) -> QueueStatusInfo:
    """
    Resolve status for a product/syndication item in posting_queue.

    Parameters
    ----------
    queue_id:
        Primary key of posting_queue row.
    """
    info: QueueStatusInfo = {
        "exists": False,
        "status": None,
        "queue_id": None,
        "raw_status": None,
    }

    if not queue_id:
        return info

    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, status
                FROM posting_queue
                WHERE id = %s
                """,
                (queue_id,),
            )
            row = cursor.fetchone()
    except Exception as exc:
        logger.warning(
            "Error resolving posting_queue status for id=%s: %s",
            queue_id,
            exc,
        )
        return info

    q_id, raw_status = _extract_id_and_status(row)
    if not q_id:
        return info

    info["exists"] = True
    info["queue_id"] = q_id
    info["raw_status"] = raw_status
    info["status"] = normalize_queue_status(raw_status)
    return info



