#!/usr/bin/env python3
"""
Clan.com API Client
Python implementation of the PHP API client for clan.com
"""

import requests
import json
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class ClanAPIClient:
    def __init__(self):
        self.base_url = 'https://clan.com/clan/api'
        self.fallback_url = 'https://bast-clan.hotcheck.co.uk/clan/api'
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.timeout = 10
    
    def make_api_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with fallback URL support"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making API request to: {url}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            # Check if JSON decoding was successful
            if result is None:
                raise ValueError("Empty response from API")
                
            logger.info(f"API request successful: {endpoint}")
            return result
            
        except requests.RequestException as e:
            logger.warning(f"Primary API failed ({endpoint}): {str(e)}")
            
            # Try fallback URL
            fallback_url = f"{self.fallback_url}{endpoint}"
            try:
                logger.info(f"Trying fallback URL: {fallback_url}")
                response = self.session.get(fallback_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
                if result is None:
                    raise ValueError("Empty response from fallback API")
                    
                logger.info(f"Fallback API request successful: {endpoint}")
                return result
                
            except requests.RequestException as e2:
                logger.error(f"Both APIs failed ({endpoint}): {str(e2)}")
                return {
                    'success': False,
                    'message': f'API error: {str(e2)}'
                }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error ({endpoint}): {str(e)}")
            return {
                'success': False,
                'message': f'JSON decoding error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error ({endpoint}): {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def get_product_data(self, sku: str, all_images: bool = False, 
                        include_categories: bool = False) -> Dict:
        """Get single product data by SKU"""
        params = {
            'sku': sku,
            'all_images': 1 if all_images else 0,
            'include_categories': 1 if include_categories else 0
        }
        return self.make_api_request('/getProductData', params)
    
    def get_products(self, limit: Optional[int] = None, include_images: bool = True) -> Dict:
        """Get multiple products with optional image data"""
        if include_images:
            # For products with images, we need to get them individually
            # First get the basic product list
            basic_result = self.make_api_request('/getProducts', {'limit': limit})
            if not basic_result.get('success', True):
                return basic_result
            
            products = basic_result.get('data', [])
            detailed_products = []
            
            # Get detailed data for each product (including images)
            for product in products[:limit] if limit else products:
                if isinstance(product, list) and len(product) > 1:
                    sku = product[1]
                    detailed_result = self.get_product_data(sku, all_images=True)
                    if detailed_result.get('success', True):
                        detailed_products.append(detailed_result.get('data'))
            
            return {
                'success': True,
                'data': detailed_products
            }
        else:
            # Basic product list without images
            params = {}
            if limit:
                params['limit'] = limit
            return self.make_api_request('/getProducts', params)
    
    def get_category_tree(self) -> Dict:
        """Get complete category tree"""
        return self.make_api_request('/getCategoryTree')
    
    def get_product_by_id(self, product_id: int, include_categories: bool = False) -> Dict:
        """Get product data by ID (convenience method)"""
        # For now, we'll get all products and filter by ID
        # In a real implementation, there might be a direct endpoint
        result = self.get_products()
        if result.get('success', True):
            products = result.get('data', [])
            for product in products:
                if isinstance(product, list) and len(product) > 1:
                    # Generate ID from SKU hash
                    if hash(product[1]) % 100000 == product_id:
                        if include_categories:
                            # Get detailed product data with categories
                            return self.get_product_data(product[1], include_categories=True)
                        return {'success': True, 'data': product}
        
        return {'success': False, 'message': f'Product {product_id} not found'}
