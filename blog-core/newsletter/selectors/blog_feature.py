"""Select blog posts to feature (latest theme post with alternatives)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from config.database import db_manager


def select_feature_articles(limit: int = 10, target_week: str = None) -> List[Dict[str, Any]]:
    """Return recent published theme posts with header images.
    
    Filters for posts that have a theme_id (themed posts) and returns
    multiple options for selection. If target_week is provided, includes
    the post for that week at the top.
    
    Args:
        limit: Maximum number of posts to return (default: 10)
        target_week: Optional target week (e.g., "2025W48") to prioritize that week's post
    
    Returns:
        List of post dicts with: id, title, url, excerpt, hero_image
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # If target_week is provided, try to get the post for that week first
            week_post_id = None
            if target_week:
                try:
                    from datetime import date
                    from utils.week_post_resolver import resolve_post_for_week
                    
                    # Parse year and week from target_week
                    if 'W' in target_week:
                        year_str, week_str = target_week.split('W')
                        year = int(year_str)
                        week_number = int(week_str)
                        week_post_id = resolve_post_for_week(year, week_number)
                except Exception:
                    pass
            
            # Get posts, prioritizing the week's post
            if week_post_id:
                # First get the week's post (include even if draft, as it's the week's post)
                # Use LEFT JOIN for images so we include posts even without header images
                cur.execute(
                    """
                    SELECT p.id, p.title, p.slug, p.summary, i.file_path AS hero_image,
                           pd.expanded_idea, p.clan_uploaded_url, p.first_published_at, p.status
                    FROM post p
                    LEFT JOIN images i ON p.header_image_id = i.id
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.id = %s
                      AND p.status != 'deleted'
                      AND p.theme_id IS NOT NULL
                    """,
                    (week_post_id,)
                )
                week_post = cur.fetchone()
                
                # Then get other recent posts (excluding the week's post)
                # Only get published posts for the "other" list
                cur.execute(
                    """
                    SELECT p.id, p.title, p.slug, p.summary, i.file_path AS hero_image,
                           pd.expanded_idea, p.clan_uploaded_url, p.first_published_at, p.status
                    FROM post p
                    LEFT JOIN images i ON p.header_image_id = i.id
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.status = 'published'
                      AND p.theme_id IS NOT NULL
                      AND p.id != %s
                    ORDER BY COALESCE(p.first_published_at, p.created_at) DESC
                    LIMIT %s
                    """,
                    (week_post_id, limit - 1)
                )
                other_posts = cur.fetchall() or []
                
                # Combine: week post first, then others
                rows = [week_post] + list(other_posts) if week_post else list(other_posts)
            else:
                # No target week, just get recent posts
                cur.execute(
                    """
                    SELECT p.id, p.title, p.slug, p.summary, i.file_path AS hero_image,
                           pd.expanded_idea, p.clan_uploaded_url, p.first_published_at, p.status
                    FROM post p
                    LEFT JOIN images i ON p.header_image_id = i.id
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.status = 'published'
                      AND p.theme_id IS NOT NULL
                    ORDER BY COALESCE(p.first_published_at, p.created_at) DESC
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


