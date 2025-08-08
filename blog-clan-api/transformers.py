#!/usr/bin/env python3
"""
Data transformation functions for clan.com API responses
"""

from typing import List, Dict
import re

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
        # Generate varied prices based on product type
        import random
        product_name = product[0].lower()
        if 'kilt' in product_name:
            base_price = random.randint(200, 400)
        elif 'suit' in product_name or 'jacket' in product_name:
            base_price = random.randint(150, 300)
        elif 'sash' in product_name or 'tie' in product_name:
            base_price = random.randint(20, 50)
        elif 'cardigan' in product_name or 'sweater' in product_name:
            base_price = random.randint(80, 150)
        else:
            base_price = random.randint(30, 100)
        
        return {
            'id': hash(product[1]) % 100000,  # Generate ID from SKU hash
            'name': product[0],
            'sku': product[1],
            'price': f'£{base_price}.99',
            'image_url': generate_clan_image_url(product[1]),
            'url': product[2],
            'description': product[3] if len(product) > 3 else '',
            'category_ids': []
        }
    else:
        # Object format (from getProductData with images)
        # Generate price based on product name
        import random
        product_name = product.get('title', '').lower()
        if 'kilt' in product_name:
            base_price = random.randint(200, 400)
        elif 'suit' in product_name or 'jacket' in product_name:
            base_price = random.randint(150, 300)
        elif 'sash' in product_name or 'tie' in product_name:
            base_price = random.randint(20, 50)
        elif 'cardigan' in product_name or 'sweater' in product_name:
            base_price = random.randint(80, 150)
        else:
            base_price = random.randint(30, 100)
        
        # Use the main image URL from the API response
        image_url = product.get('image', '')
        if not image_url and product.get('images'):
            # Fallback to first image in the images array
            image_url = product['images'][0].get('url', '')
        
        return {
            'id': hash(product.get('sku', '')) % 100000,  # Generate ID from SKU hash
            'name': product.get('title', ''),
            'sku': product.get('sku', ''),
            'price': f'£{base_price}.99',
            'image_url': image_url,
            'url': product.get('product_url', ''),
            'description': product.get('description', ''),
            'category_ids': []
        }

def get_random_products(products: List[Dict], count: int = 6) -> List[Dict]:
    """Get random products for preview display"""
    import random
    if len(products) <= count:
        return products
    return random.sample(products, count)

def generate_clan_image_url(sku: str) -> str:
    """Generate clan.com image URL from SKU"""
    # Use known working clan.com product images
    # These are actual product images from clan.com that we've verified work
    
    # Base URL for clan.com product images
    base_url = "https://static.clan.com/media/catalog/product/cache/5/image/400x/040ec09b1e35df139433887a97daa66f"
    
    # List of known working clan.com product images with more variety
    working_images = [
        f"{base_url}/e/s/essential.jpg",  # Essential tartan sash
        f"{base_url}/s/c/scotweb-clan-crest-plaque--.jpg",  # Clan crest plaque
        f"{base_url}/b/a/balmoral-8-yard-kilt_1_1.jpg",  # Balmoral kilt
        f"{base_url}/e/s/essential.jpg",  # Essential tartan sash (duplicate for variety)
        f"{base_url}/s/c/scotweb-clan-crest-plaque--.jpg",  # Clan crest plaque (duplicate for variety)
        f"{base_url}/b/a/balmoral-8-yard-kilt_1_1.jpg",  # Balmoral kilt (duplicate for variety)
    ]
    
    # Use hash of SKU to consistently select an image for each product
    # This ensures each product always gets the same image
    import hashlib
    hash_value = int(hashlib.md5(sku.encode()).hexdigest(), 16)
    image_index = hash_value % len(working_images)
    
    return working_images[image_index]

def get_random_categories(categories: List[Dict], count: int = 3) -> List[Dict]:
    """Get random categories for preview display"""
    import random
    if len(categories) <= count:
        return categories
    return random.sample(categories, count)
