#!/usr/bin/env python3
"""
Clan.com API Microservice
Provides access to clan.com product and category data
"""

from flask import Flask, jsonify, request
from clan_client import ClanAPIClient
from transformers import flatten_category_tree, transform_product_for_ui
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
clan_api = ClanAPIClient()

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'service': 'clan-api',
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({'message': 'Test endpoint working'})

@app.route('/api/categories')
def get_categories():
    """Get all categories from clan.com"""
    try:
        logger.info("Fetching categories from clan.com API")
        
        result = clan_api.get_category_tree()
        
        if result.get('success', True):
            categories = result.get('data', [])
            flat_categories = flatten_category_tree(categories)
            logger.info(f"Successfully fetched {len(flat_categories)} categories")
            return jsonify(flat_categories)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching categories: {str(e)}")
        return jsonify([]), 500

@app.route('/api/products')
def get_products():
    """Get products from clan.com with optional search"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50)
        
        logger.info(f"Fetching products from clan.com API (limit: {limit}, query: '{query}')")
        
        # Use real clan.com API data
        # Limit to 50 products for performance (individual API calls are slow)
        actual_limit = min(int(limit) if limit else 50, 50)
        result = clan_api.get_products(limit=actual_limit)
        
        if result.get('success', True):
            products = result.get('data', [])
            
            # Filter by query if provided
            if query:
                products = [p for p in products if query.lower() in p[0].lower()]
            
            # Transform products for UI
            transformed_products = [transform_product_for_ui(p) for p in products]
            logger.info(f"Successfully fetched {len(transformed_products)} products")
            return jsonify(transformed_products)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching products: {str(e)}")
        return jsonify([]), 500

@app.route('/api/categories/<int:category_id>/products')
def get_category_products(category_id):
    """Get products from a specific category"""
    try:
        logger.info(f"Fetching products for category {category_id}")
        
        # Get all products and filter by category
        result = clan_api.get_products()
        if result.get('success', True):
            products = result.get('data', [])
            
            # For now, return random products since category filtering isn't available
            import random
            if len(products) > 6:
                products = random.sample(products, 6)
            
            transformed_products = [transform_product_for_ui(p) for p in products]
            
            logger.info(f"Found {len(transformed_products)} products for category {category_id}")
            return jsonify(transformed_products)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching category products: {str(e)}")
        return jsonify([]), 500

@app.route('/api/products/<int:product_id>/related')
def get_related_products(product_id):
    """Get related products for a specific product"""
    try:
        logger.info(f"Fetching related products for product {product_id}")
        
        # Get products (no limit) and return random selection as related
        result = clan_api.get_products()
        if result.get('success', True):
            products = result.get('data', [])
            
            # Return random products as related
            import random
            if len(products) > 6:
                products = random.sample(products, 6)
            
            transformed_products = [transform_product_for_ui(p) for p in products]
            logger.info(f"Found {len(transformed_products)} related products")
            return jsonify(transformed_products)
        
        logger.error("Failed to fetch related products")
        return jsonify([]), 500
        
    except Exception as e:
        logger.error(f"Exception fetching related products: {str(e)}")
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=False)
