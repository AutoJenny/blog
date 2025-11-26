"""Unified suggestion service: routes block type to appropriate suggestion logic."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from newsletter.services.suggestion_service import generate_suggestions
from newsletter.selectors.blog_feature import select_feature_article, select_feature_articles
from newsletter.selectors.products import select_new_products, select_spotlight_product, select_spotlight_profile_post, group_variants
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
        # Get multiple recent theme posts for selection
        articles = select_feature_articles(limit=10)
        suggestions = []
        for article in articles:
            suggestions.append({
                'id': article.get('id'),
                'title': article.get('title', ''),
                'excerpt': article.get('excerpt', ''),
                'url': article.get('url', ''),
                'hero_image': article.get('hero_image', ''),
                'expanded_idea': article.get('expanded_idea', ''),
                'type': 'blog_post',
            })
        # First article is the default/current selection
        current = articles[0] if articles else None
        return {
            'suggestions': suggestions,
            'current': current,
            'metadata': {},
        }
    
    elif block_type == 'new_products':
        # Get or create product pool (up to 50 products)
        from datetime import datetime, timedelta
        from newsletter.selectors.products import get_product_pool, select_random_from_pool
        from newsletter.db.queries_issue import list_blocks_by_issue
        
        # Try to get pool from any existing new_products block in this issue
        # (pools are shared per issue to avoid duplicates)
        product_pool = []
        try:
            blocks = list_blocks_by_issue(issue_id=issue_id)
            for b in blocks:
                if b.get('type') == 'new_products':
                    payload = b.get('payload_json', {})
                    if payload.get('product_pool'):
                        product_pool = payload.get('product_pool', [])
                        break
        except Exception:
            pass
        
        # If no pool found, create a new one
        # Use 60 days to get more products
        if not product_pool or len(product_pool) == 0:
            since_date = (datetime.now() - timedelta(days=60)).isoformat()
            # First try excluding launched products
            product_pool = get_product_pool(
                since_iso_timestamp=since_date,
                pool_size=50,
                exclude_launched=True
            )
            # If we don't have enough products (less than 10), include launched ones to fill the pool
            # This ensures we always have a pool to re-choose from
            if len(product_pool) < 10:
                product_pool_with_launched = get_product_pool(
                    since_iso_timestamp=since_date,
                    pool_size=50,
                    exclude_launched=False  # Include launched to fill pool
                )
                # Merge, keeping unlaunched first, then adding launched
                existing_ids = {p.get('id') for p in product_pool}
                for p in product_pool_with_launched:
                    if p.get('id') not in existing_ids:
                        product_pool.append(p)
                        if len(product_pool) >= 50:
                            break
        
        # Randomly select 3 products from the pool with category diversity
        selected_products = select_random_from_pool(pool=product_pool, limit=3)
        
        # Format as suggestions
        suggestions = []
        for item in selected_products:
            suggestions.append({
                'id': item.get('id'),
                'name': item.get('name', ''),
                'sku': item.get('sku', ''),
                'image_url': item.get('image_url', ''),
                'url': item.get('url', ''),
                'short_description': item.get('short_description', ''),
                'category_ids': item.get('category_ids', []),
                'type': 'product',
            })
        
        return {
            'suggestions': suggestions,
            'current': {'items': suggestions} if suggestions else None,
            'metadata': {
                'count': len(suggestions),
                'pool_size': len(product_pool),
            },
            # Include pool in metadata so it can be stored in block payload
            '_product_pool': product_pool,
        }
    
    elif block_type == 'spotlight':
        # Use profile posts instead of products
        spotlight = select_spotlight_profile_post()
        suggestions = []
        if spotlight:
            suggestions.append({
                'id': spotlight.get('id'),
                'title': spotlight.get('title', ''),
                'url': spotlight.get('url', ''),
                'description': spotlight.get('summary', ''),
                'hero_image': spotlight.get('hero_image', ''),
                'type': 'post',
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
        # Generate chatty summary from title and expanded_idea
        if current and current.get('id'):
            from newsletter.services.feature_summary_service import generate_feature_summary
            title = current.get('title', '')
            expanded_idea = current.get('expanded_idea', '')
            excerpt = generate_feature_summary(title=title, expanded_idea=expanded_idea)
            return {
                'id': current.get('id'),
                'title': title,
                'url': current.get('url', ''),
                'excerpt': excerpt,
                'hero_image': current.get('hero_image', ''),
            }
        return current  # Fallback if no current
    
    elif block_type == 'new_products':
        # Use current items if available, otherwise use suggestions
        current_items = result.get('current', {}).get('items', [])
        if current_items:
            payload = {'items': current_items[:3]}  # Limit to 3 products
        else:
            # Fallback to suggestions format
            payload = {'items': result.get('suggestions', [])[:3]}
        # Mark products as newsletter launched
        from newsletter.services.product_tracking import mark_products_newsletter_launched, extract_product_ids_from_payload
        product_ids = extract_product_ids_from_payload(payload, block_type)
        if product_ids:
            mark_products_newsletter_launched(product_ids)
        return payload
    
    elif block_type == 'spotlight':
        # Mark profile post as newsletter spotlighted
        if current and current.get('id'):
            from newsletter.services.product_tracking import mark_post_newsletter_spotlighted
            mark_post_newsletter_spotlighted(current.get('id'))
        return current  # Already in correct format
    
    elif block_type == 'category':
        return current  # Already in correct format
    
    elif block_type == 'evergreen':
        return current  # Already in correct format
    
    elif block_type == 'weekly_words':
        # Weekly Words block - placeholder for now
        return {}
    
    return {}

