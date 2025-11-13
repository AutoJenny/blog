"""
Tag Browser Blueprint
Browse products by tags extracted from Product Type Identifiers
"""

from flask import Blueprint, render_template, request, jsonify
from config.database import db_manager
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('tag_browser', __name__, url_prefix='/tags')

def extract_all_tags(product_form_filter=None):
    """
    Extract all unique tags from product_type_data, organized by category.
    If product_form_filter is provided, only extract core_types for that form.
    Note: product_form_filter only affects core_type extraction, not other categories.
    
    Args:
        product_form_filter: Optional product form to filter core types by
        
    Returns:
        Dictionary with category -> list of tags with counts.
    """
    with db_manager.get_cursor() as cursor:
        # Always fetch all products (product_form_filter only affects which core_types we count)
        query = """
            SELECT product_type_data
            FROM clan_products
            WHERE product_type_data IS NOT NULL
        """
        cursor.execute(query)
        
        products = cursor.fetchall()
        
        # Organize tags by category
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
            
            # Identity & Classification
            # Only count core_type if product_form_filter matches (or no filter)
            if type_data.get('core_type'):
                # Check if product_form_filter applies
                if product_form_filter:
                    product_form = None
                    if type_data.get('disambiguation') and isinstance(type_data['disambiguation'], dict):
                        product_form = type_data['disambiguation'].get('product_form')
                    # Only count if product form matches filter
                    if product_form == product_form_filter:
                        core_type = type_data['core_type']
                        tags['identity_classification']['core_type'][core_type] = \
                            tags['identity_classification']['core_type'].get(core_type, 0) + 1
                else:
                    # No filter, count all core types
                    core_type = type_data['core_type']
                    tags['identity_classification']['core_type'][core_type] = \
                        tags['identity_classification']['core_type'].get(core_type, 0) + 1
            
            if type_data.get('subtype'):
                subtype = type_data['subtype']
                tags['identity_classification']['subtype'][subtype] = \
                    tags['identity_classification']['subtype'].get(subtype, 0) + 1
            
            # Always extract product_form (to show all forms even when filtering)
            if type_data.get('disambiguation') and isinstance(type_data['disambiguation'], dict):
                product_form = type_data['disambiguation'].get('product_form')
                if product_form:
                    tags['identity_classification']['product_form'][product_form] = \
                        tags['identity_classification']['product_form'].get(product_form, 0) + 1
            
            # Physical Attributes
            if type_data.get('materials'):
                materials = type_data['materials']
                if isinstance(materials, list) and len(materials) > 0:
                    for material in materials:
                        if material:
                            tags['physical_attributes']['materials'][material] = \
                                tags['physical_attributes']['materials'].get(material, 0) + 1
            
            # Track products with no materials (for missing materials indicator)
            if not type_data.get('materials') or not isinstance(type_data.get('materials'), list) or len(type_data.get('materials', [])) == 0:
                tags['physical_attributes']['materials']['__missing__'] = \
                    tags['physical_attributes']['materials'].get('__missing__', 0) + 1
            
            if type_data.get('patterns'):
                patterns = type_data['patterns']
                if isinstance(patterns, list):
                    for pattern in patterns:
                        if pattern:
                            tags['physical_attributes']['patterns'][pattern] = \
                                tags['physical_attributes']['patterns'].get(pattern, 0) + 1
            
            if type_data.get('decorations'):
                decorations = type_data['decorations']
                if isinstance(decorations, list):
                    for decoration in decorations:
                        if decoration:
                            tags['physical_attributes']['decorations'][decoration] = \
                                tags['physical_attributes']['decorations'].get(decoration, 0) + 1
            
            # Usage Context
            if type_data.get('occasions'):
                occasions = type_data['occasions']
                if isinstance(occasions, list):
                    for occasion in occasions:
                        if occasion:
                            tags['usage_context']['occasions'][occasion] = \
                                tags['usage_context']['occasions'].get(occasion, 0) + 1
            
            if type_data.get('styles'):
                styles = type_data['styles']
                if isinstance(styles, list):
                    for style in styles:
                        if style:
                            tags['usage_context']['styles'][style] = \
                                tags['usage_context']['styles'].get(style, 0) + 1
        
        # Convert to sorted lists
        result = {}
        for category, subcategories in tags.items():
            result[category] = {}
            for subcat, tag_dict in subcategories.items():
                # Special handling for materials: put __missing__ at the end
                if subcat == 'materials' and '__missing__' in tag_dict:
                    missing_count = tag_dict.pop('__missing__')
                    # Sort by count descending, then alphabetically
                    sorted_tags = sorted(
                        tag_dict.items(),
                        key=lambda x: (-x[1], x[0])
                    )
                    # Add missing at the end
                    sorted_tags.append(('__missing__', missing_count))
                else:
                    # Sort by count descending, then alphabetically
                    sorted_tags = sorted(
                        tag_dict.items(),
                        key=lambda x: (-x[1], x[0])
                    )
                
                result[category][subcat] = [
                    {'tag': tag, 'count': count}
                    for tag, count in sorted_tags
                ]
        
        return result

def get_products_by_tag(tag_category, tag_name):
    """
    Get products that have a specific tag.
    
    Args:
        tag_category: Category of tag (e.g., 'materials', 'core_type')
        tag_name: Name of the tag
        
    Returns:
        List of product dictionaries
    """
    with db_manager.get_cursor() as cursor:
        # Build query based on tag category
        if tag_category == 'core_type':
            query = """
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE product_type_data->>'core_type' = %s
                ORDER BY name
            """
        elif tag_category == 'subtype':
            query = """
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE product_type_data->>'subtype' = %s
                ORDER BY name
            """
        elif tag_category == 'product_form':
            query = """
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = %s
                ORDER BY name
            """
        elif tag_category == 'materials' and tag_name == '__missing__':
            # Special case: products with no materials
            query = """
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE product_type_data IS NOT NULL
                  AND (
                      product_type_data->'materials' IS NULL
                      OR product_type_data->'materials' = '[]'::jsonb
                      OR jsonb_array_length(product_type_data->'materials') = 0
                  )
                ORDER BY name
            """
            tag_name = None  # Not used in query
        elif tag_category in ['materials', 'patterns', 'decorations', 'occasions', 'styles']:
            # For JSONB arrays, check if the array contains the tag
            query = f"""
                SELECT id, name, sku, image_url, price, url
                FROM clan_products
                WHERE product_type_data->'{tag_category}' @> %s::jsonb
                ORDER BY name
            """
            # Wrap tag_name in a JSON array for containment check
            tag_name = json.dumps([tag_name])
        else:
            return []
        
        if tag_name is None:
            # For missing materials query, no parameter needed
            cursor.execute(query)
        else:
            cursor.execute(query, (tag_name,))
        products = cursor.fetchall()
        
        return [dict(p) for p in products]

@bp.route('/browser')
def browser():
    """Tag Browser main page"""
    tag_category = request.args.get('category')  # e.g., 'materials', 'core_type'
    tag_name = request.args.get('tag')  # e.g., 'pewter', 'kilt'
    product_form_filter = request.args.get('product_form')  # Filter core types by product form
    
    # Extract all tags (with optional product_form filter for core types)
    all_tags = extract_all_tags(product_form_filter=product_form_filter)
    
    # If filtering by product_form, don't show products, just filtered core types
    # If filtering by other tag, get products
    products = []
    if tag_category and tag_name and tag_category != 'product_form':
        products = get_products_by_tag(tag_category, tag_name)
    
    return render_template('tags/browser.html',
                         all_tags=all_tags,
                         selected_category=tag_category,
                         selected_tag=tag_name,
                         product_form_filter=product_form_filter,
                         products=products)

@bp.route('/api/products')
def api_products():
    """Get products filtered by tag"""
    tag_category = request.args.get('category')
    tag_name = request.args.get('tag')
    
    if not tag_category or not tag_name:
        return jsonify({
            'success': False,
            'error': 'Category and tag are required'
        }), 400
    
    try:
        products = get_products_by_tag(tag_category, tag_name)
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
    except Exception as e:
        logger.error(f"Error fetching products by tag: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

