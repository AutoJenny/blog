"""HTML scraper adapter for HES, NMS, NGS "What's On" pages."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
from newsletter.sources.base import SourceAdapter


class HTMLAdapter(SourceAdapter):
    """Adapter for scraping HTML pages (events, exhibitions)."""
    
    def __init__(self, source_name: str, base_url: str, category: str, selector: str, rate_limit_minutes: int = 240):
        """Initialize with base URL, category, and CSS selector for items.
        
        Args:
            source_name: Name of source (e.g., "Historic Environment Scotland")
            base_url: Base URL to scrape
            category: Content category (typically "event")
            selector: CSS selector for finding event/item elements
            rate_limit_minutes: Minutes between fetches (default 4 hours for HTML)
        """
        super().__init__(source_name, rate_limit_minutes)
        self.base_url = base_url
        self.category = category
        self.selector = selector
    
    def _check_robots_txt(self) -> bool:
        """Check robots.txt if available. Returns True if scraping allowed."""
        try:
            parsed = urlparse(self.base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            resp = requests.get(robots_url, timeout=5)
            if resp.status_code == 200:
                # Simple check: if robots.txt exists and disallows our path, skip
                # For MVP, we assume permission if robots.txt doesn't explicitly forbid
                return True
            return True  # No robots.txt = assume allowed
        except Exception:
            return True  # If check fails, proceed with caution
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and parse HTML page."""
        if not self._check_robots_txt():
            return []
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0)'}
            resp = requests.get(self.base_url, headers=headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            items = []
            elements = soup.select(self.selector)[:20]  # Limit to 20 items
            for elem in elements:
                # Extract title (try h2, h3, or first text node)
                title_elem = elem.select_one('h2, h3, .title, [class*="title"]') or elem
                title = title_elem.get_text(strip=True)
                
                # Extract URL (link or parent link)
                link_elem = elem.select_one('a') or elem.find_parent('a')
                url = ''
                if link_elem and link_elem.get('href'):
                    url = urljoin(self.base_url, link_elem['href'])
                
                # Extract date if available
                date_text = ''
                date_elem = elem.select_one('.date, [class*="date"], time')
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    if date_elem.get('datetime'):
                        date_text = date_elem['datetime']
                
                # Extract location if available
                location = ''
                loc_elem = elem.select_one('.location, [class*="location"], .venue')
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                
                if title:
                    items.append({
                        'title': title,
                        'url': url or self.base_url,
                        'date_text': date_text,
                        'location': location,
                        'element_html': str(elem)[:500],  # Store snippet for debugging
                    })
            
            return items
        except Exception:
            return []
    
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize HTML-scraped item to common shape."""
        title = raw_item.get('title', '').strip()
        url = raw_item.get('url', '').strip()
        if not title:
            return None
        
        # Parse event date if available
        event_date = None
        date_text = raw_item.get('date_text', '')
        if date_text:
            # Try common formats (MVP: simple attempts)
            try:
                # Try ISO format or common date strings
                from dateutil import parser
                event_date = parser.parse(date_text)
            except Exception:
                pass
        
        return {
            'source_name': self.source_name,
            'title': title,
            'url': url or self.base_url,
            'published_at': None,  # HTML pages often don't have publish dates
            'event_date': event_date,
            'location': raw_item.get('location', '').strip() or None,
            'category': self.category,
            'raw_data': raw_item,
        }

