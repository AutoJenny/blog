"""Selector for clearance products with category branch diversity."""

from __future__ import annotations

from typing import Any, Dict, List
from config.database import db_manager
from newsletter.services.category_branch_resolver import (
    find_product_leaf_category,
    find_category_branch,
    are_different_branches
)
import logging
import random

logger = logging.getLogger(__name__)


def select_clearance_products(scraped_products: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """Select clearance products with largest discounts from different category branches.
    
    Args:
        scraped_products: List of scraped product dicts from clearance page
        limit: Number of products to select (default: 5)
    
    Returns:
        List of selected products with category information added
    """
    if not scraped_products:
        return []
    
    # Filter out already promoted products and invalid products
    promoted_product_urls = get_promoted_product_urls()
    available_products = [
        p for p in scraped_products
        if (p.get('url') not in promoted_product_urls and
            p.get('price_now') and p.get('price_now') > 0 and
            p.get('title') and len(p.get('title', '')) >= 3 and
            p.get('discount_percentage', 0) > 0)  # Must have a discount
    ]
    
    if not available_products:
        logger.warning("No available products after filtering promoted ones")
        return []
    
    # Randomize product selection while still prioritizing high discounts
    # Shuffle first for true randomization
    random.shuffle(available_products)
    
    # Sort by discount with random component to ensure variety on each generation
    # Add random offset to discount to mix up selection
    sorted_products = sorted(
        available_products,
        key=lambda p: (p.get('discount_percentage', 0) + random.uniform(-10, 10), random.random()),
        reverse=True
    )
    
    # Select products ensuring different branch categories
    selected = []
    used_branch_categories = set()
    
    for product in sorted_products:
        # Limit to 4 for 2x2 layout, but respect the limit parameter
        max_items = min(limit, 4)
        if len(selected) >= max_items:
            break
        
        # Find leaf category for this product
        product_title = product.get('title', '')
        product_id = product.get('product_id')
        
        # Try to get category_ids from database if product exists
        category_ids = None
        if product_id:
            category_ids = get_product_category_ids(product_id)
            
            # Also try to get product specifications from database
            try:
                product_details = get_product_details(product_id)
                if product_details and product_details.get('specifications'):
                    db_specs = product_details['specifications']
                    # Handle JSONB or JSON string
                    if isinstance(db_specs, str):
                        import json
                        try:
                            db_specs = json.loads(db_specs)
                        except:
                            db_specs = {}
                    if isinstance(db_specs, dict) and db_specs:
                        # Merge database specs with scraped specs (database takes precedence)
                        if not product.get('specifications'):
                            product['specifications'] = {}
                        product['specifications'].update(db_specs)
            except Exception as e:
                logger.warning(f"Error getting product specs for product {product_id}: {e}")
        
        leaf_category_id = find_product_leaf_category(product_title, category_ids)
        
        # Find branch category (parent of leaf)
        branch_category_id = None
        if leaf_category_id:
            branch_category_id = find_category_branch(leaf_category_id)
            # If no branch found, use leaf itself as branch
            if not branch_category_id:
                branch_category_id = leaf_category_id
        
        # Check if this branch category is already used
        if branch_category_id and branch_category_id in used_branch_categories:
            continue  # Skip - branch category already used
        
        # Add product to selection
        product['category_leaf_id'] = leaf_category_id
        product['category_branch_id'] = branch_category_id
        selected.append(product)
        
        if branch_category_id:
            used_branch_categories.add(branch_category_id)
    
    logger.info(f"Selected {len(selected)} clearance products from {len(available_products)} available")
    return selected


def get_promoted_product_urls() -> set[str]:
    """Get set of product URLs that have already been promoted.
    
    Returns:
        Set of product URLs
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT product_url
                    FROM newsletter_clearance_promotions
                """)
                results = cur.fetchall()
                return {row['product_url'] for row in results}
    except Exception as e:
        # If table doesn't exist yet, return empty set (no products promoted yet)
        if 'does not exist' in str(e) or 'UndefinedTable' in str(e):
            logger.warning(f"newsletter_clearance_promotions table does not exist yet, returning empty set")
            return set()
        logger.error(f"Error getting promoted product URLs: {e}")
        return set()


def get_product_details(product_id: int) -> Dict[str, Any] | None:
    """Get product details including specifications from clan_products table.
    
    Args:
        product_id: Product ID
    
    Returns:
        Dict with product details or None
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, short_description, specifications, category_ids
                    FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                result = cur.fetchone()
                
                if result:
                    return dict(result)
    except Exception as e:
        logger.warning(f"Error getting product details for product {product_id}: {e}")
    
    return None


def get_product_category_ids(product_id: int) -> List[int] | None:
    """Get category_ids for a product from clan_products table.
    
    Args:
        product_id: Product ID
    
    Returns:
        List of category IDs or None
    """
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT category_ids
                    FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                result = cur.fetchone()
                
                if result and result.get('category_ids'):
                    cat_ids = result['category_ids']
                    # Handle JSONB array
                    if isinstance(cat_ids, list):
                        return cat_ids
                    elif isinstance(cat_ids, str):
                        import json
                        try:
                            parsed = json.loads(cat_ids)
                            if isinstance(parsed, list):
                                return parsed
                        except (json.JSONDecodeError, ValueError):
                            pass
    except Exception as e:
        logger.warning(f"Error getting category_ids for product {product_id}: {e}")
    
    return None

