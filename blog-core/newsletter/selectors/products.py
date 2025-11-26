"""Product selection logic (new vs updated, grouping variants).

Real implementations will query the catalogue; this is a scaffold.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from config.database import db_manager


def get_product_pool(*, since_iso_timestamp: str, pool_size: int = 50, exclude_launched: bool = True) -> List[Dict[str, Any]]:
    """Get a pool of recent products for random selection.
    
    Returns up to pool_size products from the most recent clan_created_at dates,
    excluding already launched products. This pool can be reused for multiple
    random selections.
    
    Args:
        since_iso_timestamp: Minimum clan_created_at date (ISO format)
        pool_size: Maximum number of products in the pool (default: 50)
        exclude_launched: If True, exclude products with newsletter_launched_at set
    
    Returns:
        List of product dicts with: id, name, sku, image_url, url, short_description, category_ids
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Build query to get recent products, excluding launched ones
                exclude_clause = "AND newsletter_launched_at IS NULL" if exclude_launched else ""
                
                # Use string concatenation to avoid f-string issues with LIKE patterns containing %
                # Use clan_created_at (actual creation date) instead of first_seen_at (sync discovery date)
                # Fallback to first_seen_at for products without clan_created_at (legacy products)
                query = """
                    SELECT id,
                           name,
                           sku,
                           COALESCE(image_url, '') AS image_url,
                           COALESCE(url, '') AS url,
                           COALESCE(short_description, '') AS short_description,
                           COALESCE(clan_created_at, first_seen_at) AS created_at,
                           category_ids
                    FROM clan_products
                    WHERE COALESCE(clan_created_at, first_seen_at) > %s
                      AND image_url IS NOT NULL
                      AND TRIM(image_url) <> ''
                      AND (image_url LIKE 'http://%%' OR image_url LIKE 'https://%%')
                      """ + exclude_clause + """
                    ORDER BY COALESCE(clan_created_at, first_seen_at) DESC
                    LIMIT %s
                """
                
                cur.execute(
                    query,
                    (since_iso_timestamp, pool_size),
                )
                rows = cur.fetchall() or []
                products = [dict(r) for r in rows]
                
                # Filter out any products without valid image URLs (double-check)
                valid_products = []
                for p in products:
                    image_url = p.get('image_url')
                    if image_url:
                        image_str = str(image_url).strip() if image_url else ''
                        if image_str and (image_str.startswith('http://') or image_str.startswith('https://')):
                            valid_products.append(p)
                
                # Deduplicate by product name
                seen_names = set()
                unique_products = []
                for p in valid_products:
                    name = p.get('name')
                    if name:
                        name_str = str(name).strip() if name else ''
                        if name_str and name_str not in seen_names:
                            seen_names.add(name_str)
                            unique_products.append(p)
                
                return unique_products
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting product pool: {e}", exc_info=True)
        return []


def select_random_from_pool(*, pool: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """Randomly select products from a pool, ensuring different specific categories.
    
    Args:
        pool: List of product dicts to select from
        limit: Number of products to select (default: 3)
    
    Returns:
        List of selected products with category diversity
    """
    if not pool or len(pool) < limit:
        # If pool is too small, just return what we have
        import random
        random.shuffle(pool)
        return pool[:limit] if pool else []
    
    import random
    
    # Helper to get a specific (non-generic) category ID from category_ids
    def get_specific_category(category_ids) -> int | None:
        """Get the first specific (non-12) category ID from the list."""
        if not category_ids:
            return None
        
        category_list = None
        if isinstance(category_ids, list):
            category_list = category_ids
        elif isinstance(category_ids, str):
            try:
                import json
                parsed = json.loads(category_ids)
                if isinstance(parsed, list):
                    category_list = parsed
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        if not category_list or len(category_list) == 0:
            return None
        
        # Find first category that's not 12 (skip generic root category)
        for cat_id in category_list:
            try:
                cat_int = int(cat_id) if cat_id else None
                if cat_int and cat_int != 12:  # Skip category 12
                    return cat_int
            except (ValueError, TypeError):
                continue
        
        return None
    
    # Shuffle pool for randomness
    shuffled_pool = pool.copy()
    random.shuffle(shuffled_pool)
    
    # Select diverse products: prefer different specific categories
    selected = []
    seen_categories = set()
    
    # First pass: try to get one product from each specific category
    for p in shuffled_pool:
        if len(selected) >= limit:
            break
        category_id = get_specific_category(p.get('category_ids'))
        # If product has a specific category and we haven't seen it, add it
        if category_id and category_id not in seen_categories:
            selected.append(p)
            seen_categories.add(category_id)
        # If product has no specific category, we'll handle it in second pass
    
    # Second pass: fill remaining slots with products from any category (or no category)
    if len(selected) < limit:
        remaining = [p for p in shuffled_pool if p not in selected]
        random.shuffle(remaining)
        needed = limit - len(selected)
        for p in remaining[:needed]:
            selected.append(p)
    
    return selected


def select_new_products(*, since_iso_timestamp: str, limit: int = 6, exclude_launched: bool = True) -> List[Dict[str, Any]]:
    """Return recent products from clan_products, excluding already launched ones.
    
    DEPRECATED: Use get_product_pool() and select_random_from_pool() instead.
    This function is kept for backward compatibility.
    
    Selects products by clan_created_at (most recent first), excluding those with
    newsletter_launched_at set, then randomly selects from the results.
    
    Args:
        since_iso_timestamp: Minimum clan_created_at date (ISO format)
        limit: Maximum number of products to return (default: 6)
        exclude_launched: If True, exclude products with newsletter_launched_at set
    
    Returns:
        List of product dicts with: id, name, sku, image_url, url, short_description
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Build query to get recent products, excluding launched ones
                exclude_clause = "AND newsletter_launched_at IS NULL" if exclude_launched else ""
                
                # Use string concatenation to avoid f-string issues with LIKE patterns containing %
                # Use clan_created_at (actual creation date) instead of first_seen_at (sync discovery date)
                # Fallback to first_seen_at for products without clan_created_at (legacy products)
                query = """
                    SELECT id,
                           name,
                           sku,
                           COALESCE(image_url, '') AS image_url,
                           COALESCE(url, '') AS url,
                           COALESCE(short_description, '') AS short_description,
                           COALESCE(clan_created_at, first_seen_at) AS created_at,
                           category_ids
                    FROM clan_products
                    WHERE COALESCE(clan_created_at, first_seen_at) > %s
                      AND image_url IS NOT NULL
                      AND TRIM(image_url) <> ''
                      AND (image_url LIKE 'http://%%' OR image_url LIKE 'https://%%')
                      """ + exclude_clause + """
                    ORDER BY COALESCE(clan_created_at, first_seen_at) DESC
                    LIMIT %s
                """
                
                cur.execute(
                    query,
                    (since_iso_timestamp, limit * 10),  # Get many more candidates for better randomization
                )
                rows = cur.fetchall() or []
                products = [dict(r) for r in rows]
                
                # Filter out any products without valid image URLs (double-check)
                # Since we already filtered in SQL, this is just a safety check
                valid_products = []
                for p in products:
                    image_url = p.get('image_url')
                    if image_url:
                        # Ensure image_url is a string
                        image_str = str(image_url).strip() if image_url else ''
                        if image_str and (image_str.startswith('http://') or image_str.startswith('https://')):
                            valid_products.append(p)
                products = valid_products
                
                # Deduplicate by product name to avoid showing the same product twice
                seen_names = set()
                unique_products = []
                for p in products:
                    name = p.get('name')
                    if name:
                        name_str = str(name).strip() if name else ''
                        if name_str and name_str not in seen_names:
                            seen_names.add(name_str)
                            unique_products.append(p)
                products = unique_products
                
                # Shuffle FIRST to randomize the order before any filtering
                import random
                random.shuffle(products)
                
                # Helper to get a specific (non-generic) category ID from category_ids
                # Skips category 12 (CLAN Main Category) as it's too generic
                def get_specific_category(category_ids) -> int | None:
                    """Get the first specific (non-12) category ID from the list.
                    
                    Category 12 is "CLAN Main Category" which is too generic - almost all
                    products have it. We want more specific categories for diversity.
                    """
                    if not category_ids:
                        return None
                    
                    # Handle JSONB array from database (could be list or already parsed)
                    category_list = None
                    if isinstance(category_ids, list):
                        category_list = category_ids
                    elif isinstance(category_ids, str):
                        try:
                            import json
                            parsed = json.loads(category_ids)
                            if isinstance(parsed, list):
                                category_list = parsed
                        except (json.JSONDecodeError, ValueError, TypeError):
                            pass
                    
                    if not category_list or len(category_list) == 0:
                        return None
                    
                    # Find first category that's not 12 (skip generic root category)
                    for cat_id in category_list:
                        try:
                            cat_int = int(cat_id) if cat_id else None
                            if cat_int and cat_int != 12:  # Skip category 12
                                return cat_int
                        except (ValueError, TypeError):
                            continue
                    
                    # If all categories are 12 or we couldn't parse, return None
                    return None
                
                # Select diverse products: prefer different specific categories
                selected = []
                seen_categories = set()
                
                # First pass: try to get one product from each specific category
                for p in products:
                    if len(selected) >= limit:
                        break
                    category_id = get_specific_category(p.get('category_ids'))
                    # If product has a specific category and we haven't seen it, add it
                    if category_id and category_id not in seen_categories:
                        selected.append(p)
                        seen_categories.add(category_id)
                    # If product has no specific category, we'll handle it in second pass
                
                # Second pass: fill remaining slots with products from any category (or no category)
                if len(selected) < limit:
                    remaining = [p for p in products if p not in selected]
                    random.shuffle(remaining)
                    needed = limit - len(selected)
                    for p in remaining[:needed]:
                        selected.append(p)
                
                return selected
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error selecting new products: {e}", exc_info=True)
        return []


def select_spotlight_product() -> Dict[str, Any]:
    """Return a single strong candidate product as spotlight fallback.
    
    DEPRECATED: This function is kept for backwards compatibility.
    Use select_spotlight_profile_post() instead for profile posts.
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


def select_spotlight_profile_post() -> Dict[str, Any]:
    """Select the most recent published profile post that hasn't been used in a newsletter spotlight.
    
    Returns:
        Dict with: id, title, slug, summary, hero_image, profile_standfirst, profile_product_id
        Empty dict if no post found
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.title, p.slug, 
                           COALESCE(p.profile_standfirst, p.summary, '') AS summary,
                           i.file_path AS hero_image,
                           p.profile_standfirst,
                           p.profile_product_id
                    FROM post p
                    LEFT JOIN images i ON p.header_image_id = i.id
                    WHERE p.profile_product_id IS NOT NULL
                      AND p.status = 'published'
                      AND p.newsletter_spotlighted_at IS NULL
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
        logging.getLogger(__name__).error(f"Error selecting spotlight profile post: {e}", exc_info=True)
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



