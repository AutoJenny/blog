# blueprints/launchpad/publishing_validation.py
"""Publishing validation routes and functionality."""

from flask import Blueprint, jsonify
import logging
from config.database import db_manager
from blueprints.launchpad.publishing_helpers import (
    get_post_with_development,
    get_post_sections_with_images
)

bp = Blueprint("publishing_validation", __name__)
logger = logging.getLogger(__name__)


@bp.route('/api/validate-publish/<int:post_id>')
def validate_publish_data(post_id):
    """Validate publish data consistency and completeness."""
    try:
        # Get post and sections
        post = get_post_with_development(post_id)
        if not post:
            return jsonify({'error': 'Post not found', 'valid': False}), 404
        
        sections = get_post_sections_with_images(post_id)
        
        # Check for required data
        issues = []
        
        # Check required fields
        required_fields = ['title', 'meta_title', 'meta_description', 'meta_tags']
        for field in required_fields:
            if not post.get(field):
                issues.append({
                    'type': 'missing_field',
                    'field': field
                })
        
        # Check taxonomy fields (required for publishing)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT theme_id, content_type_id, format_id
                FROM post
                WHERE id = %s
            """, (post_id,))
            taxonomy_check = cursor.fetchone()
            
            if not taxonomy_check or not taxonomy_check.get('theme_id'):
                issues.append({
                    'type': 'missing_taxonomy',
                    'field': 'theme_id',
                    'message': 'Post must have a theme assigned. Please assign taxonomy in Planning stage.'
                })
            if not taxonomy_check or not taxonomy_check.get('content_type_id'):
                issues.append({
                    'type': 'missing_taxonomy',
                    'field': 'content_type_id',
                    'message': 'Post must have a content type assigned. Please assign taxonomy in Planning stage.'
                })
            if not taxonomy_check or not taxonomy_check.get('format_id'):
                issues.append({
                    'type': 'missing_taxonomy',
                    'field': 'format_id',
                    'message': 'Post must have a format assigned. Please assign taxonomy in Planning stage.'
                })
        
        # Check meta_image points to optimized path
        meta_image = post.get('meta_image', '')
        if meta_image and '/raw/' in meta_image:
            issues.append({
                'type': 'raw_image_path',
                'field': 'meta_image',
                'path': meta_image
            })
        elif meta_image and '.png' in meta_image and '/optimized/' in meta_image:
            issues.append({
                'type': 'png_in_optimized',
                'field': 'meta_image',
                'path': meta_image
            })
        
        # Check for sections with content
        if not sections or len(sections) == 0:
            issues.append({
                'type': 'no_sections',
                'message': 'Post has no sections'
            })
        
        # Check images use optimized paths
        for section in sections:
            img = section.get('image')
            if img and img.get('path'):
                path = img['path']
                if '/raw/' in path or path.endswith('.png'):
                    issues.append({
                        'type': 'raw_section_image',
                        'section_id': section['id'],
                        'section_heading': section.get('section_heading'),
                        'path': path
                    })
        
        # Ensure cross-promotion data is attached (and auto-select if desired fields are missing)
        try:
            # Load existing cross-promo fields from DB
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cross_promotion_category_id, cross_promotion_category_title,
                           cross_promotion_product_id, cross_promotion_product_title,
                           cross_promotion_category_position, cross_promotion_product_position,
                           cross_promotion_category_widget_html, cross_promotion_product_widget_html
                    FROM post WHERE id = %s
                """, (post_id,))
                cp = cursor.fetchone() or {}

                # Attach to post for validation context
                post['cross_promotion'] = {
                    'category_id': cp.get('cross_promotion_category_id'),
                    'category_title': cp.get('cross_promotion_category_title'),
                    'product_id': cp.get('cross_promotion_product_id'),
                    'product_title': cp.get('cross_promotion_product_title'),
                    'category_position': cp.get('cross_promotion_category_position'),
                    'product_position': cp.get('cross_promotion_product_position'),
                    'category_widget_html': cp.get('cross_promotion_category_widget_html'),
                    'product_widget_html': cp.get('cross_promotion_product_widget_html')
                }

                # If nothing configured, opportunistically auto-select to avoid blocking publish
                need_persist = False
                if not post['cross_promotion'].get('category_id'):
                    cursor.execute("SELECT id, name FROM clan_categories ORDER BY RANDOM() LIMIT 1")
                    cat = cursor.fetchone()
                    if cat:
                        post['cross_promotion']['category_id'] = cat['id']
                        post['cross_promotion']['category_title'] = cat.get('name') or 'Related Department'
                        post['cross_promotion']['category_position'] = post['cross_promotion']['category_position'] or 2
                        need_persist = True
                if not post['cross_promotion'].get('product_id'):
                    cursor.execute("SELECT id, name FROM clan_products ORDER BY RANDOM() LIMIT 1")
                    prod = cursor.fetchone()
                    if prod:
                        post['cross_promotion']['product_id'] = prod['id']
                        post['cross_promotion']['product_title'] = prod.get('name') or 'Related Products'
                        post['cross_promotion']['product_position'] = post['cross_promotion']['product_position'] or 4
                        need_persist = True
                if need_persist:
                    cursor.execute("""
                        UPDATE post SET
                            cross_promotion_category_id = %s,
                            cross_promotion_category_title = %s,
                            cross_promotion_product_id = %s,
                            cross_promotion_product_title = %s,
                            cross_promotion_category_position = COALESCE(cross_promotion_category_position, %s),
                            cross_promotion_product_position = COALESCE(cross_promotion_product_position, %s),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        post['cross_promotion'].get('category_id'),
                        post['cross_promotion'].get('category_title'),
                        post['cross_promotion'].get('product_id'),
                        post['cross_promotion'].get('product_title'),
                        post['cross_promotion'].get('category_position') or 2,
                        post['cross_promotion'].get('product_position') or 4,
                        post_id
                    ))
                    cursor.connection.commit()

                # Ensure widget HTML exists for preview/publish consistency
                # Note: After syncing product-match IDs, widget HTML may need to be regenerated
                widget_changed = False
                if post['cross_promotion'].get('category_id') and post['cross_promotion'].get('category_position') and not post['cross_promotion'].get('category_widget_html'):
                    post['cross_promotion']['category_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_category\" category_id=\"{post['cross_promotion'].get('category_id')}\" title=\"{post['cross_promotion'].get('category_title') or 'Related Department'}\"}}}}"
                    widget_changed = True
                if post['cross_promotion'].get('product_id') and post['cross_promotion'].get('product_position') and not post['cross_promotion'].get('product_widget_html'):
                    post['cross_promotion']['product_widget_html'] = f"{{{{widget type=\"swcatalog/widget_crossSell_product\" product_id=\"{post['cross_promotion'].get('product_id')}\" title=\"{post['cross_promotion'].get('product_title') or 'Related Products'}\"}}}}"
                    widget_changed = True
                if widget_changed:
                    with db_manager.get_cursor() as c2:
                        c2.execute("""
                            UPDATE post SET
                                cross_promotion_category_widget_html = %s,
                                cross_promotion_product_widget_html = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            post['cross_promotion'].get('category_widget_html'),
                            post['cross_promotion'].get('product_widget_html'),
                            post_id
                        ))
                        c2.connection.commit()
        except Exception as e:
            logger.warning(f"Validation cross-promotion attach/auto-select error: {e}")

        # After attachment/generation, only warn if DB claims configured but we truly have no usable data
        cp = post.get('cross_promotion') or {}
        if (
            (post.get('cross_promotion_category_id') or post.get('cross_promotion_product_id'))
            and not (cp.get('category_widget_html') or cp.get('product_widget_html'))
        ):
            issues.append({
                'type': 'cross_promotion_missing',
                'message': 'Cross-promotion configured but no widget HTML available'
            })
        
        valid = len(issues) == 0
        
        return jsonify({
            'valid': valid,
            'issues': issues,
            'section_count': len(sections),
            'has_all_meta_fields': all(post.get(f) for f in required_fields),
            'meta_image_is_optimized': meta_image and '/optimized/' in meta_image and meta_image.endswith('.jpg'),
            'message': 'Ready to publish' if valid else f'Found {len(issues)} issues that need attention'
        })
        
    except Exception as e:
        logger.error(f"Error validating publish data for post {post_id}: {e}")
        return jsonify({'error': str(e), 'valid': False}), 500

