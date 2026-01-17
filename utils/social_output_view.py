"""
Social Output View Helper
-------------------------

Provides a unified view over posting_queue that exposes social Outputs
in the same conceptual framework as blog Outputs.

All social posts (products, weekly word/phrase/insult) are treated as Outputs
with channel, content_format, status, and explicit Content Item linkage.
"""

from __future__ import annotations

from typing import TypedDict, Optional, List
from datetime import datetime, date
import logging

from config.database import db_manager
from utils.publication_status_resolver import normalize_queue_status

logger = logging.getLogger(__name__)


class SocialOutput(TypedDict):
    """Normalized social Output structure."""

    output_kind: str  # Always "social_queue"
    output_id: int  # posting_queue.id
    channel: str  # "facebook", "instagram", "twitter", etc.
    content_format: str  # "product_post", "word_of_day", "phrase_of_day", "insult_of_day"
    status: str  # Normalized: "scheduled", "published", "error", "cancelled"
    raw_status: Optional[str]  # Original posting_queue.status

    # Slot context (derived from scheduled_date)
    year: Optional[int]
    week: Optional[int]
    day: Optional[int]  # 1-7 (Monday=1, Sunday=7)
    scheduled_date: Optional[date]
    scheduled_time: Optional[str]  # HH:MM format

    # Content Item linkage
    content_type: Optional[str]  # "product", "weekly_word", "weekly_phrase", "weekly_insult"
    content_item_id: Optional[int]  # product_id or idea_id


def _compute_week_slot(scheduled_date: Optional[date]) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Compute (year, week, day) from scheduled_date."""
    if not scheduled_date:
        return None, None, None

    iso = scheduled_date.isocalendar()
    year = iso[0]
    week = iso[1]
    day = iso[2]  # 1=Monday, 7=Sunday

    return year, week, day


def _map_content_type_and_item_id(
    product_id: Optional[int],
    idea_id: Optional[int],
    content_type: Optional[str],
) -> tuple[Optional[str], Optional[int]]:
    """
    Map posting_queue fields to unified (content_type, content_item_id).

    Rules:
    - If product_id is set: content_type="product", content_item_id=product_id
    - Else if idea_id is set: content_type from posting_queue.content_type (weekly_word/phrase/insult), content_item_id=idea_id
    - Else: content_type/content_item_id are None (unmapped)
    """
    if product_id:
        return "product", product_id

    if idea_id:
        # Use the posting_queue.content_type to distinguish weekly subtypes
        # Expected values: "weekly_word", "weekly_phrase", "weekly_insult"
        mapped_type = content_type if content_type in ("weekly_word", "weekly_phrase", "weekly_insult") else None
        return mapped_type, idea_id

    return None, None


def _normalize_channel(platform: Optional[str]) -> str:
    """Normalize posting_queue.platform to channel name."""
    if not platform:
        return "unknown"

    platform_lower = platform.lower()
    if platform_lower in ("facebook", "fb"):
        return "facebook"
    if platform_lower in ("instagram", "ig"):
        return "instagram"
    if platform_lower in ("twitter", "x"):
        return "twitter"

    return platform_lower


def _derive_content_format(content_type: Optional[str], channel: str) -> str:
    """
    Derive content_format from content_type and channel.

    Rules:
    - product → "product_post"
    - weekly_word → "word_of_day"
    - weekly_phrase → "phrase_of_day"
    - weekly_insult → "insult_of_day"
    """
    if content_type == "product":
        return "product_post"

    if content_type == "weekly_word":
        return "word_of_day"
    if content_type == "weekly_phrase":
        return "phrase_of_day"
    if content_type == "weekly_insult":
        return "insult_of_day"

    # Fallback: use content_type as-is if unrecognized
    return content_type or "unknown"


def get_social_outputs_for_week(
    year: int,
    week: int,
    *,
    channel: Optional[str] = None,
    content_type: Optional[str] = None,
    cursor=None,
) -> List[SocialOutput]:
    """
    Get all social Outputs for a given (year, week) slot.

    Parameters
    ----------
    year, week:
        ISO year and week number.
    channel:
        Optional filter by channel ("facebook", "instagram", etc.).
    content_type:
        Optional filter by content_type ("product", "weekly_word", etc.).
    cursor:
        Optional DB cursor (for transaction sharing).

    Returns
    -------
    List of SocialOutput dicts, sorted by scheduled_date, scheduled_time.
    """
    # Compute week start/end dates
    jan4 = datetime(year, 1, 4)
    from datetime import timedelta
    week_start = (jan4 + timedelta(weeks=week - 1, days=-jan4.weekday())).date()
    week_end = week_start + timedelta(days=6)

    close_cursor = False
    if cursor is None:
        cursor = db_manager.get_cursor()
        close_cursor = True

    try:
        # Build query
        where_clauses = [
            "pq.scheduled_date BETWEEN %s AND %s",
        ]
        params = [week_start, week_end]

        if channel:
            where_clauses.append("LOWER(pq.platform) = LOWER(%s)")
            params.append(channel)

        if content_type:
            if content_type == "product":
                where_clauses.append("pq.product_id IS NOT NULL")
            elif content_type in ("weekly_word", "weekly_phrase", "weekly_insult"):
                where_clauses.append("pq.idea_id IS NOT NULL AND pq.content_type = %s")
                params.append(content_type)

        query = f"""
            SELECT
                pq.id,
                pq.platform,
                pq.content_type,
                pq.scheduled_date,
                pq.scheduled_time,
                pq.status,
                pq.product_id,
                pq.idea_id
            FROM posting_queue pq
            WHERE {' AND '.join(where_clauses)}
            ORDER BY pq.scheduled_date, pq.scheduled_time
        """

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        outputs = []
        for row in rows:
            year_slot, week_slot, day_slot = _compute_week_slot(row.get("scheduled_date"))

            channel_norm = _normalize_channel(row.get("platform"))
            content_type_mapped, content_item_id = _map_content_type_and_item_id(
                row.get("product_id"),
                row.get("idea_id"),
                row.get("content_type"),
            )
            content_format = _derive_content_format(content_type_mapped, channel_norm)

            scheduled_time_str = None
            if row.get("scheduled_time"):
                if isinstance(row["scheduled_time"], str):
                    scheduled_time_str = row["scheduled_time"]
                else:
                    # Time object
                    scheduled_time_str = row["scheduled_time"].strftime("%H:%M")

            output: SocialOutput = {
                "output_kind": "social_queue",
                "output_id": row["id"],
                "channel": channel_norm,
                "content_format": content_format,
                "status": normalize_queue_status(row.get("status")),
                "raw_status": row.get("status"),
                "year": year_slot,
                "week": week_slot,
                "day": day_slot,
                "scheduled_date": row.get("scheduled_date"),
                "scheduled_time": scheduled_time_str,
                "content_type": content_type_mapped,
                "content_item_id": content_item_id,
            }

            outputs.append(output)

        return outputs

    finally:
        if close_cursor:
            cursor.close()


def get_social_outputs_for_content_item(
    content_type: str,
    content_item_id: int,
    *,
    year: Optional[int] = None,
    week: Optional[int] = None,
    cursor=None,
) -> List[SocialOutput]:
    """
    Get social Outputs for a specific Content Item.

    Parameters
    ----------
    content_type:
        "product" or "weekly_word" / "weekly_phrase" / "weekly_insult"
    content_item_id:
        product_id or idea_id
    year, week:
        Optional filters to narrow results to a specific slot.
    cursor:
        Optional DB cursor.

    Returns
    -------
    List of SocialOutput dicts.
    """
    close_cursor = False
    if cursor is None:
        cursor = db_manager.get_cursor()
        close_cursor = True

    try:
        where_clauses = []
        params = []

        if content_type == "product":
            where_clauses.append("pq.product_id = %s")
            params.append(content_item_id)
        elif content_type in ("weekly_word", "weekly_phrase", "weekly_insult"):
            where_clauses.append("pq.idea_id = %s AND pq.content_type = %s")
            params.extend([content_item_id, content_type])
        else:
            logger.warning(f"Unknown content_type for social output lookup: {content_type}")
            return []

        if year and week:
            jan4 = datetime(year, 1, 4)
            from datetime import timedelta
            week_start = (jan4 + timedelta(weeks=week - 1, days=-jan4.weekday())).date()
            week_end = week_start + timedelta(days=6)
            where_clauses.append("pq.scheduled_date BETWEEN %s AND %s")
            params.extend([week_start, week_end])

        query = f"""
            SELECT
                pq.id,
                pq.platform,
                pq.content_type,
                pq.scheduled_date,
                pq.scheduled_time,
                pq.status,
                pq.product_id,
                pq.idea_id
            FROM posting_queue pq
            WHERE {' AND '.join(where_clauses)}
            ORDER BY pq.scheduled_date DESC, pq.scheduled_time
        """

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        outputs = []
        for row in rows:
            year_slot, week_slot, day_slot = _compute_week_slot(row.get("scheduled_date"))

            channel_norm = _normalize_channel(row.get("platform"))
            content_type_mapped, content_item_id_mapped = _map_content_type_and_item_id(
                row.get("product_id"),
                row.get("idea_id"),
                row.get("content_type"),
            )
            content_format = _derive_content_format(content_type_mapped, channel_norm)

            scheduled_time_str = None
            if row.get("scheduled_time"):
                if isinstance(row["scheduled_time"], str):
                    scheduled_time_str = row["scheduled_time"]
                else:
                    scheduled_time_str = row["scheduled_time"].strftime("%H:%M")

            output: SocialOutput = {
                "output_kind": "social_queue",
                "output_id": row["id"],
                "channel": channel_norm,
                "content_format": content_format,
                "status": normalize_queue_status(row.get("status")),
                "raw_status": row.get("status"),
                "year": year_slot,
                "week": week_slot,
                "day": day_slot,
                "scheduled_date": row.get("scheduled_date"),
                "scheduled_time": scheduled_time_str,
                "content_type": content_type_mapped,
                "content_item_id": content_item_id_mapped,
            }

            outputs.append(output)

        return outputs

    finally:
        if close_cursor:
            cursor.close()

