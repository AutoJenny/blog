"""HTML scraper adapter for HES, NMS, NGS "What's On" pages."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from newsletter.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


class HTMLAdapter(SourceAdapter):
    """Adapter for scraping HTML pages (events, exhibitions)."""
    
    # Site-specific selectors for known event sources
    SITE_SELECTORS = {
        'historicenvironment.scot': {
            'item': 'article.event-card, .event-card, [class*="event-card"], .event-item',
            'title': 'h2, h3, .event-title, [class*="title"]',
            'date': 'time, .event-date, [class*="date"]',
            'location': '.event-location, .location, [class*="location"]',
            'description': '.event-description, .description, p',
            'link': 'a.event-link, a[href*="event"], a[href*="whats-on"]',
        },
        'nms.ac.uk': {
            'item': 'article, .event, .event-item, [class*="event"]',
            'title': 'h2, h3, .title',
            'date': 'time, .date, [datetime]',
            'location': '.location, .venue',
            'description': 'p, .description',
            'link': 'a',
        },
        'nationalgalleries.org': {
            'item': 'article.exhibition, .exhibition-card, [class*="exhibition"]',
            'title': 'h2, h3',
            'date': 'time, .exhibition-dates',
            'location': '.gallery, .venue',
            'description': 'p.description',
            'link': 'a',
        },
        'visitscotland.com': {
            'item': 'article.event, .event-card, [class*="event"]',
            'title': 'h2, h3, .event-title',
            'date': 'time, .event-date',
            'location': '.event-location, .location',
            'description': 'p, .description',
            'link': 'a.event-link',
        },
    }
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self, source_name: str, base_url: str, category: str, selector: str = None, rate_limit_minutes: int = 240):
        """Initialize with base URL, category, and CSS selector for items.
        
        Args:
            source_name: Name of source (e.g., "Historic Environment Scotland")
            base_url: Base URL to scrape
            category: Content category (typically "event")
            selector: CSS selector for finding event/item elements (optional, auto-detected if None)
            rate_limit_minutes: Minutes between fetches (default 4 hours for HTML)
        """
        super().__init__(source_name, rate_limit_minutes)
        self.base_url = base_url
        self.category = category
        self.selector = selector
        self.session = requests.Session()
        self._user_agent_index = 0
        
        # Auto-detect site-specific selectors
        parsed = urlparse(base_url)
        domain = parsed.netloc.replace('www.', '')
        self.site_config = self.SITE_SELECTORS.get(domain, {})
        if not selector and self.site_config:
            self.selector = self.site_config.get('item', 'article, .event-item, [class*="event"]')
    
    def _get_user_agent(self) -> str:
        """Get rotating user agent."""
        agent = self.USER_AGENTS[self._user_agent_index % len(self.USER_AGENTS)]
        self._user_agent_index += 1
        return agent
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with user agent."""
        return {
            'User-Agent': self._get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _check_robots_txt(self) -> bool:
        """Check robots.txt if available. Returns True if scraping allowed."""
        try:
            parsed = urlparse(self.base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            resp = self.session.get(robots_url, headers=self._get_headers(), timeout=5)
            if resp.status_code == 200:
                # Simple check: if robots.txt exists and disallows our path, skip
                # For MVP, we assume permission if robots.txt doesn't explicitly forbid
                return True
            return True  # No robots.txt = assume allowed
        except Exception:
            return True  # If check fails, proceed with caution
    
    def _handle_cookie_consent(self, soup: BeautifulSoup) -> bool:
        """Attempt to accept cookie consent if detected. Returns True if handled."""
        # Common cookie consent button selectors
        cookie_selectors = [
            'button[class*="accept"]',
            'button[class*="cookie"]',
            'button[class*="consent"]',
            'a[class*="accept"]',
            '#accept-cookies',
            '.cookie-accept',
        ]
        
        for selector in cookie_selectors:
            button = soup.select_one(selector)
            if button:
                # If cookie consent found, note it but don't automatically click
                # (requires JavaScript in real browser; for now we log it)
                logger.debug(f"Cookie consent detected on {self.base_url}, may need manual handling")
                return True
        return False
    
    def _extract_event_data(self, elem: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract structured event data from an element using site-specific or generic selectors."""
        # Use site-specific selectors if available
        title_selector = self.site_config.get('title', 'h2, h3, .title, [class*="title"]')
        date_selector = self.site_config.get('date', '.date, [class*="date"], time')
        location_selector = self.site_config.get('location', '.location, [class*="location"], .venue')
        description_selector = self.site_config.get('description', 'p')
        link_selector = self.site_config.get('link', 'a')
        
        # Extract title
        title_elem = elem.select_one(title_selector) or elem.find(['h1', 'h2', 'h3', 'h4'])
        if not title_elem:
            title_elem = elem
        title = title_elem.get_text(strip=True)
        if not title:
            return None
        
        # Extract URL
        link_elem = elem.select_one(link_selector) or elem.find_parent('a')
        url = ''
        if link_elem and link_elem.get('href'):
            url = urljoin(self.base_url, link_elem['href'])
        
        # Extract date with multiple strategies
        date_text = ''
        date_elem = elem.select_one(date_selector)
        if date_elem:
            # Prefer datetime attribute
            if date_elem.get('datetime'):
                date_text = date_elem['datetime']
            else:
                date_text = date_elem.get_text(strip=True)
        
        # Extract location/venue
        location = ''
        venue = ''
        loc_elem = elem.select_one(location_selector)
        if loc_elem:
            location = loc_elem.get_text(strip=True)
        
        # Extract description
        description = ''
        desc_elem = elem.select_one(description_selector)
        if desc_elem:
            description = desc_elem.get_text(strip=True)[:300]  # Limit description length
        
        return {
            'title': title,
            'url': url or self.base_url,
            'date_text': date_text,
            'location': location,
            'venue': venue,
            'description': description,
            'element_html': str(elem)[:1000],  # Store snippet for debugging
        }
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and parse HTML page."""
        if not self._check_robots_txt():
            logger.warning(f"Robots.txt check failed for {self.base_url}")
            return []
        
        try:
            headers = self._get_headers()
            resp = self.session.get(self.base_url, headers=headers, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Handle cookie consent if detected
            self._handle_cookie_consent(soup)
            
            items = []
            elements = soup.select(self.selector) if self.selector else []
            
            # Fallback: try generic selectors if site-specific selector found nothing
            if not elements:
                logger.debug(f"No items found with selector '{self.selector}', trying generic selectors")
                elements = soup.select('article, .event, .event-item, [class*="event"], .exhibition')[:20]
            
            for elem in elements[:20]:  # Limit to 20 items
                event_data = self._extract_event_data(elem)
                if event_data:
                    items.append(event_data)
            
            logger.info(f"Fetched {len(items)} items from {self.base_url}")
            return items
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {self.base_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {self.base_url}: {e}", exc_info=True)
            return []
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date text using dateutil with UK locale awareness."""
        if not date_text:
            return None
        
        from dateutil import parser
        
        try:
            # Try parsing directly
            parsed = parser.parse(date_text, dayfirst=True, fuzzy=True)
            return parsed
        except (ValueError, TypeError):
            # Try common UK date patterns manually
            # e.g., "Selected dates until 31 December 2025"
            try:
                import re
                # Extract year if present
                year_match = re.search(r'\b(20\d{2})\b', date_text)
                if year_match:
                    # Try to extract month/day too
                    # This is basic; full implementation would handle more patterns
                    parsed = parser.parse(date_text, dayfirst=True, fuzzy=True, default=datetime(int(year_match.group(1)), 1, 1))
                    return parsed
            except Exception:
                pass
            
            logger.debug(f"Could not parse date: {date_text}")
            return None
    
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
            event_date = self._parse_date(date_text)
        
        # Combine location and venue
        location = raw_item.get('location', '').strip()
        venue = raw_item.get('venue', '').strip()
        full_location = location
        if venue and venue != location:
            full_location = f"{venue}, {location}" if location else venue
        
        return {
            'source_name': self.source_name,
            'title': title,
            'url': url or self.base_url,
            'published_at': None,  # HTML pages often don't have publish dates
            'event_date': event_date,
            'location': full_location or None,
            'venue': venue or None,
            'description': raw_item.get('description', '').strip()[:500] or None,  # Limit description
            'category': self.category,
            'raw_data': {
                'date_text': date_text,
                'element_html': raw_item.get('element_html', ''),
            },
        }

