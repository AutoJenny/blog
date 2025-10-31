"""Database queries for newsletter source items and cache management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from psycopg.types.json import Json
from config.database import db_manager


def store_source_items(items: List[Dict[str, Any]]) -> int:
    """Store normalized source items in newsletter_source_item table.
    
    Returns count of items stored.
    """
    if not items:
        return 0
    
    stored = 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                try:
                    cur.execute(
                        """
                        INSERT INTO newsletter_source_item 
                        (source_name, title, url, published_at, event_date, location, category, raw_data, signal_score, freshness_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            item.get('source_name'),
                            item.get('title'),
                            item.get('url'),
                            item.get('published_at'),
                            item.get('event_date'),
                            item.get('location'),
                            item.get('category', 'other'),
                            Json(item.get('raw_data', {})),
                            item.get('signal_score', 0.0),
                            item.get('freshness_score', 0.0),
                        ),
                    )
                    stored += 1
                except Exception:
                    continue
            conn.commit()
    return stored


def get_cached_items(*, category: str | None = None, days_back: int = 14, limit: int = 100) -> List[Dict[str, Any]]:
    """Get cached source items, optionally filtered by category.
    
    Returns items from last N days, sorted by combined_score descending.
    """
    where_clauses = []
    params: List[Any] = []
    
    if category:
        where_clauses.append("category = %s")
        params.append(category)
    
    if days_back > 0:
        cutoff = datetime.now() - timedelta(days=days_back)
        where_clauses.append("(published_at >= %s OR event_date >= %s OR cached_at >= %s)")
        params.extend([cutoff, cutoff, cutoff])
    
    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    
    sql = f"""
        SELECT id, source_name, title, url, published_at, event_date, location, category, 
               raw_data, signal_score, freshness_score, combined_score, cached_at
        FROM newsletter_source_item
        {where_sql}
        ORDER BY combined_score DESC, cached_at DESC
        LIMIT %s
    """
    params.append(limit)
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def mark_used(*, item_id: int, issue_id: int | None = None) -> None:
    """Mark a source item as used (for cooldown tracking)."""
    # For MVP: we can track in raw_data or a separate table later
    # For now, this is a placeholder for future cooldown logic
    pass


def check_repeat_cooldown(*, source_name: str, weeks: int = 2) -> bool:
    """Check if source was used recently (within N weeks).
    
    Returns True if source is available (not in cooldown).
    """
    # MVP: Simple check against recent items from same source
    cutoff = datetime.now() - timedelta(weeks=weeks)
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM newsletter_source_item
                WHERE source_name = %s AND cached_at >= %s
                """,
                (source_name, cutoff),
            )
            row = cur.fetchone()
            count = row['n'] if row else 0
            # If many recent items exist, source is active (no cooldown needed)
            # This is a simple heuristic; can be refined later
            return True  # Always allow for now


def update_source_cache(*, source_name: str, status: str = 'success', notes: str | None = None) -> None:
    """Update or create source cache entry."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newsletter_source_cache (source_name, last_fetched_at, last_status, notes, updated_at)
                VALUES (%s, NOW(), %s, %s, NOW())
                ON CONFLICT (source_name) DO UPDATE
                SET last_fetched_at = NOW(), last_status = EXCLUDED.last_status, 
                    notes = EXCLUDED.notes, updated_at = NOW()
                """,
                (source_name, status, notes),
            )
            conn.commit()

