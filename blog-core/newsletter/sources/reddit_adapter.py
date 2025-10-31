"""Reddit Data API adapter for /r/Scotland, /r/Highlands, etc."""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from newsletter.sources.base import SourceAdapter


class RedditAdapter(SourceAdapter):
    """Adapter for Reddit Data API (read-only, no OAuth needed for public listings)."""
    
    def __init__(self, source_name: str, subreddit: str, category: str = 'community', rate_limit_minutes: int = 60):
        """Initialize with subreddit name.
        
        Uses public JSON API (no auth required for read-only):
        https://www.reddit.com/r/{subreddit}/hot.json
        """
        super().__init__(source_name, rate_limit_minutes)
        self.subreddit = subreddit
        self.category = category
        self.api_base = 'https://www.reddit.com'
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch hot posts from subreddit."""
        try:
            url = f"{self.api_base}/r/{self.subreddit}/hot.json"
            headers = {'User-Agent': 'NewsletterBot/1.0 (by /u/your_username)'}  # Reddit requires User-Agent
            params = {'limit': 25}
            
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            items = []
            for child in data.get('data', {}).get('children', [])[:20]:
                post = child.get('data', {})
                # Skip stickied posts (usually mod announcements)
                if post.get('stickied'):
                    continue
                
                items.append({
                    'title': post.get('title', ''),
                    'url': post.get('url', ''),
                    'selftext': post.get('selftext', ''),
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc'),
                    'permalink': post.get('permalink', ''),
                    'domain': post.get('domain', ''),
                })
            
            return items
        except Exception:
            return []
    
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize Reddit post to common shape."""
        title = raw_item.get('title', '').strip()
        if not title:
            return None
        
        # Use permalink for Reddit posts (absolute URL)
        permalink = raw_item.get('permalink', '')
        if permalink and not permalink.startswith('http'):
            url = f"{self.api_base}{permalink}"
        else:
            url = raw_item.get('url', '')
        
        # Parse created timestamp
        published_at = None
        created_utc = raw_item.get('created_utc')
        if created_utc:
            try:
                published_at = datetime.fromtimestamp(created_utc)
            except Exception:
                pass
        
        return {
            'source_name': f"Reddit/{self.subreddit}",
            'title': title,
            'url': url,
            'published_at': published_at,
            'event_date': None,
            'location': None,
            'category': self.category,
            'raw_data': {
                **raw_item,
                'reddit_score': raw_item.get('score', 0),
                'reddit_comments': raw_item.get('num_comments', 0),
            },
        }

