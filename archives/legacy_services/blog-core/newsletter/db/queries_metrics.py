"""Metrics and send-log queries for newsletter."""

from __future__ import annotations

from typing import Any, Dict, List
from config.database import db_manager


def insert_send_log(*, issue_id: int, provider: str, provider_id: str, checksum: str) -> None:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_send_log (issue_id, provider, provider_id, checksum)
                VALUES (%s, %s, %s, %s)
                """,
                (issue_id, provider, provider_id, checksum),
            )
            conn.commit()
    return None


def list_send_logs(*, issue_id: int) -> List[Dict[str, Any]]:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, issue_id, provider, provider_id, sent_at, checksum, created_at
                FROM newsletter_send_log
                WHERE issue_id = %s
                ORDER BY sent_at DESC
                """,
                (issue_id,),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


