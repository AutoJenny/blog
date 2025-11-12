"""
Product Browser Blueprint
Standalone product browsing and review interface
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
from utils.content_generation.clan_data_extractor import ClanDataExtractor
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('product_browser', __name__, url_prefix='/products')

@bp.route('/browser')
def browser():
    """Product Browser main page"""
    product_id = request.args.get('product_id', type=int)
    product_data = None
    validation = None
    
    if product_id:
        try:
            extractor = ClanDataExtractor()
            product_data = extractor.extract_product_data(product_id)
            validation = extractor.validate_data_completeness(product_data)
        except Exception as e:
            logger.error(f"Error loading product {product_id}: {e}")
            return render_template('products/browser.html',
                                 error=f"Error loading product: {str(e)}")
    
    return render_template('products/browser.html',
                         product_data=product_data,
                         validation=validation,
                         current_product_id=product_id)

@bp.route('/api/list')
def api_list():
    """Get list of all products for navigation"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, sku
                FROM clan_products
                ORDER BY id
            """)
            products = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'products': [dict(p) for p in products]
            })
    except Exception as e:
        logger.error(f"Error fetching product list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/<int:product_id>/full')
def api_product_full(product_id):
    """Get full product data with validation"""
    try:
        import json as json_lib
        from datetime import datetime
        
        extractor = ClanDataExtractor()
        product_data = extractor.extract_product_data(product_id)
        validation = extractor.validate_data_completeness(product_data)
        
        # Convert to JSON-serializable format
        def make_serializable(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return make_serializable(obj.__dict__)
            else:
                return obj
        
        serializable_product_data = make_serializable(product_data)
        serializable_validation = make_serializable(validation)
        
        return jsonify({
            'success': True,
            'product_data': serializable_product_data,
            'validation': serializable_validation
        })
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/search')
def api_search():
    """Search products by name, SKU, or producer"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({
            'success': True,
            'products': []
        })
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, sku, supplier_name
                FROM clan_products
                WHERE LOWER(name) LIKE %s
                   OR LOWER(sku) LIKE %s
                   OR LOWER(supplier_name) LIKE %s
                ORDER BY name
                LIMIT 20
            """, (f'%{query.lower()}%', f'%{query.lower()}%', f'%{query.lower()}%'))
            
            products = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'products': [dict(p) for p in products]
            })
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/<int:product_id>/next')
def api_next_product(product_id):
    """Get next product ID (by ID or name)"""
    nav_mode = request.args.get('mode', 'id')  # 'id' or 'name'
    direction = request.args.get('direction', 'next')  # 'next' or 'prev'
    
    try:
        with db_manager.get_cursor() as cursor:
            if nav_mode == 'id':
                if direction == 'next':
                    cursor.execute("""
                        SELECT id FROM clan_products
                        WHERE id > %s
                        ORDER BY id ASC
                        LIMIT 1
                    """, (product_id,))
                else:
                    cursor.execute("""
                        SELECT id FROM clan_products
                        WHERE id < %s
                        ORDER BY id DESC
                        LIMIT 1
                    """, (product_id,))
            else:  # name
                # Get current product name
                cursor.execute("SELECT name FROM clan_products WHERE id = %s", (product_id,))
                current = cursor.fetchone()
                if not current:
                    return jsonify({'success': False, 'error': 'Product not found'}), 404
                
                current_name = current['name']
                
                if direction == 'next':
                    cursor.execute("""
                        SELECT id FROM clan_products
                        WHERE name > %s
                        ORDER BY name ASC
                        LIMIT 1
                    """, (current_name,))
                else:
                    cursor.execute("""
                        SELECT id FROM clan_products
                        WHERE name < %s
                        ORDER BY name DESC
                        LIMIT 1
                    """, (current_name,))
            
            result = cursor.fetchone()
            if result:
                return jsonify({
                    'success': True,
                    'product_id': result['id']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No more products'
                })
    except Exception as e:
        logger.error(f"Error finding next product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

