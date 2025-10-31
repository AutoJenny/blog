"""Service for importing extracted events into calendar_events table."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
from config.database import db_manager
from newsletter.services.deduplication_service import check_calendar_event_duplicate, should_skip_item

logger = logging.getLogger(__name__)


def calculate_week_number(date: datetime) -> int:
    """Calculate ISO week number from date."""
    return date.isocalendar()[1]


def get_or_create_events_category() -> Optional[int]:
    """Get or create 'Events' category in calendar_categories."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Try to find existing "Events" category
            cur.execute("""
                SELECT id FROM calendar_categories
                WHERE name = 'Events'
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                return row['id']
            
            # Create if not exists
            cur.execute("""
                INSERT INTO calendar_categories (name, description, is_active)
                VALUES ('Events', 'Events imported from external sources', true)
                RETURNING id
            """)
            row = cur.fetchone()
            if row:
                return row['id']
    
    return None


def import_event_to_calendar(
    title: str,
    description: Optional[str],
    start_date: datetime,
    end_date: Optional[datetime],
    url: Optional[str],
    location: Optional[str],
    source_name: str,
    skip_duplicates: bool = True
) -> Optional[Dict[str, Any]]:
    """Import a single event into calendar_events table.
    
    Args:
        title: Event title
        description: Event description
        start_date: Event start date (required)
        end_date: Event end date (defaults to start_date if None)
        url: Source URL for the event
        location: Event location/venue
        source_name: Name of source organization
        skip_duplicates: If True, skip if duplicate found
    
    Returns:
        Dict with imported event data if successful, None if skipped or failed
    """
    if not title or not start_date:
        logger.warning(f"Cannot import event: missing title or start_date")
        return None
    
    # Default end_date to start_date if not provided
    if not end_date:
        end_date = start_date
    
    # Calculate week_number and year
    week_number = calculate_week_number(start_date)
    year = start_date.year
    
    # Check for duplicates if enabled
    if skip_duplicates:
        duplicate = check_calendar_event_duplicate(
            title=title,
            event_date=start_date,
            url=url,
            year=year,
            week_number=week_number
        )
        
        if duplicate:
            logger.info(f"Skipping duplicate event: {title} (match: {duplicate.get('match_type')})")
            return {
                'skipped': True,
                'reason': 'duplicate',
                'duplicate_event_id': duplicate.get('id'),
                'match_type': duplicate.get('match_type'),
            }
    
    # Import event
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Insert event
            cur.execute("""
                INSERT INTO calendar_events (
                    event_title,
                    event_description,
                    start_date,
                    end_date,
                    week_number,
                    year,
                    content_type,
                    priority,
                    tags,
                    is_recurring
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, event_title, start_date, end_date, year, week_number
            """, (
                title,
                description,
                start_date.date(),
                end_date.date(),
                week_number,
                year,
                'event',
                1,  # Default priority
                {'source': source_name, 'location': location, 'url': url} if url or location else {'source': source_name},
                False  # Not recurring by default
            ))
            
            row = cur.fetchone()
            event_id = row['id']
            
            # Link to "Events" category
            category_id = get_or_create_events_category()
            if category_id:
                try:
                    cur.execute("""
                        INSERT INTO calendar_event_categories (event_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (event_id, category_id))
                except Exception as e:
                    logger.warning(f"Could not link event to category: {e}")
            
            conn.commit()
            
            logger.info(f"Imported event: {title} (ID: {event_id}, Week {week_number}/{year})")
            
            return {
                'id': event_id,
                'title': row['event_title'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'year': row['year'],
                'week_number': row['week_number'],
                'imported': True,
            }


def import_events_from_items(items: List[Dict[str, Any]], skip_duplicates: bool = True) -> Dict[str, Any]:
    """Import multiple events from normalized source items.
    
    Args:
        items: List of normalized items (from HTML/RSS adapters)
        skip_duplicates: If True, skip duplicate events
    
    Returns:
        Dict with import summary:
        {
            'imported': int,
            'skipped': int,
            'failed': int,
            'results': List[Dict]
        }
    """
    imported = 0
    skipped = 0
    failed = 0
    results = []
    
    for item in items:
        # Only process event-type items
        if item.get('category') != 'event':
            continue
        
        title = item.get('title')
        description = item.get('description')
        event_date = item.get('event_date')
        url = item.get('url')
        location = item.get('location')
        source_name = item.get('source_name', 'Unknown')
        
        if not event_date:
            # Try to use published_at as fallback
            event_date = item.get('published_at')
        
        if not event_date:
            logger.warning(f"Skipping event {title}: no event_date or published_at")
            failed += 1
            continue
        
        # If event_date is a datetime, use it; otherwise treat as start_date
        if isinstance(event_date, datetime):
            start_date = event_date
            end_date = event_date  # Default to same day
        else:
            logger.warning(f"Event date is not datetime: {type(event_date)}")
            failed += 1
            continue
        
        # Extract end_date from raw_data if available
        raw_data = item.get('raw_data', {})
        if raw_data and isinstance(raw_data, dict):
            # Check for date ranges in raw_data
            # This is a placeholder; actual implementation would parse date ranges
            pass
        
        result = import_event_to_calendar(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            url=url,
            location=location,
            source_name=source_name,
            skip_duplicates=skip_duplicates
        )
        
        if result:
            if result.get('skipped'):
                skipped += 1
            elif result.get('imported'):
                imported += 1
            results.append(result)
        else:
            failed += 1
    
    logger.info(f"Event import complete: {imported} imported, {skipped} skipped, {failed} failed")
    
    return {
        'imported': imported,
        'skipped': skipped,
        'failed': failed,
        'results': results,
    }

