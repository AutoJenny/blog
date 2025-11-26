"""Select seasonal recipe posts for newsletter."""

from __future__ import annotations

from typing import Any, Dict, Optional
from config.database import db_manager


def select_seasonal_recipe_post() -> Dict[str, Any]:
    """Select the most recent published recipe post that hasn't been used in a newsletter.
    
    Returns:
        Dict with: id, title, slug, summary, hero_image, recipe_id, url
        Empty dict if no post found
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.title, p.slug, 
                           COALESCE(p.summary, '') AS summary,
                           i.file_path AS hero_image,
                           p.recipe_id
                    FROM post p
                    LEFT JOIN images i ON p.header_image_id = i.id
                    WHERE p.recipe_id IS NOT NULL
                      AND p.status = 'published'
                      AND p.newsletter_recipe_featured_at IS NULL
                    ORDER BY p.first_published_at DESC NULLS LAST, p.updated_at DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if row:
                    post = dict(row)
                    # Build URL from slug
                    if post.get('slug'):
                        post['url'] = f"/posts/{post['slug']}"
                    else:
                        post['url'] = f"/posts/{post['id']}"
                    return post
                return {}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error selecting seasonal recipe post: {e}", exc_info=True)
        return {}

