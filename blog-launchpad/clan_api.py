#!/usr/bin/env python3
"""
Clan API functionality for blog-launchpad
Handles communication with the blog-clan-api microservice with local caching
"""

import requests
import logging
from typing import Dict, List, Optional
from clan_cache import clan_cache

logger = logging.getLogger(__name__)

class ClanAPIClient:
    """Client for interacting with the blog-clan-api microservice."""
    
    def __init__(self, base_url: str = 'http://localhost:5007'):
        self.base_url = base_url
        self.timeout = 30  # Increased timeout for large product fetches
    
    def get_categories(self) -> List[Dict]:
        """Get available categories from clan.com API."""
        try:
            response = requests.get(f'{self.base_url}/api/categories', timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch categories: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching categories: {str(e)}")
            return []
    
    def get_products(self, limit: int = 50, query: str = '') -> List[Dict]:
        """Search products from clan.com API."""
        try:
            url = f'{self.base_url}/api/products?limit={limit}'
            if query:
                url += f'&q={query}'
            
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch products: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching products: {str(e)}")
            return []

# Global client instance
clan_client = ClanAPIClient()

def get_categories() -> List[Dict]:
    """Get available categories from cache or API."""
    # Check if cache is fresh
    if clan_cache.is_cache_fresh('categories'):
        logger.info("Using cached categories")
        return clan_cache.get_categories()
    
    # Fetch from API and cache
    logger.info("Fetching categories from API")
    categories = clan_client.get_categories()
    if categories:
        clan_cache.store_categories(categories)
    return categories

def get_products(limit: int = 50, query: str = '') -> List[Dict]:
    """Search products from cache or API."""
    # Check if cache is fresh
    if clan_cache.is_cache_fresh('products'):
        logger.info("Using cached products")
        return clan_cache.get_products(limit=limit, query=query)
    
    # Fetch from API and cache
    logger.info("Fetching products from API")
    products = clan_client.get_products(limit=limit, query=query)
    if products:
        clan_cache.store_products(products)
    return products

def get_category_products(category_id: int) -> List[Dict]:
    """Get products from a specific category (random selection from cache)."""
    # Use cached products and return random selection
    products = clan_cache.get_random_products(3)
    return products

def get_related_products(product_id: int) -> List[Dict]:
    """Get related products for a specific product (random selection from cache)."""
    # Use cached products and return random selection
    products = clan_cache.get_random_products(3)
    return products

def refresh_cache() -> Dict:
    """Manually refresh the cache from the API."""
    logger.info("Manually refreshing cache")
    
    # Fetch and store categories
    categories = clan_client.get_categories()
    if categories:
        clan_cache.store_categories(categories)
    
    # Fetch and store products (get a large batch for cache)
    products = clan_client.get_products(limit=1000)  # Get 1000+ products for cache
    logger.info(f"Fetched {len(products)} products from API")
    if products:
        # The products are already transformed by the blog-clan-api service
        clan_cache.store_products(products)
        logger.info(f"Stored {len(products)} products in cache")
    else:
        logger.error("No products fetched from API")
    
    return clan_cache.get_cache_stats()

def get_cache_stats() -> Dict:
    """Get cache statistics."""
    return clan_cache.get_cache_stats()
