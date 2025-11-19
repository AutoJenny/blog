"""Service for tracking product launches and profiles in newsletters and blog posts."""

from __future__ import annotations

from typing import List, Dict, Any
from config.database import db_manager
import logging

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
        product_id = payload.get('id')
        if product_id:
            try:
                product_ids.append(int(product_id))
            except (ValueError, TypeError):
                pass
    
    return product_ids

