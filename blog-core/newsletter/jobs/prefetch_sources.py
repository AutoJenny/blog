"""Daily prefetch job to refresh source item cache."""

from __future__ import annotations

import logging
from newsletter.sources.manager import fetch_all_sources
from newsletter.services.scoring import score_items
from newsletter.db.queries_sources import store_source_items, update_source_cache

logger = logging.getLogger(__name__)


def run() -> dict:
    """Fetch from all enabled sources, score items, store in cache.
    
    Returns summary dict with counts.
    """
    try:
        # Fetch from all sources
        items = fetch_all_sources()
        logger.info(f"Fetched {len(items)} raw items from sources")
        
        # Score all items
        scored = score_items(items)
        logger.info(f"Scored {len(scored)} items")
        
        # Store in database
        stored = store_source_items(scored)
        logger.info(f"Stored {len(scored)} items in cache")
        
        # Update cache metadata (one per source)
        sources_seen = set(item.get('source_name') for item in items if item.get('source_name'))
        for source_name in sources_seen:
            update_source_cache(source_name=source_name, status='success', notes=f"Fetched {len([i for i in items if i.get('source_name') == source_name])} items")
        
        return {
            'success': True,
            'fetched': len(items),
            'scored': len(scored),
            'stored': stored,
        }
    except Exception as e:
        logger.error(f"Prefetch job failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }

