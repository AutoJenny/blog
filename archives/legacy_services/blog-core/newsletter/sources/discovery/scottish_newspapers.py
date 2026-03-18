"""Discover Scottish weekly newspapers from Wikipedia and identify accessible feeds/pages.

This script parses the Wikipedia list of local weekly newspapers in Scotland,
attempts to discover RSS feeds and article listing pages, checks robots.txt,
and determines access modes for each source.
"""

from __future__ import annotations

import json
import re
import requests
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScottishNewspaperDiscovery:
    """Discover and catalog Scottish weekly newspapers."""
    
    WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_newspapers_in_Scotland"
    
    # Common RSS feed patterns to try
    RSS_PATTERNS = [
        '/rss',
        '/feed',
        '/rss.xml',
        '/feed.xml',
        '/news/rss',
        '/news/feed',
        '/feeds/all.rss',
    ]
    
    # Common article listing page patterns
    LISTING_PATTERNS = [
        '/news',
        '/local-news',
        '/community',
        '/local',
        '/news/local',
        '/community-news',
    ]
    
    def __init__(self, output_file: str = "data/scottish_newspaper_sources.json"):
        """Initialize discovery with output file path."""
        self.output_file = output_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0; +https://example.com/bot)'
        })
    
    def fetch_wikipedia_page(self) -> Optional[str]:
        """Fetch the Wikipedia page content."""
        try:
            response = self.session.get(self.WIKIPEDIA_URL, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch Wikipedia page: {e}")
            return None
    
    def parse_wikipedia_list(self, html: str) -> List[Dict[str, str]]:
        """Parse Wikipedia HTML to extract newspaper names and regions.
        
        Returns list of dicts with 'name' and 'region' keys.
        """
        soup = BeautifulSoup(html, 'html.parser')
        newspapers = []
        
        # Find the "Local weekly newspapers" section
        # Try multiple strategies to find the section
        local_section = None
        
        # Strategy 1: Look for heading with "Local weekly" or "Weekly newspapers"
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            text = heading.get_text().lower()
            if 'local weekly' in text or ('weekly' in text and 'newspaper' in text):
                local_section = heading
                logger.info(f"Found section heading: {heading.get_text()}")
                break
        
        # Strategy 2: Look for span with id containing "weekly"
        if not local_section:
            for span in soup.find_all('span', class_='mw-headline'):
                text = span.get_text().lower()
                if 'local weekly' in text or ('weekly' in text and 'newspaper' in text):
                    local_section = span.find_parent(['h2', 'h3', 'h4'])
                    if local_section:
                        logger.info(f"Found section via span: {local_section.get_text()}")
                        break
        
        if not local_section:
            logger.warning("Could not find 'Local weekly newspapers' section")
            # Try to find any section with "weekly" in it
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                text = heading.get_text().lower()
                if 'weekly' in text:
                    local_section = heading
                    logger.info(f"Using fallback section: {heading.get_text()}")
                    break
        
        if not local_section:
            logger.error("Could not find any weekly newspapers section")
            return []
        
        # Find the content div that follows the heading
        # Wikipedia structure: h2 -> div.mw-parser-output or div containing the content
        content_container = None
        
        # Strategy 1: Look for div after heading
        current = local_section.find_next_sibling()
        while current:
            if current.name == 'div':
                # Check if this div contains lists or links
                if current.find_all(['ul', 'ol', 'table']) or current.find_all('a', href=re.compile(r'/wiki/[^:]+$')):
                    content_container = current
                    break
            elif current.name in ['h2', 'h3']:
                # Hit next section, stop
                break
            current = current.find_next_sibling()
        
        # Strategy 2: If no div found, look for parent div
        if not content_container:
            parent = local_section.find_parent('div', class_='mw-parser-output')
            if parent:
                # Find all content between this heading and next h2
                content_container = parent
        
        if not content_container:
            logger.warning("Could not find content container for Local weekly newspapers section")
            return []
        
        # Extract newspapers from the content container
        region = None
        processed = set()
        
        # Find all elements between this heading and next h2
        start_found = False
        for element in content_container.find_all(['h2', 'h3', 'h4', 'ul', 'ol', 'table', 'p', 'div']):
            # Check if we've reached our target section
            if element.name in ['h2', 'h3']:
                text = element.get_text().lower()
                if 'local weekly' in text or ('weekly' in text and 'newspaper' in text):
                    start_found = True
                    continue
                elif start_found and any(x in text for x in ['specialist', 'university', 'defunct', 'see also', 'references']):
                    # Reached end of section
                    break
            
            if not start_found:
                continue
            
            # Process region subheadings
            if element.name == 'h4':
                region = element.get_text().strip()
                logger.debug(f"Found region: {region}")
                continue
            
            # Extract links from this element
            links = element.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Filter out non-newspaper links
                if not text or len(text) < 3:
                    continue
                if href.startswith('#') or href.startswith('/wiki/File:') or '/wiki/Category:' in href:
                    continue
                if '/wiki/Help:' in href or '/wiki/Template:' in href:
                    continue
                if any(skip in text.lower() for skip in ['edit', 'main page', 'contents', 'citation', '[', ']']):
                    continue
                
                # Must be a Wikipedia article link
                if not href.startswith('/wiki/') or ':' in href.split('/wiki/')[-1]:
                    continue
                
                # Check if this looks like a newspaper name
                if self._looks_like_newspaper(text) and text not in processed:
                    processed.add(text)
                    newspapers.append({
                        'name': text,
                        'region': region or 'Unknown',
                        'wikipedia_url': urljoin('https://en.wikipedia.org', href) if href.startswith('/') else href
                    })
                    logger.debug(f"Found newspaper: {text} ({region or 'Unknown'})")
        
        logger.info(f"Found {len(newspapers)} newspapers in Wikipedia list")
        return newspapers
    
    def _looks_like_newspaper(self, text: str) -> bool:
        """Heuristic to check if text looks like a newspaper name."""
        text_lower = text.lower()
        # Common newspaper indicators
        indicators = ['times', 'herald', 'news', 'journal', 'courier', 'express', 'gazette', 
                     'observer', 'advertiser', 'chronicle', 'record', 'post', 'mail']
        return any(ind in text_lower for ind in indicators)
    
    def discover_base_url(self, newspaper: Dict[str, str]) -> Optional[str]:
        """Try to discover the newspaper's website URL.
        
        First tries Wikipedia page for external link, then tries common patterns.
        """
        # Try to get from Wikipedia page
        if 'wikipedia_url' in newspaper:
            try:
                response = self.session.get(newspaper['wikipedia_url'], timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Look for official website link in infobox
                    infobox = soup.find('table', class_='infobox')
                    if infobox:
                        for link in infobox.find_all('a', href=True):
                            href = link.get('href', '')
                            if href.startswith('http') and 'wikipedia' not in href:
                                # Check if it's likely the main site
                                if any(x in link.get_text().lower() for x in ['website', 'site', 'home']):
                                    return href
                    # Look for external links section
                    ext_links = soup.find('div', id='External_links') or soup.find('span', id='External_links')
                    if ext_links:
                        parent = ext_links.find_parent()
                        if parent:
                            for link in parent.find_all('a', href=True, class_='external'):
                                href = link.get('href', '')
                                if href.startswith('http') and 'wikipedia' not in href:
                                    return href
            except Exception as e:
                logger.debug(f"Could not fetch Wikipedia page for {newspaper['name']}: {e}")
        
        # Try common domain patterns based on newspaper name
        name_lower = newspaper['name'].lower()
        # Extract key words
        words = re.findall(r'\w+', name_lower)
        if words:
            # Try first word + .co.uk or .com
            first_word = words[0]
            for domain in [f'{first_word}.co.uk', f'{first_word}.com', f'www.{first_word}.co.uk']:
                url = f'https://{domain}'
                if self._check_url_exists(url):
                    return url
        
        return None
    
    def _check_url_exists(self, url: str, timeout: int = 5) -> bool:
        """Quick check if URL exists and is accessible."""
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except Exception:
            return False
    
    def discover_rss_feeds(self, base_url: str) -> List[str]:
        """Try to discover RSS feed URLs for a newspaper."""
        feeds = []
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        for pattern in self.RSS_PATTERNS:
            feed_url = urljoin(base, pattern)
            if self._check_rss_feed(feed_url):
                feeds.append(feed_url)
        
        # Also try to find RSS link in page HTML
        try:
            response = self.session.get(base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for RSS link tags
                for link in soup.find_all('link', type=re.compile(r'application/(rss|atom)')):
                    href = link.get('href')
                    if href:
                        feed_url = urljoin(base_url, href)
                        if self._check_rss_feed(feed_url):
                            feeds.append(feed_url)
        except Exception as e:
            logger.debug(f"Could not check HTML for RSS links: {e}")
        
        return list(set(feeds))  # Remove duplicates
    
    def _check_rss_feed(self, url: str) -> bool:
        """Check if URL is a valid RSS feed."""
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'xml' in content_type or 'rss' in content_type or 'atom' in content_type:
                    # Quick check for RSS/Atom markers
                    text = response.text[:500].lower()
                    if any(marker in text for marker in ['<rss', '<feed', '<rdf:rdf']):
                        return True
        except Exception:
            pass
        return False
    
    def discover_listing_pages(self, base_url: str) -> List[str]:
        """Try to discover article listing page URLs."""
        pages = []
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        for pattern in self.LISTING_PATTERNS:
            page_url = urljoin(base, pattern)
            if self._check_listing_page(page_url):
                pages.append(page_url)
        
        return list(set(pages))
    
    def _check_listing_page(self, url: str) -> bool:
        """Check if URL looks like an article listing page."""
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for article indicators
                articles = soup.find_all(['article', 'div'], class_=re.compile(r'article|story|news-item', re.I))
                if len(articles) >= 3:  # At least 3 articles suggests a listing page
                    return True
        except Exception:
            pass
        return False
    
    def check_robots_txt(self, base_url: str) -> Dict[str, Any]:
        """Check robots.txt for access restrictions."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        result = {
            'robots_txt_exists': False,
            'allows_crawling': True,
            'crawl_delay': None,
        }
        
        try:
            response = self.session.get(robots_url, timeout=5)
            if response.status_code == 200:
                result['robots_txt_exists'] = True
                content = response.text.lower()
                
                # Check for disallow rules (simplified check)
                if 'disallow: /' in content or 'user-agent: *' in content:
                    # More detailed parsing would be needed for accurate assessment
                    result['allows_crawling'] = True  # Default to allowing, manual review needed
                
                # Extract crawl delay if present
                delay_match = re.search(r'crawl-delay:\s*(\d+)', content)
                if delay_match:
                    result['crawl_delay'] = int(delay_match.group(1))
        except Exception:
            pass
        
        return result
    
    def determine_access_mode(self, newspaper: Dict[str, Any]) -> str:
        """Determine access mode based on discovered resources."""
        has_rss = len(newspaper.get('rss_feeds', [])) > 0
        has_listing = len(newspaper.get('listing_pages', [])) > 0
        robots_allows = newspaper.get('robots', {}).get('allows_crawling', True)
        
        if not robots_allows:
            return 'blocked'
        elif has_rss:
            return 'rss_only'
        elif has_listing:
            return 'html_list_only'
        else:
            return 'blocked'  # No accessible content found
    
    def discover_all(self) -> List[Dict[str, Any]]:
        """Run full discovery process for all newspapers."""
        logger.info("Starting Scottish newspaper discovery...")
        
        # Fetch and parse Wikipedia
        html = self.fetch_wikipedia_page()
        if not html:
            logger.error("Failed to fetch Wikipedia page")
            return []
        
        newspapers = self.parse_wikipedia_list(html)
        if not newspapers:
            logger.error("No newspapers found in Wikipedia list")
            return []
        
        # Discover resources for each newspaper
        results = []
        for i, newspaper in enumerate(newspapers, 1):
            logger.info(f"Discovering {i}/{len(newspapers)}: {newspaper['name']}")
            
            base_url = self.discover_base_url(newspaper)
            if not base_url:
                logger.warning(f"Could not find base URL for {newspaper['name']}")
                newspaper['base_url'] = None
                newspaper['access_mode'] = 'blocked'
                results.append(newspaper)
                continue
            
            newspaper['base_url'] = base_url
            
            # Discover RSS feeds
            rss_feeds = self.discover_rss_feeds(base_url)
            newspaper['rss_feeds'] = rss_feeds
            
            # Discover listing pages
            listing_pages = self.discover_listing_pages(base_url)
            newspaper['listing_pages'] = listing_pages
            
            # Check robots.txt
            robots_info = self.check_robots_txt(base_url)
            newspaper['robots'] = robots_info
            
            # Determine access mode
            newspaper['access_mode'] = self.determine_access_mode(newspaper)
            
            # Add discovery notes
            notes = []
            if rss_feeds:
                notes.append(f"Found {len(rss_feeds)} RSS feed(s)")
            if listing_pages:
                notes.append(f"Found {len(listing_pages)} listing page(s)")
            if not robots_info['allows_crawling']:
                notes.append("Robots.txt may restrict crawling")
            newspaper['discovery_notes'] = '; '.join(notes) if notes else 'No accessible content found'
            
            results.append(newspaper)
        
        logger.info(f"Discovery complete: {len(results)} newspapers processed")
        return results
    
    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save discovery results to JSON file."""
        import os
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save as list format (seed script can handle both)
        output_data = {
            'discovery_date': datetime.now().isoformat(),
            'total_sources': len(results),
            'sources': results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {self.output_file}")
    
    def run(self) -> List[Dict[str, Any]]:
        """Run discovery and save results."""
        results = self.discover_all()
        if results:
            self.save_results(results)
        return results


if __name__ == '__main__':
    import sys
    import os
    
    # Add blog-core to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
    
    logging.basicConfig(level=logging.INFO)
    
    discovery = ScottishNewspaperDiscovery()
    results = discovery.run()
    
    print(f"\nDiscovery complete: {len(results)} newspapers found")
    print(f"Results saved to: {discovery.output_file}")
    
    # Print summary
    rss_count = sum(1 for n in results if n.get('rss_feeds'))
    listing_count = sum(1 for n in results if n.get('listing_pages'))
    accessible_count = sum(1 for n in results if n.get('access_mode') != 'blocked')
    
    print(f"\nSummary:")
    print(f"  - Newspapers with RSS feeds: {rss_count}")
    print(f"  - Newspapers with listing pages: {listing_count}")
    print(f"  - Accessible sources: {accessible_count}")

