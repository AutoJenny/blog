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

@bp.route('/api/tags/filtered')
def api_filtered_tags():
    """Get tags filtered by product_form, core_type, subtype with dynamic counts"""
    product_form = request.args.get('product_form')
    core_type = request.args.get('core_type')
    subtype = request.args.get('subtype')
    
    try:
        with db_manager.get_cursor() as cursor:
            # Build WHERE clause based on filters
            where_conditions = ["product_type_data IS NOT NULL"]
            params = []
            
            if product_form:
                where_conditions.append("product_type_data->'disambiguation'->>'product_form' = %s")
                params.append(product_form)
            
            if core_type:
                where_conditions.append("product_type_data->>'core_type' = %s")
                params.append(core_type)
            
            if subtype:
                where_conditions.append("product_type_data->>'subtype' = %s")
                params.append(subtype)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get all matching products
            cursor.execute(f"""
                SELECT product_type_data
                FROM clan_products
                WHERE {where_clause}
            """, tuple(params))
            
            products = cursor.fetchall()
            
            # Count tags in filtered products
            tags = {
                'identity_classification': {
                    'core_type': {},
                    'subtype': {},
                    'product_form': {}
                },
                'physical_attributes': {
                    'materials': {},
                    'patterns': {},
                    'decorations': {}
                },
                'usage_context': {
                    'occasions': {},
                    'styles': {}
                }
            }
            
            for product in products:
                type_data = product.get('product_type_data')
                if not type_data:
                    continue
                
                # Only count core_type if product_form matches (or no product_form filter)
                if type_data.get('core_type'):
                    if not product_form or (type_data.get('disambiguation') and isinstance(type_data['disambiguation'], dict) and type_data['disambiguation'].get('product_form') == product_form):
                        core_type_val = type_data['core_type']
                        tags['identity_classification']['core_type'][core_type_val] = \
                            tags['identity_classification']['core_type'].get(core_type_val, 0) + 1
                
                # Only count subtype if core_type matches (or no core_type filter)
                if type_data.get('subtype'):
                    if not core_type or type_data.get('core_type') == core_type:
                        subtype_val = type_data['subtype']
                        tags['identity_classification']['subtype'][subtype_val] = \
                            tags['identity_classification']['subtype'].get(subtype_val, 0) + 1
                
                # Always count product_form
                if type_data.get('disambiguation') and isinstance(type_data['disambiguation'], dict):
                    product_form_val = type_data['disambiguation'].get('product_form')
                    if product_form_val:
                        tags['identity_classification']['product_form'][product_form_val] = \
                            tags['identity_classification']['product_form'].get(product_form_val, 0) + 1
                
                # Count materials, patterns, decorations, occasions, styles
                for tag_type in ['materials', 'patterns', 'decorations', 'occasions', 'styles']:
                    if type_data.get(tag_type):
                        tag_list = type_data[tag_type]
                        if isinstance(tag_list, list):
                            for tag_val in tag_list:
                                if tag_val:
                                    category = 'physical_attributes' if tag_type in ['materials', 'patterns', 'decorations'] else 'usage_context'
                                    tags[category][tag_type][tag_val] = tags[category][tag_type].get(tag_val, 0) + 1
                
                # Track missing materials
                if not type_data.get('materials') or not isinstance(type_data.get('materials'), list) or len(type_data.get('materials', [])) == 0:
                    tags['physical_attributes']['materials']['__missing__'] = \
                        tags['physical_attributes']['materials'].get('__missing__', 0) + 1
            
            # Convert to sorted lists
            result = {}
            for category, subcategories in tags.items():
                result[category] = {}
                for subcat, tag_dict in subcategories.items():
                    if subcat == 'materials' and '__missing__' in tag_dict:
                        missing_count = tag_dict.pop('__missing__')
                        sorted_tags = sorted(
                            tag_dict.items(),
                            key=lambda x: (-x[1], x[0])
                        )
                        sorted_tags.append(('__missing__', missing_count))
                    else:
                        sorted_tags = sorted(
                            tag_dict.items(),
                            key=lambda x: (-x[1], x[0])
                        )
                    
                    result[category][subcat] = [
                        {'tag': tag, 'count': count}
                        for tag, count in sorted_tags
                    ]
            
            return jsonify({
                'success': True,
                'tags': result
            })
    except Exception as e:
        logger.error(f"Error fetching filtered tags: {e}")
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
            
            # Build tree structure with paths
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
    """Search products for tag editor with pagination and optional category/tag filters"""
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    
    # Get tag filters from query parameters
    tag_filters = {}
    i = 1
    while True:
        cat_key = f'tag_category_{i}'
        val_key = f'tag_value_{i}'
        if cat_key in request.args and val_key in request.args:
            tag_filters[request.args.get(cat_key)] = request.args.get(val_key)
            i += 1
        else:
            break
    
    # Allow category/tag-only filtering (query can be '*' or empty if filters are provided)
    if not query or (len(query) < 2 and query != '*'):
        if category_id or tag_filters:
            # Category/tag-only filtering - allow it
            query = '*'
        elif query == '*':
            # Explicit '*' means get all products
            pass
        else:
            return jsonify({
                'success': False,
                'error': 'Query must be at least 2 characters, or use "*" for all products, or provide a category_id or tag filter'
            }), 400
    
    try:
        with db_manager.get_cursor() as cursor:
            # Build WHERE clause
            where_conditions = []
            params = []
            
            # If query is not '*', add search conditions
            if query != '*':
                search_pattern = f'%{query}%'
                where_conditions.extend([
                    "name ILIKE %s",
                    "sku ILIKE %s"
                ])
                params.extend([search_pattern, search_pattern])
            
            # Add category filter if provided
            if category_id:
                where_conditions.append("category_ids @> %s::jsonb")
                params.append(json.dumps([category_id]))
            
            # Add tag filters
            for tag_category, tag_value in tag_filters.items():
                if tag_category == 'product_form':
                    where_conditions.append("product_type_data->'disambiguation'->>'product_form' = %s")
                    params.append(tag_value)
                elif tag_category == 'core_type':
                    where_conditions.append("product_type_data->>'core_type' = %s")
                    params.append(tag_value)
                elif tag_category == 'subtype':
                    where_conditions.append("product_type_data->>'subtype' = %s")
                    params.append(tag_value)
                elif tag_category in ['materials', 'patterns', 'decorations', 'occasions', 'styles']:
                    # For JSONB arrays, check if the array contains the tag
                    where_conditions.append(f"product_type_data->'{tag_category}' @> %s::jsonb")
                    params.append(json.dumps([tag_value]))
            
            # Build final WHERE clause - all conditions are ANDed together
            if len(where_conditions) == 0:
                where_clause = "1=1"  # No filters - get all products
            elif len(where_conditions) == 1:
                where_clause = where_conditions[0]
            else:
                # Combine text search with OR, then AND with other filters
                text_conditions = []
                other_conditions = []
                
                for i, condition in enumerate(where_conditions):
                    if query != '*' and i < 2:  # First two are text search
                        text_conditions.append(condition)
                    else:
                        other_conditions.append(condition)
                
                if text_conditions and other_conditions:
                    where_clause = f"({' OR '.join(text_conditions)}) AND {' AND '.join(other_conditions)}"
                elif text_conditions:
                    where_clause = ' OR '.join(text_conditions)
                else:
                    where_clause = ' AND '.join(other_conditions)
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM clan_products
                WHERE {where_clause}
            """, tuple(params))
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0
            
            # Get paginated results
            offset = (page - 1) * per_page
            params.append(per_page)
            params.append(offset)
            cursor.execute(f"""
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE {where_clause}
                ORDER BY name
                LIMIT %s OFFSET %s
            """, tuple(params))
            
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

@bp.route('/api/bulk-tags', methods=['POST'])
def api_bulk_tags():
    """Apply tags to a product (with add or replace mode)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        product_id = data.get('product_id')
        tags = data.get('tags', {})
        mode = data.get('mode', 'add')  # 'add' or 'replace'
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID required'
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
            
            # Merge or replace tags based on mode
            current_data = product['product_type_data'] or {}
            if not isinstance(current_data, dict):
                current_data = {}
            
            logger.info(f"Updating product {product_id}: mode={mode}, tags={tags}, current_data keys={list(current_data.keys())}")
            
            if mode == 'replace':
                # Replace mode: replace entire groups
                # For single-value tags, replace directly
                if 'disambiguation' in tags:
                    if not current_data.get('disambiguation'):
                        current_data['disambiguation'] = {}
                    current_data['disambiguation'].update(tags['disambiguation'])
                    # Remove if set to None
                    if current_data['disambiguation'].get('product_form') is None:
                        current_data['disambiguation'].pop('product_form', None)
                
                if 'core_type' in tags:
                    if tags['core_type']:
                        current_data['core_type'] = tags['core_type']
                    else:
                        current_data.pop('core_type', None)
                        current_data.pop('subtype', None)  # Clear subtype if core_type removed
                
                if 'subtype' in tags:
                    if tags['subtype']:
                        current_data['subtype'] = tags['subtype']
                    else:
                        current_data.pop('subtype', None)
                
                # For array tags, replace the entire array
                for tag_type in ['materials', 'patterns', 'decorations', 'occasions', 'styles']:
                    if tag_type in tags:
                        if tags[tag_type] and len(tags[tag_type]) > 0:
                            current_data[tag_type] = tags[tag_type]
                        else:
                            current_data.pop(tag_type, None)
            
            else:  # mode == 'add'
                # Add mode: merge with existing tags
                # For single-value tags, set them (overwrite if they exist)
                if 'disambiguation' in tags and tags['disambiguation']:
                    if not current_data.get('disambiguation'):
                        current_data['disambiguation'] = {}
                    if 'product_form' in tags['disambiguation'] and tags['disambiguation']['product_form']:
                        current_data['disambiguation']['product_form'] = tags['disambiguation']['product_form']
                
                if 'core_type' in tags and tags['core_type']:
                    # In add mode, we still overwrite core_type if provided
                    current_data['core_type'] = tags['core_type']
                
                if 'subtype' in tags and tags['subtype']:
                    # In add mode, we still overwrite subtype if provided
                    current_data['subtype'] = tags['subtype']
                
                # For array tags, merge arrays (avoid duplicates)
                for tag_type in ['materials', 'patterns', 'decorations', 'occasions', 'styles']:
                    if tag_type in tags and tags[tag_type]:
                        existing = current_data.get(tag_type, [])
                        if not isinstance(existing, list):
                            existing = []
                        # Merge and deduplicate
                        merged = list(set(existing + tags[tag_type]))
                        current_data[tag_type] = merged
            
            # Save updated product_type_data
            logger.info(f"Saving product {product_id}: new core_type={current_data.get('core_type')}, new product_form={current_data.get('disambiguation', {}).get('product_form')}")
            
            cursor.execute("""
                UPDATE clan_products
                SET product_type_data = %s
                WHERE id = %s
            """, (json.dumps(current_data), product_id))
            
            db_manager.get_connection().commit()
            
            # Verify the update
            cursor.execute("""
                SELECT product_type_data->>'core_type' as core_type,
                       product_type_data->'disambiguation'->>'product_form' as product_form
                FROM clan_products
                WHERE id = %s
            """, (product_id,))
            verify = cursor.fetchone()
            logger.info(f"Verified product {product_id}: core_type={verify.get('core_type')}, product_form={verify.get('product_form')}")
            
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

