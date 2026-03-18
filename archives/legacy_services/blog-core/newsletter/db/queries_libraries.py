"""Queries for evergreen, category features, and snapshot sources."""

from __future__ import annotations

from typing import Any, Dict, List
from config.database import db_manager


def list_evergreen(*, limit: int = 100) -> List[Dict[str, Any]]:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, topic, text, length, season, region_tags, last_used_at, created_at, updated_at
                FROM newsletter_evergreen
                ORDER BY COALESCE(last_used_at, to_timestamp(0)) ASC, id ASC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def list_category_features(*, limit: int = 50) -> List[Dict[str, Any]]:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, body_html, topic, approved, last_used_at, created_at, updated_at
                FROM newsletter_category_feature
                WHERE approved = TRUE
                ORDER BY COALESCE(last_used_at, to_timestamp(0)) ASC, id ASC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def list_snapshot_sources(*, enabled_only: bool = True) -> List[Dict[str, Any]]:
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            if enabled_only:
                cur.execute(
                    """
                    SELECT id, name, base_url, type, enabled, api_key_ref, created_at, updated_at
                    FROM newsletter_snapshot_source
                    WHERE enabled = TRUE
                    ORDER BY id ASC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, base_url, type, enabled, api_key_ref, created_at, updated_at
                    FROM newsletter_snapshot_source
                    ORDER BY id ASC
                    """
                )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


