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
                cursor.execute("""
                    SELECT p.id FROM post p
                    JOIN post_development pd ON p.id = pd.post_id
                    WHERE pd.idea_seed ILIKE %s AND p.status != 'deleted'
                    ORDER BY p.created_at DESC
                    LIMIT 1
                """, (f'%{theme_title}%',))
                existing_post = cursor.fetchone()
                if existing_post:
                    existing_post_id = existing_post['id']
                    logger.info(f"Found existing post {existing_post_id} for theme '{theme_title}'")
            
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
    """Select an idea for the current week"""
    try:
        data = request.get_json()
        idea_id = data.get('idea_id')
        
        if not idea_id:
            return jsonify({'success': False, 'error': 'Idea ID is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current week
            cursor.execute("""
                SELECT week_number, year FROM calendar_weeks 
                WHERE is_current_week = TRUE
                ORDER BY year DESC, week_number DESC
                LIMIT 1
            """)
            current_week = cursor.fetchone()
            
            if not current_week:
                return jsonify({'success': False, 'error': 'No current week found'}), 404
            
            # Check if idea exists for this week
            cursor.execute("""
                SELECT id FROM calendar_ideas 
                WHERE id = %s AND week_number = %s
            """, (idea_id, current_week['week_number']))
            
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Idea not found for current week'}), 404
            
            # Update or create schedule entry
            cursor.execute("""
                INSERT INTO calendar_schedule (year, week_number, idea_id, status, requires_approval, automation_enabled)
                VALUES (%s, %s, %s, 'planned', true, true)
                ON CONFLICT (year, week_number) 
                DO UPDATE SET idea_id = %s, updated_at = NOW()
                RETURNING idea_id
            """, (current_week['year'], current_week['week_number'], idea_id, idea_id))
            
            result = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'message': 'Idea selected successfully',
                'idea_id': result['idea_id']
            })
            
    except Exception as e:
        logger.error(f"Error selecting idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/update-schedule', methods=['POST'])
def update_schedule():
    """Update the scheduled date and time for a post"""
    try:
        data = request.get_json()
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        
        if not scheduled_date:
            return jsonify({'success': False, 'error': 'Scheduled date is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get current week
            cursor.execute("""
                SELECT week_number, year FROM calendar_weeks 
                WHERE is_current_week = TRUE
                ORDER BY year DESC, week_number DESC
                LIMIT 1
            """)
            current_week = cursor.fetchone()
            
            if not current_week:
                return jsonify({'success': False, 'error': 'No current week found'}), 404
            
            # Parse the scheduled date
            try:
                from datetime import datetime, date, timedelta
                scheduled_datetime = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
                scheduled_date_only = scheduled_datetime.date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format'}), 400
            
            # Update the schedule
            cursor.execute("""
                UPDATE calendar_schedule 
                SET scheduled_date = %s, scheduled_time = %s, updated_at = NOW()
                WHERE year = %s AND week_number = %s
                RETURNING scheduled_date, scheduled_time
            """, (scheduled_date_only, scheduled_time or '14:00:00', current_week['year'], current_week['week_number']))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'success': False, 'error': 'Schedule not found'}), 404
            
            return jsonify({
                'success': True,
                'message': 'Schedule updated successfully',
                'scheduled_date': result['scheduled_date'].strftime('%Y-%m-%d'),
                'scheduled_time': str(result['scheduled_time'])
            })
            
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
