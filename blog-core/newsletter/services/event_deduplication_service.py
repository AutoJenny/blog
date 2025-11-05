"""Enhanced event deduplication service using fuzzy matching and intelligent merging."""

from __future__ import annotations

import logging
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from config.database import db_manager
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Similarity thresholds
TITLE_SIMILARITY_THRESHOLD = 0.85  # 85% similarity considered duplicate
STRICT_TITLE_SIMILARITY = 0.95  # 95% similarity for strict matching
DATE_TOLERANCE_DAYS = 7  # Events within 7 days can be considered same


def normalize_title(title: str) -> str:
    """Normalize title for comparison: lowercase, strip, remove common prefixes."""
    if not title:
        return ""
    
    # Lowercase and strip
    normalized = title.lower().strip()
    
    # Remove common prefixes/suffixes that don't add meaning
    prefixes = [
        "ring of", "stone circle and", "and", "the ", "a ", "an ",
        "walk", "tour", "visit", "explore", "discover"
    ]
    
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
        if normalized.endswith(prefix):
            normalized = normalized[:-len(prefix)].strip()
    
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    
    return normalized


def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles using fuzzy matching."""
    if not title1 or not title2:
        return 0.0
    
    # Direct similarity
    direct = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
    
    # Normalized similarity
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    normalized = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Return the higher of the two
    return max(direct, normalized)


def dates_are_similar(date1: Optional[datetime], date2: Optional[datetime], tolerance_days: int = DATE_TOLERANCE_DAYS) -> bool:
    """Check if two dates are within tolerance."""
    if not date1 or not date2:
        return False
    
    # Convert to datetime if needed
    if isinstance(date1, datetime):
        d1 = date1
    else:
        try:
            d1 = datetime.fromisoformat(str(date1)) if isinstance(date1, str) else date1
        except:
            return False
    
    if isinstance(date2, datetime):
        d2 = date2
    else:
        try:
            d2 = datetime.fromisoformat(str(date2)) if isinstance(date2, str) else date2
        except:
            return False
    
    # Compare dates (ignore time)
    d1_date = d1.date() if isinstance(d1, datetime) else d1
    d2_date = d2.date() if isinstance(d2, datetime) else d2
    
    diff = abs((d1_date - d2_date).days)
    return diff <= tolerance_days


def find_duplicate_event(
    title: str,
    url: Optional[str] = None,
    event_date: Optional[datetime] = None,
    location: Optional[str] = None,
    source_name: Optional[str] = None,
    exclude_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Find duplicate event in database using fuzzy matching.
    
    Args:
        title: Event title to match
        url: Optional URL for exact matching
        event_date: Optional event date
        location: Optional location
        source_name: Optional source name (if provided, prefer matches from same source)
        exclude_id: ID to exclude from search (e.g., when updating)
    
    Returns:
        Dict with duplicate event data if found, else None
        {
            'id': int,
            'title': str,
            'url': str,
            'event_date': datetime,
            'location': str,
            'source_name': str,
            'match_type': str,  # 'exact_url', 'similar_title', 'similar_title_date'
            'similarity': float,
            'needs_update': bool  # True if duplicate found but has different/missing data
        }
    """
    if not title:
        return None
    
    with db_manager.get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # First check: exact URL match (if URL provided)
            if url:
                url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
                # Handle None exclude_id properly
                if exclude_id is None:
                    cur.execute("""
                        SELECT id, title, url, event_date, location, source_name, cached_at,
                               raw_data, suitability_score, suitability_notes
                        FROM newsletter_source_item
                        WHERE category = 'event'
                        AND source_url_hash = %s
                        ORDER BY cached_at DESC
                        LIMIT 1
                    """, (url_hash,))
                else:
                    cur.execute("""
                        SELECT id, title, url, event_date, location, source_name, cached_at,
                               raw_data, suitability_score, suitability_notes
                        FROM newsletter_source_item
                        WHERE category = 'event'
                        AND source_url_hash = %s
                        AND id != %s
                        ORDER BY cached_at DESC
                        LIMIT 1
                    """, (url_hash, exclude_id))
                
                row = cur.fetchone()
                if row:
                    similarity = calculate_title_similarity(title, row['title'])
                    return {
                        'id': row['id'],
                        'title': row['title'],
                        'url': row.get('url'),
                        'event_date': row.get('event_date'),
                        'location': row.get('location'),
                        'source_name': row.get('source_name'),
                        'raw_data': row.get('raw_data', {}),
                        'suitability_score': row.get('suitability_score'),
                        'suitability_notes': row.get('suitability_notes'),
                        'match_type': 'exact_url',
                        'similarity': similarity,
                        'needs_update': similarity < 0.95 or not row.get('event_date') or not row.get('location'),
                    }
            
            # Second check: similar title (fuzzy match)
            # Get recent events to check
            cutoff_date = datetime.now() - timedelta(days=365)  # Check last year
            # Handle None exclude_id properly
            if exclude_id is None:
                cur.execute("""
                    SELECT id, title, url, event_date, location, source_name, cached_at,
                           raw_data, suitability_score, suitability_notes
                    FROM newsletter_source_item
                    WHERE category = 'event'
                    AND (event_date >= %s OR event_date IS NULL OR cached_at >= %s)
                    ORDER BY 
                        CASE WHEN source_name = %s THEN 0 ELSE 1 END,
                        cached_at DESC
                """, (cutoff_date, cutoff_date, source_name or ''))
            else:
                cur.execute("""
                    SELECT id, title, url, event_date, location, source_name, cached_at,
                           raw_data, suitability_score, suitability_notes
                    FROM newsletter_source_item
                    WHERE category = 'event'
                    AND id != %s
                    AND (event_date >= %s OR event_date IS NULL OR cached_at >= %s)
                    ORDER BY 
                        CASE WHEN source_name = %s THEN 0 ELSE 1 END,
                        cached_at DESC
                """, (exclude_id, cutoff_date, cutoff_date, source_name or ''))
            
            rows = cur.fetchall() or []
            
            best_match = None
            best_similarity = 0.0
            
            for row in rows:
                existing_title = row['title']
                similarity = calculate_title_similarity(title, existing_title)
                
                if similarity < TITLE_SIMILARITY_THRESHOLD:
                    continue
                
                # If we have dates, check if they're similar
                existing_date = row.get('event_date')
                date_match = True
                if event_date and existing_date:
                    date_match = dates_are_similar(event_date, existing_date)
                
                # If we have locations, check if they match (case-insensitive)
                location_match = True
                if location and row.get('location'):
                    location_match = location.lower().strip() == row.get('location', '').lower().strip()
                
                # Prefer matches with same source, similar date, and similar location
                match_score = similarity
                if source_name and row.get('source_name') == source_name:
                    match_score += 0.1  # Boost same source
                if date_match:
                    match_score += 0.05  # Boost similar date
                if location_match:
                    match_score += 0.05  # Boost same location
                
                if match_score > best_similarity:
                    best_similarity = match_score
                    best_match = {
                        'id': row['id'],
                        'title': row['title'],
                        'url': row.get('url'),
                        'event_date': row.get('event_date'),
                        'location': row.get('location'),
                        'source_name': row.get('source_name'),
                        'raw_data': row.get('raw_data', {}),
                        'suitability_score': row.get('suitability_score'),
                        'suitability_notes': row.get('suitability_notes'),
                        'match_type': 'similar_title' if not date_match else 'similar_title_date',
                        'similarity': similarity,
                        'needs_update': (
                            similarity < STRICT_TITLE_SIMILARITY or
                            (event_date and not existing_date) or
                            (location and not row.get('location')) or
                            (url and not row.get('url'))
                        ),
                    }
            
            return best_match


def merge_event_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge new event data into existing, preferring non-empty values from new.
    
    Args:
        existing: Existing event data from database
        new: New event data to merge
    
    Returns:
        Merged event data dict
    """
    merged = existing.copy()
    
    # Always update title if new one is longer (likely more descriptive)
    if new.get('title') and len(new['title']) > len(existing.get('title', '')):
        merged['title'] = new['title']
    
    # Update URL if existing doesn't have one
    if new.get('url') and not existing.get('url'):
        merged['url'] = new['url']
        # Update hash
        merged['source_url_hash'] = hashlib.sha256(new['url'].encode('utf-8')).hexdigest()
    
    # Update event_date if existing doesn't have one
    if new.get('event_date') and not existing.get('event_date'):
        merged['event_date'] = new['event_date']
        # Also update end_date and date_qualifier if they come with event_date
        if new.get('end_date') and not existing.get('end_date'):
            merged['end_date'] = new['end_date']
        if new.get('date_qualifier') and not existing.get('date_qualifier'):
            merged['date_qualifier'] = new['date_qualifier']
    
    # Update end_date if existing doesn't have one (even if event_date exists)
    if new.get('end_date') and not existing.get('end_date'):
        merged['end_date'] = new['end_date']
        if new.get('date_qualifier') and not existing.get('date_qualifier'):
            merged['date_qualifier'] = new['date_qualifier']
    
    # Update date_qualifier if existing doesn't have one
    if new.get('date_qualifier') and not existing.get('date_qualifier'):
        merged['date_qualifier'] = new['date_qualifier']
    
    # Update location if existing doesn't have one
    if new.get('location') and not existing.get('location'):
        merged['location'] = new['location']
    
    # Merge raw_data (prefer new keys, keep existing keys if new doesn't have them)
    existing_raw = existing.get('raw_data', {}) or {}
    new_raw = new.get('raw_data', {}) or {}
    if isinstance(existing_raw, dict) and isinstance(new_raw, dict):
        merged_raw = existing_raw.copy()
        merged_raw.update(new_raw)
        merged['raw_data'] = merged_raw
    elif new_raw:
        merged['raw_data'] = new_raw
    
    # Update scores if new ones are better
    if new.get('combined_score', 0) > existing.get('combined_score', 0):
        merged['combined_score'] = new.get('combined_score')
        merged['signal_score'] = new.get('signal_score')
        merged['freshness_score'] = new.get('freshness_score')
    
    # Update cached_at to most recent
    if new.get('cached_at'):
        merged['cached_at'] = new.get('cached_at')
    
    return merged


def find_and_merge_duplicate(
    new_item: Dict[str, Any],
    update_existing: bool = True
) -> Tuple[Optional[int], bool]:
    """Find duplicate event and either skip or update.
    
    Args:
        new_item: New event item to check
        update_existing: If True, update existing record; if False, skip if duplicate
    
    Returns:
        Tuple of (existing_id, was_updated)
        - If duplicate found and updated: (existing_id, True)
        - If duplicate found and skipped: (existing_id, False)
        - If no duplicate: (None, False)
    """
    title = new_item.get('title')
    url = new_item.get('url')
    event_date = new_item.get('event_date')
    location = new_item.get('location')
    source_name = new_item.get('source_name')
    
    duplicate = find_duplicate_event(
        title=title,
        url=url,
        event_date=event_date,
        location=location,
        source_name=source_name
    )
    
    if not duplicate:
        return (None, False)
    
    # If update is enabled and duplicate needs updating, merge and update
    if update_existing and duplicate.get('needs_update'):
        merged = merge_event_data(duplicate, new_item)
        
        # Update existing record
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Update title if changed
                if merged.get('title') != duplicate.get('title'):
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET title = %s
                        WHERE id = %s
                    """, (merged['title'], duplicate['id']))
                
                # Update URL and hash if added
                if merged.get('url') and merged.get('url') != duplicate.get('url'):
                    new_hash = hashlib.sha256(merged['url'].encode('utf-8')).hexdigest()
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET url = %s, source_url_hash = %s
                        WHERE id = %s
                    """, (merged['url'], new_hash, duplicate['id']))
                
                # Update event_date if added (also update end_date and date_qualifier if present)
                if merged.get('event_date') and not duplicate.get('event_date'):
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET event_date = %s, end_date = %s, date_qualifier = %s
                        WHERE id = %s
                    """, (merged['event_date'], merged.get('end_date'), merged.get('date_qualifier'), duplicate['id']))
                
                # Update location if added
                if merged.get('location') and not duplicate.get('location'):
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET location = %s
                        WHERE id = %s
                    """, (merged['location'], duplicate['id']))
                
                # Update raw_data if merged
                if merged.get('raw_data') != duplicate.get('raw_data'):
                    from psycopg.types.json import Json
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET raw_data = %s
                        WHERE id = %s
                    """, (Json(merged['raw_data']), duplicate['id']))
                
                # Update scores if improved
                if merged.get('combined_score', 0) > duplicate.get('combined_score', 0):
                    cur.execute("""
                        UPDATE newsletter_source_item
                        SET combined_score = %s,
                            signal_score = %s,
                            freshness_score = %s
                        WHERE id = %s
                    """, (
                        merged.get('combined_score'),
                        merged.get('signal_score'),
                        merged.get('freshness_score'),
                        duplicate['id']
                    ))
                
                # Update cached_at
                cur.execute("""
                    UPDATE newsletter_source_item
                    SET cached_at = NOW()
                    WHERE id = %s
                """, (duplicate['id'],))
                
                conn.commit()
                
                logger.info(f"Updated existing event {duplicate['id']}: {duplicate['title'][:50]} (similarity: {duplicate['similarity']:.2%})")
                return (duplicate['id'], True)
    
    # Otherwise, skip (duplicate found but not updating)
    logger.debug(f"Skipping duplicate event: {title[:50]} (matches {duplicate['id']}, similarity: {duplicate['similarity']:.2%})")
    return (duplicate['id'], False)


def find_all_duplicates() -> List[Dict[str, Any]]:
    """Find all duplicate events in the database.
    
    Returns:
        List of duplicate groups, each containing event IDs that are duplicates
    """
    with db_manager.get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, title, url, event_date, location, source_name, cached_at
                FROM newsletter_source_item
                WHERE category = 'event'
                ORDER BY title, source_name, cached_at
            """)
            
            events = cur.fetchall() or []
    
    # Group duplicates
    duplicate_groups = []
    processed = set()
    
    for i, event1 in enumerate(events):
        if event1['id'] in processed:
            continue
        
        group = [event1['id']]
        processed.add(event1['id'])
        
        for event2 in events[i+1:]:
            if event2['id'] in processed:
                continue
            
            similarity = calculate_title_similarity(event1['title'], event2['title'])
            
            if similarity >= TITLE_SIMILARITY_THRESHOLD:
                # Check if dates are similar (if both have dates)
                date_match = True
                if event1.get('event_date') and event2.get('event_date'):
                    date_match = dates_are_similar(event1['event_date'], event2['event_date'])
                
                # Check if same source (more likely to be duplicate)
                same_source = event1.get('source_name') == event2.get('source_name')
                
                # If very similar title and (same source OR similar date), consider duplicate
                if similarity >= STRICT_TITLE_SIMILARITY or (similarity >= TITLE_SIMILARITY_THRESHOLD and (same_source or date_match)):
                    group.append(event2['id'])
                    processed.add(event2['id'])
        
        if len(group) > 1:
            duplicate_groups.append({
                'count': len(group),
                'ids': group,
                'title': event1['title'],
                'source': event1.get('source_name'),
            })
    
    return duplicate_groups

