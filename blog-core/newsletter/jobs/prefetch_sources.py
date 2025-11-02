"""Daily prefetch job to refresh source item cache with specialized processing per source type."""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from newsletter.sources.manager import get_enabled_sources, create_adapter_from_source
from newsletter.services.scoring import score_items
from newsletter.services.content_analysis_service import analyze_item
from newsletter.services.deduplication_service import (
    check_calendar_event_duplicate,
    check_source_item_duplicate,
    should_skip_item
)
from newsletter.services.event_import_service import import_events_from_items
from newsletter.db.queries_sources import store_source_items, update_source_cache

logger = logging.getLogger(__name__)


def process_events(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process event-type items: filter false positives, deduplicate and import to calendar."""
    from newsletter.services.event_filtering_service import filter_false_positives
    
    event_items = [item for item in items if item.get('category') == 'event']
    
    if not event_items:
        return {'processed': 0, 'imported': 0, 'skipped': 0, 'filtered': 0}
    
    # Filter out false positives (page headings, navigation elements)
    valid_events, filtered = filter_false_positives(event_items)
    filtered_count = len(filtered)
    
    if filtered_count > 0:
        logger.info(f"Filtered {filtered_count} false positive events (page headings/navigation)")
    
    # Check for duplicates before processing
    deduplicated = []
    skipped_count = 0
    
    for item in valid_events:
        # Check if item should be skipped using should_skip_item helper
        skip_result = should_skip_item(
            item,
            check_calendar=True,
            check_source_items=True
        )
        
        if skip_result and skip_result.get('skip'):
            skipped_count += 1
            reason = skip_result.get('reason', 'unknown')
            logger.debug(f"Skipping duplicate event: {item.get('title', 'Unknown')[:50]} ({reason})")
            continue
        
        deduplicated.append(item)
    
    # Import events to calendar
    import_result = import_events_from_items(deduplicated, skip_duplicates=True)
    
    logger.info(f"Event processing: {len(valid_events)} valid, {filtered_count} filtered, {len(deduplicated)} deduplicated")
    
    # Mark imported events in source items
    for item, result in zip(deduplicated, import_result.get('results', [])):
        if result.get('imported') and result.get('id'):
            item['is_event'] = True
            item['calendar_event_id'] = result['id']
    
    return {
        'processed': len(event_items),
        'imported': import_result.get('imported', 0),
        'skipped': skipped_count + import_result.get('skipped', 0),
    }


def process_news(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process news-type items: fetch full content, analyze, generate synopsis."""
    from newsletter.services.news_synopsis_service import process_news_with_synopsis
    
    news_items = [item for item in items if item.get('category') == 'news']
    
    if news_items:
        logger.info(f"Processing {len(news_items)} news items with full content analysis and synopsis generation")
    
    # Process each news item: fetch content, analyze, generate synopsis
    processed = []
    for item in news_items:
        try:
            processed_item = process_news_with_synopsis(item, cache_results=True)
            if processed_item:
                processed.append(processed_item)
                logger.info(f"✓ Processed news: {item.get('title', 'Unknown')[:50]} (score: {processed_item.get('suitability_score', 0)})")
            else:
                logger.debug(f"Filtered out news item: {item.get('title', 'Unknown')[:50]}")
        except Exception as e:
            logger.error(f"Error processing news item {item.get('title', 'Unknown')[:50]}: {e}", exc_info=True)
            continue
    
    logger.info(f"Processed {len(processed)} relevant news items out of {len(news_items)} total")
    return processed


def process_weather(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process weather-type items: score and store."""
    weather_items = [item for item in items if item.get('category') == 'weather']
    
    # Weather items are generally all useful, no filtering needed
    # Just ensure they're properly scored
    return weather_items


def process_reddit(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process Reddit/community items: already filtered by adapter, just return."""
    community_items = [item for item in items if item.get('category') == 'community']
    
    # Reddit adapter already applies engagement thresholds and suitability checks
    return community_items


def run() -> dict:
    """Fetch from all enabled sources and process by type.
    
    Processing pipeline:
    - Events: Deduplicate → Import to calendar_events → Mark as imported
    - News: Analyze suitability (LLM) → Filter by threshold → Cache results
    - Weather: Score and store (no filtering)
    - Reddit/Community: Already filtered by adapter → Store
    - Others: Score and store
    
    Returns summary dict with counts per category.
    """
    try:
        sources = get_enabled_sources()
        all_items = []
        
        # Fetch from all sources
        for source in sources:
            adapter = create_adapter_from_source(source)
            if adapter:
                try:
                    items = adapter.fetch_and_normalize()
                    logger.info(f"Fetched {len(items)} items from {source.get('name')}")
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source.get('name')} ({source.get('base_url')}): {e}", exc_info=True)
                    update_source_cache(source_name=source.get('name'), status='error', notes=str(e))
                    continue
            else:
                logger.warning(f"Could not create adapter for {source.get('name')} (type: {source.get('type')})")
        
        logger.info(f"Total fetched: {len(all_items)} items from {len(sources)} sources")
        
        # Process by category
        events_result = process_events(all_items)
        news_items = process_news(all_items)
        weather_items = process_weather(all_items)
        reddit_items = process_reddit(all_items)
        
        # Get other category items
        other_items = [item for item in all_items 
                      if item.get('category') not in ('event', 'news', 'weather', 'community')]
        
        # Combine all processed items (events already imported, don't re-store)
        items_to_store = news_items + weather_items + reddit_items + other_items
        
        # Score all items
        scored = score_items(items_to_store)
        logger.info(f"Scored {len(scored)} items")
        
        # Store in database
        stored = store_source_items(scored)
        logger.info(f"Stored {len(scored)} items in cache")
        
        # Update cache metadata per source
        sources_seen = set(item.get('source_name') for item in all_items if item.get('source_name'))
        for source_name in sources_seen:
            source_items = [i for i in all_items if i.get('source_name') == source_name]
            update_source_cache(
                source_name=source_name, 
                status='success', 
                notes=f"Fetched {len(source_items)} items"
            )
        
        return {
            'success': True,
            'fetched': len(all_items),
            'events': events_result,
            'news_analyzed': len(news_items),
            'weather': len(weather_items),
            'community': len(reddit_items),
            'other': len(other_items),
            'scored': len(scored),
            'stored': stored,
        }
    except Exception as e:
        logger.error(f"Prefetch job failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }

