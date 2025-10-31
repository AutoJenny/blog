"""Queries for newsletter issues and blocks.

Use the existing project DB connection utilities; this module only defines
functions and must remain small. Split further if it approaches 400–500 LOC.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from config.database import db_manager


def get_latest_issue() -> Optional[Dict[str, Any]]:
    """Return the most recent newsletter issue as a dict, or None."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, target_week, status, subject, preheader, last_sent_at, created_at, updated_at
                FROM newsletter_issue
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            return dict(row) if row else None


def create_issue(*, target_week: str, subject: str, preheader: str) -> int:
    """Create a new issue and return its ID."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_issue (target_week, status, subject, preheader)
                VALUES (%s, 'draft', %s, %s)
                RETURNING id
                """,
                (target_week, subject, preheader),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Failed to create issue")
            new_id = row['id']
            conn.commit()
            return int(new_id)


def upsert_block(*, issue_id: int, block_type: str, position: int, enabled: bool, payload: Dict[str, Any]) -> None:
    """Create or update a block for an issue."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_block (issue_id, type, position, enabled, payload_json)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (issue_id, block_type, position, enabled, payload),
            )
            conn.commit()
            return None


def list_issues(*, limit: int = 50, status: str | None = None) -> List[Dict[str, Any]]:
    """List recent issues for dashboard."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """
                    SELECT id, target_week, status, subject, preheader, last_sent_at, created_at, updated_at
                    FROM newsletter_issue
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (status, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, target_week, status, subject, preheader, last_sent_at, created_at, updated_at
                    FROM newsletter_issue
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def list_blocks_by_issue(*, issue_id: int) -> List[Dict[str, Any]]:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, issue_id, type, enabled, position, payload_json, pinned_ids, created_at, updated_at
                FROM newsletter_block
                WHERE issue_id = %s
                ORDER BY position ASC, id ASC
                """,
                (issue_id,),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def set_block_enabled(*, block_id: int, enabled: bool) -> None:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE newsletter_block
                SET enabled = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (enabled, block_id),
            )
            conn.commit()


def update_block_payload(*, block_id: int, payload: Dict[str, Any]) -> None:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE newsletter_block
                SET payload_json = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (payload, block_id),
            )
            conn.commit()


def delete_block(*, block_id: int) -> None:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM newsletter_block WHERE id = %s", (block_id,))
            conn.commit()


def insert_block(*, issue_id: int, block_type: str, position: int, enabled: bool, payload: Dict[str, Any]) -> int:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_block (issue_id, type, position, enabled, payload_json)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (issue_id, block_type, position, enabled, payload),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Failed to create block")
            new_id = row['id']
            conn.commit()
            return int(new_id)


def move_block(*, block_id: int, direction: str) -> None:
    """Move block up or down by swapping positions with neighbor."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get current block
            cur.execute(
                "SELECT issue_id, position FROM newsletter_block WHERE id = %s",
                (block_id,),
            )
            row = cur.fetchone()
            if not row:
                return
            issue_id, pos = row['issue_id'], row['position']
            if direction == "up":
                neighbor_order_sql = "<"
                sort_sql = "DESC"
            else:
                neighbor_order_sql = ">"
                sort_sql = "ASC"
            # Find neighbor
            cur.execute(
                f"""
                SELECT id, position FROM newsletter_block
                WHERE issue_id = %s AND position {neighbor_order_sql} %s
                ORDER BY position {sort_sql}
                LIMIT 1
                """,
                (issue_id, pos),
            )
            n = cur.fetchone()
            if not n:
                return
            neighbor_id, neighbor_pos = n['id'], n['position']
            # Swap positions
            cur.execute(
                "UPDATE newsletter_block SET position = %s WHERE id = %s",
                (neighbor_pos, block_id),
            )
            cur.execute(
                "UPDATE newsletter_block SET position = %s WHERE id = %s",
                (pos, neighbor_id),
            )
            conn.commit()


