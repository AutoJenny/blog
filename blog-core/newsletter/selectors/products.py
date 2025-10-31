"""Product selection logic (new vs updated, grouping variants).

Real implementations will query the catalogue; this is a scaffold.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from config.database import db_manager


def select_new_products(*, since_iso_timestamp: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Return published products created after the given timestamp, newest first.

    Defensive to unknown schemas: returns [] on any failure.
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id,
                           COALESCE(name, title) AS name,
                           COALESCE(slug, url, '') AS slug,
                           COALESCE(image_url, hero_image, '') AS image_url,
                           created_at,
                           COALESCE(is_published, TRUE) AS is_published,
                           COALESCE(short_description, '') AS short_description
                    FROM product
                    WHERE created_at > %s
                      AND COALESCE(is_published, TRUE) = TRUE
                      AND COALESCE(image_url, hero_image, '') <> ''
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (since_iso_timestamp, limit),
                )
                rows = cur.fetchall() or []
                return [dict(r) for r in rows]
    except Exception:
        return []


def select_spotlight_product() -> Dict[str, Any]:
    """Return a single strong candidate product as spotlight fallback."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id,
                           COALESCE(name, title) AS name,
                           COALESCE(slug, url, '') AS slug,
                           COALESCE(image_url, hero_image, '') AS image_url,
                           COALESCE(short_description, '') AS short_description,
                           updated_at
                    FROM product
                    WHERE COALESCE(is_published, TRUE) = TRUE
                      AND COALESCE(image_url, hero_image, '') <> ''
                    ORDER BY updated_at DESC NULLS LAST, id DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                return dict(row) if row else {}
    except Exception:
        return {}


def group_variants(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Group variants by parent; returns (parents, num_hidden_variants)."""
    parent_key = None
    if not items:
        return items, 0
    # Infer parent key
    if "parent_id" in items[0]:
        parent_key = "parent_id"
    elif "variant_parent_id" in items[0]:
        parent_key = "variant_parent_id"
    else:
        return items, 0

    parents: Dict[Any, Dict[str, Any]] = {}
    hidden = 0
    for it in items:
        pid = it.get(parent_key)
        if pid is not None:  # Use is not None to handle pid=0 case
            if pid not in parents:
                # First time seeing this parent; surface this as parent shell
                parents[pid] = {
                    "id": pid,
                    "name": it.get("parent_name") or it.get("name"),
                    "slug": it.get("parent_slug") or it.get("slug"),
                    "image_url": it.get("parent_image_url") or it.get("image_url"),
                    "short_description": it.get("short_description", ""),
                }
            hidden += 1
        else:
            # Already a parent-level product
            item_id = it.get("id")
            if item_id is None:
                # Use a fallback key that won't conflict
                item_id = f"__item_{len(parents)}"
            parents[item_id] = it

    grouped = list(parents.values())
    return grouped if grouped else items, hidden



