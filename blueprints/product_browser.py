"""
Product Browser Blueprint
Standalone product browsing and review interface
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
from utils.content_generation.clan_data_extractor import ClanDataExtractor
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('product_browser', __name__, url_prefix='/products')

def get_category_breadcrumbs(category_id):
    """Build breadcrumb trail from category hierarchy"""
    if not category_id:
        return []
    
    with db_manager.get_cursor() as cursor:
        breadcrumbs = []
        current_id = category_id
        
        # Walk up the hierarchy
        while current_id:
            cursor.execute("""
                SELECT id, name, parent_id, level
                FROM clan_categories
                WHERE id = %s
            """, (current_id,))
            
            cat = cursor.fetchone()
            if not cat:
                break
            
            breadcrumbs.insert(0, {
                'id': cat['id'],
                'name': cat['name'],
                'level': cat.get('level', 0)
            })
            
            current_id = cat.get('parent_id')
        
        # Filter out root/system categories (level 0-1 typically)
        breadcrumbs = [b for b in breadcrumbs if b.get('level', 0) >= 2]
        
        return breadcrumbs

def get_product_category_routes(product_id):
    """
    Get all category routes for a product.
    Returns primary route (longest/deepest) and other routes.
    """
    with db_manager.get_cursor() as cursor:
        # Get product's category IDs
        cursor.execute("""
            SELECT category_ids FROM clan_products WHERE id = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        if not product or not product.get('category_ids'):
            return {'primary': [], 'others': []}
        
        category_ids = product['category_ids']
        if not isinstance(category_ids, list):
            return {'primary': [], 'others': []}
        
        # Build breadcrumbs for each category
        routes = []
        for cat_id in category_ids:
            breadcrumbs = get_category_breadcrumbs(cat_id)
            if breadcrumbs:
                routes.append(breadcrumbs)
        
        if not routes:
            return {'primary': [], 'others': []}
        
        # Primary route is the longest/deepest
        primary = max(routes, key=len)
        others = [r for r in routes if r != primary]
        
        return {'primary': primary, 'others': others}

@bp.route('/browser')
def browser():
    """Product Browser main page"""
    product_id = request.args.get('product_id', type=int)
    category_id = request.args.get('category_id', type=int)
    
    product_data = None
    validation = None
    category_routes = None
    
    if product_id:
        try:
            extractor = ClanDataExtractor()
            product_data = extractor.extract_product_data(product_id)
            validation = extractor.validate_data_completeness(product_data)
            category_routes = get_product_category_routes(product_id)
        except Exception as e:
            logger.error(f"Error loading product {product_id}: {e}")
            return render_template('products/browser.html',
                                 error=f"Error loading product: {str(e)}")
    
    # If viewing by category, get category data
    category_data = None
    category_products = []
    if category_id and not product_id:
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, parent_id, level, description
                    FROM clan_categories
                    WHERE id = %s
                """, (category_id,))
                category_data = cursor.fetchone()
                
                if category_data:
                    # Get products in this category
                    # category_ids is a JSONB array, so we need to check if it contains the category_id
                    cursor.execute("""
                        SELECT id, name, sku
                        FROM clan_products
                        WHERE category_ids @> %s::jsonb
                        ORDER BY name
                        LIMIT 50
                    """, (json.dumps([category_id]),))
                    category_products = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error loading category {category_id}: {e}")
    
    return render_template('products/browser.html',
                         product_data=product_data,
                         validation=validation,
                         category_routes=category_routes,
                         category_data=category_data,
                         category_products=category_products,
                         current_product_id=product_id,
                         current_category_id=category_id)

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

@bp.route('/api/categories/tree')
def api_categories_tree():
    """Get category tree for filtering"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all categories including level 1 (top level)
            cursor.execute("""
                SELECT id, name, parent_id, level
                FROM clan_categories
                WHERE level >= 1
                ORDER BY level, name
            """)
            
            categories = cursor.fetchall()
            
            # Build tree structure
            category_dict = {cat['id']: dict(cat) for cat in categories}
            tree = []
            
            # Build paths for each category
            for cat in categories:
                path = []
                current_id = cat['id']
                visited = set()
                
                while current_id and current_id not in visited:
                    visited.add(current_id)
                    if current_id in category_dict:
                        cat_data = category_dict[current_id]
                        path.insert(0, cat_data['name'])
                        current_id = cat_data.get('parent_id')
                    else:
                        break
                
                tree.append({
                    'id': cat['id'],
                    'name': cat['name'],
                    'level': cat.get('level', 0),
                    'path': ' > '.join(path),
                    'parent_id': cat.get('parent_id')
                })
            
            return jsonify({
                'success': True,
                'categories': tree
            })
    except Exception as e:
        logger.error(f"Error fetching category tree: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/search')
def api_search():
    """Search products by name, SKU, or producer, optionally filtered by category"""
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    
    if not query or len(query) < 2:
        return jsonify({
            'success': True,
            'products': []
        })
    
    try:
        with db_manager.get_cursor() as cursor:
            # Build base query
            base_conditions = [
                "LOWER(name) LIKE %s",
                "LOWER(sku) LIKE %s",
                "LOWER(supplier_name) LIKE %s"
            ]
            params = [f'%{query.lower()}%', f'%{query.lower()}%', f'%{query.lower()}%']
            
            # Add category filter if provided
            if category_id:
                base_conditions.append("category_ids @> %s::jsonb")
                params.append(json.dumps([category_id]))
            
            where_clause = " OR ".join(base_conditions[:3])
            if category_id:
                where_clause = f"({where_clause}) AND {base_conditions[3]}"
            
            cursor.execute(f"""
                SELECT id, name, sku, supplier_name
                FROM clan_products
                WHERE {where_clause}
                ORDER BY name
                LIMIT 20
            """, tuple(params))
            
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

@bp.route('/api/<int:product_id>/tags', methods=['POST'])
def api_update_tags(product_id):
    """Update product tags"""
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No update data provided'
            }), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current product_type_data
            cursor.execute("""
                SELECT product_type_data
                FROM clan_products
                WHERE id = %s
            """, (product_id,))
            
            product = cursor.fetchone()
            if not product:
                return jsonify({
                    'success': False,
                    'error': 'Product not found'
                }), 404
            
            # Merge update data into existing product_type_data
            current_data = product['product_type_data'] or {}
            if not isinstance(current_data, dict):
                current_data = {}
            
            # Update disambiguation (product_form)
            if 'disambiguation' in update_data:
                if not current_data.get('disambiguation'):
                    current_data['disambiguation'] = {}
                current_data['disambiguation'].update(update_data['disambiguation'])
                # Remove product_form if set to None
                if current_data['disambiguation'].get('product_form') is None:
                    current_data['disambiguation'].pop('product_form', None)
            
            # Update core_type
            if 'core_type' in update_data:
                if update_data['core_type']:
                    current_data['core_type'] = update_data['core_type']
                else:
                    current_data.pop('core_type', None)
            
            # Update subtype
            if 'subtype' in update_data:
                if update_data['subtype']:
                    current_data['subtype'] = update_data['subtype']
                else:
                    current_data.pop('subtype', None)
            
            # Update array-based tags
            for tag_type in ['materials', 'patterns', 'decorations', 'occasions', 'styles']:
                if tag_type in update_data:
                    if update_data[tag_type] and len(update_data[tag_type]) > 0:
                        current_data[tag_type] = update_data[tag_type]
                    else:
                        current_data.pop(tag_type, None)
            
            # Save updated product_type_data
            cursor.execute("""
                UPDATE clan_products
                SET product_type_data = %s
                WHERE id = %s
            """, (json.dumps(current_data), product_id))
            
            db_manager.get_connection().commit()
            
            return jsonify({
                'success': True,
                'message': 'Tags updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating tags for product {product_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

