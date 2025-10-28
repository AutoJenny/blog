# blueprints/launchpad/cross_promotion.py
"""Cross-promotion management routes."""

from flask import Blueprint, render_template, jsonify
import logging
from config.database import db_manager

bp = Blueprint('cross_promotion', __name__)
logger = logging.getLogger(__name__)

@bp.route('/cross-promotion')
def cross_promotion():
    """Cross-promotion management page."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug,
                       pd.idea_seed, pd.intro_blurb, pd.main_title,
                       p.cross_promotion_category_id, p.cross_promotion_category_title,
                       p.cross_promotion_product_id, p.cross_promotion_product_title,
                       p.cross_promotion_category_position, p.cross_promotion_product_position,
                       p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC NULLS LAST, p.created_at DESC
            """)
            posts = cursor.fetchall()
            
            for post in posts:
                post['cross_promotion'] = {
                    'category_id': post.get('cross_promotion_category_id'),
                    'category_title': post.get('cross_promotion_category_title'),
                    'product_id': post.get('cross_promotion_product_id'),
                    'product_title': post.get('cross_promotion_product_title'),
                    'category_position': post.get('cross_promotion_category_position'),
                    'product_position': post.get('cross_promotion_product_position'),
                    'category_widget_html': post.get('cross_promotion_category_widget_html'),
                    'product_widget_html': post.get('cross_promotion_product_widget_html')
                }
                # Note: get_post_sections_with_images would need to be implemented
                post['sections'] = []
    
        default_post = posts[0] if posts else None
        return render_template('launchpad/cross_promotion.html', posts=posts, default_post=default_post)
    except Exception as e:
        logger.error(f"Error in cross_promotion: {e}")
        return jsonify({"error": str(e)}), 500

