# blueprints/settings.py
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging
import json

bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Settings interface."""
    return render_template('settings/index.html')

@bp.route('/taxonomy')
def taxonomy():
    """Taxonomy viewing page - hierarchical display of taxonomy system."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get all tiers
            cursor.execute("""
                SELECT id, name, display_name, description
                FROM taxonomy_tier
                ORDER BY id
            """)
            tiers = list(cursor.fetchall())
            
            # Get all items with parent information
            cursor.execute("""
                SELECT ti.id, ti.tier_id, ti.parent_id, ti.slug, ti.display_name,
                       ti.description, ti.common_assets, ti.display_order, ti.is_active,
                       ti.illustration_method,
                       tt.name as tier_name, tt.display_name as tier_display_name,
                       parent.display_name as parent_display_name,
                       parent.slug as parent_slug
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                LEFT JOIN taxonomy_item parent ON ti.parent_id = parent.id
                WHERE ti.is_active = TRUE
                ORDER BY ti.tier_id, ti.display_order, ti.display_name
            """)
            items = list(cursor.fetchall())
            
            # Organize items by tier and hierarchy
            organized_data = {}
            for tier in tiers:
                tier_items = [item for item in items if item['tier_id'] == tier['id']]
                
                if tier['name'] == 'category':
                    # Categories have no parents, list them directly
                    organized_data[tier['name']] = {
                        'tier': tier,
                        'items': sorted(tier_items, key=lambda x: x.get('display_order', 0))
                    }
                elif tier['name'] == 'content_type':
                    # Content types have parent categories - group by parent
                    content_by_theme = {}
                    for item in tier_items:
                        parent_slug = item.get('parent_slug') or 'unassigned'
                        if parent_slug not in content_by_theme:
                            content_by_theme[parent_slug] = {
                                'parent_name': item.get('parent_display_name') or 'Unassigned',
                                'items': []
                            }
                        content_by_theme[parent_slug]['items'].append(item)
                    # Sort items within each theme
                    for theme_slug in content_by_theme:
                        content_by_theme[theme_slug]['items'].sort(key=lambda x: x.get('display_order', 0))
                    organized_data[tier['name']] = {
                        'tier': tier,
                        'by_category': content_by_theme
                    }
                else:
                    # Formats have no parents
                    organized_data[tier['name']] = {
                        'tier': tier,
                        'items': sorted(tier_items, key=lambda x: x.get('display_order', 0))
                    }
            
            return render_template('settings/taxonomy.html', taxonomy_data=organized_data)
            
    except Exception as e:
        logger.error(f"Error loading taxonomy data: {e}", exc_info=True)
        return render_template('settings/taxonomy.html', 
                             taxonomy_data={}, 
                             error=str(e))

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "settings"})
