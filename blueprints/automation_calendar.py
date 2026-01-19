"""
Calendar and Scheduling API Endpoints
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta, date
from config.database import db_manager
import logging
from utils.calendar_resolver import resolve_item_for_week

logger = logging.getLogger(__name__)

bp = Blueprint('automation_calendar', __name__)

def iso_year_week(dt: date) -> tuple[int, int]:
    """Calculate ISO year and week number from a date."""
    # ISO week: week 1 is the first week with a Thursday
    # Algorithm: Find the Thursday of the week containing the date
    days_since_monday = dt.weekday()
    thursday = dt + timedelta(days=(3 - days_since_monday))
    year = thursday.year
    week = int(thursday.strftime('%V'))
    return year, week

@bp.route('/next-up', methods=['GET'])
def get_next_up():
    """Get next scheduled week and selected theme/item using new calendar system"""
    try:
        # Get current ISO week
        today = date.today()
        current_year, current_week = iso_year_week(today)
        
        # Calculate week start date (Monday of ISO week)
        jan4 = date(current_year, 1, 4)
        jan4_weekday = jan4.weekday()  # 0 = Monday
        week1_monday = jan4 - timedelta(days=jan4_weekday)
        week_start = week1_monday + timedelta(weeks=current_week - 1, days=0)
        week_end = week_start + timedelta(days=6)
        
        # Get theme for current week using new calendar system
        theme_item = resolve_item_for_week('theme', current_year, current_week)
        
        if not theme_item:
            return jsonify({
                "success": False,
                "error": f"No theme found for week {current_week} of {current_year}"
            }), 404
            
        # Check if there's an existing post for this theme
        with db_manager.get_cursor() as cursor:
            existing_post_id = None
            theme_title = theme_item.get('theme_title') or theme_item.get('title', '')
            if theme_title:
                # Only reuse posts in workflow states, never published
                cursor.execute("""
                    SELECT p.id, p.status FROM post p
                    JOIN post_development pd ON p.id = pd.post_id
                    WHERE pd.idea_seed ILIKE %s 
                      AND p.status IN ('draft', 'in_process')
                    ORDER BY p.created_at DESC
                    LIMIT 1
                """, (f'%{theme_title}%',))
                existing_post = cursor.fetchone()
                if existing_post:
                    existing_post_id = existing_post['id']
                    logger.info(f"Found existing post {existing_post_id} with status '{existing_post['status']}' for theme '{theme_title}'")
            
            # Get production status
            production_status = "not_started"
            if existing_post_id:
                cursor.execute("SELECT status FROM post WHERE id = %s", (existing_post_id,))
                post_data = cursor.fetchone()
                if post_data and post_data['status'] == 'published':
                    production_status = "completed"
                else:
                    production_status = "in_progress"
            
            # Get default publication day from post_type_config for themed posts
            try:
                from blueprints.post_type_config import get_publication_day_for_post_type
                themed_config = get_publication_day_for_post_type('themed')
                default_day = themed_config['day'] if themed_config else 3  # Fallback to Wednesday
            except:
                default_day = 3  # Wednesday
            
            # Calculate publication date based on configured day
            days_since_monday = week_start.weekday()  # Monday = 0
            target_day_offset = (default_day - 1) - days_since_monday
            publish_date = week_start + timedelta(days=target_day_offset)
            
            # If today is past the target day, use next week or end of week
            if today > publish_date:
                next_occurrence = publish_date + timedelta(days=7)
                if next_occurrence <= week_end:
                    publish_date = next_occurrence
                else:
                    publish_date = week_end
            
            # Format schedule date
            scheduled_date = publish_date.strftime('%b %d, %Y')
            days_diff = (publish_date - today).days
            if days_diff == 0:
                scheduled_relative = "Today"
            elif days_diff == 1:
                scheduled_relative = "Tomorrow"
            elif days_diff > 1:
                scheduled_relative = f"In {days_diff} days"
            elif days_diff == -1:
                scheduled_relative = "Yesterday"
            else:
                scheduled_relative = f"{abs(days_diff)} days ago"
            
            # Build response
            data = {
                "success": True,
                "data": {
                    "current_week": {
                        "week_number": current_week,
                        "year": current_year,
                        "start_date": week_start.strftime('%Y-%m-%d'),
                        "end_date": week_end.strftime('%Y-%m-%d'),
                        "month_name": week_start.strftime('%B')
                    },
                    "selected_idea": {
                        "id": theme_item.get('id'),
                        "title": theme_item.get('theme_title') or theme_item.get('title', ''),
                        "description": theme_item.get('theme_description') or theme_item.get('description', ''),
                        "categories": [],  # Categories not in new system
                        "priority": "normal",  # Default priority
                        "seasonal_context": None,
                        "content_type": "themed",
                        "tags": []
                    },
                    "alternative_ideas": [],  # No alternatives in new system
                    "production_status": production_status,
                    "scheduled_date": scheduled_date,
                    "scheduled_relative": scheduled_relative,
                    "post_id": existing_post_id,
                    "can_start_automation": True,
                    "next_available_slot": publish_date.strftime('%Y-%m-%dT14:00:00Z')
                }
            }
            
            return jsonify(data)
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route('/select-idea', methods=['POST'])
def select_idea():
    """LEGACY ENDPOINT (DEPRECATED)
    
    This endpoint previously wrote to the legacy calendar_schedule table and relied on
    calendar_weeks.is_current_week. The new system uses the cyclic calendar resolver
    and week persistence V2 tables/views (calendar_week_items, calendar_week_selection_v2).
    
    To avoid silently writing to deprecated tables, this endpoint is now disabled.
    """
    return jsonify({
        'success': False,
        'error': 'Legacy automation calendar endpoint /select-idea is deprecated. '
                 'Use the new week persistence V2 and cyclic calendar flows instead.'
    }), 410

@bp.route('/update-schedule', methods=['POST'])
def update_schedule():
    """LEGACY ENDPOINT (DEPRECATED)
    
    This endpoint previously updated calendar_schedule using calendar_weeks.is_current_week.
    The new scheduling system uses unified week persistence (calendar_week_items/calendar_week_posts_v2)
    and per-channel publication configs instead.
    
    To prevent accidental writes to deprecated tables, this endpoint is now disabled.
    """
    return jsonify({
        'success': False,
        'error': 'Legacy automation calendar endpoint /update-schedule is deprecated. '
                 'Use the new publication scheduling/dashboard flows instead.'
    }), 410
