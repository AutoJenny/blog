"""Block editor service: handles suggestions, selection, override logic."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from newsletter.db.queries_issue import get_block, update_block_payload
from newsletter.services.suggestion_service import generate_suggestions
from newsletter.services.block_suggestion_service import get_suggestions_for_block, auto_select_for_block
from newsletter.rendering.intro_text import generate_intro_text
from newsletter.rendering.snapshot_text import generate_snapshot_text
from newsletter.selectors.intro import select_intro_content
from newsletter.selectors.snapshot import select_snapshot


def get_suggestions(*, block_id: int, block_type: str, issue_id: int, target_week: str) -> Dict[str, Any]:
    """Get suggestions for a block.
    
    Uses unified suggestion service for all block types.
    Returns dict with:
    - suggestions: List of scored suggestions
    - current: Currently selected item (if any)
    - metadata: Type-specific metadata
    """
    # Get current block to see if there's already a selection
    block = get_block(block_id=block_id)
    current_payload = block.get('payload_json', {}) if block else {}
    
    # Use unified suggestion service
    # For intro/snapshot, this calls select_intro_content/select_snapshot which already
    # uses generate_suggestions with skip_validation=True
    result = get_suggestions_for_block(block_type=block_type, issue_id=issue_id, target_week=target_week)
    
    # If we got suggestions from the unified service, use them
    # Otherwise, try direct generation as fallback (shouldn't be needed now)
    if not result.get('suggestions') and block_type in ('intro', 'snapshot'):
        # Fallback: try direct generation (shouldn't happen if selectors work)
        source_suggestions = generate_suggestions(block_type=block_type, target_week=target_week, count=3, skip_validation=True)
        if source_suggestions:
            result['suggestions'] = source_suggestions
    
    # Merge current selection from payload if exists
    if current_payload:
        if block_type == 'intro':
            result['current'] = current_payload.get('selected') or result.get('current')
        elif block_type == 'snapshot':
            result['current'] = current_payload or result.get('current')
        elif block_type == 'feature':
            # Feature block stores post data directly in payload
            if current_payload.get('id'):
                result['current'] = current_payload
        elif block_type == 'new_products':
            # new_products block stores items array in payload
            if current_payload.get('items'):
                result['current'] = {'items': current_payload.get('items')}
        else:
            result['current'] = current_payload.get('selected') or current_payload or result.get('current')
    
    return result


def apply_suggestion(*, block_id: int, block_type: str, issue_id: int, target_week: str, suggestion_id: int | None = None, product_ids: List[int] | None = None) -> Dict[str, Any]:
    """Apply a suggestion to a block.
    
    If suggestion_id provided, uses that; otherwise auto-selects top suggestion.
    """
    # For feature blocks, get suggestions from block_suggestion_service
    if block_type == 'feature':
        from newsletter.services.block_suggestion_service import get_suggestions_for_block
        result = get_suggestions_for_block(block_type=block_type, issue_id=issue_id, target_week=target_week)
        suggestions = result.get('suggestions', [])
        
        if not suggestions:
            return {'success': False, 'error': 'No theme posts available'}
        
        # Find selected suggestion
        selected = None
        if suggestion_id:
            for s in suggestions:
                if s.get('id') == suggestion_id:
                    selected = s
                    break
        if not selected:
            selected = suggestions[0]  # Auto-select top
        
        # Format payload for feature block
        # Generate chatty summary from title and expanded_idea
        from newsletter.services.feature_summary_service import generate_feature_summary
        title = selected.get('title', '')
        expanded_idea = selected.get('expanded_idea', '')
        excerpt = generate_feature_summary(title=title, expanded_idea=expanded_idea)
        
        payload = {
            "id": selected.get('id'),
            "title": title,
            "url": selected.get('url', ''),
            "excerpt": excerpt,
            "hero_image": selected.get('hero_image', ''),
        }
    elif block_type == 'new_products':
        # For new_products, get fresh suggestions (which randomly selects 3 products from pool)
        from newsletter.services.block_suggestion_service import get_suggestions_for_block
        result = get_suggestions_for_block(block_type=block_type, issue_id=issue_id, target_week=target_week)
        suggestions = result.get('suggestions', [])
        product_pool = result.get('_product_pool', [])  # Get the pool to store in payload
        
        if not suggestions:
            return {'success': False, 'error': 'No recent products available. Make sure there are products that haven\'t been launched yet.'}
        
        # If product_ids provided (from frontend), use those specific products
        if product_ids:
            products = [s for s in suggestions if s.get('id') in product_ids]
            # If we couldn't find all requested IDs, fall back to first 3
            if len(products) < 3:
                products = suggestions[:3]
        else:
            # Use suggestions (already randomly selected 3 products)
            products = suggestions[:3]
        
        # Clean product pool: remove non-serializable fields (like datetime objects)
        cleaned_pool = []
        for p in product_pool:
            cleaned_product = {
                'id': p.get('id'),
                'name': p.get('name', ''),
                'sku': p.get('sku', ''),
                'image_url': p.get('image_url', ''),
                'url': p.get('url', ''),
                'short_description': p.get('short_description', ''),
                'category_ids': p.get('category_ids', []),
            }
            cleaned_pool.append(cleaned_product)
        
        # Format payload for new_products block (3 products + pool for future re-chooses)
        # Don't mark as launched yet - wait for user to confirm
        payload = {
            'items': products[:3],
            'product_pool': cleaned_pool,  # Store cleaned pool so we can reuse it for re-chooses
            # intro will be added when user confirms
        }
        
        # NOTE: Products are NOT marked as launched here
        # They will be marked when user clicks "Confirm Selection & Generate Intro"
    else:
        # Skip validation for cached items - faster and more reliable
        suggestions = generate_suggestions(block_type=block_type, target_week=target_week, count=3, skip_validation=True)
        
        if not suggestions:
            return {'success': False, 'error': 'No suggestions available'}
        
        # Find selected suggestion
        selected = None
        if suggestion_id:
            for s in suggestions:
                if s.get('id') == suggestion_id:
                    selected = s
                    break
        if not selected:
            selected = suggestions[0]  # Auto-select top
        
        # Generate text based on block type
        if block_type == 'intro':
            # For intro, we need multiple items (weather/event/community)
            intro_content = select_intro_content(target_week=target_week)
            text = intro_content.get('text', '')
            payload = {
                "text": text,
                "suggestions": intro_content.get('suggestions', []),
                "selected": intro_content.get('selected'),
                "items_by_category": intro_content.get('items_by_category', {}),
            }
        elif block_type == 'snapshot':
            text = generate_snapshot_text(selected)
            payload = {
                "title": selected.get('title', ''),
                "publisher": selected.get('source_name', ''),
                "url": selected.get('url', ''),
                "comment": text,
                "suggestions": suggestions,
                "selected_id": selected.get('id'),
            }
        else:
            # Other block types: store selected item
            payload = {
                "selected": selected,
                "suggestions": suggestions,
            }
    
    # Update block payload
    update_block_payload(block_id=block_id, payload=payload)
    
    # Mark products as newsletter launched if this is a product block
    if block_type in ('new_products', 'spotlight'):
        from newsletter.services.product_tracking import mark_products_newsletter_launched, extract_product_ids_from_payload
        product_ids = extract_product_ids_from_payload(payload, block_type)
        if product_ids:
            mark_products_newsletter_launched(product_ids)
    
    return {
        'success': True,
        'payload': payload,
        'text': text if block_type in ('intro', 'snapshot') else '',
    }


def save_override(*, block_id: int, block_type: str, override_text: str) -> Dict[str, Any]:
    """Save manual text override for a block."""
    block = get_block(block_id=block_id)
    if not block:
        return {'success': False, 'error': 'Block not found'}
    
    current_payload = block.get('payload_json', {}) or {}
    
    # Update payload with override
    if block_type == 'intro':
        current_payload['text'] = override_text
        current_payload['manual_override'] = True
    elif block_type == 'snapshot':
        current_payload['comment'] = override_text
        current_payload['manual_override'] = True
    else:
        current_payload['override_text'] = override_text
        current_payload['manual_override'] = True
    
    update_block_payload(block_id=block_id, payload=current_payload)
    
    return {
        'success': True,
        'payload': current_payload,
    }


def regenerate_text(*, block_id: int, block_type: str, issue_id: int, target_week: str) -> Dict[str, Any]:
    """Regenerate text from current selection (useful after manual edits)."""
    return apply_suggestion(block_id=block_id, block_type=block_type, issue_id=issue_id, target_week=target_week, suggestion_id=None)

