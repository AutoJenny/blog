"""
Product Tag Editor Blueprint
Bulk tag editing interface for products
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('product_tag_editor', __name__, url_prefix='/products/tag-editor')

@bp.route('')
def editor():
    """Product Tag Editor main page"""
    return render_template('products/tag_editor.html')

@bp.route('/api/search')
def api_search():
    """Search products for tag editor with pagination"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'error': 'Query must be at least 2 characters'
        }), 400
    
    try:
        with db_manager.get_cursor() as cursor:
            # Search by name, SKU, or producer
            search_pattern = f'%{query}%'
            
            # Get total count
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM clan_products
                WHERE name ILIKE %s
                   OR sku ILIKE %s
            """, (search_pattern, search_pattern))
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0
            
            # Get paginated results
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE name ILIKE %s
                   OR sku ILIKE %s
                ORDER BY name
                LIMIT %s OFFSET %s
            """, (search_pattern, search_pattern, per_page, offset))
            
            products = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'products': [dict(p) for p in products],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/products')
def api_products():
    """Get products by IDs (for displaying selected products)"""
    product_ids = request.args.getlist('ids')
    
    if not product_ids:
        return jsonify({
            'success': False,
            'error': 'No product IDs provided'
        }), 400
    
    try:
        with db_manager.get_cursor() as cursor:
            # Convert string IDs to integers
            ids = [int(id) for id in product_ids if id.isdigit()]
            
            if not ids:
                return jsonify({
                    'success': True,
                    'products': []
                })
            
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(f"""
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE id IN ({placeholders})
                ORDER BY name
            """, tuple(ids))
            
            products = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'products': [dict(p) for p in products]
            })
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

