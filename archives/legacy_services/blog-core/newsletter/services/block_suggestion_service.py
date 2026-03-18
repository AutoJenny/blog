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
        # Get multiple recent theme posts for selection, prioritizing the week's post
        articles = select_feature_articles(limit=10, target_week=target_week)
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
        # First article is the default/current selection (should be the week's post if available)
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
        # Get top 30 most recently added products that haven't been launched
        # No date filter - just get the most recent products
        if not product_pool or len(product_pool) == 0:
            product_pool = get_product_pool(
                since_iso_timestamp=None,  # No date filter - get top 30 regardless of date
                pool_size=30,
                exclude_launched=True  # Only get products that haven't been launched
            )
        
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
        # Use profile posts (not themed blog posts)
        spotlight = select_spotlight_profile_post()
        suggestions = []
        if spotlight:
            suggestions.append({
                'id': spotlight.get('id'),
                'title': spotlight.get('title', ''),
                'url': spotlight.get('url', ''),
                'description': spotlight.get('summary', ''),
                'hero_image': spotlight.get('hero_image', ''),
                'expanded_idea': spotlight.get('expanded_idea', ''),
                'type': 'post',
            })
        return {
            'suggestions': suggestions,
            'current': spotlight,
            'metadata': {},
        }
    
    elif block_type == 'last_chance':
        # Scrape clearance page and select products
        try:
            from newsletter.sources.clan_clearance_scraper import scrape_clearance_page
            from newsletter.selectors.clearance import select_clearance_products
            from newsletter.services.clearance_cache import save_clearance_data
            
            # Scrape clearance page
            scraped_products = scrape_clearance_page(limit=120)
            
            if not scraped_products:
                return {
                    'suggestions': [],
                    'current': None,
                    'metadata': {'error': 'No products scraped from clearance page'}
                }
            
            # Save to temp file
            cache_file = save_clearance_data(scraped_products)
            
            # Select 5 products with different branch categories
            selected_products = select_clearance_products(scraped_products, limit=5)
            
            return {
                'suggestions': selected_products,
                'current': {'items': selected_products} if selected_products else None,
                'metadata': {
                    'cache_file': cache_file,
                    'total_scraped': len(scraped_products),
                    'selected_count': len(selected_products)
                }
            }
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting last_chance suggestions: {e}", exc_info=True)
            return {
                'suggestions': [],
                'current': None,
                'metadata': {'error': str(e)}
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
    
    elif block_type == 'words_of_the_week':
        # Words of the Week block - get word and phrase for the week
        from newsletter.selectors.words_of_the_week import get_words_of_the_week
        from datetime import date
        
        # Parse week from target_week (e.g., "2025W48")
        week_number = None
        if 'W' in target_week:
            _, week_str = target_week.split('W')
            week_number = int(week_str)
        else:
            try:
                week_number = int(target_week)
            except:
                # Fallback to current week
                _, week_number, _ = date.today().isocalendar()
        
        words = get_words_of_the_week(week_number=week_number) if week_number else {}
        
        return {
            'suggestions': [],
            'current': words,
            'metadata': {
                'week_number': week_number,
            },
        }
    
    elif block_type == 'seasonal_recipe':
        # Seasonal Recipe block - get most recent recipe post not yet used
        from newsletter.selectors.seasonal_recipe import select_seasonal_recipe_post
        recipe_post = select_seasonal_recipe_post()
        
        suggestions = []
        if recipe_post:
            suggestions.append({
                'id': recipe_post.get('id'),
                'title': recipe_post.get('title', ''),
                'url': recipe_post.get('url', ''),
                'summary': recipe_post.get('summary', ''),
                'hero_image': recipe_post.get('hero_image', ''),
                'type': 'post',
            })
        
        return {
            'suggestions': suggestions,
            'current': recipe_post,
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
    
    elif block_type == 'seasonal_recipe':
        # Mark recipe post as newsletter featured
        if current and current.get('id'):
            from newsletter.services.product_tracking import mark_post_newsletter_recipe_featured
            mark_post_newsletter_recipe_featured(current.get('id'))
        return current  # Already in correct format
    
    elif block_type == 'category':
        return current  # Already in correct format
    
    elif block_type == 'evergreen':
        return current  # Already in correct format
    
    elif block_type == 'weekly_words':
        # Weekly Words block - placeholder for now
        return {}
    
    return {}

