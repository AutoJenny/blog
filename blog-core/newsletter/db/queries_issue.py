"""Queries for newsletter issues and blocks.

Use the existing project DB connection utilities; this module only defines
functions and must remain small. Split further if it approaches 400–500 LOC.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from psycopg.types.json import Json
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
                (issue_id, block_type, position, enabled, Json(payload)),
            )
            conn.commit()
            return None


def list_issues(*, limit: int = 12, offset: int = 0, status: str | None = None, q: str | None = None) -> List[Dict[str, Any]]:
    """List issues with optional status filter, search, and pagination."""
    where = []
    params: List[Any] = []
    if status:
        where.append("status = %s")
        params.append(status)
    if q:
        where.append("(subject ILIKE %s OR preheader ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT id, target_week, status, subject, preheader, last_sent_at, created_at, updated_at
        FROM newsletter_issue
        {where_sql}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def count_issues(*, status: str | None = None, q: str | None = None) -> int:
    """Total issues count for pagination with same filters as list_issues."""
    where = []
    params: List[Any] = []
    if status:
        where.append("status = %s")
        params.append(status)
    if q:
        where.append("(subject ILIKE %s OR preheader ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = f"SELECT COUNT(*) AS n FROM newsletter_issue {where_sql}"
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            return int(row['n']) if row else 0


def get_block_type_description(*, block_type: str) -> str:
    """Get default description for a block type from newsletter_block_type table."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT description FROM newsletter_block_type WHERE type = %s",
                (block_type,),
            )
            row = cur.fetchone()
            return row['description'] if row else ''


def list_blocks_by_issue(*, issue_id: int) -> List[Dict[str, Any]]:
    """List blocks for an issue, including description from block or default from type."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, issue_id, type, enabled, position, payload_json, pinned_ids, 
                       COALESCE(description, '') AS description, created_at, updated_at
                FROM newsletter_block
                WHERE issue_id = %s
                ORDER BY position ASC, id ASC
                """,
                (issue_id,),
            )
            rows = cur.fetchall() or []
            blocks = [dict(r) for r in rows]
            # Fill in descriptions from default if block description is empty
            for block in blocks:
                if not block.get('description'):
                    block['description'] = get_block_type_description(block_type=block['type'])
            return blocks


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
                (Json(payload), block_id),
            )
            conn.commit()


def delete_block(*, block_id: int) -> None:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM newsletter_block WHERE id = %s", (block_id,))
            conn.commit()


def shift_positions(*, issue_id: int, from_position: int) -> None:
    """Shift positions down starting at from_position (inclusive)."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE newsletter_block
                SET position = position + 1, updated_at = NOW()
                WHERE issue_id = %s AND position >= %s
                """,
                (issue_id, from_position),
            )
            conn.commit()


def insert_block(*, issue_id: int, block_type: str, position: int, enabled: bool, payload: Dict[str, Any], description: str | None = None) -> int:
    """Insert a new block, getting default description if not provided."""
    if description is None:
        description = get_block_type_description(block_type=block_type)
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_block (issue_id, type, position, enabled, payload_json, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (issue_id, block_type, position, enabled, Json(payload), description),
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


