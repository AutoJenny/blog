"""RSS/Atom feed adapter for BBC Scotland, Met Office, etc."""

from __future__ import annotations

import feedparser
from typing import Any, Dict, List, Optional
from datetime import datetime
from newsletter.sources.base import SourceAdapter


class RSSAdapter(SourceAdapter):
    """Adapter for RSS/Atom feeds."""
    
    def __init__(self, source_name: str, feed_url: str, category: str, rate_limit_minutes: int = 60):
        """Initialize with feed URL and content category."""
        super().__init__(source_name, rate_limit_minutes)
        self.feed_url = feed_url
        self.category = category  # weather|event|community|news|other
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            feed = feedparser.parse(self.feed_url)
            
            # Check for feed errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS feed parse error for {self.feed_url}: {feed.bozo_exception}")
            
            items = []
            for entry in feed.entries[:20]:  # Limit to recent 20
                items.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'summary': entry.get('summary', ''),
                    'description': entry.get('description', ''),
                })
            
            logger.debug(f"Fetched {len(items)} items from {self.feed_url}")
            return items
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {self.feed_url}: {e}", exc_info=True)
            return []
    
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize RSS entry to common shape."""
        title = raw_item.get('title', '').strip()
        url = raw_item.get('link', '').strip()
        if not title or not url:
            return None
        
        # Parse published date
        published_at = None
        if raw_item.get('published_parsed'):
            try:
                import time
                ts = raw_item['published_parsed']
                published_at = datetime(*ts[:6])
            except Exception:
                pass
        
        return {
            'source_name': self.source_name,
            'title': title,
            'url': url,
            'published_at': published_at,
            'event_date': None,
            'location': None,
            'category': self.category,
            'raw_data': raw_item,
        }

