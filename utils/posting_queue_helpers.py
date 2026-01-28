"""
Posting Queue Helpers
--------------------

Utility functions for creating posting_queue rows with proper Content Item linkage.
Ensures ID-only linkage (no text matching) for weekly word/phrase/insult Content Items.
"""

from __future__ import annotations

from typing import Optional
import logging

from config.database import db_manager

logger = logging.getLogger(__name__)


def create_weekly_social_post(
    idea_id: int,
    content_type: str,  # "weekly_word", "weekly_phrase", or "weekly_insult"
    platform: str,
    generated_content: str,
    *,
    status: str = "draft",
    scheduled_date: Optional[str] = None,
    scheduled_time: Optional[str] = None,
    cursor=None,
) -> int:
    """
    Create a posting_queue row for a weekly Content Item (word/phrase/insult).

    Parameters
    ----------
    idea_id:
        calendar_ideas.id for the weekly Content Item.
    content_type:
        Must be "weekly_word", "weekly_phrase", or "weekly_insult".
    platform:
        Social platform ("facebook", "instagram", "twitter", etc.).
    generated_content:
        The post content text.
    status:
        Initial status (default: "draft").
    scheduled_date:
        Optional scheduled date (ISO format string or date object).
    scheduled_time:
        Optional scheduled time (HH:MM format string or time object).
    cursor:
        Optional DB cursor (for transaction sharing).

    Returns
    -------
    posting_queue.id of the created row.

    Raises
    ------
    ValueError:
        If content_type is not a valid weekly type.
    """
    if content_type not in ("weekly_word", "weekly_phrase", "weekly_insult"):
        raise ValueError(
            f"content_type must be 'weekly_word', 'weekly_phrase', or 'weekly_insult', got: {content_type}"
        )

    close_cursor = False
    if cursor is None:
        cursor = db_manager.get_cursor()
        close_cursor = True

    try:
        # Build INSERT with idea_id explicitly set. Matrix v1: weekly_word/phrase/insult → role = 'CULTURE'.
        insert_fields = [
            "idea_id",
            "content_type",
            "platform",
            "role",
            "generated_content",
            "status",
            "created_at",
            "updated_at",
        ]
        insert_values = [
            idea_id,
            content_type,
            platform,
            "CULTURE",
            generated_content,
            status,
            "NOW()",
            "NOW()",
        ]
        placeholders = ["%s"] * (len(insert_values) - 2) + ["NOW()", "NOW()"]

        if scheduled_date:
            insert_fields.append("scheduled_date")
            insert_values.append(scheduled_date)
            placeholders.insert(-2, "%s")

        if scheduled_time:
            insert_fields.append("scheduled_time")
            insert_values.append(scheduled_time)
            placeholders.insert(-2, "%s")

        query = f"""
            INSERT INTO posting_queue ({', '.join(insert_fields)})
            VALUES ({', '.join(placeholders)})
            RETURNING id
        """

        # Filter out NOW() from params
        params = [v for v, p in zip(insert_values, placeholders) if p == "%s"]

        cursor.execute(query, tuple(params))
        result = cursor.fetchone()

        if result:
            queue_id = result["id"] if isinstance(result, dict) else result[0]
            logger.info(
                f"Created weekly social post: queue_id={queue_id}, idea_id={idea_id}, content_type={content_type}, platform={platform}"
            )
            return queue_id
        else:
            raise RuntimeError("INSERT did not return an id")

    finally:
        if close_cursor:
            cursor.close()


def update_weekly_social_post_idea_id(
    queue_id: int,
    idea_id: int,
    *,
    cursor=None,
) -> bool:
    """
    Update an existing posting_queue row to set idea_id (for backfilling).

    Parameters
    ----------
    queue_id:
        posting_queue.id to update.
    idea_id:
        calendar_ideas.id to link.
    cursor:
        Optional DB cursor.

    Returns
    -------
    True if update succeeded, False if row not found.
    """
    close_cursor = False
    if cursor is None:
        cursor = db_manager.get_cursor()
        close_cursor = True

    try:
        cursor.execute(
            """
            UPDATE posting_queue
            SET idea_id = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """,
            (idea_id, queue_id),
        )
        result = cursor.fetchone()

        if result:
            logger.info(f"Updated posting_queue.id={queue_id} with idea_id={idea_id}")
            return True
        else:
            logger.warning(f"posting_queue.id={queue_id} not found for idea_id update")
            return False

    finally:
        if close_cursor:
            cursor.close()


def get_posting_queue_row(queue_id: int, cursor=None) -> Optional[dict]:
    """
    Get a posting_queue row by ID.
    
    Parameters
    ----------
    queue_id:
        posting_queue.id to fetch.
    cursor:
        Optional DB cursor (for transaction sharing).
    
    Returns
    -------
    Dict with posting_queue row data, or None if not found.
    """
    close_cursor = False
    if cursor is None:
        cursor = db_manager.get_cursor()
        close_cursor = True
    
    try:
        cursor.execute("""
            SELECT *
            FROM posting_queue
            WHERE id = %s
        """, (queue_id,))
        
        row = cursor.fetchone()
        return row
        
    finally:
        if close_cursor:
            cursor.close()

