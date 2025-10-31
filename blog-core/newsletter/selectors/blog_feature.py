"""Select a blog post to feature (latest with hero image)."""

from __future__ import annotations

from typing import Any, Dict, Optional
from config.database import db_manager


def select_feature_article() -> Optional[Dict[str, Any]]:
    """Return latest published post with a header image, including title, url, hero image, and excerpt."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.title, p.slug, p.summary, i.path AS hero_image
                FROM post p
                JOIN image i ON p.header_image_id = i.id
                WHERE p.status = 'published'
                ORDER BY p.created_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            url = f"/posts/{d.get('slug') or d['id']}"
            return {
                "id": d["id"],
                "title": d["title"],
                "url": url,
                "excerpt": d.get("summary") or "",
                "hero_image": d.get("hero_image"),
            }


