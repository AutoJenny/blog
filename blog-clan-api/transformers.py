#!/usr/bin/env python3
"""
Data transformation functions for clan.com API responses
"""

from typing import List, Dict

def flatten_category_tree(category_tree: List[Dict]) -> List[Dict]:
    """Convert nested category tree to flat list for UI dropdowns"""
    flat_categories = []
    
    def traverse(categories, level=0):
        for category in categories:
            flat_categories.append({
                'id': category.get('id'),
                'name': category.get('name'),
                'description': category.get('description'),
                'level': level,
                'parent_id': category.get('parent_id')
            })
            if category.get('children'):
                traverse(category['children'], level + 1)
    
    traverse(category_tree)
    return flat_categories

def transform_product_for_ui(product: Dict) -> Dict:
    """Transform API product data to match our UI expectations"""
    # Handle both array format (from clan.com API) and object format
    if isinstance(product, list):
        # Array format: [name, sku, url, description]
        return {
            'id': hash(product[1]) % 100000,  # Generate ID from SKU hash
            'name': product[0],
            'sku': product[1],
            'price': '£29.99',  # Default price since not provided
            'image_url': f"https://clan.com/images/{product[1]}.jpg",
            'url': product[2],
            'description': product[3] if len(product) > 3 else '',
            'category_ids': []
        }
    else:
        # Object format (fallback)
        return {
            'id': product.get('id'),
            'name': product.get('name'),
            'sku': product.get('sku'),
            'price': product.get('price'),
            'image_url': product.get('image_url') or product.get('main_image'),
            'url': f"https://clan.com/product/{product.get('url_key', '')}",
            'description': product.get('short_description') or product.get('description'),
            'category_ids': product.get('category_ids', [])
        }

def get_random_products(products: List[Dict], count: int = 6) -> List[Dict]:
    """Get random products for preview display"""
    import random
    if len(products) <= count:
        return products
    return random.sample(products, count)

def get_random_categories(categories: List[Dict], count: int = 3) -> List[Dict]:
    """Get random categories for preview display"""
    import random
    if len(categories) <= count:
        return categories
    return random.sample(categories, count)
