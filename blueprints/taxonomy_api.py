"""
Taxonomy API Module

Provides endpoints for managing and querying the taxonomy system
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('taxonomy_api', __name__, url_prefix='/api/taxonomy')

@bp.route('/tiers', methods=['GET'])
def get_tiers():
    """Get all taxonomy tiers"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, display_name, description, created_at, updated_at
                FROM taxonomy_tier
                ORDER BY id
            """)
            tiers = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'tiers': tiers
            })
    except Exception as e:
        logger.error(f"Error fetching taxonomy tiers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/items', methods=['GET'])
def get_items():
    """Get taxonomy items, optionally filtered by tier"""
    try:
        tier = request.args.get('tier')  # 'category', 'content_type', or 'format'
        theme_id = request.args.get('theme_id', type=int)
        
        with db_manager.get_cursor() as cursor:
            if theme_id:
                # Get content types for a specific theme
                cursor.execute("""
                    SELECT ti.id, ti.tier_id, ti.parent_id, ti.slug, ti.display_name,
                           ti.description, ti.common_assets, ti.display_order, ti.is_active
                    FROM taxonomy_item ti
                    JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                    WHERE tt.name = 'content_type' AND ti.parent_id = %s AND ti.is_active = TRUE
                    ORDER BY ti.display_order, ti.display_name
                """, (theme_id,))
            elif tier:
                # Get items for a specific tier
                cursor.execute("""
                    SELECT ti.id, ti.tier_id, ti.parent_id, ti.slug, ti.display_name,
                           ti.description, ti.common_assets, ti.display_order, ti.is_active
                    FROM taxonomy_item ti
                    JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                    WHERE tt.name = %s AND ti.is_active = TRUE
                    ORDER BY ti.display_order, ti.display_name
                """, (tier,))
            else:
                # Get all items
                cursor.execute("""
                    SELECT ti.id, ti.tier_id, ti.parent_id, ti.slug, ti.display_name,
                           ti.description, ti.common_assets, ti.display_order, ti.is_active,
                           tt.name as tier_name
                    FROM taxonomy_item ti
                    JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                    WHERE ti.is_active = TRUE
                    ORDER BY ti.tier_id, ti.display_order, ti.display_name
                """)
            
            items = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'items': items
            })
    except Exception as e:
        logger.error(f"Error fetching taxonomy items: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a single taxonomy item with full details"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ti.id, ti.tier_id, ti.parent_id, ti.slug, ti.display_name,
                       ti.description, ti.common_assets, ti.display_order, ti.is_active,
                       tt.name as tier_name, tt.display_name as tier_display_name,
                       parent.display_name as parent_display_name
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                LEFT JOIN taxonomy_item parent ON ti.parent_id = parent.id
                WHERE ti.id = %s
            """, (item_id,))
            
            item = cursor.fetchone()
            
            if not item:
                return jsonify({'success': False, 'error': 'Taxonomy item not found'}), 404
            
            return jsonify({
                'success': True,
                'item': item
            })
    except Exception as e:
        logger.error(f"Error fetching taxonomy item: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/content-types', methods=['GET'])
def get_content_types_by_theme():
    """Get content types filtered by theme_id"""
    theme_id = request.args.get('theme_id', type=int)
    
    if not theme_id:
        return jsonify({'success': False, 'error': 'theme_id parameter required'}), 400
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ti.id, ti.slug, ti.display_name, ti.description, ti.common_assets, ti.display_order
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                WHERE tt.name = 'content_type' AND ti.parent_id = %s AND ti.is_active = TRUE
                ORDER BY ti.display_order, ti.display_name
            """, (theme_id,))
            
            content_types = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'content_types': content_types
            })
    except Exception as e:
        logger.error(f"Error fetching content types by theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

