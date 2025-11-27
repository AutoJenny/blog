"""Service for tracking product launches and profiles in newsletters and blog posts."""

from __future__ import annotations

from typing import List, Dict, Any
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)


def mark_products_newsletter_launched(product_ids: List[int]) -> None:
    """Mark products as launched in newsletter by setting newsletter_launched_at.
    
    Only sets the timestamp if it's not already set (first launch only).
    
    Args:
        product_ids: List of product IDs to mark as launched
    """
    if not product_ids:
        return
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Update only products that don't already have newsletter_launched_at set
                cur.execute(
                    """
                    UPDATE clan_products
                    SET newsletter_launched_at = NOW()
                    WHERE id = ANY(%s)
                      AND newsletter_launched_at IS NULL
                    """,
                    (product_ids,)
                )
                updated_count = cur.rowcount
                conn.commit()
                if updated_count > 0:
                    logger.info(f"Marked {updated_count} products as newsletter launched: {product_ids}")
    except Exception as e:
        logger.error(f"Error marking products as newsletter launched: {e}", exc_info=True)


def mark_product_blog_profiled(product_id: int) -> None:
    """Mark a product as blog profiled by setting blog_profiled_at.
    
    Only sets the timestamp if it's not already set (first profile only).
    
    Args:
        product_id: Product ID to mark as profiled
    """
    if not product_id:
        return
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Update only if blog_profiled_at is not already set
                cur.execute(
                    """
                    UPDATE clan_products
                    SET blog_profiled_at = NOW()
                    WHERE id = %s
                      AND blog_profiled_at IS NULL
                    """,
                    (product_id,)
                )
                updated_count = cur.rowcount
                conn.commit()
                if updated_count > 0:
                    logger.info(f"Marked product {product_id} as blog profiled")
    except Exception as e:
        logger.error(f"Error marking product as blog profiled: {e}", exc_info=True)


def mark_post_newsletter_spotlighted(post_id: int) -> None:
    """Mark a profile post as spotlighted in newsletter by setting newsletter_spotlighted_at.
    
    Only sets the timestamp if it's not already set (first spotlight only).
    
    Args:
        post_id: Post ID to mark as spotlighted
    """
    if not post_id:
        return
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Update only if newsletter_spotlighted_at is not already set
                cur.execute(
                    """
                    UPDATE post
                    SET newsletter_spotlighted_at = NOW()
                    WHERE id = %s
                      AND newsletter_spotlighted_at IS NULL
                    """,
                    (post_id,)
                )
                updated_count = cur.rowcount
                conn.commit()
                if updated_count > 0:
                    logger.info(f"Marked post {post_id} as newsletter spotlighted")
    except Exception as e:
        logger.error(f"Error marking post as newsletter spotlighted: {e}", exc_info=True)


def mark_clearance_products_promoted(products: List[Dict[str, Any]], issue_id: int, block_id: int) -> None:
    """Mark clearance products as promoted in newsletter.
    
    Saves product details to newsletter_clearance_promotions table.
    
    Args:
        products: List of product dicts with url, title, image_url, price_now, price_was, 
                 discount_percentage, specifications, category_branch_id, category_leaf_id
        issue_id: Newsletter issue ID
        block_id: Newsletter block ID
    """
    if not products:
        return
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                for product in products:
                    cur.execute("""
                        INSERT INTO newsletter_clearance_promotions (
                            product_id, product_url, product_title, image_url,
                            price_now, price_was, discount_percentage,
                            specifications, category_branch_id, category_leaf_id,
                            issue_id, block_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        product.get('product_id'),
                        product.get('url', ''),
                        product.get('title', ''),
                        product.get('image_url', ''),
                        product.get('price_now', 0),
                        product.get('price_was'),
                        product.get('discount_percentage', 0),
                        json.dumps(product.get('specifications', {})),
                        product.get('category_branch_id'),
                        product.get('category_leaf_id'),
                        issue_id,
                        block_id
                    ))
                
                conn.commit()
                logger.info(f"Marked {len(products)} clearance products as promoted for issue {issue_id}")
    except Exception as e:
        # If table doesn't exist yet, log warning but don't fail
        if 'does not exist' in str(e) or 'UndefinedTable' in str(e):
            logger.warning(f"newsletter_clearance_promotions table does not exist yet, skipping promotion tracking")
            return
        logger.error(f"Error marking clearance products as promoted: {e}", exc_info=True)


def extract_product_ids_from_payload(payload: Dict[str, Any], block_type: str) -> List[int]:
    """Extract product IDs from newsletter block payload.
    
    Args:
        payload: Block payload JSON
        block_type: Block type ('new_products' or 'spotlight')
    
    Returns:
        List of product IDs found in payload
    """
    product_ids = []
    
    if block_type == 'new_products':
        items = payload.get('items', [])
        for item in items:
            # Items can be dicts with 'id' field
            product_id = item.get('id') if isinstance(item, dict) else None
            if product_id:
                try:
                    product_ids.append(int(product_id))
                except (ValueError, TypeError):
                    pass
    
    elif block_type == 'spotlight':
        # Spotlight now uses profile posts, not products
        # But keep this for backwards compatibility with old payloads
        product_id = payload.get('id')
        if product_id:
            try:
                product_ids.append(int(product_id))
            except (ValueError, TypeError):
                pass
    
    return product_ids


def mark_post_newsletter_recipe_featured(post_id: int) -> None:
    """Mark a recipe post as featured in newsletter by setting newsletter_recipe_featured_at.
    
    Only sets the timestamp if it's not already set (first feature only).
    
    Args:
        post_id: Post ID to mark as featured
    """
    if not post_id:
        return
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Update only if newsletter_recipe_featured_at is not already set
                cur.execute(
                    """
                    UPDATE post
                    SET newsletter_recipe_featured_at = NOW()
                    WHERE id = %s
                      AND newsletter_recipe_featured_at IS NULL
                    """,
                    (post_id,)
                )
                updated_count = cur.rowcount
                conn.commit()
                if updated_count > 0:
                    logger.info(f"Marked post {post_id} as newsletter recipe featured")
    except Exception as e:
        logger.error(f"Error marking post as newsletter recipe featured: {e}", exc_info=True)


def extract_post_id_from_spotlight_payload(payload: Dict[str, Any]) -> int | None:
    """Extract post ID from spotlight block payload.
    
    Args:
        payload: Spotlight block payload JSON
    
    Returns:
        Post ID if found, None otherwise
    """
    post_id = payload.get('id')
    if post_id:
        try:
            return int(post_id)
        except (ValueError, TypeError):
            pass
    return None

