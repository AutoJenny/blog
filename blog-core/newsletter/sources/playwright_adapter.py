"""Playwright-based adapter for JavaScript-rendered pages and JSON/XHR payload extraction."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import re
from bs4 import BeautifulSoup
from newsletter.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, Browser, Page, Response
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install")


class PlaywrightAdapter(SourceAdapter):
    """Adapter for scraping JavaScript-rendered pages using Playwright.
    
    Features:
    - Real browser rendering (handles JS, cookies, sessions)
    - Automatic cookie consent handling
    - JSON/XHR payload interception (bypasses DOM scraping when possible)
    - JSON-LD extraction from rendered DOM
    """
    
    # Site-specific configurations
    SITE_CONFIGS = {
        'nationalgalleries.org': {
            'wait_selector': 'body',
            'wait_timeout': 60000,  # Very long wait for slow-loading page
            'cookie_consent_selectors': [
                'button[class*="accept"]',
                'button[class*="cookie"]',
                '#accept-cookies',
                '.cookie-accept',
            ],
            'json_ld_extract': True,
            'xhr_patterns': [
                r'/api/.*exhibitions?',
                r'/api/.*events?',
                r'/api/.*whats-on',
            ],
            # Try to extract from links or content
            'item_selector': 'a[href*="exhibition"], a[href*="/whats-on/"]',
            'min_text_length': 10,
            'skip_text': ['what\'s on', 'whats on', 'home', 'exhibitions', 'quicklinks'],
        },
        'nms.ac.uk': {
            'wait_selector': 'main, body',
            'wait_timeout': 20000,  # Longer wait for JS-loaded content
            'cookie_consent_selectors': [
                'button[class*="accept"]',
                'button[class*="cookie"]',
                '#accept-cookies',
            ],
            'json_ld_extract': True,
            'xhr_patterns': [
                r'/api/.*events?',
                r'/api/.*whats-on',
                r'/api/.*activities?',
            ],
            # National Museums uses /events/ URLs for individual events
            'item_selector': 'a[href*="/events/"]',
            'skip_text': ['what\'s on', 'whats on', 'home', 'exhibitions', 'events', 'view all', 'all events'],
            'min_text_length': 10,
        },
        'visitscotland.com': {
            'wait_selector': 'main, article, [class*="event"]',
            'wait_timeout': 15000,
            'cookie_consent_selectors': [
                'button[class*="accept"]',
                'button[class*="cookie"]',
                '#accept-cookies',
            ],
            'json_ld_extract': True,
            'xhr_patterns': [
                r'/api/.*events?',
            ],
            # VisitScotland lists events directly on category pages (not linked)
            # Extract from page content - events are listed with dates
            'extract_from_content': True,
            'content_patterns': [
                r'^([A-Z][^–-]{10,60}?)\s*[–-]\s*(\d+\s+\w+\s+[–-]\s*\d+\s+\w+\s+\d{4})',  # Name – Date range (start of line)
                r'^([A-Z][^–-]{10,60}?)\s*[–-]\s*(\d+\s+\w+\s+\d{4})',  # Name – Single date (start of line)
                r'^([A-Z][^–-]{10,60}?)\s*[–-]\s*(\w+\s+[–-]\s*\w+)',  # Name – Month range (start of line)
            ],
        },
    }
    
    def __init__(self, source_name: str, base_url: str, category: str, rate_limit_minutes: int = 240):
        """Initialize Playwright adapter.
        
        Args:
            source_name: Name of source
            base_url: Base URL to scrape
            category: Content category (typically "event")
            rate_limit_minutes: Minutes between fetches
        """
        super().__init__(source_name, rate_limit_minutes)
        self.base_url = base_url
        self.category = category
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available. Install with: pip install playwright && playwright install chromium")
        
        parsed = urlparse(base_url)
        domain = parsed.netloc.replace('www.', '')
        self.site_config = self.SITE_CONFIGS.get(domain, {})
    
    def __init__(self, source_name: str, base_url: str, category: str, rate_limit_minutes: int = 240):
        """Initialize Playwright adapter.
        
        Args:
            source_name: Name of source
            base_url: Base URL to scrape
            category: Content category (typically "event")
            rate_limit_minutes: Minutes between fetches
        """
        super().__init__(source_name, rate_limit_minutes)
        self.base_url = base_url
        self.category = category
        self._intercepted_responses = []  # Store intercepted responses
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available. Install with: pip install playwright && playwright install chromium")
        
        parsed = urlparse(base_url)
        domain = parsed.netloc.replace('www.', '')
        self.site_config = self.SITE_CONFIGS.get(domain, {})
    
    def _handle_cookie_consent(self, page: Page) -> bool:
        """Attempt to accept cookie consent. Returns True if handled."""
        selectors = self.site_config.get('cookie_consent_selectors', [
            'button[class*="accept"]',
            'button[class*="cookie"]',
            '#accept-cookies',
            '.cookie-accept',
        ])
        
        for selector in selectors:
            try:
                button = page.query_selector(selector)
                if button:
                    button.click()
                    page.wait_for_timeout(1000)  # Wait for consent to process
                    logger.info(f"Accepted cookie consent on {self.base_url}")
                    return True
            except Exception as e:
                logger.debug(f"Cookie consent selector '{selector}' not found: {e}")
                continue
        return False
    
    def _setup_xhr_interception(self, page: Page) -> None:
        """Set up XHR/JSON response interception."""
        xhr_patterns = self.site_config.get('xhr_patterns', [])
        self._intercepted_responses = []
        
        def handle_response(response: Response):
            try:
                url = response.url
                # Check if URL matches any pattern
                matches = any(re.search(pattern, url, re.IGNORECASE) for pattern in xhr_patterns)
                
                if matches and response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        try:
                            data = response.json()
                            self._intercepted_responses.append({
                                'url': url,
                                'data': data,
                                'type': 'xhr_json'
                            })
                            logger.debug(f"Intercepted JSON response from {url}")
                        except Exception as e:
                            logger.debug(f"Error parsing JSON from {url}: {e}")
            except Exception as e:
                logger.debug(f"Error intercepting response: {e}")
        
        page.on('response', handle_response)
    
    def _extract_json_ld(self, page: Page) -> List[Dict[str, Any]]:
        """Extract JSON-LD structured data from page."""
        json_ld_items = []
        
        try:
            # Execute JavaScript to extract JSON-LD
            json_ld_scripts = page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    return Array.from(scripts).map(s => {
                        try {
                            return JSON.parse(s.textContent);
                        } catch (e) {
                            return null;
                        }
                    }).filter(d => d !== null);
                }
            """)
            
            for item in json_ld_scripts:
                # Check if it's event/exhibition related
                item_type = item.get('@type', '').lower()
                if any(keyword in item_type for keyword in ['event', 'exhibition', 'thing']):
                    json_ld_items.append(item)
                    logger.debug(f"Extracted JSON-LD: {item.get('@type', 'unknown')}")
        except Exception as e:
            logger.debug(f"Error extracting JSON-LD: {e}")
        
        return json_ld_items
    
    def _extract_from_content(self, page: Page) -> List[Dict[str, Any]]:
        """Extract events from page content using regex patterns (for sites that list events inline)."""
        items = []
        
        try:
            extract_from_content = self.site_config.get('extract_from_content', False)
            if not extract_from_content:
                return []
            
            # Get page text content - split by lines for better pattern matching
            page_text = page.inner_text('main, article, body')
            lines = page_text.split('\n')
            
            # Try patterns to extract event names and dates
            import re
            patterns = self.site_config.get('content_patterns', [])
            
            seen_titles = set()
            
            for line in lines:
                line = line.strip()
                if not line or len(line) < 15:
                    continue
                
                # Try each pattern on this line
                for pattern in patterns:
                    match = re.match(pattern, line, re.MULTILINE)
                    if match:
                        name = match.group(1).strip()
                        date_text = match.group(2).strip() if len(match.groups()) > 1 else ''
                        
                        # Clean name (remove extra whitespace, trailing dashes)
                        name = re.sub(r'\s+', ' ', name).strip(' –-')
                        
                        # Skip if too short or generic
                        if len(name) < 10 or len(name) > 100:
                            continue
                        
                        # Skip common non-event text
                        skip_keywords = ['toggle', 'caption', 'share', 'home', 'things to do', 'events', 'categories', 
                                       'october, november', 'january, february', 'april, may', 'july, august']
                        if any(kw in name.lower() for kw in skip_keywords):
                            continue
                        
                        # Skip if already seen (deduplicate)
                        name_lower = name.lower()
                        if name_lower in seen_titles:
                            continue
                        seen_titles.add(name_lower)
                        
                        items.append({
                            'title': name,
                            'url': self.base_url,  # Category page URL
                            'date_text': date_text,
                            'location': '',
                            'description': '',
                        })
                        break  # Found match, move to next line
            
            if items:
                logger.info(f"Extracted {len(items)} items from page content")
            
        except Exception as e:
            logger.debug(f"Content extraction failed: {e}")
        
        return items
    
    def _extract_from_dom(self, page: Page) -> List[Dict[str, Any]]:
        """Extract event data from rendered DOM."""
        items = []
        
        try:
            # First try content-based extraction (for sites like VisitScotland that list events inline)
            content_items = self._extract_from_content(page)
            if content_items:
                return content_items
            
            # Use site-specific item selector if available (for link-based extraction)
            item_selector = self.site_config.get('item_selector')
            skip_text = self.site_config.get('skip_text', [])
            
            if item_selector:
                # Extract directly via Playwright (better for dynamic content)
                try:
                    # Wait a bit more for dynamic content to load
                    page.wait_for_timeout(3000)
                    
                    links = page.query_selector_all(item_selector)
                    logger.debug(f"Found {len(links)} links matching item selector")
                    
                    min_length = self.site_config.get('min_text_length', 10)
                    seen_urls = set()
                    
                    for link in links[:50]:  # Check more links
                        text = link.inner_text().strip()
                        href = link.get_attribute('href') or ''
                        
                        # Skip navigation URLs (but allow specific event pages)
                        if not href:
                            continue
                        
                        # For NMS: skip if it's just "/events/" but allow "/events/specific-event"
                        if '/events/' in href:
                            # Extract the event slug after /events/
                            parts = href.split('/events/')
                            if len(parts) > 1 and parts[1]:
                                event_slug = parts[1].split('/')[0].split('?')[0]
                                # Allow if it has an actual event slug
                                if event_slug and len(event_slug) > 3:
                                    pass  # This is a valid event URL
                                else:
                                    continue  # Just "/events/" - skip
                            else:
                                continue  # No event slug - skip
                        elif '/whats-on/' in href or '/activities/' in href:
                            # Similar check for whats-on and activities
                            continue  # Skip base category pages
                        
                        # Build full URL
                        if not href.startswith('http'):
                            href = urljoin(self.base_url, href)
                        
                        # Skip navigation/header links
                        if not text:
                            continue
                        
                        if any(skip in text.lower() for skip in skip_text):
                            continue
                        
                        # Enforce minimum text length
                        if len(text) < min_length:
                            continue
                        
                        # Skip if it's not an actual event page (should have more path after /whats-on/)
                        if '/whats-on/' in href:
                            # Extract path after /whats-on/
                            parts = href.split('/whats-on/')
                            if len(parts) > 1:
                                after_path = parts[1].split('/')[0].split('?')[0]
                            else:
                                after_path = ''
                            
                            # If after_path is empty or just navigation, skip
                            if not after_path or after_path in ['', '#']:
                                continue
                        
                        # Build full URL
                        if href and not href.startswith('http'):
                            from urllib.parse import urljoin
                            href = urljoin(self.base_url, href)
                        
                        items.append({
                            'title': text,
                            'url': href or self.base_url,
                            'date_text': '',
                            'location': '',
                            'description': '',
                        })
                    
                    if items:
                        logger.info(f"Extracted {len(items)} items from links")
                        return items
                except Exception as e:
                    logger.debug(f"Link-based extraction failed: {e}, falling back to DOM")
            
            # Fallback: Use BeautifulSoup for DOM parsing
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # For National Museums: try to find /events/ links in the DOM first
            if 'nms.ac.uk' in self.base_url:
                event_links = soup.select('a[href*="/events/"]')
                logger.debug(f"Found {len(event_links)} /events/ links in DOM")
                
                seen = set()
                skip_text = ['events', 'what\'s on', 'whats on', 'home', 'view all', 'all events']
                
                for link in event_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    # Build full URL
                    if not href.startswith('http'):
                        from urllib.parse import urljoin
                        href = urljoin(self.base_url, href)
                    
                    if href in seen:
                        continue
                    
                    # Validate event slug
                    if '/events/' in href:
                        parts = href.split('/events/')
                        if len(parts) > 1 and parts[1]:
                            slug = parts[1].split('/')[0].split('?')[0]
                            if slug and len(slug) > 3:
                                # Extract text - try link first, then parent
                                text = link.get_text(strip=True)
                                
                                # Clean text: remove "Events" prefix, extract title
                                # Format is often "EventsEvent TitleDate info"
                                import re
                                # Remove "Events" at start
                                text = re.sub(r'^events\s*', '', text, flags=re.IGNORECASE)
                                
                                # Try to extract just the title (before date pattern)
                                # Dates often start with day name or number
                                date_pattern = r'\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|\d{1,2}\s+\w+\s+-)'
                                match = re.search(date_pattern, text)
                                if match:
                                    text = text[:match.start()].strip()
                                
                                # If still messy, get parent text and extract first meaningful line
                                if not text or len(text) < 10 or any(skip in text.lower() for skip in skip_text):
                                    parent = link.find_parent(['div', 'article', 'li', 'section', 'h2', 'h3'])
                                    if parent:
                                        parent_text = parent.get_text(strip=True)
                                        # Try to get the title line (usually first or second line)
                                        lines = [l.strip() for l in parent_text.split('\n') if l.strip()]
                                        for line in lines[:3]:
                                            # Skip date-only lines
                                            if re.match(r'^\d+', line) and ('-' in line or len(line) < 30):
                                                continue
                                            if len(line) > 15 and not any(skip in line.lower() for skip in skip_text):
                                                text = line[:100]
                                                break
                                
                                # Final cleanup
                                text = re.sub(r'\s+', ' ', text).strip()
                                text = text.strip(' –-')
                                
                                if text and len(text) > 10 and len(text) < 150:
                                    if not any(skip in text.lower() for skip in skip_text):
                                        # Extract date from parent if available
                                        date_text = ''
                                        parent = link.find_parent(['div', 'article', 'li', 'section'])
                                        if parent:
                                            parent_text = parent.get_text()
                                            # Look for date patterns
                                            date_match = re.search(r'(\d+\s+\w+\s+-?\s*\d*\s*\w*\s*\d{4})', parent_text)
                                            if date_match:
                                                date_text = date_match.group(1)
                                        
                                        items.append({
                                            'title': text,
                                            'url': href,
                                            'date_text': date_text,
                                            'location': '',
                                            'description': '',
                                        })
                                        seen.add(href)
                
                if items:
                    logger.info(f"Extracted {len(items)} items from DOM /events/ links")
                    return items
            
            # For National Galleries: try to extract exhibition links
            if 'nationalgalleries.org' in self.base_url:
                # Look for links to specific exhibitions
                exhibition_links = soup.select('a[href*="exhibition"], a[href*="/whats-on/"]')
                logger.debug(f"Found {len(exhibition_links)} exhibition links in DOM")
                
                skip_text = self.site_config.get('skip_text', ['what\'s on', 'whats on', 'home', 'exhibitions'])
                seen = set()
                
                for link in exhibition_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    # Build full URL
                    if not href.startswith('http'):
                        from urllib.parse import urljoin
                        href = urljoin(self.base_url, href)
                    
                    if href in seen:
                        continue
                    
                    # Validate - should be a specific exhibition page, not category
                    if '/whats-on/' in href:
                        parts = href.split('/whats-on/')
                        if len(parts) > 1 and parts[1]:
                            page_slug = parts[1].split('/')[0].split('?')[0]
                            if page_slug and page_slug not in ['', 'exhibitions', '#'] and len(page_slug) > 3:
                                text = link.get_text(strip=True)
                                
                                # Clean text
                                if text and len(text) > 10:
                                    if not any(skip in text.lower() for skip in skip_text):
                                        items.append({
                                            'title': text[:150],
                                            'url': href,
                                            'date_text': '',
                                            'location': '',
                                            'description': '',
                                        })
                                        seen.add(href)
                
                if items:
                    logger.info(f"Extracted {len(items)} items from National Galleries links")
                    return items
            
            # Generic DOM extraction for other sites
            # Use site-specific or generic selectors
            wait_selector = self.site_config.get('wait_selector', 'article, .event, .exhibition, [class*="event"], [class*="exhibition"]')
            elements = soup.select(wait_selector)
            
            if not elements:
                # Fallback to generic selectors
                elements = soup.select('article, .event, .exhibition, [class*="event"], [class*="exhibition"]')
            
            for elem in elements[:20]:  # Limit to 20 items
                event_data = self._parse_event_element(elem)
                if event_data:
                    # Skip cookie consent and error messages
                    title_lower = event_data.get('title', '').lower()
                    if any(word in title_lower for word in ['cookie', 'cookiebot', 'accept', 'hmm, it seems', 'error', 'quicklinks']):
                        continue
                    
                    # Skip if URL points to cookie consent or error pages
                    url = event_data.get('url', '')
                    if 'cookiebot' in url.lower() or 'error' in url.lower():
                        continue
                    
                    items.append(event_data)
            
            logger.info(f"Extracted {len(items)} items from DOM")
        except Exception as e:
            logger.error(f"Error extracting from DOM: {e}", exc_info=True)
        
        return items
    
    def _parse_event_element(self, elem: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse a single event element from DOM."""
        # Extract title
        title_elem = elem.select_one('h1, h2, h3, h4, .title, [class*="title"], [class*="heading"]')
        if not title_elem:
            title_elem = elem
        title = title_elem.get_text(strip=True)
        
        if not title or len(title) < 3:
            return None
        
        # Extract URL
        link_elem = elem.select_one('a[href]') or elem.find_parent('a')
        url = ''
        if link_elem and link_elem.get('href'):
            url = urljoin(self.base_url, link_elem['href'])
        
        # Extract date
        date_text = ''
        date_elem = elem.select_one('time, [datetime], [class*="date"]')
        if date_elem:
            if date_elem.get('datetime'):
                date_text = date_elem['datetime']
            else:
                date_text = date_elem.get_text(strip=True)
        
        # Extract location
        location = ''
        loc_elem = elem.select_one('[class*="location"], [class*="venue"], [class*="place"]')
        if loc_elem:
            location = loc_elem.get_text(strip=True)
        
        # Extract description
        description = ''
        desc_elem = elem.select_one('p, [class*="description"], [class*="summary"]')
        if desc_elem:
            description = desc_elem.get_text(strip=True)[:300]
        
        return {
            'title': title,
            'url': url or self.base_url,
            'date_text': date_text,
            'location': location,
            'description': description,
        }
    
    def _parse_xhr_json_data(self, json_data: Dict[str, Any], source_url: str) -> List[Dict[str, Any]]:
        """Parse intercepted XHR JSON responses into event items."""
        items = []
        
        try:
            # Common JSON structures for event data
            if isinstance(json_data, dict):
                # Try different common structures
                events = (
                    json_data.get('events', []) or
                    json_data.get('items', []) or
                    json_data.get('data', []) or
                    json_data.get('results', []) or
                    [json_data] if json_data.get('title') or json_data.get('name') else []
                )
                
                for event in events:
                    if isinstance(event, dict):
                        title = event.get('title') or event.get('name') or event.get('label', '')
                        if title:
                            items.append({
                                'title': title,
                                'url': event.get('url') or event.get('link') or source_url,
                                'date_text': event.get('date') or event.get('startDate') or event.get('when', ''),
                                'location': event.get('location') or event.get('venue') or event.get('where', ''),
                                'description': event.get('description') or event.get('summary', '')[:300],
                            })
            
            elif isinstance(json_data, list):
                # If data is already a list of events
                for event in json_data:
                    if isinstance(event, dict):
                        title = event.get('title') or event.get('name') or event.get('label', '')
                        if title:
                            items.append({
                                'title': title,
                                'url': event.get('url') or event.get('link') or source_url,
                                'date_text': event.get('date') or event.get('startDate') or event.get('when', ''),
                                'location': event.get('location') or event.get('venue') or event.get('where', ''),
                                'description': event.get('description') or event.get('summary', '')[:300],
                            })
        
        except Exception as e:
            logger.error(f"Error parsing XHR JSON data: {e}", exc_info=True)
        
        return items
    
    def _parse_json_ld_data(self, json_ld_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse JSON-LD structured data into event items."""
        items = []
        
        for item in json_ld_items:
            try:
                # Check if it's an Event type
                item_type = item.get('@type', '').lower()
                if 'event' not in item_type and 'exhibition' not in item_type:
                    continue
                
                title = item.get('name') or item.get('headline', '')
                if not title:
                    continue
                
                # Extract date
                date_text = ''
                if 'startDate' in item:
                    date_text = item['startDate']
                elif 'datePublished' in item:
                    date_text = item['datePublished']
                
                # Extract location
                location = ''
                if 'location' in item:
                    loc = item['location']
                    if isinstance(loc, dict):
                        location = loc.get('name') or loc.get('address', '')
                    elif isinstance(loc, str):
                        location = loc
                
                # Extract URL
                url = item.get('url') or item.get('sameAs', '') or self.base_url
                if isinstance(url, list):
                    url = url[0] if url else self.base_url
                
                # Extract description
                description = ''
                if 'description' in item:
                    desc = item['description']
                    if isinstance(desc, list):
                        desc = desc[0] if desc else ''
                    description = str(desc)[:300]
                
                items.append({
                    'title': title,
                    'url': url,
                    'date_text': date_text,
                    'location': location,
                    'description': description,
                })
            except Exception as e:
                logger.debug(f"Error parsing JSON-LD item: {e}")
                continue
        
        return items
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch events using Playwright browser automation."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return []
        
        all_items = []
        json_ld_items = []
        
        try:
            with sync_playwright() as p:
                # Launch browser (headless)
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                # Set up XHR interception
                self._setup_xhr_interception(page)
                
                # Navigate to page
                logger.info(f"Loading {self.base_url} with Playwright...")
                wait_timeout = self.site_config.get('wait_timeout', 30000)
                
                # For slow sites like National Galleries, use load instead of networkidle
                if 'nationalgalleries.org' in self.base_url:
                    try:
                        # Use 'load' which is less strict than 'networkidle'
                        page.goto(self.base_url, wait_until='load', timeout=120000)
                    except Exception:
                        try:
                            # Fallback to domcontentloaded
                            page.goto(self.base_url, wait_until='domcontentloaded', timeout=120000)
                        except Exception as e:
                            logger.warning(f"Navigation timeout for {self.base_url}, continuing anyway: {e}")
                else:
                    try:
                        page.goto(self.base_url, wait_until='domcontentloaded', timeout=wait_timeout)
                    except Exception:
                        # If domcontentloaded times out, try load
                        try:
                            page.goto(self.base_url, wait_until='load', timeout=wait_timeout)
                        except Exception as e:
                            logger.warning(f"Navigation timeout, continuing anyway: {e}")
                
                # Handle cookie consent
                self._handle_cookie_consent(page)
                
                # Wait for content to load
                wait_selector = self.site_config.get('wait_selector', 'body')
                wait_timeout = self.site_config.get('wait_timeout', 10000)
                
                try:
                    page.wait_for_selector(wait_selector, timeout=wait_timeout)
                except Exception:
                    logger.debug(f"Wait selector '{wait_selector}' not found, continuing...")
                
                # Give extra time for XHR requests and JS rendering
                # Longer wait for slow sites
                extra_wait = 20000 if 'nationalgalleries.org' in self.base_url else 5000
                page.wait_for_timeout(extra_wait)
                
                # Extract JSON-LD if configured
                if self.site_config.get('json_ld_extract', False):
                    json_ld_items = self._extract_json_ld(page)
                
                # Extract from DOM
                dom_items = self._extract_from_dom(page)
                all_items.extend(dom_items)
                
                browser.close()
        
        except Exception as e:
            logger.error(f"Playwright fetch failed for {self.base_url}: {e}", exc_info=True)
            return []
        
        # Parse intercepted XHR responses
        for intercepted in self._intercepted_responses:
            try:
                xhr_items = self._parse_xhr_json_data(intercepted['data'], intercepted['url'])
                all_items.extend(xhr_items)
                logger.info(f"Parsed {len(xhr_items)} items from XHR response {intercepted['url']}")
            except Exception as e:
                logger.debug(f"Error parsing XHR data: {e}")
        
        # Parse JSON-LD items
        if json_ld_items:
            json_ld_parsed = self._parse_json_ld_data(json_ld_items)
            all_items.extend(json_ld_parsed)
            logger.info(f"Parsed {len(json_ld_parsed)} items from JSON-LD")
        
        # Deduplicate by title+url
        seen = set()
        unique_items = []
        for item in all_items:
            key = (item.get('title', ''), item.get('url', ''))
            if key not in seen and item.get('title'):
                seen.add(key)
                unique_items.append(item)
        
        logger.info(f"Fetched {len(unique_items)} unique items from {self.base_url}")
        # Return raw items (will be normalized via normalize() method)
        return unique_items
    
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert raw item to common normalized shape."""
        title = raw_item.get('title', '')
        if not title:
            return None
        
        return {
            'source_name': self.source_name,
            'title': title,
            'url': raw_item.get('url', ''),
            'published_at': None,  # Will be parsed from date_text if needed
            'event_date': self._parse_date(raw_item.get('date_text', '')),
            'location': raw_item.get('location', ''),
            'category': self.category,
            'raw_data': {
                'description': raw_item.get('description', ''),
                'date_text': raw_item.get('date_text', ''),
            },
        }
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date text using dateutil with UK locale awareness."""
        if not date_text:
            return None
        
        try:
            from dateutil import parser
            # Try parsing with dateutil (handles various formats)
            parsed = parser.parse(date_text, dayfirst=True)
            return parsed
        except Exception:
            return None

