"""Newsletter Blocks Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_blocks', __name__)


@bp.route('/newsletter/block/<int:block_id>/toggle', methods=['POST'])
def toggle_block(block_id: int):
    enabled = request.form.get('enabled', 'true').lower() == 'true'
    set_block_enabled(block_id=block_id, enabled=enabled)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter_blocks.view_issue', issue_id=issue_id))



@bp.route('/newsletter/block/<int:block_id>/update', methods=['POST'])
def update_block(block_id: int):
    import json
    from newsletter.db.queries_issue import get_block
    from newsletter.services.product_tracking import mark_products_newsletter_launched, extract_product_ids_from_payload
    
    raw = request.form.get('payload_json') or '{}'
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}
    
    # Get block type to check if we need to mark products as launched
    block = get_block(block_id=block_id)
    block_type = block.get('type', '') if block else ''
    
    update_block_payload(block_id=block_id, payload=payload)
    
    # Mark products as newsletter launched if this is a new_products block
    if block_type == 'new_products':
        product_ids = extract_product_ids_from_payload(payload, block_type)
        if product_ids:
            mark_products_newsletter_launched(product_ids)
    
    # Mark profile post as newsletter spotlighted if this is a spotlight block
    if block_type == 'spotlight':
        from newsletter.services.product_tracking import mark_post_newsletter_spotlighted, extract_post_id_from_spotlight_payload
        post_id = extract_post_id_from_spotlight_payload(payload)
        if post_id:
            mark_post_newsletter_spotlighted(post_id)
    
    # Mark recipe post as newsletter featured if this is a seasonal_recipe block
    if block_type == 'seasonal_recipe':
        from newsletter.services.product_tracking import mark_post_newsletter_recipe_featured
        post_id = payload.get('id')
        if post_id:
            try:
                post_id = int(post_id)
                mark_post_newsletter_recipe_featured(post_id)
            except (ValueError, TypeError):
                pass
    
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter_blocks.view_issue', issue_id=issue_id))



@bp.route('/newsletter/block/<int:block_id>/delete', methods=['POST'])
def remove_block(block_id: int):
    issue_id = int(request.form.get('issue_id', '0'))
    delete_block(block_id=block_id)
    return redirect(url_for('newsletter_blocks.view_issue', issue_id=issue_id))



@bp.route('/newsletter/issue/<int:issue_id>/block/add', methods=['POST'])
def add_block(issue_id: int):
    block_type = request.form.get('type', 'evergreen')
    # Calculate position: optional provided, else append to end
    try:
        existing = list_blocks_by_issue(issue_id=issue_id)
        desired = request.form.get('position')
        if desired is not None and desired != '':
            try:
                desired_pos = int(desired)
            except Exception:
                desired_pos = 0
            if desired_pos < 0:
                desired_pos = 0
            if existing:
                max_pos = max(b.get('position', 0) for b in existing)
                if desired_pos > max_pos + 1:
                    desired_pos = max_pos + 1
                # Shift existing blocks at and after desired_pos
                shift_positions(issue_id=issue_id, from_position=desired_pos)
            position = desired_pos
        else:
            if existing:
                max_pos = max(b.get('position', 0) for b in existing)
                position = max_pos + 1
            else:
                position = 0
    except Exception:
        position = 9999
    payload = {}
    insert_block(issue_id=issue_id, block_type=block_type, position=position, enabled=True, payload=payload)
    return redirect(url_for('newsletter_blocks.view_issue', issue_id=issue_id))



@bp.route('/newsletter/block/<int:block_id>/move', methods=['POST'])
def move_block_route(block_id: int):
    direction = request.form.get('direction', 'up')
    move_block(block_id=block_id, direction=direction)
    issue_id = int(request.form.get('issue_id', '0'))
    return redirect(url_for('newsletter_blocks.view_issue', issue_id=issue_id))


# Block editor API endpoints (JSON)


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/suggestions', methods=['GET'])
def get_block_suggestions(issue_id: int, block_id: int):
    """Get suggestions for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        block_type = block.get('type', '')
        
        logger.debug(f"Getting suggestions for block {block_id} (type: {block_type}, week: {target_week})")
        
        result = get_suggestions(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week
        )
        
        logger.debug(f"Suggestions result: {len(result.get('suggestions', []))} suggestions found")
        
        # If no suggestions and no error, provide helpful message
        if not result.get('suggestions') and not result.get('error'):
            result['error'] = 'No suggestions available. Make sure source prefetch has run and there is content in the database.'
        
        return jsonify(result)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting suggestions: {e}", exc_info=True)
        return jsonify({'error': str(e), 'suggestions': [], 'current': None, 'metadata': {}}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/select-suggestion', methods=['POST'])
def select_block_suggestion(issue_id: int, block_id: int):
    """Apply a suggestion to a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        block_type = block.get('type', '')
        
        request_data = request.json if request.is_json else {}
        suggestion_id = request_data.get('suggestion_id')
        auto_select = request_data.get('auto_select', False)
        product_ids = request_data.get('product_ids')  # For new_products blocks
        
        if suggestion_id:
            try:
                suggestion_id = int(suggestion_id)
            except Exception:
                suggestion_id = None
        
        # For auto_select (e.g., re-choose products), ignore suggestion_id
        if auto_select:
            suggestion_id = None
        
        result = apply_suggestion(
            block_id=block_id,
            block_type=block_type,
            issue_id=issue_id,
            target_week=target_week,
            suggestion_id=suggestion_id,
            product_ids=product_ids  # Pass product IDs for new_products
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/override', methods=['POST'])
def override_block_text(issue_id: int, block_id: int):
    """Save manual text override for a block."""
    try:
        from newsletter.db.queries_issue import get_block
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        block_type = block.get('type', '')
        override_text = ''
        
        if request.is_json:
            override_text = request.json.get('text', '')
        else:
            override_text = request.form.get('text', '')
        
        result = save_override(
            block_id=block_id,
            block_type=block_type,
            override_text=override_text
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


