"""Deduplication service for events and source items using fuzzy matching and URL checks."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import logging
from config.database import db_manager

logger = logging.getLogger(__name__)

# Similarity threshold (0.0 to 1.0) - 0.85 = 85% match
FUZZY_THRESHOLD = 0.85

# Date proximity window (days) for fuzzy matching
DATE_PROXIMITY_DAYS = 3


def similarity_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()


def hash_url(url: str) -> str:
    """Generate SHA256 hash of URL for exact duplicate detection."""
    return hashlib.sha256(url.encode('utf-8')).digest().hex()


def is_url_duplicate(url: str, existing_urls: List[str]) -> bool:
    """Check if URL already exists (exact match)."""
    url_hash = hash_url(url)
    existing_hashes = [hash_url(u) for u in existing_urls]
    return url_hash in existing_hashes


def fuzzy_match_title(title: str, existing_titles: List[str], threshold: float = FUZZY_THRESHOLD) -> Optional[Tuple[str, float]]:
    """Find best matching title using fuzzy matching.
    
    Returns:
        Tuple of (matched_title, similarity_ratio) if match found above threshold, else None
    """
    best_match = None
    best_ratio = 0.0
    
    for existing_title in existing_titles:
        ratio = similarity_ratio(title, existing_title)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = existing_title
    
    if best_ratio >= threshold:
        return (best_match, best_ratio)
    return None


def dates_within_range(date1: Optional[datetime], date2: Optional[datetime], days: int = DATE_PROXIMITY_DAYS) -> bool:
    """Check if two dates are within specified days of each other."""
    if not date1 or not date2:
        return False
    
    diff = abs((date1 - date2).days)
    return diff <= days


def check_calendar_event_duplicate(
    title: str,
    event_date: Optional[datetime],
    url: Optional[str] = None,
    year: Optional[int] = None,
    week_number: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Check if an event already exists in calendar_events table.
    
    Uses:
    1. URL hash exact match (if URL provided)
    2. Fuzzy title match + date proximity (if dates within 3 days)
    
    Returns:
        Dict with duplicate event data if found, else None
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Strategy 1: URL-based exact match (requires source_url field in calendar_events)
            # TODO: Enable once migration adds source_url to calendar_events
            # if url:
            #     url_hash = hash_url(url)
            #     cur.execute("""
            #         SELECT id, event_title, start_date, end_date, year, week_number, source_url
            #         FROM calendar_events
            #         WHERE source_url = %s
            #         LIMIT 1
            #     """, (url,))
            #     
            #     row = cur.fetchone()
            #     if row:
            #         return {
            #             'id': row['id'],
            #             'title': row['event_title'],
            #             'start_date': row['start_date'],
            #             'end_date': row['end_date'],
            #             'year': row['year'],
            #             'week_number': row['week_number'],
            #             'source_url': row.get('source_url'),
            #             'match_type': 'url_exact',
            #         }
            
            # Strategy 2: Fuzzy title + date proximity
            if event_date and year and week_number:
                # Get events within date range
                date_start = event_date - timedelta(days=DATE_PROXIMITY_DAYS)
                date_end = event_date + timedelta(days=DATE_PROXIMITY_DAYS)
                
                cur.execute("""
                    SELECT id, event_title, start_date, end_date, year, week_number
                    FROM calendar_events
                    WHERE (
                        (start_date BETWEEN %s AND %s)
                        OR (end_date BETWEEN %s AND %s)
                        OR (%s BETWEEN start_date AND end_date)
                    )
                    AND year = %s
                """, (date_start, date_end, date_start, date_end, event_date, year))
                
                candidates = [dict(r) for r in cur.fetchall()]
                
                if candidates:
                    # Check fuzzy title match
                    existing_titles = [c['event_title'] for c in candidates]
                    match_result = fuzzy_match_title(title, existing_titles)
                    
                    if match_result:
                        matched_title, similarity = match_result
                        # Find the matching candidate
                        for candidate in candidates:
                            if candidate['event_title'] == matched_title:
                                return {
                                    'id': candidate['id'],
                                    'title': candidate['event_title'],
                                    'start_date': candidate['start_date'],
                                    'end_date': candidate['end_date'],
                                    'year': candidate['year'],
                                    'week_number': candidate['week_number'],
                                    'match_type': 'fuzzy_title_date',
                                    'similarity': similarity,
                                }
            
            # Strategy 3: Fuzzy title only (if no date available)
            if not event_date:
                cur.execute("""
                    SELECT id, event_title, start_date, end_date, year, week_number
                    FROM calendar_events
                    WHERE year = %s OR year = %s
                    LIMIT 100
                """, (year or datetime.now().year, (year or datetime.now().year) + 1))
                
                candidates = [dict(r) for r in cur.fetchall()]
                existing_titles = [c['event_title'] for c in candidates]
                match_result = fuzzy_match_title(title, existing_titles)
                
                if match_result:
                    matched_title, similarity = match_result
                    for candidate in candidates:
                        if candidate['event_title'] == matched_title:
                            return {
                                'id': candidate['id'],
                                'title': candidate['event_title'],
                                'start_date': candidate['start_date'],
                                'end_date': candidate['end_date'],
                                'year': candidate['year'],
                                'week_number': candidate['week_number'],
                                'match_type': 'fuzzy_title_only',
                                'similarity': similarity,
                            }
    
    return None


def check_source_item_duplicate(url: str) -> Optional[Dict[str, Any]]:
    """Check if a source item URL already exists in newsletter_source_item.
    
    Returns:
        Dict with duplicate item data if found, else None
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            url_hash = hash_url(url)
            
            cur.execute("""
                SELECT id, title, url, published_at, event_date, source_name
                FROM newsletter_source_item
                WHERE source_url_hash = %s
                LIMIT 1
            """, (url_hash,))
            
            row = cur.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'url': row['url'],
                    'published_at': row.get('published_at'),
                    'event_date': row.get('event_date'),
                    'source_name': row.get('source_name'),
                    'match_type': 'url_exact',
                }
    
    return None


def should_skip_item(item: Dict[str, Any], check_calendar: bool = True, check_source_items: bool = True) -> Optional[Dict[str, Any]]:
    """Check if an item should be skipped due to duplicates.
    
    Args:
        item: Normalized item dict with title, url, event_date, etc.
        check_calendar: Whether to check calendar_events table
        check_source_items: Whether to check newsletter_source_item table
    
    Returns:
        Dict with duplicate info if duplicate found, else None
    """
    url = item.get('url')
    title = item.get('title')
    event_date = item.get('event_date')
    
    if not url and not title:
        return {'skip': True, 'reason': 'Missing URL and title'}
    
    # Check source items cache
    if check_source_items and url:
        duplicate = check_source_item_duplicate(url)
        if duplicate:
            logger.info(f"Skipping duplicate source item: {title} (URL: {url[:50]}...)")
            return {'skip': True, 'duplicate': duplicate, 'reason': 'source_item_duplicate'}
    
    # Check calendar events (for event-type items)
    if check_calendar and event_date and item.get('category') == 'event':
        event_year = event_date.year
        # Calculate week_number from start_date (ISO week)
        event_week = event_date.isocalendar()[1]
        
        duplicate = check_calendar_event_duplicate(
            title=title,
            event_date=event_date,
            url=url,
            year=event_year,
            week_number=event_week
        )
        
        if duplicate:
            logger.info(f"Skipping duplicate calendar event: {title} (match: {duplicate.get('match_type')})")
            return {'skip': True, 'duplicate': duplicate, 'reason': 'calendar_event_duplicate'}
    
    return None

