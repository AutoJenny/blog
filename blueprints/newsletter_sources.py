"""Newsletter Sources Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
from newsletter.db.queries_source_management import (
    list_all_sources,
    get_source,
    create_source,
    update_source,
    delete_source,
    get_cache_status,
    get_item_stats
)
from newsletter.db.queries_sources import get_cached_items
from newsletter.jobs.prefetch_sources import run as run_prefetch
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_sources', __name__)


@bp.route('/newsletter/sources')
def sources_management():
    """Source aggregation management page."""
    sources = list_all_sources()
    cache_status = get_cache_status()
    item_stats = get_item_stats()
    
    # Get cached items for preview (recent 20)
    recent_items = get_cached_items(days_back=14, limit=20)
    
    return render_template(
        'newsletter/sources.html',
        sources=sources,
        cache_status=cache_status,
        item_stats=item_stats,
        recent_items=recent_items,
    )



@bp.route('/newsletter/sources/add', methods=['POST'])
def add_source():
    """Add a new source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('type', 'rss').strip()
    enabled = request.form.get('enabled', 'off') == 'on'
    api_key_ref = request.form.get('api_key_ref', '').strip() or None
    
    if not name or not base_url:
        return redirect(url_for('newsletter_sources.sources_management')), 302
    
    create_source(name=name, base_url=base_url, type=source_type, enabled=enabled, api_key_ref=api_key_ref)
    return redirect(url_for('newsletter_sources.sources_management'))



@bp.route('/newsletter/sources/<int:source_id>/edit', methods=['POST'])
def edit_source(source_id: int):
    """Update an existing source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('type', 'rss').strip()
    enabled = request.form.get('enabled', 'off') == 'on'
    api_key_ref = request.form.get('api_key_ref', '').strip() or None
    
    updates = {}
    if name:
        updates['name'] = name
    if base_url:
        updates['base_url'] = base_url
    if source_type:
        updates['type'] = source_type
    updates['enabled'] = enabled
    if api_key_ref is not None:
        updates['api_key_ref'] = api_key_ref
    
    update_source(source_id, **updates)
    return redirect(url_for('newsletter_sources.sources_management'))



@bp.route('/newsletter/sources/<int:source_id>/delete', methods=['POST'])
def delete_source_route(source_id: int):
    """Delete a source."""
    delete_source(source_id)
    return redirect(url_for('newsletter_sources.sources_management'))



@bp.route('/newsletter/sources/<int:source_id>/toggle', methods=['POST'])
def toggle_source(source_id: int):
    """Toggle source enabled/disabled."""
    source = get_source(source_id)
    if source:
        update_source(source_id, enabled=not source.get('enabled', False))
    return redirect(url_for('newsletter_sources.sources_management'))



@bp.route('/newsletter/sources/fetch', methods=['POST'])
def trigger_fetch():
    """Manually trigger source prefetch job."""
    result = run_prefetch()
    # Could show success/error message, but for now just redirect
    return redirect(url_for('newsletter_sources.sources_management'))



@bp.route('/newsletter/sources/<int:source_id>/test', methods=['GET'])
def test_source(source_id: int):
    """Test a source by fetching and returning sample items with proper error handling."""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        source = get_source(source_id)
        if not source:
            logger.warning(f"Source test: source {source_id} not found")
            return jsonify({
                'success': False, 
                'error': 'Source not found',
                'error_type': 'not_found'
            }), 404
        
        if not source.get('enabled'):
            logger.info(f"Source test: {source.get('name')} is disabled")
            return jsonify({
                'success': False, 
                'error': 'Source is disabled. Enable it first to test.',
                'error_type': 'disabled'
            }), 400
        
        # Use manager to create adapter and fetch
        from newsletter.sources.manager import create_adapter_from_source
        
        source_name = source.get('name', 'Unknown')
        source_type = source.get('type', 'unknown')
        source_url = source.get('base_url', '')
        
        logger.info(f"Testing source: {source_name} (type: {source_type}, url: {source_url})")
        
        # Create adapter with explicit error handling
        try:
            adapter = create_adapter_from_source(source)
        except Exception as adapter_error:
            error_msg = f"Failed to create adapter: {str(adapter_error)}"
            logger.error(f"Source test adapter creation failed: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'adapter_creation_error',
                'source_name': source_name,
                'source_type': source_type
            }), 500
        
        if not adapter:
            error_msg = f"Could not create adapter for type: {source_type}. Supported types: rss, reddit, html, weather, event, museum"
            logger.error(f"Source test: {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg,
                'error_type': 'unsupported_type',
                'source_type': source_type
            }), 400
        
        # Log adapter category assignment for debugging
        adapter_category = None
        if hasattr(adapter, 'category'):
            adapter_category = adapter.category
            logger.info(f"Adapter created: {type(adapter).__name__} with category: {adapter_category}")
        else:
            logger.warning(f"Adapter {type(adapter).__name__} has no category attribute")
        
        # Fetch items with error handling
        try:
            logger.info(f"Fetching items from {source_name}...")
            items = adapter.fetch_and_normalize()
            logger.info(f"Fetched {len(items)} items from {source_name}")
        except Exception as fetch_error:
            error_msg = f"Failed to fetch from source: {str(fetch_error)}"
            logger.error(f"Source test fetch failed for {source_name}: {error_msg}", exc_info=True)
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_type': 'fetch_error',
                'source_name': source_name,
                'details': str(fetch_error)
            }), 500
        
        if not items:
            return jsonify({
                'success': True,
                'items_count': 0,
                'categories': {},
                'items': [],
                'warning': 'No items found. The source may be empty, require authentication, or the URL may be incorrect.',
                'adapter_category': adapter_category
            })
        
        # Limit to first 10 for preview
        preview_items = items[:10]
        
        # Group by category for debugging and validation
        categories = {}
        category_breakdown = {}
        for item in items:
            cat = item.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
            if cat not in category_breakdown:
                category_breakdown[cat] = []
            category_breakdown[cat].append(item.get('title', 'No title')[:50])
        
        # Validate category assignment
        category_mismatch = False
        expected_category = None
        if adapter_category and categories:
            # Check if adapter category matches items
            if adapter_category not in categories:
                category_mismatch = True
                expected_category = adapter_category
                logger.warning(
                    f"Category mismatch: adapter category '{adapter_category}' but items have categories: {list(categories.keys())}"
                )
        
        return jsonify({
            'success': True,
            'items_count': len(items),
            'categories': categories,
            'category_breakdown': {k: len(v) for k, v in category_breakdown.items()},
            'adapter_category': adapter_category,
            'category_validation': {
                'match': not category_mismatch,
                'expected': expected_category,
                'found': list(categories.keys())
            },
            'items': [
                {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'category': item.get('category', 'other'),
                    'source_name': item.get('source_name', ''),
                    'published_at': item.get('published_at').isoformat() if item.get('published_at') else None,
                    'event_date': item.get('event_date').isoformat() if item.get('event_date') else None,
                    'raw_data_preview': str(item.get('raw_data', {}))[:100] if item.get('raw_data') else None,
                }
                for item in preview_items
            ],
        })
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Source test failed for source {source_id}: {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'unexpected_error',
            'traceback': error_trace if logger.level <= logging.DEBUG else None
        }), 500



@bp.route('/newsletter/sources/items')
def cached_items():
    """Full cached items page with filters."""
    from newsletter.db.queries_source_management import list_all_sources
    
    # Get filter parameters
    category_filter = request.args.get('category', '')
    source_filter = request.args.get('source', '')
    days_back = int(request.args.get('days', '14'))
    
    # Get items
    items = get_cached_items(
        category=category_filter if category_filter else None,
        days_back=days_back,
        limit=500  # Increased limit to show more items
    )
    
    # Filter by source if provided
    if source_filter:
        items = [item for item in items if item.get('source_name', '').lower() == source_filter.lower()]
    
    # Get all possible categories (including weather)
    all_categories = ['news', 'weather', 'event', 'community', 'other']
    
    # Get all sources from database (not just cached items)
    all_sources = list_all_sources()
    sources = sorted([s.get('name', '') for s in all_sources if s.get('name')])
    
    return render_template(
        'newsletter/cached_items.html',
        items=items,
        categories=all_categories,
        sources=sources,
        category_filter=category_filter,
        source_filter=source_filter,
        days_back=days_back,
    )


