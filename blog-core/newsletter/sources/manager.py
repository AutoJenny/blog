"""Source manager orchestrates all adapters and handles configuration."""

from __future__ import annotations

from typing import Any, Dict, List
from config.database import db_manager
from newsletter.sources.rss_adapter import RSSAdapter
from newsletter.sources.reddit_adapter import RedditAdapter
from newsletter.sources.html_adapter import HTMLAdapter


def get_enabled_sources() -> List[Dict[str, Any]]:
    """Get enabled sources from newsletter_snapshot_source table."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, base_url, type, enabled, api_key_ref
                FROM newsletter_snapshot_source
                WHERE enabled = TRUE
                ORDER BY id
                """
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def create_adapter_from_source(source: Dict[str, Any]) -> RSSAdapter | RedditAdapter | HTMLAdapter | None:
    """Create appropriate adapter based on source type.
    
    Source types map:
    - rss: RSSAdapter
    - reddit: RedditAdapter
    - html: HTMLAdapter
    """
    source_type = source.get('type', '').lower()
    name = source.get('name', '')
    base_url = source.get('base_url', '')
    
    if source_type == 'rss':
        # Category from name/type hints - be explicit to avoid misclassification
        name_lower = name.lower()
        category = 'news'  # default
        
        # Weather sources: explicit checks
        if any(term in name_lower for term in ['weather', 'met office', 'metoffice', 'forecast', 'warnings']):
            category = 'weather'
        # News sources: explicit checks
        elif any(term in name_lower for term in ['bbc', 'scotsman', 'news']):
            category = 'news'
        # Default to news if unclear
        
        return RSSAdapter(source_name=name, feed_url=base_url, category=category)
    
    elif source_type == 'reddit':
        # Extract subreddit from URL (e.g., https://reddit.com/r/Scotland -> Scotland)
        subreddit = 'Scotland'  # default
        if '/r/' in base_url:
            parts = base_url.split('/r/')
            if len(parts) > 1:
                subreddit = parts[1].split('/')[0].split('?')[0]
        return RedditAdapter(source_name=name, subreddit=subreddit, category='community')
    
    elif source_type in ('html', 'event', 'museum'):
        # HTML scraper for "What's On" pages
        # Default selector targets common event listing patterns
        selector = 'article, .event-item, .event, [class*="event"]'
        return HTMLAdapter(
            source_name=name,
            base_url=base_url,
            category='event',
            selector=selector
        )
    
    return None


def fetch_all_sources() -> List[Dict[str, Any]]:
    """Fetch from all enabled sources and return normalized items."""
    import logging
    logger = logging.getLogger(__name__)
    
    sources = get_enabled_sources()
    all_items = []
    
    for source in sources:
        adapter = create_adapter_from_source(source)
        if adapter:
            try:
                items = adapter.fetch_and_normalize()
                logger.info(f"Fetched {len(items)} items from {source.get('name')}")
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source.get('name')} ({source.get('base_url')}): {e}", exc_info=True)
                continue  # Skip on error, continue with other sources
        else:
            logger.warning(f"Could not create adapter for {source.get('name')} (type: {source.get('type')})")
    
    return all_items

