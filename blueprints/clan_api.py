# blueprints/clan_api.py
from flask import Blueprint, jsonify, request
import logging
import os
import sys

# Add the clan-api directory to the path to import clan_client
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-clan-api'))

try:
    from clan_client import ClanAPIClient
    from transformers import flatten_category_tree, transform_product_for_ui
except ImportError as e:
    logging.warning(f"Could not import clan_client: {e}")
    # Create dummy classes for when clan_client is not available
    class ClanAPIClient:
        def get_category_tree(self):
            return {'success': False, 'message': 'Clan API not available'}
        def get_products(self, limit=None, include_images=False):
            return {'success': False, 'message': 'Clan API not available'}
        def get_product(self, product_id):
            return {'success': False, 'message': 'Clan API not available'}
    
    def flatten_category_tree(categories):
        return []
    
    def transform_product_for_ui(product):
        return {}

bp = Blueprint('clan_api', __name__)
logger = logging.getLogger(__name__)

# Initialize clan API client
clan_api = ClanAPIClient()

@bp.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'service': 'clan-api',
        'status': 'running',
        'version': '1.0.0'
    })

@bp.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({'message': 'Test endpoint working'})

@bp.route('/api/test-product')
def test_single_product():
    """Test endpoint to get a single product with images and categories"""
    try:
        logger.info("Testing single product fetch from clan.com API")
        
        # Get a single product
        result = clan_api.get_product(1)  # Assuming product ID 1 exists
        
        if result.get('success', True):
            product = result.get('data')
            if product:
                transformed_product = transform_product_for_ui(product)
                logger.info("Successfully fetched test product")
                return jsonify(transformed_product)
            else:
                return jsonify({'error': 'No product data returned'}), 404
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify({'error': result.get('message', 'Unknown error')}), 500
            
    except Exception as e:
        logger.error(f"Exception fetching test product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/categories')
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

@bp.route('/api/products')
def get_products():
    """Get products from clan.com with optional search"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50)
        
        logger.info(f"Fetching products from clan.com API (limit: {limit}, query: '{query}')")
        
        # Use real clan.com API data
        # Get ALL products with real images
        actual_limit = int(limit) if limit and limit != 'None' else None
        result = clan_api.get_products(limit=actual_limit, include_images=True)
        
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

@bp.route('/api/products/<int:product_id>')
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        logger.info(f"Fetching product {product_id} from clan.com API")
        
        result = clan_api.get_product(product_id)
        
        if result.get('success', True):
            product = result.get('data')
            if product:
                transformed_product = transform_product_for_ui(product)
                logger.info(f"Successfully fetched product {product_id}")
                return jsonify(transformed_product)
            else:
                return jsonify({'error': 'Product not found'}), 404
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify({'error': result.get('message', 'Unknown error')}), 500
            
    except Exception as e:
        logger.error(f"Exception fetching product {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/products/<int:product_id>/related')
def get_related_products(product_id):
    """Get related products for a specific product"""
    try:
        logger.info(f"Fetching related products for product {product_id}")
        
        # For now, return a simple related products list
        # This could be enhanced with actual related product logic
        result = clan_api.get_products(limit=5, include_images=True)
        
        if result.get('success', True):
            products = result.get('data', [])
            # Filter out the current product
            related_products = [p for p in products if p[0] != product_id]
            transformed_products = [transform_product_for_ui(p) for p in related_products[:4]]  # Limit to 4 related products
            logger.info(f"Successfully fetched {len(transformed_products)} related products")
            return jsonify(transformed_products)
        else:
            logger.error(f"API error: {result.get('message', 'Unknown error')}")
            return jsonify([]), 500
            
    except Exception as e:
        logger.error(f"Exception fetching related products for {product_id}: {str(e)}")
        return jsonify([]), 500

@bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'clan-api'})