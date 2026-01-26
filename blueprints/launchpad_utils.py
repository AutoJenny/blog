# blueprints/launchpad_utils.py
"""Shared utility functions for launchpad functionality."""

import logging
import json
from datetime import datetime, date, timedelta
from config.database import db_manager

logger = logging.getLogger(__name__)

def get_next_posting_slot(cursor, platform='facebook', content_type='product'):
    """Calculate the next available posting slot based on schedules and existing queue."""
    try:
        # Get active schedules for the specific platform and content type
        cursor.execute("""
            SELECT id, time, timezone, days, is_active
            FROM daily_posts_schedule
            WHERE is_active = true AND platform = %s AND content_type = %s
            ORDER BY time ASC
        """, (platform, content_type))
        schedules = cursor.fetchall()
        
        if not schedules:
            return None
        
        # Get the latest scheduled post for THIS content type to know where to start
        cursor.execute("""
            SELECT scheduled_timestamp, scheduled_date, scheduled_time
            FROM posting_queue
            WHERE scheduled_timestamp IS NOT NULL AND content_type = %s
            ORDER BY scheduled_timestamp DESC
            LIMIT 1
        """, (content_type,))
        latest_scheduled = cursor.fetchone()
        
        # Start from current time or latest scheduled time + 1 day
        if latest_scheduled and latest_scheduled['scheduled_timestamp']:
            start_date = latest_scheduled['scheduled_date'] + timedelta(days=1)
        else:
            start_date = date.today()
        
        # First, try to fill existing scheduled days for THIS content type
        cursor.execute("""
            SELECT scheduled_date, scheduled_time, COUNT(*) as count
            FROM posting_queue
            WHERE scheduled_timestamp IS NOT NULL AND content_type = %s
            GROUP BY scheduled_date, scheduled_time
            ORDER BY scheduled_date, scheduled_time
        """, (content_type,))
        existing_slots = cursor.fetchall()
        
        # Check existing slots first to fill them up
        for slot in existing_slots:
            slot_date = slot['scheduled_date']
            slot_time = slot['scheduled_time']
            existing_count = slot['count']
            
            # Allow only 1 post per time slot
            max_posts_per_slot = 1
            
            if existing_count < max_posts_per_slot:
                # Found an available slot in existing day
                slot_timestamp = datetime.combine(slot_date, slot_time)
                return {
                    'date': slot_date,
                    'time': slot_time,
                    'timestamp': slot_timestamp,
                    'schedule_name': f'Existing Slot',
                    'timezone': 'GMT'
                }
        
        # If no existing slots available, find the next new slot
        for days_ahead in range(30):  # Look up to 30 days ahead
            check_date = start_date + timedelta(days=days_ahead)
            day_of_week = check_date.isoweekday()  # ISO: 1=Monday, 7=Sunday
            
            # CRITICAL: Exclude Sunday (day 7) - reserved for DEPTH_LONG posts
            if day_of_week == 7:  # Sunday
                # Check if Content Roles rail exists for Sunday 15:00
                try:
                    from config.content_roles_schedule_rails import get_rails_for_platform
                    rails = get_rails_for_platform('facebook', role='DEPTH_LONG')
                    # Check if any rail is for Sunday (day 7) at 15:00
                    if rails and any(r['day'] == 7 and r['time'] == '15:00' for r in rails):
                        logger.debug(f"Skipping Sunday {check_date} - reserved for DEPTH_LONG posts")
                        continue
                except Exception as e:
                    logger.warning(f"Error checking Content Roles rails: {e}, skipping Sunday to be safe")
                    continue
            
            for schedule in schedules:
                schedule_days = schedule['days'] if isinstance(schedule['days'], list) else json.loads(schedule['days'])
                
                if day_of_week in schedule_days:
                    # This schedule applies to this day
                    schedule_time = schedule['time']
                    schedule_timestamp = datetime.combine(check_date, schedule_time)
                    
                    # Check if this slot already exists for THIS content type
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM posting_queue
                        WHERE scheduled_date = %s AND scheduled_time = %s AND content_type = %s
                    """, (check_date, schedule_time, content_type))
                    
                    existing_count = cursor.fetchone()['count']
                    
                    if existing_count == 0:
                        # Found a new available slot
                        return {
                            'date': check_date,
                            'time': schedule_time,
                            'timestamp': schedule_timestamp,
                            'schedule_name': f'Schedule {schedule["id"]}',
                            'timezone': schedule['timezone']
                        }
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculating next posting slot: {e}")
        return None

def strip_html_doc(content):
    """Strip HTML document structure and return only body content."""
    if not content:
        return content
    
    import re
    
    # Remove DOCTYPE declaration
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove html, head, and body tags, keeping only the content inside body
    content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove any remaining malformed HTML closing tags
    content = re.sub(r'</html[^>]*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*', '', content, flags=re.IGNORECASE)
    
    # Clean up any remaining whitespace and newlines
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'>\s+<', '><', content)
    
    return content.strip()

