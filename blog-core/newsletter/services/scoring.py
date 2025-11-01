"""Scoring service for ranking source items by freshness, signal, diversity, safety."""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timedelta
import math


def calculate_freshness_score(item: Dict[str, Any], reference_date: datetime | None = None) -> float:
    """Calculate freshness score based on time proximity.
    
    Boost for items in -3 to +10 day window relative to reference_date.
    Reference date defaults to today.
    
    Returns score 0.0 to 10.0 (higher = more timely).
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    # Prefer published_at if available, fall back to event_date
    item_date = item.get('published_at') or item.get('event_date')
    if not item_date:
        return 0.0
    
    # Ensure datetime object
    if isinstance(item_date, str):
        try:
            from dateutil import parser
            item_date = parser.parse(item_date)
        except Exception:
            return 0.0
    
    # Normalize both to date for comparison if needed
    from datetime import date
    if isinstance(item_date, date) and not isinstance(item_date, datetime):
        # Convert date to datetime at midnight for comparison
        item_date = datetime.combine(item_date, datetime.min.time())
    elif isinstance(item_date, datetime):
        # Normalize to date
        item_date = item_date.date()
        item_date = datetime.combine(item_date, datetime.min.time())
    
    if isinstance(reference_date, date) and not isinstance(reference_date, datetime):
        reference_date = datetime.combine(reference_date, datetime.min.time())
    elif isinstance(reference_date, datetime):
        # Keep as datetime
        pass
    
    # Calculate days difference
    delta = (item_date - reference_date).days
    
    # Boost for -3 to +10 day window
    if -3 <= delta <= 10:
        # Peak at 0 days (today): score 10.0
        # Decay linearly: 10.0 at 0, 5.0 at -3 or +10, 0.0 beyond
        if delta >= 0:
            # Future: decay from 10.0 at day 0 to 5.0 at day 10
            score = 10.0 - (delta / 10.0) * 5.0
        else:
            # Past: decay from 10.0 at day 0 to 5.0 at day -3
            score = 10.0 - (abs(delta) / 3.0) * 5.0
        return max(0.0, min(10.0, score))
    
    # Outside window: decay rapidly
    if delta < -3:
        # Older than 3 days: decay
        days_old = abs(delta) - 3
        score = 5.0 / (1 + days_old * 0.2)  # Rapid decay
        return max(0.0, score)
    else:
        # More than 10 days future: decay
        days_future = delta - 10
        score = 5.0 / (1 + days_future * 0.1)
        return max(0.0, score)


def calculate_signal_score(item: Dict[str, Any]) -> float:
    """Calculate signal score based on source authority and engagement.
    
    Source weights (0-10):
    - National broadcaster (BBC): 10.0
    - Official sources (Met Office, HES): 9.0
    - Museums/Galleries: 8.0
    - Reddit (high engagement): 6.0-8.0 (based on upvotes/comments)
    - Other: 5.0
    
    Returns score 0.0 to 10.0 (higher = more authoritative).
    """
    source_name = item.get('source_name', '').lower()
    raw_data = item.get('raw_data', {})
    
    # Source weight base
    source_weight = 5.0  # default
    
    if 'bbc' in source_name or 'scotland' in source_name and 'bbc' in source_name:
        source_weight = 10.0
    elif 'met office' in source_name or 'metoffice' in source_name:
        source_weight = 9.0
    elif any(x in source_name for x in ['historic environment', 'hes', 'museum', 'gallery', 'national museum']):
        source_weight = 9.0
    elif 'reddit' in source_name:
        # Reddit: base 6.0, boost with engagement
        base = 6.0
        score = raw_data.get('reddit_score', 0) or 0
        comments = raw_data.get('reddit_comments', 0) or 0
        # Boost: +0.5 per 100 upvotes, +0.5 per 50 comments, cap at +2.0
        engagement_boost = min(2.0, (score / 100.0) * 0.5 + (comments / 50.0) * 0.5)
        source_weight = base + engagement_boost
    elif 'visit scotland' in source_name or 'royal scottish' in source_name:
        source_weight = 8.0
    
    # Weather warning boost (if detected in title/category)
    warning_boost = 0.0
    title = item.get('title', '').lower()
    if item.get('category') == 'weather' and any(word in title for word in ['warning', 'alert', 'severe', 'storm', 'flood']):
        warning_boost = 2.0
    
    return min(10.0, source_weight + warning_boost)


def apply_diversity_rules(items: List[Dict[str, Any]], max_per_category: int = 1) -> List[Dict[str, Any]]:
    """Apply diversity rules: prefer variety across categories.
    
    Filters/ranks items to prefer having one of each category type
    rather than multiple from same category.
    
    Args:
        items: List of scored items (should have category field)
        max_per_category: Maximum items per category in result
    
    Returns:
        Filtered list maintaining diversity
    """
    if not items:
        return items
    
    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        cat = item.get('category', 'other')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    # Sort each category by combined score (descending)
    for cat in by_category:
        by_category[cat].sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    
    # Build diverse result: take top N from each category
    result = []
    for cat, cat_items in by_category.items():
        result.extend(cat_items[:max_per_category])
    
    # Sort result by combined score
    result.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    return result


def apply_safety_rules(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out unsafe/problematic content.
    
    Rules:
    - Title length: max 110 chars
    - Must have working URL
    - Filter political/controversial keywords (in title)
    - Filter tragedy/obituaries in intro slot
    
    Returns filtered list.
    """
    filtered = []
    
    # Keywords to filter (political, sensitive topics for intro)
    filter_keywords = [
        'death', 'died', 'killed', 'murder', 'tragedy', 'obituary',
        # Political (can mention events but not opinions)
        'blames', 'accuses', 'criticises', 'scandal', 'corruption',
    ]
    
    for item in items:
        title = item.get('title', '')
        url = item.get('url', '')
        
        # Title length check
        if len(title) > 110:
            continue
        
        # URL required
        if not url or url == '':
            continue
        
        # Safety keyword check (case-insensitive)
        title_lower = title.lower()
        if any(kw in title_lower for kw in filter_keywords):
            continue
        
        filtered.append(item)
    
    return filtered


def score_items(items: List[Dict[str, Any]], reference_date: datetime | None = None) -> List[Dict[str, Any]]:
    """Apply all scoring rules and return sorted list.
    
    Adds freshness_score, signal_score, combined_score to each item.
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    scored = []
    for item in items:
        item['freshness_score'] = calculate_freshness_score(item, reference_date)
        item['signal_score'] = calculate_signal_score(item)
        item['combined_score'] = item['freshness_score'] + item['signal_score']
        scored.append(item)
    
    # Apply safety rules
    scored = apply_safety_rules(scored)
    
    # Sort by combined score
    scored.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    
    return scored

