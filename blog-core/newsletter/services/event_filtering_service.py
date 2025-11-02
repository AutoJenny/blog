"""Service for filtering out page headings and non-event content from event items."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Generic page heading patterns that indicate navigation, not events
PAGE_HEADING_PATTERNS = [
    r'^what[\'s\s]*on',
    r'^events?$',
    r'^calendar$',
    r'^schedule$',
    r'^programme?$',
    r'^tickets?$',
    r'^visit',
    r'^about',
    r'^home$',
    r'^news$',
    r'^contact',
    r'^gallery$',
    r'^exhibitions?$',
    r'^collections?$',
    r'^explore$',
    r'^discover$',
    r'^learn',
    r'^shop',
    r'^support',
    r'^plan\s+your\s+visit',
    r'^getting\s+here',
    r'^opening\s+hours',
    r'^accessibility',
]

# URL patterns that suggest page navigation rather than specific events
NAVIGATION_URL_PATTERNS = [
    r'/events/?$',
    r'/whats-on/?$',
    r'/what[\'s\s]*-?on/?$',
    r'/about',
    r'/home',
    r'/contact',
    r'/news/?$',
    r'/exhibitions?/?$',
    r'/collections?/?$',
    r'/visit',
    r'/plan',
    r'/access',
    r'/shop',
    r'/support',
    r'/learn',
]

# Generic navigation phrases that should not be events
NAVIGATION_PHRASES = [
    'what\'s on',
    'whats on',
    'what is on',
    'upcoming events',
    'current exhibitions',
    'visit us',
    'get in touch',
    'find us',
    'opening hours',
    'plan your visit',
    'getting here',
    'accessibility information',
    'tickets and booking',
    'school visits',
    'group visits',
]


def normalize_title(title: str) -> str:
    """Normalize title for pattern matching."""
    if not title:
        return ""
    return title.lower().strip()


def is_page_heading(title: str, url: Optional[str] = None) -> bool:
    """Check if a title/URL combination appears to be a page heading rather than an event.
    
    Args:
        title: Event title to check
        url: Optional URL to check
    
    Returns:
        True if this appears to be a page heading/navigation element, False otherwise
    """
    if not title:
        return True  # Empty titles are not events
    
    normalized = normalize_title(title)
    
    # Very short titles are suspicious
    if len(normalized) < 8:
        return True
    
    # Check against generic page heading patterns
    for pattern in PAGE_HEADING_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            logger.debug(f"Matched page heading pattern '{pattern}': {title}")
            return True
    
    # Check against navigation phrases
    for phrase in NAVIGATION_PHRASES:
        if normalized == phrase or normalized.startswith(phrase + ' '):
            logger.debug(f"Matched navigation phrase '{phrase}': {title}")
            return True
    
    # Check URL patterns
    if url:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for pattern in NAVIGATION_URL_PATTERNS:
            if re.search(pattern, path):
                # If title is also generic, definitely a page heading
                if len(normalized.split()) <= 3:
                    logger.debug(f"Matched navigation URL pattern '{pattern}' with generic title: {title}")
                    return True
        
        # URLs that end with /events/ or /events without more path are likely category pages
        if re.match(r'/events/?$', path):
            logger.debug(f"Matched events category URL: {title}")
            return True
        
        # URLs that are just the domain or homepage
        if path == '' or path == '/':
            if len(normalized.split()) <= 4:
                logger.debug(f"Matched homepage URL with generic title: {title}")
                return True
    
    # Titles that are just numbers or special characters
    if re.match(r'^[\d\s\-\:\.,]+$', normalized):
        logger.debug(f"Title is just numbers/symbols: {title}")
        return True
    
    # Titles with very few words and no date-like content
    words = normalized.split()
    if len(words) <= 2 and not any(char.isdigit() for char in normalized):
        # Check if it's not a proper event name
        if normalized not in ['highland games', 'tartan week']:  # Known valid short names
            logger.debug(f"Too few words and no dates: {title}")
            return True
    
    return False


def is_likely_false_positive(item: Dict[str, Any]) -> tuple[bool, str]:
    """Check if an event item is likely a false positive (page heading/navigation).
    
    Args:
        item: Event item dict with title, url, event_date, etc.
    
    Returns:
        Tuple of (is_false_positive, reason)
    """
    title = item.get('title', '')
    url = item.get('url')
    event_date = item.get('event_date')
    location = item.get('location')
    raw_data = item.get('raw_data', {})
    
    # Check if it's a page heading
    if is_page_heading(title, url):
        return (True, 'page_heading')
    
    # Additional checks for suspicious content
    
    # Missing critical event information
    if not event_date and not location:
        # If title is also generic, likely false positive
        if len(normalize_title(title).split()) <= 3:
            return (True, 'missing_info_generic')
    
    # Check raw_data for clues
    if isinstance(raw_data, dict):
        description = raw_data.get('description', '')
        if description:
            desc_lower = description.lower()
            # Generic descriptions that suggest navigation
            if any(phrase in desc_lower for phrase in ['click here', 'see our', 'visit our', 'learn more about', 'find out about']):
                if len(normalize_title(title).split()) <= 4:
                    return (True, 'generic_description')
    
    return (False, '')


def filter_false_positives(items: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filter out false positive events (page headings, navigation elements).
    
    Args:
        items: List of event items to filter
    
    Returns:
        Tuple of (valid_events, filtered_out) where filtered_out includes reason
    """
    valid = []
    filtered = []
    
    for item in items:
        is_false, reason = is_likely_false_positive(item)
        
        if is_false:
            item['_filter_reason'] = reason
            filtered.append(item)
            logger.info(f"Filtered false positive: {item.get('title', 'Unknown')[:50]} ({reason})")
        else:
            valid.append(item)
    
    logger.info(f"Filtered {len(filtered)} false positives from {len(items)} events, kept {len(valid)}")
    
    return valid, filtered

