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
    
    import hashlib
    
    stored = 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                try:
                    url = item.get('url', '')
                    title = item.get('title', '')
                    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest() if url else None
                    
                    # Check if URL hash already exists to avoid duplicates
                    # For content-extracted items (same URL, different titles), use title+URL hash
                    if url_hash:
                        # Check if exact duplicate (same URL + title from same source)
                        cur.execute(
                            """
                            SELECT id FROM newsletter_source_item 
                            WHERE source_url_hash = %s 
                            AND source_name = %s
                            AND title = %s
                            LIMIT 1
                            """,
                            (url_hash, item.get('source_name'), title)
                        )
                        if cur.fetchone():
                            # Skip exact duplicate (same URL + title + source)
                            continue
                        
                        # For content-extracted items: if same URL but different title, allow it
                        # (This handles VisitScotland category pages with multiple events)
                        # But check if this exact title+URL combination exists
                        if title:
                            # Use a combined hash for title+URL to dedupe same event on same page
                            combined = f"{title}|{url}"
                            combined_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
                            cur.execute(
                                """
                                SELECT id FROM newsletter_source_item 
                                WHERE source_url_hash = %s 
                                AND source_name = %s
                                LIMIT 1
                                """,
                                (combined_hash, item.get('source_name'))
                            )
                            # Don't skip - allow same URL with different titles
                    
                        # For content-extracted items with same URL, use title+URL hash
                        # Otherwise use URL hash
                        final_hash = url_hash
                        if title and url:
                            # Create hash from title+URL for better deduplication of content-extracted items
                            combined = f"{title}|{url}"
                            final_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
                        
                        cur.execute(
                            """
                            INSERT INTO newsletter_source_item 
                            (source_name, title, url, published_at, event_date, location, category, 
                             raw_data, signal_score, freshness_score, source_url_hash, 
                             suitability_score, suitability_notes, is_event, calendar_event_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                item.get('source_name'),
                                item.get('title'),
                                url,
                                item.get('published_at'),
                                item.get('event_date'),
                                item.get('location'),
                                item.get('category', 'other'),
                                Json(item.get('raw_data', {})),
                                item.get('signal_score', 0.0),
                                item.get('freshness_score', 0.0),
                                final_hash,
                                item.get('suitability_score'),
                                item.get('suitability_notes'),
                                item.get('is_event', False),
                                item.get('calendar_event_id'),
                            ),
                        )
                    stored += 1
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to store source item: {e}")
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
               raw_data, signal_score, freshness_score, combined_score, cached_at,
               suitability_score, suitability_notes, is_event, calendar_event_id
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

