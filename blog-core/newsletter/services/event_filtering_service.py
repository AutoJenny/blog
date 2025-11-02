"""Service for filtering out page headings and non-event content from event items."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Generic page heading patterns that indicate navigation, not events
PAGE_HEADING_PATTERNS = [
    r'^what[\'s\s]*on$',  # Exact "What's on", "Whats on", etc.
    r'^events?$',  # Exact "Event" or "Events"
    r'^calendar$',
    r'^schedule$',
    r'^programme?$',
    r'^tickets?$',
    r'^visit\s+(us|our)$',  # Only "Visit us" or "Visit our", not "Visit Scotland"
    r'^about$',  # Exact "About"
    r'^home$',
    r'^news$',
    r'^contact$',  # Exact "Contact"
    r'^gallery$',
    r'^exhibitions?$',
    r'^collections?$',
    r'^explore$',
    r'^discover$',
    r'^learn\s+(more|about)$',  # Only "Learn more" or "Learn about"
    r'^shop$',
    r'^support$',
    r'^plan\s+your\s+visit$',
    r'^getting\s+here$',
    r'^opening\s+hours$',
    r'^accessibility$',
]

# URL patterns that suggest page navigation rather than specific events
# Must match as standalone paths or with word boundaries
NAVIGATION_URL_PATTERNS = [
    r'/events/?$',  # Exact /events or /events/
    r'/whats-on/?$',  # Exact /whats-on or /whats-on/
    r'/what[\'s\s]*-?on/?$',  # Exact what's-on variants
    r'/about/?$',  # Exact /about or /about/
    r'/home/?$',
    r'/contact/?$',
    r'/news/?$',
    r'/exhibitions?/?$',  # Exact /exhibition(s) or /exhibition(s)/
    r'/collections?/?$',
    r'/visit/?$',  # Only exact /visit, not /visit-* or /festivals/visit-*
    r'/plan/?$',  # Only exact /plan
    r'/access/?$',
    r'/shop/?$',
    r'/support/?$',
    r'/learn/?$',
]

    # Generic navigation phrases that should not be events
    # Must be exact matches or clearly generic
NAVIGATION_PHRASES = [
    'what\'s on',
    'whats on',
    'what is on',
    'upcoming events',
    'current exhibitions',
    'visit us',
    'visit our',
    'get in touch',
    'find us',
    'opening hours',
    'plan your visit',
    'getting here',
    'accessibility information',
    'tickets and booking',
    'school visits',
    'group visits',
    'quicklinks',
    'quick links',
]

# Error message patterns that indicate broken links or error pages
ERROR_MESSAGE_PATTERNS = [
    r'.*wall.*',  # "come up against a wall"
    r'.*doesn\'t exist.*',
    r'.*does not exist.*',
    r'.*not found.*',
    r'.*404.*',
    r'.*page not found.*',
    r'.*error.*',
    r'.*something went wrong.*',
    r'.*oops.*',
    r'.*try again.*',
    r'.*broken.*link.*',
    r'.*cannot.*find.*',
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
    
    # Check for error messages first (these are never events)
    for pattern in ERROR_MESSAGE_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            logger.debug(f"Matched error message pattern '{pattern}': {title}")
            return True
    
    # Very short titles are suspicious (but not if they're proper event names)
    # Single words < 8 chars are likely navigation, but multi-word titles can be events
    words = normalized.split()
    if len(normalized) < 8 and len(words) == 1:
        return True
    
    # Check against generic page heading patterns
    for pattern in PAGE_HEADING_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            logger.debug(f"Matched page heading pattern '{pattern}': {title}")
            return True
    
    # Check against navigation phrases (exact match only)
    for phrase in NAVIGATION_PHRASES:
        if normalized == phrase:
            logger.debug(f"Matched navigation phrase '{phrase}': {title}")
            return True
    
    # Check URL patterns
    if url:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for pattern in NAVIGATION_URL_PATTERNS:
            # Use match instead of search to ensure pattern matches the full path segment
            if re.match(pattern, path):
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
    # But allow common event patterns (festivals, shows, connections, etc.)
    words = normalized.split()
    if len(words) <= 2 and not any(char.isdigit() for char in normalized):
        # Check if it's a proper event name (contains event keywords)
        event_keywords = ['festival', 'show', 'connections', 'gathering', 'games', 
                         'parade', 'celebration', 'event', 'fringe', 'hogmanay',
                         'tattoo', 'mod', 'open', 'week', 'day']
        has_event_keyword = any(keyword in normalized for keyword in event_keywords)
        
        # Also check known valid short names
        known_valid = ['highland games', 'tartan week', 'celtic connections', 
                      'edinburgh\'s hogmanay', "edinburgh's hogmanay"]
        
        if not has_event_keyword and normalized not in known_valid:
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
    normalized = normalize_title(title)
    
    # Primary check: is it a page heading?
    if is_page_heading(title, url):
        return (True, 'page_heading')
    
    # Additional checks for suspicious content
    # NOTE: Be conservative - only filter clearly non-event content
    # Many valid events may not have dates yet but are still real events
    
    # Very short single-word titles without dates might be navigation
    words = normalized.split()
    if len(words) == 1 and len(normalized) < 10 and not event_date:
        # But allow if it's a proper name (capitalized in original)
        # This is a conservative check - only filter obvious single-word nav terms
        if normalized in ['events', 'home', 'about', 'contact', 'news', 'shop']:
            return (True, 'single_word_nav_term')
    
    # Generic venue/location names without dates - but only if URL suggests venue page
    # Don't filter venue names if they have actual event URLs
    venue_patterns = ['castle', 'house', 'park', 'museum', 'gallery', 'cathedral', 'abbey']
    is_venue_name = any(pattern in normalized for pattern in venue_patterns) and len(normalized.split()) <= 3
    
    if is_venue_name and not event_date:
        # Only filter if URL clearly indicates it's a venue/about page, not an event page
        if url:
            if any(path in url.lower() for path in ['/places/', '/venues/', '/visit-a-place/', '/about/']):
                # Check if URL also has /event/ or /events/ - if so, it might be an event
                if '/event' not in url.lower():
                    return (True, 'venue_page_not_event')
        # If no URL at all, be conservative - don't filter (might be a real event without URL yet)
    
    # Generic phrases that are clearly navigation (exact matches)
    generic_nav_phrases = [
        'multiple venues', 'various locations', 'across scotland',
        'scotland\'s calendar', 'scotland\'s calendar of events',
        'events & festivals', 'events and festivals', 'events & festivals in scotland'
    ]
    if normalized in [p.lower() for p in generic_nav_phrases]:
        return (True, 'generic_navigation_phrase')
    
    # Check raw_data for clues
    if isinstance(raw_data, dict):
        description = raw_data.get('description', '')
        if description:
            desc_lower = description.lower()
            # Generic descriptions that suggest navigation pages
            navigation_indicators = [
                'click here', 'see our', 'visit our', 'learn more about', 
                'find out about', 'discover more', 'explore our'
            ]
            if any(phrase in desc_lower for phrase in navigation_indicators):
                # If title is also short/generic, likely navigation
                if len(normalized.split()) <= 4:
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

