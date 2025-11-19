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
        else:
            result['current'] = current_payload.get('selected') or current_payload or result.get('current')
    
    return result


def apply_suggestion(*, block_id: int, block_type: str, issue_id: int, target_week: str, suggestion_id: int | None = None) -> Dict[str, Any]:
    """Apply a suggestion to a block.
    
    If suggestion_id provided, uses that; otherwise auto-selects top suggestion.
    """
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

