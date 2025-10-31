"""Script to validate all newsletter source URLs and report issues."""

import sys
import os
sys.path.append('blog-core')

import feedparser
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sources from migration file
SOURCES = [
    {
        'name': 'Met Office Scotland',
        'url': 'https://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/Scotland',
        'type': 'rss',
        'category': 'weather'
    },
    {
        'name': 'BBC Scotland',
        'url': 'https://feeds.bbci.co.uk/news/scotland/rss.xml',
        'type': 'rss',
        'category': 'news'
    },
    {
        'name': 'The Scotsman',
        'url': 'https://www.scotsman.com/rss',
        'type': 'rss',
        'category': 'news'
    },
    {
        'name': 'Reddit /r/Scotland',
        'url': 'https://www.reddit.com/r/Scotland/',
        'type': 'reddit',
        'category': 'community'
    },
    {
        'name': 'Reddit /r/Highlands',
        'url': 'https://www.reddit.com/r/Highlands/',
        'type': 'reddit',
        'category': 'community'
    },
    {
        'name': 'Historic Environment Scotland - What\'s On',
        'url': 'https://www.historicenvironment.scot/whats-on/',
        'type': 'html',
        'category': 'event'
    },
    {
        'name': 'National Museums Scotland - Events',
        'url': 'https://www.nms.ac.uk/whats-on/',
        'type': 'html',
        'category': 'event'
    },
    {
        'name': 'National Galleries Scotland - Exhibitions',
        'url': 'https://www.nationalgalleries.org/whats-on/exhibitions',
        'type': 'html',
        'category': 'event'
    },
    {
        'name': 'VisitScotland Events',
        'url': 'https://www.visitscotland.com/events/',
        'type': 'html',
        'category': 'event'
    },
    {
        'name': 'Royal Scottish Highland Games Association',
        'url': 'https://www.rsghga.org/',
        'type': 'html',
        'category': 'event'
    },
]


def test_rss(url: str) -> dict:
    """Test an RSS feed."""
    try:
        feed = feedparser.parse(url)
        return {
            'success': not feed.bozo,
            'entries': len(feed.entries) if feed.entries else 0,
            'error': str(feed.bozo_exception) if feed.bozo else None,
            'title': feed.feed.get('title', ''),
            'link': feed.feed.get('link', ''),
        }
    except Exception as e:
        return {
            'success': False,
            'entries': 0,
            'error': str(e),
            'title': '',
            'link': '',
        }


def test_reddit(url: str) -> dict:
    """Test Reddit JSON API (no auth needed for read-only)."""
    try:
        # Reddit JSON endpoint
        if not url.endswith('.json'):
            json_url = url.rstrip('/') + '/.json?limit=10'
        else:
            json_url = url
        
        headers = {'User-Agent': 'NewsletterBot/1.0'}
        r = requests.get(json_url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        posts = data.get('data', {}).get('children', [])
        return {
            'success': True,
            'entries': len(posts),
            'error': None,
            'title': f"Reddit {url}",
            'link': url,
        }
    except Exception as e:
        return {
            'success': False,
            'entries': 0,
            'error': str(e),
            'title': '',
            'link': '',
        }


def test_html(url: str) -> dict:
    """Test HTML page accessibility."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        r.raise_for_status()
        
        # Check if we can parse it
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'No title found'
        
        # Look for event-like content indicators
        event_indicators = soup.find_all(['article', 'div'], class_=lambda x: x and ('event' in str(x).lower() or 'exhibition' in str(x).lower()))
        
        return {
            'success': True,
            'entries': len(event_indicators) if event_indicators else 0,
            'error': None,
            'title': title_text[:100],
            'link': r.url,  # Final URL after redirects
        }
    except Exception as e:
        return {
            'success': False,
            'entries': 0,
            'error': str(e),
            'title': '',
            'link': '',
        }


def main():
    """Test all sources and print report."""
    print("=" * 80)
    print("NEWSLETTER SOURCE VALIDATION REPORT")
    print("=" * 80)
    print()
    
    results = []
    
    for source in SOURCES:
        print(f"Testing: {source['name']} ({source['type']})")
        print(f"  URL: {source['url']}")
        
        if source['type'] == 'rss':
            result = test_rss(source['url'])
        elif source['type'] == 'reddit':
            result = test_reddit(source['url'])
        elif source['type'] == 'html':
            result = test_html(source['url'])
        else:
            result = {'success': False, 'entries': 0, 'error': 'Unknown type', 'title': '', 'link': ''}
        
        result['source'] = source
        results.append(result)
        
        if result['success']:
            print(f"  ✓ SUCCESS - {result['entries']} entries found")
            if result.get('title'):
                print(f"  Title: {result['title'][:60]}")
        else:
            print(f"  ✗ FAILED - {result['error']}")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    print()
    
    if failed:
        print("FAILED SOURCES:")
        for r in failed:
            print(f"  - {r['source']['name']}: {r['error']}")
        print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    for r in results:
        if not r['success']:
            source = r['source']
            if source['name'] == 'Met Office Scotland':
                print(f"  - {source['name']}: Met Office warnings RSS may require active warnings to work.")
                print("    Consider alternative: Met Office DataPoint API or HTML scraping of forecast pages.")
            elif source['type'] == 'html' and r['entries'] == 0:
                print(f"  - {source['name']}: Page loads but no event elements detected. May need custom selectors.")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()

