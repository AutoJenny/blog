"""Unified suggestion service: routes block type to appropriate suggestion logic."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from newsletter.services.suggestion_service import generate_suggestions
from newsletter.selectors.blog_feature import select_feature_article
from newsletter.selectors.products import select_new_products, select_spotlight_product, group_variants
from newsletter.selectors.category import select_category_feature
from newsletter.selectors.evergreen import select_evergreen
from newsletter.selectors.intro import select_intro_content
from newsletter.selectors.snapshot import select_snapshot
from datetime import date


def get_suggestions_for_block(*, block_type: str, issue_id: int, target_week: str) -> Dict[str, Any]:
    """Unified interface to get suggestions for any block type.
    
    Routes to type-specific logic:
    - intro: aggregated weather/event/community from source items
    - snapshot: single item from source items
    - feature: latest blog post
    - new_products: recent products
    - spotlight: single featured product
    - category: rotating category feature
    - evergreen: reusable snippet
    
    Returns dict with:
    - suggestions: List of suggestion options
    - current: Currently selected item/content
    - metadata: Type-specific metadata (scores, counts, etc.)
    """
    if block_type == 'intro':
        intro_content = select_intro_content(target_week=target_week)
        return {
            'suggestions': intro_content.get('suggestions', []),
            'current': intro_content.get('selected'),
            'metadata': {
                'items_by_category': intro_content.get('items_by_category', {}),
                'text': intro_content.get('text', ''),
            },
        }
    
    elif block_type == 'snapshot':
        snapshot = select_snapshot(target_week=target_week)
        if snapshot:
            return {
                'suggestions': snapshot.get('suggestions', []),
                'current': snapshot,
                'metadata': {
                    'selected_id': snapshot.get('selected_id'),
                    'comment': snapshot.get('comment', ''),
                },
            }
        return {'suggestions': [], 'current': None, 'metadata': {}}
    
    elif block_type == 'feature':
        feature = select_feature_article()
        # For feature, we can return the selected article plus alternatives
        # In future, could fetch multiple recent posts for suggestions
        suggestions = []
        if feature:
            suggestions.append({
                'id': feature.get('id'),
                'title': feature.get('title', ''),
                'excerpt': feature.get('excerpt', ''),
                'url': feature.get('url', ''),
                'type': 'blog_post',
            })
        return {
            'suggestions': suggestions,
            'current': feature,
            'metadata': {},
        }
    
    elif block_type == 'new_products':
        since_date = f"{date.today().isoformat()}T00:00:00Z"
        products = select_new_products(since_iso_timestamp=since_date, limit=12)
        grouped, _ = group_variants(products)
        suggestions = []
        for item in grouped[:6]:
            suggestions.append({
                'id': item.get('id'),
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'price': item.get('price'),
                'type': 'product',
            })
        return {
            'suggestions': suggestions,
            'current': {'items': grouped[:6]} if grouped else None,
            'metadata': {'count': len(grouped)},
        }
    
    elif block_type == 'spotlight':
        spotlight = select_spotlight_product()
        suggestions = []
        if spotlight:
            suggestions.append({
                'id': spotlight.get('id'),
                'title': spotlight.get('title', ''),
                'url': spotlight.get('url', ''),
                'description': spotlight.get('description', ''),
                'type': 'product',
            })
        return {
            'suggestions': suggestions,
            'current': spotlight,
            'metadata': {},
        }
    
    elif block_type == 'category':
        category = select_category_feature()
        suggestions = []
        if category:
            suggestions.append({
                'id': category.get('id'),
                'title': category.get('title', ''),
                'description': category.get('description', ''),
                'type': 'category',
            })
        return {
            'suggestions': suggestions,
            'current': category,
            'metadata': {},
        }
    
    elif block_type == 'evergreen':
        evergreen = select_evergreen()
        suggestions = []
        if evergreen:
            suggestions.append({
                'id': evergreen.get('id'),
                'topic': evergreen.get('topic', ''),
                'text': evergreen.get('text', ''),
                'type': 'evergreen',
            })
        return {
            'suggestions': suggestions,
            'current': evergreen,
            'metadata': {},
        }
    
    elif block_type == 'weekly_words':
        # Weekly Words block - placeholder for now (will need its own selector)
        return {
            'suggestions': [],
            'current': None,
            'metadata': {},
        }
    
    else:
        # Unknown block type: return empty
        return {'suggestions': [], 'current': None, 'metadata': {}}


def auto_select_for_block(*, block_type: str, issue_id: int, target_week: str) -> Dict[str, Any]:
    """Auto-select content for a block type using appropriate selector.
    
    Returns the selected content payload ready for block.payload_json.
    """
    result = get_suggestions_for_block(block_type=block_type, issue_id=issue_id, target_week=target_week)
    current = result.get('current')
    
    if not current:
        return {}
    
    # Format payload based on block type
    if block_type == 'intro':
        intro_content = select_intro_content(target_week=target_week)
        return {
            'text': intro_content.get('text', ''),
            'suggestions': intro_content.get('suggestions', []),
            'selected': intro_content.get('selected'),
            'items_by_category': intro_content.get('items_by_category', {}),
        }
    
    elif block_type == 'snapshot':
        snapshot = select_snapshot(target_week=target_week)
        if snapshot:
            return {
                'title': snapshot.get('title', ''),
                'publisher': snapshot.get('publisher', ''),
                'url': snapshot.get('url', ''),
                'comment': snapshot.get('comment', ''),
                'suggestions': snapshot.get('suggestions', []),
                'selected_id': snapshot.get('selected_id'),
            }
        return {}
    
    elif block_type == 'feature':
        return current  # Already in correct format
    
    elif block_type == 'new_products':
        return {'items': result.get('suggestions', [])[:6]}
    
    elif block_type == 'spotlight':
        return current  # Already in correct format
    
    elif block_type == 'category':
        return current  # Already in correct format
    
    elif block_type == 'evergreen':
        return current  # Already in correct format
    
    elif block_type == 'weekly_words':
        # Weekly Words block - placeholder for now
        return {}
    
    return {}

