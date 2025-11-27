"""Service for resolving category branches and leaf categories for products."""

from __future__ import annotations

from typing import Optional
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)


def find_product_leaf_category(product_title: str, category_ids: List[int] | None = None) -> Optional[int]:
    """Find the leaf (deepest) category for a product.
    
    Args:
        product_title: Product title (may contain category keywords)
        category_ids: Optional list of category IDs from clan_products table
    
    Returns:
        Category ID of leaf category, or None if not found
    """
    if not category_ids:
        # Try to match product title to category names
        return _find_category_from_title(product_title)
    
    # Find the deepest category from category_ids
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get all categories and their levels
            cur.execute("""
                SELECT id, name, level, parent_id
                FROM clan_categories
                WHERE id = ANY(%s)
                ORDER BY level DESC
            """, (category_ids,))
            categories = cur.fetchall()
            
            if not categories:
                return None
            
            # Find leaf category (one with no children, or deepest level)
            # A leaf category has no other categories that have it as parent_id
            for cat in categories:
                cat_id = cat['id']
                # Check if this category has any children
                cur.execute("""
                    SELECT COUNT(*) as child_count
                    FROM clan_categories
                    WHERE parent_id = %s
                """, (cat_id,))
                result = cur.fetchone()
                if result and result['child_count'] == 0:
                    # This is a leaf category
                    return cat_id
            
            # If no leaf found, return deepest level category
            return categories[0]['id']
    
    return None


def find_category_branch(leaf_category_id: int) -> Optional[int]:
    """Find the branch category (parent of leaf) for a leaf category.
    
    Args:
        leaf_category_id: ID of leaf category
    
    Returns:
        Category ID of branch (parent), or None if leaf is root
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT parent_id
                FROM clan_categories
                WHERE id = %s
            """, (leaf_category_id,))
            result = cur.fetchone()
            
            if result and result['parent_id']:
                return result['parent_id']
    
    return None


def are_different_branches(category_id1: Optional[int], category_id2: Optional[int]) -> bool:
    """Check if two category IDs are in different branches.
    
    Two categories are in different branches if:
    - They are different branch categories (not leaf categories)
    - Or their branch categories (parents) are different
    
    Args:
        category_id1: First category ID (can be branch or leaf)
        category_id2: Second category ID (can be branch or leaf)
    
    Returns:
        True if categories are in different branches
    """
    if not category_id1 or not category_id2:
        return True  # NULL categories are considered different
    
    if category_id1 == category_id2:
        return False
    
    # Get branch categories for both
    branch1 = _get_branch_category(category_id1)
    branch2 = _get_branch_category(category_id2)
    
    # If either is None, they're different
    if not branch1 or not branch2:
        return True
    
    # Compare branch categories
    return branch1 != branch2


def _get_branch_category(category_id: int) -> Optional[int]:
    """Get branch category for a given category ID.
    
    If category_id is a leaf, return its parent.
    If category_id is a branch, return itself.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Check if this category has children (is a branch)
            cur.execute("""
                SELECT COUNT(*) as child_count
                FROM clan_categories
                WHERE parent_id = %s
            """, (category_id,))
            result = cur.fetchone()
            
            if result and result['child_count'] > 0:
                # This is a branch category, return itself
                return category_id
            
            # This is a leaf, get its parent
            cur.execute("""
                SELECT parent_id
                FROM clan_categories
                WHERE id = %s
            """, (category_id,))
            result = cur.fetchone()
            
            if result and result['parent_id']:
                return result['parent_id']
    
    return None


def _find_category_from_title(product_title: str) -> Optional[int]:
    """Try to find category from product title keywords.
    
    This is a fallback when category_ids are not available.
    Matches common category keywords in title to category names.
    
    Args:
        product_title: Product title
    
    Returns:
        Category ID if match found, None otherwise
    """
    # Common category keywords to match
    category_keywords = {
        'kilt': ['kilt', 'kilts'],
        'sporran': ['sporran', 'sporrans'],
        'sgian': ['sgian', 'dubh'],
        'brogue': ['brogue', 'brogues'],
        'tartan': ['tartan'],
        'scarf': ['scarf', 'scarves'],
        'waistcoat': ['waistcoat', 'waistcoats'],
        'jacket': ['jacket', 'jackets'],
        'trews': ['trews'],
        'hose': ['hose', 'socks'],
    }
    
    title_lower = product_title.lower()
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Try to match keywords to category names
            for keyword, variations in category_keywords.items():
                for variation in variations:
                    if variation in title_lower:
                        # Search for category with this keyword in name
                        cur.execute("""
                            SELECT id, name, level
                            FROM clan_categories
                            WHERE LOWER(name) LIKE %s
                            ORDER BY level DESC
                            LIMIT 1
                        """, (f'%{variation}%',))
                        result = cur.fetchone()
                        if result:
                            return result['id']
    
    return None

