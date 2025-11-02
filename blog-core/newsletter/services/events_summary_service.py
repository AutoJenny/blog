"""Event summary service for newsletter snapshot block."""

from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from config.database import db_manager
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


def get_event_items(days_back: int = 365, days_ahead: int = 365, source_name: Optional[str] = None, location: Optional[str] = None, include_all_without_dates: bool = True, recurrence_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get event items from database for specified date range.
    
    Args:
        days_back: Number of days in the past to include (for events WITH dates)
        days_ahead: Number of days in the future to include (for events WITH dates)
        source_name: Optional filter by source
        location: Optional filter by location
        include_all_without_dates: If True, include ALL events without dates regardless of range
    
    Returns:
        List of event items
    """
    today = date.today()
    start_date = today - timedelta(days=days_back)
    end_date = today + timedelta(days=days_ahead)
    
    where_clauses = ["category = 'event'"]
    params: List[Any] = []
    
    # Date range filter - be inclusive
    # Include:
    # 1. ALL events without dates (they're still valid events, just no date info extracted yet)
    # 2. Events with dates in the specified range
    # 3. Events with published_at in range
    if include_all_without_dates:
        # Include all events without dates PLUS events with dates in range
        where_clauses.append("""
            (
                event_date IS NULL 
                OR event_date::date BETWEEN %s AND %s 
                OR published_at::date BETWEEN %s AND %s
            )
        """)
    else:
        # Strict date range filtering
        where_clauses.append("""
            (
                event_date::date BETWEEN %s AND %s 
                OR published_at::date BETWEEN %s AND %s
            )
        """)
    params.extend([start_date, end_date, start_date, end_date])
    
    # Optional filters
    if source_name:
        where_clauses.append("source_name = %s")
        params.append(source_name)
    
    if location:
        where_clauses.append("(location ILIKE %s OR raw_data->>'location' ILIKE %s)")
        params.extend([f'%{location}%', f'%{location}%'])
    
    if recurrence_type:
        if recurrence_type in ('annual', 'one_off'):
            where_clauses.append("event_recurrence_type = %s")
            params.append(recurrence_type)
    
    sql = f"""
        SELECT 
            id, source_name, title, url, published_at, event_date, location, category,
            raw_data, signal_score, freshness_score, combined_score, cached_at,
            suitability_score, suitability_notes, is_event, calendar_event_id,
            event_recurrence_type
        FROM newsletter_source_item
        WHERE {' AND '.join(where_clauses)}
        ORDER BY 
            CASE 
                WHEN event_date IS NOT NULL THEN event_date
                WHEN published_at IS NOT NULL THEN published_at
                ELSE cached_at
            END ASC,
            combined_score DESC NULLS LAST
    """
    
    with db_manager.get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def generate_events_summary(days_back: int = 365, days_ahead: int = 365, source_name: Optional[str] = None, location: Optional[str] = None, recurrence_type: Optional[str] = None) -> Dict[str, Any]:
    """Generate events summary from database.
    
    Args:
        days_back: Days to look back (for events with dates)
        days_ahead: Days to look ahead (for events with dates)
        source_name: Optional source filter
        location: Optional location filter
        recurrence_type: Optional recurrence type filter ('annual' or 'one_off')
        
    Returns:
        Dict with summary and event lists
    """
    # Include all events without dates, plus events with dates in range
    items = get_event_items(
        days_back=days_back, 
        days_ahead=days_ahead, 
        source_name=source_name, 
        location=location,
        recurrence_type=recurrence_type,
        include_all_without_dates=True  # Show all events, not just those in date range
    )
    
    if not items:
        return {
            'generated_at': datetime.now(),
            'days_back': days_back,
            'days_ahead': days_ahead,
            'total_events': 0,
            'summary_text': f'No events found for the period {days_back} days ago to {days_ahead} days ahead.',
            'upcoming_events': [],
            'past_events': [],
            'sources': {},
            'locations': {},
        }
    
    # Split into past and upcoming
    today = date.today()
    upcoming = []
    past = []
    
    for item in items:
        event_date = item.get('event_date')
        if event_date:
            if isinstance(event_date, datetime):
                event_date = event_date.date()
            elif isinstance(event_date, date):
                pass  # Already a date
            else:
                # Try to parse
                try:
                    event_date = event_date.date()
                except:
                    continue
        elif item.get('published_at'):
            try:
                pub_date = item['published_at']
                if isinstance(pub_date, datetime):
                    event_date = pub_date.date()
                else:
                    event_date = pub_date
            except:
                continue
        else:
            # No date, treat as upcoming
            upcoming.append(item)
            continue
        
        if event_date >= today:
            upcoming.append(item)
        else:
            past.append(item)
    
    # Group by source
    sources = {}
    for item in items:
        source = item.get('source_name', 'Unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(item)
    
    # Group by location
    locations = {}
    for item in items:
        loc = item.get('location') or item.get('raw_data', {}).get('location', '') or 'Unspecified'
        if loc not in locations:
            locations[loc] = []
        locations[loc].append(item)
    
    # Generate summary text
    summary_parts = []
    if upcoming:
        summary_parts.append(f"Found {len(upcoming)} upcoming events and {len(past)} past events.")
        summary_parts.append(f"Events span from {len(sources)} sources across {len(locations)} locations.")
    else:
        summary_parts.append(f"Found {len(items)} events, mostly in the past.")
    
    summary_text = ' '.join(summary_parts)
    
    return {
        'generated_at': datetime.now(),
        'days_back': days_back,
        'days_ahead': days_ahead,
        'total_events': len(items),
        'upcoming_count': len(upcoming),
        'past_count': len(past),
        'summary_text': summary_text,
        'upcoming_events': [
            {
                'id': e.get('id'),
                'title': e.get('title', ''),
                'url': e.get('url', ''),
                'source': e.get('source_name', ''),
                'event_date': e.get('event_date').isoformat() if e.get('event_date') else None,
                'location': e.get('location', ''),
                'description': e.get('raw_data', {}).get('description', ''),
                'date_text': e.get('raw_data', {}).get('date_text', ''),
                'combined_score': e.get('combined_score', 0),
            }
            for e in upcoming[:50]  # Limit upcoming
        ],
        'past_events': [
            {
                'id': e.get('id'),
                'title': e.get('title', ''),
                'url': e.get('url', ''),
                'source': e.get('source_name', ''),
                'event_date': e.get('event_date').isoformat() if e.get('event_date') else None,
                'location': e.get('location', ''),
                'description': e.get('raw_data', {}).get('description', ''),
                'date_text': e.get('raw_data', {}).get('date_text', ''),
                'combined_score': e.get('combined_score', 0),
            }
            for e in past[-20:]  # Last 20 past events
        ],
        'sources': {
            name: len(events) for name, events in sources.items()
        },
        'locations': {
            loc: len(events) for loc, events in locations.items() if loc != 'Unspecified'
        },
    }


def get_event_detail(event_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed view of a single event.
    
    Args:
        event_id: ID of event in newsletter_source_item
        
    Returns:
        Event details or None if not found
    """
    sql = """
        SELECT 
            id, source_name, title, url, published_at, event_date, location, category,
            raw_data, signal_score, freshness_score, combined_score, cached_at,
            suitability_score, suitability_notes, is_event, calendar_event_id
        FROM newsletter_source_item
        WHERE id = %s AND category = 'event'
        LIMIT 1
    """
    
    with db_manager.get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (event_id,))
            row = cur.fetchone()
            
            if not row:
                return None
            
            item = dict(row)
            
            # Get related calendar event if linked
            calendar_event = None
            if item.get('calendar_event_id'):
                cur.execute("""
                    SELECT id, title, event_date, location, description
                    FROM calendar_events
                    WHERE id = %s
                """, (item['calendar_event_id'],))
                cal_row = cur.fetchone()
                if cal_row:
                    calendar_event = dict(cal_row)
            
            return {
                'id': item.get('id'),
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'source_name': item.get('source_name', ''),
                'event_date': item.get('event_date').isoformat() if item.get('event_date') else None,
                'published_at': item.get('published_at').isoformat() if item.get('published_at') else None,
                'location': item.get('location', ''),
                'description': item.get('raw_data', {}).get('description', ''),
                'date_text': item.get('raw_data', {}).get('date_text', ''),
                'raw_data': item.get('raw_data', {}),
                'signal_score': item.get('signal_score'),
                'freshness_score': item.get('freshness_score'),
                'combined_score': item.get('combined_score'),
                'suitability_score': item.get('suitability_score'),
                'suitability_notes': item.get('suitability_notes'),
                'cached_at': item.get('cached_at').isoformat() if item.get('cached_at') else None,
                'is_event': item.get('is_event', False),
                'calendar_event': calendar_event,
            }

