"""Reddit Data API adapter for /r/Scotland, /r/Highlands, etc."""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from newsletter.sources.base import SourceAdapter

logger = logging.getLogger(__name__)

# Default engagement thresholds
DEFAULT_MIN_UPVOTES = 50
DEFAULT_MIN_COMMENTS = 10


class RedditAdapter(SourceAdapter):
    """Adapter for Reddit Data API (read-only, no OAuth needed for public listings)."""
    
    def __init__(
        self, 
        source_name: str, 
        subreddit: str, 
        category: str = 'community', 
        rate_limit_minutes: int = 60,
        min_upvotes: int = DEFAULT_MIN_UPVOTES,
        min_comments: int = DEFAULT_MIN_COMMENTS
    ):
        """Initialize with subreddit name.
        
        Uses public JSON API (no auth required for read-only):
        https://www.reddit.com/r/{subreddit}/hot.json
        
        Args:
            source_name: Name of source
            subreddit: Subreddit name (e.g., 'Scotland')
            category: Content category (default: 'community')
            rate_limit_minutes: Minutes between fetches
            min_upvotes: Minimum upvotes to consider post (default: 50)
            min_comments: Minimum comments to consider post (default: 10)
        """
        super().__init__(source_name, rate_limit_minutes)
        self.subreddit = subreddit
        self.category = category
        self.api_base = 'https://www.reddit.com'
        self.min_upvotes = min_upvotes
        self.min_comments = min_comments
    
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
    
    def _check_engagement_threshold(self, score: int, num_comments: int) -> bool:
        """Check if post meets engagement thresholds."""
        return score >= self.min_upvotes and num_comments >= self.min_comments
    
    def _assess_suitability(self, title: str, selftext: str = '') -> tuple[bool, str]:
        """Assess if Reddit post is suitable for newsletter.
        
        Returns:
            (is_suitable: bool, reasoning: str)
        """
        text_to_check = f"{title} {selftext}".lower()
        
        # Filter out low-quality indicators
        low_quality_keywords = [
            'help me', 'rant', 'vent', 'am i the asshole', 'aita',
            'unpopular opinion', 'change my mind', 'reddit', 'upvote',
        ]
        
        if any(keyword in text_to_check for keyword in low_quality_keywords):
            return False, "Low-quality post indicator detected"
        
        # Check for Scottish/cultural relevance
        scottish_keywords = [
            'scotland', 'scottish', 'edinburgh', 'glasgow', 'highland',
            'heritage', 'culture', 'tartan', 'clan', 'celtic', 'gaelic',
            'loch', 'castle', 'whisky', 'haggis', 'bagpipe',
        ]
        
        has_scottish_connection = any(keyword in text_to_check for keyword in scottish_keywords)
        
        # Filter out overtly political or sensitive topics
        sensitive_keywords = [
            'brexit', 'independence referendum', 'snp vs', 'tory vs',
            'election', 'vote', 'political', 'controversial',
        ]
        
        has_sensitive_topic = any(keyword in text_to_check for keyword in sensitive_keywords)
        
        if has_sensitive_topic:
            return False, "Contains sensitive/political topic"
        
        if has_scottish_connection:
            return True, "Scottish connection found, suitable for community content"
        
        # Neutral posts without clear Scottish connection might still be interesting
        # but score lower
        if len(title) > 20 and '?' not in title:  # Avoid question-heavy posts
            return True, "Potentially interesting community discussion"
        
        return False, "No clear Scottish connection or community interest"
    
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize Reddit post to common shape with engagement and suitability checks."""
        title = raw_item.get('title', '').strip()
        if not title:
            return None
        
        score = raw_item.get('score', 0)
        num_comments = raw_item.get('num_comments', 0)
        selftext = raw_item.get('selftext', '')
        
        # Check engagement threshold
        if not self._check_engagement_threshold(score, num_comments):
            logger.debug(f"Skipping post '{title[:50]}...': engagement too low (score: {score}, comments: {num_comments})")
            return None
        
        # Assess suitability
        is_suitable, reasoning = self._assess_suitability(title, selftext)
        if not is_suitable:
            logger.debug(f"Skipping post '{title[:50]}...': {reasoning}")
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
        
        # Calculate upvote ratio if available
        upvote_ratio = raw_item.get('upvote_ratio', 0.0)
        
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
                'reddit_score': score,
                'reddit_comments': num_comments,
                'reddit_upvote_ratio': upvote_ratio,
                'suitability_reasoning': reasoning,
                'engagement_met': True,
            },
        }

