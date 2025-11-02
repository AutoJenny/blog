"""Dedicated scraper for VisitScotland event pages.
    
This scraper:
1. Loads VisitScotland pages with Playwright
2. Extracts event entries (title, URL, date text, description)
3. Saves raw JSON for each event
4. Handles deduplication against existing events
5. Uses LLM to intelligently parse dates, locations, and titles
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from newsletter.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

# Check if Playwright is available
try:
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install chromium")


class VisitScotlandScraper(SourceAdapter):
    """Dedicated scraper for VisitScotland event pages.
    
    VisitScotland events are structured as:
    - Event title (linked) - e.g., "Genesis Scottish Open"
    - Date range text - e.g., "9 - 12 July 2026"
    - Description paragraph
    
    Events are grouped by month sections on the page.
    """
    
    # Pages to scrape
    VISITSCOTLAND_PAGES = [
        'https://www.visitscotland.com/things-to-do/events/scottish-culture',
        'https://www.visitscotland.com/things-to-do/events/edinburgh-festivals',
        'https://www.visitscotland.com/things-to-do/events/highland-games',
        'https://www.visitscotland.com/things-to-do/events/music-festivals',
    ]
    
    # Navigation/context patterns to exclude
    NAVIGATION_PATTERNS = [
        r'^what.*on.*this year',
        r'^find experiences',
        r'^join our newsletter',
        r'^get in touch',
        r'^our other sites',
        r'^skip to',
        r'^main menu',
        r'^search',
    ]
    
    def __init__(self, source_name: str, base_url: str, category: str = 'event', rate_limit_minutes: int = 240):
        """Initialize VisitScotland scraper.
        
        Args:
            source_name: Name of source
            base_url: Base URL to scrape (one of VISITSCOTLAND_PAGES)
            category: Content category (typically "event")
            rate_limit_minutes: Minutes between fetches
        """
        super().__init__(source_name, rate_limit_minutes)
        self.base_url = base_url
        self.category = category
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available. Install with: pip install playwright && playwright install chromium")
        
        # Directory for storing raw JSON files
        self.raw_data_dir = Path('blog-core/newsletter/data/raw_visitscotland')
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    def _is_navigation(self, text: str) -> bool:
        """Check if text is navigation/context, not an event."""
        normalized = text.lower().strip()
        for pattern in self.NAVIGATION_PATTERNS:
            if re.match(pattern, normalized, re.IGNORECASE):
                return True
        return False
    
    def _extract_events_from_page(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """Extract event entries from a VisitScotland page.
        
        VisitScotland structure:
        - Events are listed under month headings (h2/h3)
        - Each event is typically:
          - A linked title (a tag)
          - Date range text after the link (e.g., "9 - 12 July 2026")
          - Description paragraph following
        
        Args:
            page: Playwright page object
            url: Page URL
            
        Returns:
            List of raw event dicts with title, url, date_text, description
        """
        events = []
        
        try:
            # Wait for main content
            page.wait_for_selector('main', timeout=15000)
            page.wait_for_timeout(2000)  # Wait for any JS rendering
            
            # Get page HTML
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find main content area
            main = soup.find('main')
            if not main:
                logger.warning(f"No main content found on {url}")
                return []
            
            # VisitScotland events are typically structured as:
            # - Headings (h2, h3) for month sections
            # - Event titles as links (a tags) within paragraphs or list items
            # - Date text follows the link (often in same paragraph or adjacent)
            # - Description paragraphs follow
            
            # Actual page structure (from browser inspection):
            # Events are in <p> paragraphs with format:
            # <p><a href="...">Event Name</a> - date range - description</p>
            #
            # Example: <p><a href="https://www.wigtownbookfestival.com/">Wigtown Book Festival</a> 
            #          - 26 September - 5 October 2025 - celebrate Scottish literature...</p>
            #
            # Strategy: Find paragraphs containing date patterns, then extract event link from them
            
            # Find all paragraphs in main content
            paragraphs = main.find_all('p')
            
            # Date patterns to identify event paragraphs
            date_patterns = [
                r'\d+\s*[-–]\s*\d+\s+\w+\s+\d{4}',  # "26 September - 5 October 2025"
                r'\d+\s+\w+\s*[-–]\s*\d+\s+\w+\s+\d{4}',  # "9 July - 12 July 2026"
                r'\d+\s+\w+\s+\d{4}',  # "9 July 2026"
                r'\w+\s*[-–]\s*\w+\s+\d{4}',  # "July - August 2026"
                r'\w+\s+\d{4}',  # "August 2026"
            ]
            
            for para in paragraphs:
                para_text = para.get_text(strip=True)
                
                # Skip if paragraph too short
                if len(para_text) < 30:
                    continue
                
                # Check if this paragraph contains a date pattern (indicating it's an event entry)
                date_text = ''
                for pattern in date_patterns:
                    match = re.search(pattern, para_text, re.IGNORECASE)
                    if match:
                        date_text = match.group(0).strip()
                        # Remove leading "-" or "–" if present
                        if date_text.startswith('-') or date_text.startswith('–'):
                            date_text = date_text[1:].strip()
                        break
                
                # If no date found, skip this paragraph
                if not date_text:
                    continue
                
                # Find the first substantial link in this paragraph (the event title)
                link = para.find('a', href=True)
                if not link:
                    continue
                
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                # Skip if title too short or looks like navigation
                if not title or len(title) < 10:
                    continue
                
                if self._is_navigation(title):
                    continue
                
                # Build full URL (may be external, that's OK)
                if not href.startswith('http'):
                    href = urljoin(url, href)
                
                # Skip if it's just a category/navigation page
                if href.endswith('/events/') or href.endswith('/events') or href == url:
                    continue
                
                # Extract description (text after the date in the paragraph)
                description = ''
                if date_text:
                    date_idx = para_text.find(date_text)
                    if date_idx > -1:
                        after_date = para_text[date_idx + len(date_text):].strip()
                        # Remove leading "-" or "–" separators
                        if after_date.startswith('-') or after_date.startswith('–'):
                            after_date = after_date[1:].strip()
                        description = after_date[:500]  # Limit length
                
                # Include this event (we already confirmed it has a date)
                    events.append({
                        'title': title,
                        'url': href,
                        'date_text': date_text,
                        'description': description,
                        'source_url': url,
                        'extracted_at': datetime.now().isoformat(),
                    })
            
            logger.info(f"Extracted {len(events)} events from {url}")
            return events
            
        except Exception as e:
            logger.error(f"Error extracting events from {url}: {e}", exc_info=True)
            return []
    
    def _save_raw_json(self, events: List[Dict[str, Any]]) -> str:
        """Save raw event data to JSON file.
        
        Args:
            events: List of event dicts
            
        Returns:
            Path to saved JSON file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"visitscotland_{timestamp}.json"
        filepath = self.raw_data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'source': self.source_name,
                'base_url': self.base_url,
                'extracted_at': datetime.now().isoformat(),
                'event_count': len(events),
                'events': events,
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(events)} events to {filepath}")
        return str(filepath)
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch events from VisitScotland page.
        
        Returns:
            List of raw event dicts
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return []
        
        events = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                )
                
                # Handle cookies if needed
                # VisitScotland may show cookie consent
                page = context.new_page()
                
                try:
                    # Navigate to page
                    page.goto(self.base_url, wait_until='networkidle', timeout=30000)
                    
                    # Handle cookie consent if present
                    try:
                        cookie_button = page.query_selector('button:has-text("Accept"), button:has-text("Cookie"), #accept-cookies')
                        if cookie_button:
                            cookie_button.click()
                            page.wait_for_timeout(1000)
                    except:
                        pass  # No cookie banner
                    
                    # Extract events
                    page_events = self._extract_events_from_page(page, self.base_url)
                    events.extend(page_events)
                    
                finally:
                    page.close()
                    context.close()
                    browser.close()
        
        except Exception as e:
            logger.error(f"Error fetching from {self.base_url}: {e}", exc_info=True)
            return []
        
        # Save raw JSON
        if events:
            self._save_raw_json(events)
        
        return events
    
    def fetch_and_normalize(self) -> List[Dict[str, Any]]:
        """Fetch and return normalized items (raw events for now, will be parsed by LLM later)."""
        raw_events = self.fetch()
        
        # Return in format expected by the system
        # Full parsing will happen in a second pass with LLM
        normalized = []
        for event in raw_events:
            normalized.append({
                'title': event['title'],
                'url': event['url'],
                'date_text': event.get('date_text', ''),
                'description': event.get('description', ''),
                'category': self.category,
                'source_name': self.source_name,
                'raw_data': event,  # Preserve all raw data
            })
        
        return normalized

