"""
Calendar and Scheduling API Endpoints
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta, date
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('automation_calendar', __name__)

@bp.route('/next-up', methods=['GET'])
def get_next_up():
    """Get next scheduled week and selected idea"""
    try:
        from config.database import db_manager
        
        # Get current week
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT week_number, start_date, end_date, month_name, year
                FROM calendar_weeks 
                WHERE is_current_week = TRUE
                ORDER BY year DESC, week_number DESC
                LIMIT 1
            """)
            current_week = cursor.fetchone()
            
            if not current_week:
                return jsonify({
                    "success": False,
                    "error": "No current week found"
                }), 404
            
            # Get ideas for current week
            cursor.execute("""
                SELECT ci.id, ci.idea_title, ci.idea_description, ci.priority,
                       ci.seasonal_context, ci.content_type, ci.tags,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', cc.id,
                                   'name', cc.name,
                                   'color', cc.color,
                                   'icon', cc.icon
                               )
                           ) FILTER (WHERE cc.id IS NOT NULL), 
                           '[]'::json
                       ) as categories
                FROM calendar_ideas ci
                LEFT JOIN calendar_idea_categories cic ON ci.id = cic.idea_id
                LEFT JOIN calendar_categories cc ON cic.category_id = cc.id
                WHERE ci.week_number = %s
                GROUP BY ci.id, ci.idea_title, ci.idea_description, ci.priority,
                         ci.seasonal_context, ci.content_type, ci.tags
                ORDER BY 
                    CASE ci.priority 
                        WHEN 'mandatory' THEN 1 
                        WHEN 'random' THEN 2 
                        ELSE 3 
                    END,
                    ci.id
            """, (current_week['week_number'],))
            
            ideas = cursor.fetchall()
            
            if not ideas:
                return jsonify({
                    "success": False,
                    "error": f"No ideas found for week {current_week['week_number']}"
                }), 404
            
            # Determine selected idea: use idea_id from schedule if exists, otherwise first idea
            selected_idea = None
            alternative_ideas = []
            
            # Get schedule data for current week
            cursor.execute("""
                SELECT scheduled_date, scheduled_time, publish_time, status, post_id, idea_id
                FROM calendar_schedule 
                WHERE year = %s AND week_number = %s
                ORDER BY scheduled_date ASC
                LIMIT 1
            """, (current_week['year'], current_week['week_number']))
            
            schedule_data = cursor.fetchone()
            
            # Determine selected idea based on schedule or default to first idea
            if schedule_data and schedule_data['idea_id']:
                # Find the selected idea by ID
                for idea in ideas:
                    if idea['id'] == schedule_data['idea_id']:
                        selected_idea = idea
                        break
                # All other ideas are alternatives
                alternative_ideas = [idea for idea in ideas if idea['id'] != schedule_data['idea_id']]
            else:
                # No idea selected yet - use first idea as default
                selected_idea = ideas[0]
                alternative_ideas = ideas[1:] if len(ideas) > 1 else []
            
            # If no schedule exists, create one dynamically for this week
            if not schedule_data:
                from datetime import datetime, date, timedelta
                
                # Calculate appropriate publish date within the current week
                week_start = current_week['start_date']
                week_end = current_week['end_date']
                today = date.today()
                
                # Get default publication day from post_type_config for themed posts
                from blueprints.post_type_config import get_publication_day_for_post_type
                themed_config = get_publication_day_for_post_type('themed')
                default_day = themed_config['day'] if themed_config else 3  # Fallback to Wednesday
                
                # Calculate publication date based on configured day
                # default_day is 1-7 (Monday-Sunday), but week_start.weekday() is 0-6 (Monday-Sunday)
                if week_start and week_end:
                    # Calculate the target day of the week
                    days_since_monday = (week_start.weekday()) % 7  # Monday = 0
                    target_day_offset = (default_day - 1) - days_since_monday
                    publish_date = week_start + timedelta(days=target_day_offset)
                    
                    # If today is past the target day, schedule for next week or next available day
                    if today > publish_date:
                        # Try next occurrence in the same week
                        next_occurrence = publish_date + timedelta(days=7)
                        if next_occurrence <= week_end:
                            publish_date = next_occurrence
                        else:
                            # Use the last day of the week
                            publish_date = week_end
                    
                    # Check if there's already a post for the selected idea
                    existing_post_id = None
                    cursor.execute("""
                        SELECT p.id FROM post p
                        JOIN post_development pd ON p.id = pd.post_id
                        WHERE pd.idea_seed ILIKE %s AND p.status != 'deleted'
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    """, (f'%{selected_idea["idea_title"]}%',))
                    
                    existing_post = cursor.fetchone()
                    if existing_post:
                        existing_post_id = existing_post['id']
                        logger.info(f"Found existing post {existing_post_id} for idea '{selected_idea['idea_title']}'")
                    
                    # Insert the schedule with the selected idea
                    cursor.execute("""
                        INSERT INTO calendar_schedule 
                        (year, week_number, scheduled_date, scheduled_time, publish_time, status, requires_approval, automation_enabled, idea_id, post_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING scheduled_date, scheduled_time, publish_time, status, post_id, idea_id
                    """, (
                        current_week['year'], 
                        current_week['week_number'],
                        publish_date,
                        '14:00:00',
                        '14:00:00', 
                        'planned',
                        True,
                        True,
                        selected_idea['id'],
                        existing_post_id
                    ))
                    
                    schedule_data = cursor.fetchone()
            
            # Determine production status based on post existence and schedule
            production_status = "not_started"
            scheduled_date = "Not scheduled"
            scheduled_relative = ""
            
            if schedule_data:
                if schedule_data['post_id']:
                    # Post exists - check if it's published
                    cursor.execute("SELECT status FROM post WHERE id = %s", (schedule_data['post_id'],))
                    post_data = cursor.fetchone()
                    if post_data and post_data['status'] == 'published':
                        production_status = "completed"
                    else:
                        production_status = "in_progress"
                else:
                    production_status = "not_started"
                
                # Format schedule date
                if schedule_data['scheduled_date']:
                    from datetime import datetime, date
                    scheduled_date_obj = schedule_data['scheduled_date']
                    scheduled_date = scheduled_date_obj.strftime('%b %d, %Y')
                    
                    # Calculate relative time
                    today = date.today()
                    days_diff = (scheduled_date_obj - today).days
                    
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
            
            data = {
                        "success": True,
                        "data": {
                            "current_week": {
                                "week_number": current_week['week_number'],
                                "year": current_week['year'],
                                "start_date": current_week['start_date'].strftime('%Y-%m-%d') if current_week['start_date'] else None,
                                "end_date": current_week['end_date'].strftime('%Y-%m-%d') if current_week['end_date'] else None,
                                "month_name": current_week['month_name']
                            },
                            "selected_idea": {
                                "id": selected_idea['id'],
                                "title": selected_idea['idea_title'],
                                "description": selected_idea['idea_description'],
                                "categories": [cat['name'] for cat in selected_idea['categories']] if selected_idea['categories'] else [],
                                "priority": selected_idea['priority'],
                                "seasonal_context": selected_idea['seasonal_context'],
                                "content_type": selected_idea['content_type'],
                                "tags": selected_idea['tags'] if selected_idea['tags'] else []
                            },
                            "alternative_ideas": [
                                {
                                    "id": idea['id'],
                                    "title": idea['idea_title'],
                                    "description": idea['idea_description'],
                                    "categories": [cat['name'] for cat in idea['categories']] if idea['categories'] else [],
                                    "priority": idea['priority'],
                                    "seasonal_context": idea['seasonal_context'],
                                    "content_type": idea['content_type'],
                                    "tags": idea['tags'] if idea['tags'] else []
                                }
                                for idea in alternative_ideas
                            ],
                            "production_status": production_status,
                            "scheduled_date": scheduled_date,
                            "scheduled_relative": scheduled_relative,
                            "post_id": schedule_data['post_id'] if schedule_data and schedule_data['post_id'] else None,
                            "can_start_automation": True,
                            "next_available_slot": "2025-10-15T09:00:00Z"  # Keep mock for now
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
