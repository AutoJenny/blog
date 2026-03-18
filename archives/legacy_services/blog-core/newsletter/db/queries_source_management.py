"""Database queries for managing newsletter sources (CRUD operations)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from config.database import db_manager


def list_all_sources() -> List[Dict[str, Any]]:
    """List all sources (enabled and disabled), including region for local sources."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, base_url, type, enabled, api_key_ref, region, 
                       preferred_sections, excluded_sections, access_mode, created_at, updated_at
                FROM newsletter_snapshot_source
                ORDER BY enabled DESC, name ASC
                """
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def get_source(source_id: int) -> Optional[Dict[str, Any]]:
    """Get a single source by ID."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, base_url, type, enabled, api_key_ref, created_at, updated_at
                FROM newsletter_snapshot_source
                WHERE id = %s
                """,
                (source_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def create_source(
    *,
    name: str,
    base_url: str,
    type: str,
    enabled: bool = True,
    api_key_ref: str | None = None,
    region: str | None = None,
    preferred_sections: List[str] | None = None,
    excluded_sections: List[str] | None = None,
    access_mode: str | None = None,
    discovery_notes: str | None = None,
) -> int:
    """Create a new source. Returns the new source ID."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_snapshot_source 
                (name, base_url, type, enabled, api_key_ref, region, preferred_sections, excluded_sections, access_mode, discovery_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, base_url, type, enabled, api_key_ref, region, preferred_sections, excluded_sections, access_mode, discovery_notes),
            )
            row = cur.fetchone()
            conn.commit()
            return row['id']


def update_source(
    source_id: int,
    *,
    name: str | None = None,
    base_url: str | None = None,
    type: str | None = None,
    enabled: bool | None = None,
    api_key_ref: str | None = None,
) -> None:
    """Update a source. Only provided fields are updated."""
    updates = []
    params: List[Any] = []
    
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if base_url is not None:
        updates.append("base_url = %s")
        params.append(base_url)
    if type is not None:
        updates.append("type = %s")
        params.append(type)
    if enabled is not None:
        updates.append("enabled = %s")
        params.append(enabled)
    if api_key_ref is not None:
        updates.append("api_key_ref = %s")
        params.append(api_key_ref)
    
    if not updates:
        return
    
    updates.append("updated_at = NOW()")
    params.append(source_id)
    
    sql = f"""
        UPDATE newsletter_snapshot_source
        SET {', '.join(updates)}
        WHERE id = %s
    """
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            conn.commit()


def delete_source(source_id: int) -> None:
    """Delete a source."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM newsletter_snapshot_source WHERE id = %s",
                (source_id,),
            )
            conn.commit()


def get_cache_status() -> List[Dict[str, Any]]:
    """Get cache status for all sources (from newsletter_source_cache)."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source_name, last_fetched_at, last_status, notes, updated_at
                FROM newsletter_source_cache
                ORDER BY last_fetched_at DESC NULLS LAST
                """
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def get_item_stats() -> Dict[str, Any]:
    """Get statistics about cached items."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Total items
            cur.execute("SELECT COUNT(*) AS total FROM newsletter_source_item")
            total_row = cur.fetchone()
            total = total_row['total'] if total_row else 0
            
            # By category
            cur.execute(
                """
                SELECT category, COUNT(*) AS count
                FROM newsletter_source_item
                GROUP BY category
                ORDER BY count DESC
                """
            )
            by_category = {row['category']: row['count'] for row in cur.fetchall()}
            
            # By source
            cur.execute(
                """
                SELECT source_name, COUNT(*) AS count
                FROM newsletter_source_item
                GROUP BY source_name
                ORDER BY count DESC
                LIMIT 10
                """
            )
            by_source = {row['source_name']: row['count'] for row in cur.fetchall()}
            
            return {
                'total_items': total,
                'by_category': by_category,
                'by_source': by_source,
            }

