#!/usr/bin/env python3
"""
Clan API functionality for blog-launchpad
Handles communication with the blog-clan-api microservice
"""

import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ClanAPIClient:
    """Client for interacting with the blog-clan-api microservice."""
    
    def __init__(self, base_url: str = 'http://localhost:5006'):
        self.base_url = base_url
        self.timeout = 5
    
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
    
    def get_category_products(self, category_id: int) -> List[Dict]:
        """Get products from a specific category."""
        try:
            response = requests.get(f'{self.base_url}/api/categories/{category_id}/products', timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch category products: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching category products: {str(e)}")
            return []
    
    def get_related_products(self, product_id: int) -> List[Dict]:
        """Get related products for a specific product."""
        try:
            response = requests.get(f'{self.base_url}/api/products/{product_id}/related', timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch related products: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching related products: {str(e)}")
            return []

# Global client instance
clan_client = ClanAPIClient()

def get_categories() -> List[Dict]:
    """Get available categories."""
    return clan_client.get_categories()

def get_products(limit: int = 50, query: str = '') -> List[Dict]:
    """Search products."""
    return clan_client.get_products(limit=limit, query=query)

def get_category_products(category_id: int) -> List[Dict]:
    """Get products from a specific category."""
    return clan_client.get_category_products(category_id)

def get_related_products(product_id: int) -> List[Dict]:
    """Get related products for a specific product."""
    return clan_client.get_related_products(product_id)
