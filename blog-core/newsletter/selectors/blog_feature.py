"""Select blog posts to feature (latest theme post with alternatives)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from config.database import db_manager


def select_feature_articles(limit: int = 10) -> List[Dict[str, Any]]:
    """Return recent published theme posts with header images.
    
    Filters for posts that have a theme_id (themed posts) and returns
    multiple options for selection.
    
    Args:
        limit: Maximum number of posts to return (default: 10)
    
    Returns:
        List of post dicts with: id, title, url, excerpt, hero_image
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.title, p.slug, p.summary, i.file_path AS hero_image,
                       pd.expanded_idea, p.clan_uploaded_url
                FROM post p
                JOIN images i ON p.header_image_id = i.id
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status = 'published'
                  AND p.theme_id IS NOT NULL
                ORDER BY p.created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cur.fetchall()
            if not rows:
                return []
            
            results = []
            for row in rows:
                d = dict(row)
                # Use clan_uploaded_url if available, otherwise fall back to local path
                url = d.get('clan_uploaded_url') or f"/posts/{d.get('slug') or d['id']}"
                results.append({
                    "id": d["id"],
                    "title": d["title"],
                    "url": url,
                    "excerpt": d.get("summary") or "",
                    "hero_image": d.get("hero_image"),
                    "expanded_idea": d.get("expanded_idea") or "",
                })
            return results


def select_feature_article() -> Optional[Dict[str, Any]]:
    """Return latest published theme post with a header image.
    
    This is a convenience function that returns just the first result
    from select_feature_articles() for backward compatibility.
    """
    articles = select_feature_articles(limit=1)
    return articles[0] if articles else None


