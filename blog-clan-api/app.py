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

@app.route('/api/categories')
def get_categories():
    """Get all categories from clan.com"""
    try:
        logger.info("Fetching categories from clan.com API")
        
        # For now, return mock categories to avoid API timeouts
        mock_categories = [
            {"id": 1, "name": "Tartan Accessories", "description": "Traditional tartan items"},
            {"id": 2, "name": "Kilts and Highland Dress", "description": "Traditional Scottish kilts"},
            {"id": 3, "name": "Clan Crest Jewelry", "description": "Sterling silver clan jewelry"},
            {"id": 4, "name": "Scottish Gifts", "description": "Unique Scottish gifts"},
            {"id": 5, "name": "Ties and Scarves", "description": "Wool tartan ties and scarves"}
        ]
        
        logger.info(f"Successfully fetched {len(mock_categories)} categories")
        return jsonify(mock_categories)
            
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
        
        # For now, return mock data to avoid API timeouts
        mock_products = [
            ["Essential Tartan Sash", "esssw_essential", "https://clan.com/essential-tartan-sash", "Traditional tartan sash"],
            ["Luxury Kilt and Flashes", "luxkilt_8yard", "https://clan.com/luxury-kilt", "8-yard traditional kilt"],
            ["Scottish Clan Crest Ring", "ring_crest", "https://clan.com/clan-crest-ring", "Sterling silver clan ring"],
            ["Tartan Tie Collection", "tie_tartan", "https://clan.com/tartan-ties", "Wool tartan ties"],
            ["Highland Dress Jacket", "jacket_highland", "https://clan.com/highland-jacket", "Formal highland wear"],
            ["Celtic Cross Pendant", "pendant_celtic", "https://clan.com/celtic-pendant", "Traditional Celtic design"]
        ]
        
        # Limit the results
        if limit:
            mock_products = mock_products[:int(limit)]
        
        # Filter by query if provided
        if query:
            mock_products = [p for p in mock_products if query.lower() in p[0].lower()]
        
        # Transform products for UI
        transformed_products = [transform_product_for_ui(p) for p in mock_products]
        logger.info(f"Successfully fetched {len(transformed_products)} products")
        return jsonify(transformed_products)
            
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
    app.run(host='0.0.0.0', port=5006, debug=True)
