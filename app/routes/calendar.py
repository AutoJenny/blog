"""
Calendar Api Routes module
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from config.database import db_manager
import logging
from datetime import datetime, date
import json
import requests

logger = logging.getLogger(__name__)

# Create calendar_bp blueprint
calendar_bp = Blueprint('calendar_bp', __name__, url_prefix='/api/calendar')

"""
Calendar API routes
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template
from config.database import db_manager
import logging
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)

# Create calendar blueprint
calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')

@calendar_bp.route('/weeks/<int:year>')
@calendar_bp.route('/calendar-weeks')
def api_calendar_weeks(year):
    """Get all calendar weeks for a given year"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, week_number, start_date, end_date, month_name, is_current_week
                FROM calendar_weeks 
                WHERE year = %s 
                ORDER BY week_number
            """, (year,))
            
            weeks = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'weeks': weeks
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar weeks: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-ideas')
def api_calendar_ideas(week_number):
    """Get perpetual ideas for a specific week number"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ci.*, 
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
                GROUP BY ci.id
                ORDER BY ci.priority DESC, ci.idea_title
            """, (week_number,))
            
            ideas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'ideas': ideas
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar ideas: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-events')
def api_calendar_events(year, week_number):
    """Get events for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ce.*, 
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
                FROM calendar_events ce
                LEFT JOIN calendar_event_categories cec ON ce.id = cec.event_id
                LEFT JOIN calendar_categories cc ON cec.category_id = cc.id
                WHERE ce.year = %s AND ce.week_number = %s
                GROUP BY ce.id
                ORDER BY ce.priority DESC, ce.event_title
            """, (year, week_number))
            
            events = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'week_number': week_number,
                'events': events
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-schedule')
def api_calendar_schedule(year, week_number):
    """Get scheduled items for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cs.*, 
                       p.title as post_title, p.status as post_status
                FROM calendar_schedule cs
                LEFT JOIN post p ON cs.post_id = p.id
                WHERE cs.year = %s AND cs.week_number = %s
                ORDER BY cs.scheduled_date, cs.created_at
            """, (year, week_number))
            
            schedule = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'week_number': week_number,
                'schedule': schedule
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar schedule: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-schedule-create')
def api_calendar_schedule_create():
    """Create a new calendar schedule entry"""
    try:
        data = request.get_json()
        
        required_fields = ['year', 'week_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_schedule 
                (year, week_number, post_id, scheduled_date)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                data['year'],
                data['week_number'],
                data.get('post_id'),
                data.get('scheduled_date')
            ))
            
            schedule_id = cursor.fetchone()['id']
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Schedule entry created successfully',
                'schedule_id': schedule_id
            })
            
    except Exception as e:
        logger.error(f"Error creating calendar schedule: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-categories')
def api_calendar_categories():
    """Get all calendar categories"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, color, icon, is_active
                FROM calendar_categories 
                WHERE is_active = TRUE
                ORDER BY name
            """)
            
            categories = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'categories': categories
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar categories: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-category-create')
def api_calendar_category_create():
    """Create a new calendar category"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'color']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO calendar_categories (name, description, color, icon, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['name'],
                data.get('description', ''),
                data['color'],
                data.get('icon', ''),
                data.get('is_active', True)
            ))
            
            category_id = cursor.fetchone()['id']
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Category created successfully',
                'category_id': category_id
            })
            
    except Exception as e:
        logger.error(f"Error creating calendar category: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-category-update')
def api_calendar_category_update(category_id):
    """Update a calendar category"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Check if category exists
            cursor.execute("SELECT id FROM calendar_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Category not found'}), 404
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            allowed_fields = ['name', 'description', 'color', 'icon', 'is_active']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    values.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            values.append(category_id)
            query = f"UPDATE calendar_categories SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
            
            cursor.execute(query, values)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Category updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error updating calendar category: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-category-delete')
def api_calendar_category_delete(category_id):
    """Delete a calendar category"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if category exists
            cursor.execute("SELECT id FROM calendar_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Category not found'}), 404
            
            # Delete the category (cascade will handle related records)
            cursor.execute("DELETE FROM calendar_categories WHERE id = %s", (category_id,))
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Category deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Error deleting calendar category: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-evergreen')
def api_calendar_evergreen(week_number):
    """Get available evergreen content for a specific week"""
    try:
        year = request.args.get('year', 2025, type=int)
        frequency = request.args.get('frequency', None)
        
        with db_manager.get_cursor() as cursor:
            # Build query based on frequency
            where_clause = "ci.is_evergreen = TRUE"
            params = []
            
            if frequency:
                where_clause += " AND ci.evergreen_frequency = %s"
                params.append(frequency)
            
            # Get evergreen ideas with usage tracking
            cursor.execute(f"""
                SELECT ci.*, 
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
                WHERE {where_clause}
                GROUP BY ci.id
                ORDER BY ci.usage_count ASC, ci.last_used_date ASC NULLS FIRST, ci.priority DESC
            """, params)
            
            ideas = cursor.fetchall()
            
            # Filter based on frequency rules (simplified for now)
            available_ideas = []
            for idea in ideas:
                # Simple availability check - can be enhanced later
                if idea['usage_count'] < 3:  # Allow up to 3 uses per year
                    available_ideas.append(idea)
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'year': year,
                'frequency': frequency,
                'ideas': available_ideas
            })
            
    except Exception as e:
        logger.error(f"Error fetching evergreen content: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-evergreen-usage-report')
def api_calendar_evergreen_usage_report():
    """Get evergreen content usage report"""
    try:
        year = request.args.get('year', 2025, type=int)
        
        with db_manager.get_cursor() as cursor:
            # Get frequency statistics
            cursor.execute("""
                SELECT 
                    evergreen_frequency,
                    COUNT(*) as total_ideas,
                    AVG(usage_count) as avg_usage,
                    MAX(usage_count) as max_usage,
                    COUNT(CASE WHEN usage_count > 0 THEN 1 END) as used_ideas
                FROM calendar_ideas 
                WHERE is_evergreen = TRUE
                GROUP BY evergreen_frequency
                ORDER BY evergreen_frequency
            """)
            
            frequency_stats = cursor.fetchall()
            
            # Get usage details
            cursor.execute("""
                SELECT 
                    ci.idea_title,
                    ci.evergreen_frequency,
                    ci.usage_count,
                    ci.last_used_date,
                    ci.week_number
                FROM calendar_ideas ci
                WHERE ci.is_evergreen = TRUE
                ORDER BY ci.usage_count DESC, ci.last_used_date DESC
            """)
            
            usage_details = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'year': year,
                'frequency_stats': frequency_stats,
                'usage_details': usage_details
            })
            
    except Exception as e:
        logger.error(f"Error fetching evergreen usage report: {e}")
        return jsonify({'error': str(e)}), 500


@calendar_bp.route('/calendar-ideas-for-week')
def api_calendar_ideas_for_week(week_number):
    """Get all calendar ideas for a specific week number"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, idea_title, idea_description, seasonal_context, 
                       content_type, priority, tags, is_recurring
                FROM calendar_ideas 
                WHERE week_number = %s
                ORDER BY 
                    CASE priority 
                        WHEN 'mandatory' THEN 1 
                        WHEN 'random' THEN 2 
                        ELSE 3 
                    END,
                    id
            """, (week_number,))
            
            ideas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'ideas': [dict(idea) for idea in ideas]
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar ideas for week {week_number}: {e}")
        return jsonify({'error': str(e)}), 500


