"""Newsletter Generation Other Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_generation_other', __name__)


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-products-intro', methods=['POST'])
def generate_products_intro(issue_id: int, block_id: int):
    """Generate intro paragraph for New Products Spotlight block."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.services.products_intro_service import generate_products_intro as generate_intro
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if block.get('type') != 'new_products':
            return jsonify({'error': 'This endpoint is only for new_products blocks'}), 400
        
        payload = block.get('payload_json', {})
        products = payload.get('items', [])
        
        if not products or len(products) == 0:
            return jsonify({'error': 'No products selected. Please select products first.'}), 400
        
        # Generate intro paragraph
        intro = generate_intro(products)
        
        return jsonify({
            'success': True,
            'intro': intro
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating products intro: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/confirm-products', methods=['POST'])
def confirm_products(issue_id: int, block_id: int):
    """Confirm product selection: save intro and mark products as launched."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.product_tracking import mark_products_newsletter_launched, extract_product_ids_from_payload
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if block.get('type') != 'new_products':
            return jsonify({'error': 'This endpoint is only for new_products blocks'}), 400
        
        # Get intro from request
        request_data = request.json if request.is_json else {}
        intro = request_data.get('intro', '')
        
        # Get current payload
        payload = block.get('payload_json', {})
        products = payload.get('items', [])
        
        if not products or len(products) == 0:
            return jsonify({'error': 'No products selected. Please select products first.'}), 400
        
        # Update payload with intro
        payload['intro'] = intro
        
        # Update block payload
        update_block_payload(block_id=block_id, payload=payload)
        
        # Mark products as newsletter launched
        product_ids = extract_product_ids_from_payload(payload, 'new_products')
        if product_ids:
            mark_products_newsletter_launched(product_ids)
        
        return jsonify({
            'success': True,
            'message': 'Products confirmed and marked as launched'
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error confirming products: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-feature-summary', methods=['POST'])
def generate_feature_summary(issue_id: int, block_id: int):
    """Generate chatty summary for feature block post using LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.feature_summary_service import generate_feature_summary as generate_summary
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        post_id = data.get('post_id')
        title = data.get('title', '')
        expanded_idea = data.get('expanded_idea', '')
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        # Generate chatty summary
        summary = generate_summary(title=title, expanded_idea=expanded_idea)
        
        # Update block payload with new summary
        payload = block.get('payload_json', {}) or {}
        payload['excerpt'] = summary
        payload['id'] = post_id
        payload['title'] = title
        payload['url'] = data.get('url', payload.get('url', ''))
        payload['hero_image'] = data.get('hero_image', payload.get('hero_image', ''))
        
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'excerpt': summary
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating feature summary: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-spotlight-summary', methods=['POST'])
def generate_spotlight_summary(issue_id: int, block_id: int):
    """Generate chatty summary for spotlight block using profile post and LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.feature_summary_service import generate_feature_summary as generate_summary
        from newsletter.selectors.products import select_spotlight_profile_post
        from config.database import db_manager
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        # Get profile post for spotlight
        profile_post = select_spotlight_profile_post()
        if not profile_post:
            return jsonify({'error': 'No profile post available for spotlight'}), 404
        
        post_id = profile_post.get('id')
        if not post_id:
            return jsonify({'error': 'Profile post has no ID'}), 400
        
        # Get post details with header image and expanded_idea
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.title, p.slug, p.summary, 
                           i.file_path AS hero_image,
                           pd.expanded_idea, p.clan_uploaded_url, p.status
                    FROM post p
                    LEFT JOIN images i ON p.header_image_id = i.id
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    WHERE p.id = %s
                      AND p.status != 'deleted'
                """, (post_id,))
                post_row = cur.fetchone()
                
                if not post_row:
                    return jsonify({'error': 'Post not found'}), 404
                
                post_data = dict(post_row)
                
                # If no image from images table, try image_archive
                if not post_data.get('hero_image'):
                    cur.execute("""
                        SELECT ia.path
                        FROM post_images pi
                        JOIN image_archive ia ON pi.image_id = ia.id
                        WHERE pi.post_id = %s AND pi.image_type LIKE 'header%%'
                        ORDER BY CASE WHEN pi.image_type = 'header_optimized' THEN 1 
                                     WHEN pi.image_type = 'header_watermarked' THEN 2
                                     ELSE 3 END
                        LIMIT 1
                    """, (post_id,))
                    img_row = cur.fetchone()
                    if img_row and img_row.get('path'):
                        post_data['hero_image'] = img_row['path']
                
                # Generate URL
                if post_data.get('clan_uploaded_url'):
                    post_url = post_data['clan_uploaded_url']
                elif post_data.get('slug'):
                    post_url = f"/posts/{post_data['slug']}"
                else:
                    post_url = f"/posts/{post_data['id']}"
        
        # Generate chatty summary using LLM
        title = post_data.get('title', '')
        expanded_idea = post_data.get('expanded_idea', '') or post_data.get('summary', '')
        summary = generate_summary(title=title, expanded_idea=expanded_idea)
        
        # Update block payload
        payload = block.get('payload_json', {}) or {}
        payload['title'] = title
        payload['summary'] = summary
        payload['url'] = post_url
        payload['hero_image'] = post_data.get('hero_image', '')
        payload['id'] = post_id
        
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'title': title,
            'url': post_url,
            'hero_image': post_data.get('hero_image', '')
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating spotlight summary: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


# Source Management Routes

