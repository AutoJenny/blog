"""
Planning Calendar API Module

Micro-file for calendar-specific API endpoints
"""

from flask import request, jsonify
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

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

def api_calendar_ideas(week_number):
    """Get perpetual ideas for a specific week number"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, ci.created_at, ci.updated_at,
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
                GROUP BY ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                         ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                         ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                         ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                         ci.evergreen_notes, ci.created_at, ci.updated_at
                ORDER BY 
                    CASE ci.priority 
                        WHEN 'mandatory' THEN 1 
                        WHEN 'random' THEN 2 
                        ELSE 3 
                    END,
                    ci.id
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

def api_calendar_events(year, week_number):
    """Get events for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ce.id, ce.event_title, ce.event_description, ce.start_date, ce.end_date,
                       ce.is_recurring, ce.priority, ce.tags, ce.content_type,
                       ce.created_at, ce.updated_at,
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
                GROUP BY ce.id, ce.event_title, ce.event_description, ce.start_date, ce.end_date,
                         ce.is_recurring, ce.priority, ce.tags, ce.content_type,
                         ce.created_at, ce.updated_at
                ORDER BY ce.start_date, ce.priority
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

def api_calendar_schedule(year, week_number):
    """Get schedule for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cs.id, cs.post_id, cs.year, cs.week_number, cs.scheduled_date,
                       cs.created_at, cs.updated_at,
                       p.title as post_title, p.status as post_status,
                       pd.idea_seed as post_idea_seed
                FROM calendar_schedule cs
                LEFT JOIN post p ON cs.post_id = p.id
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE cs.year = %s AND cs.week_number = %s
                ORDER BY cs.scheduled_date
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

def api_add_calendar_idea():
    """Create a new week idea and persist it to calendar_ideas."""
    try:
        data = request.get_json(force=True) or {}
        required = ['idea_title', 'week_number']
        for f in required:
            if not data.get(f):
                return jsonify({'success': False, 'error': f'Missing field: {f}'}), 400

        idea_title = data['idea_title'].strip()
        idea_description = (data.get('idea_description') or '').strip()
        priority = (data.get('priority') or 'random').strip()
        content_type = (data.get('content_type') or 'guide').strip()
        week_number = int(data['week_number'])

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO calendar_ideas (week_number, idea_title, idea_description, content_type, priority, is_recurring)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, week_number, idea_title, idea_description, content_type, priority, is_recurring
                    """,
                    (week_number, idea_title, idea_description, content_type, priority, False)
                )
                row = cursor.fetchone()
                conn.commit()

        return jsonify({'success': True, 'idea': row})
    except Exception as e:
        logger.error(f"Error adding calendar idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_update_calendar_idea(idea_id: int):
    """Update an existing week idea."""
    try:
        data = request.get_json(force=True) or {}
        fields = []
        values = []
        for col in ('idea_title', 'idea_description', 'priority', 'content_type', 'week_number'):
            if col in data and data[col] is not None:
                fields.append(col)
                values.append(data[col])
        if not fields:
            return jsonify({'success': False, 'error': 'No fields provided'}), 400

        set_clause = ", ".join(f"{c} = %s" for c in fields)
        values.append(idea_id)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE calendar_ideas SET {set_clause} WHERE id = %s RETURNING id, week_number, idea_title, idea_description, content_type, priority, is_recurring", values)
                row = cursor.fetchone()
                conn.commit()
        if not row:
            return jsonify({'success': False, 'error': 'Idea not found'}), 404
        return jsonify({'success': True, 'idea': row})
    except Exception as e:
        logger.error(f"Error updating calendar idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_delete_calendar_idea(idea_id: int):
    """Delete a week idea."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM calendar_ideas WHERE id = %s RETURNING id", (idea_id,))
                row = cursor.fetchone()
                conn.commit()
        if not row:
            return jsonify({'success': False, 'error': 'Idea not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting calendar idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_calendar_idea_status(idea_id: int):
    """Resolve the post creation status for the selected idea by matching scheduled posts in the same week/year.
    Heuristic: find most recent post scheduled in that (year, week) whose title ilike the idea title; otherwise latest scheduled for the week.
    """
    try:
        year = request.args.get('year', type=int)
        week_number = request.args.get('week_number', type=int)
        if not year or not week_number:
            return jsonify({'success': False, 'error': 'year and week_number are required'}), 400

        with db_manager.get_cursor() as cursor:
            # Fetch idea title
            cursor.execute("SELECT idea_title FROM calendar_ideas WHERE id = %s", (idea_id,))
            idea_row = cursor.fetchone()
            if not idea_row:
                return jsonify({'success': False, 'error': 'Idea not found'}), 404
            idea_title = idea_row['idea_title']

            # Try title match first
            cursor.execute(
                """
                SELECT p.id, p.title, p.status, cs.scheduled_date
                FROM calendar_schedule cs
                LEFT JOIN post p ON cs.post_id = p.id
                WHERE cs.year = %s AND cs.week_number = %s AND p.title ILIKE %s
                ORDER BY cs.scheduled_date DESC NULLS LAST, p.updated_at DESC NULLS LAST
                LIMIT 1
                """,
                (year, week_number, f"%{idea_title}%")
            )
            post = cursor.fetchone()
            if not post:
                # Fallback: any scheduled post for that week
                cursor.execute(
                    """
                    SELECT p.id, p.title, p.status, cs.scheduled_date
                    FROM calendar_schedule cs
                    LEFT JOIN post p ON cs.post_id = p.id
                    WHERE cs.year = %s AND cs.week_number = %s
                    ORDER BY cs.scheduled_date DESC NULLS LAST, p.updated_at DESC NULLS LAST
                    LIMIT 1
                    """,
                    (year, week_number)
                )
                post = cursor.fetchone()

        status = None
        post_id = None
        title = None
        scheduled_date = None
        if post:
            post_id = post['id']
            title = post['title']
            status = post['status']
            scheduled_date = post['scheduled_date'].isoformat() if post['scheduled_date'] else None

        return jsonify({'success': True, 'post': {'id': post_id, 'title': title, 'status': status, 'scheduled_date': scheduled_date}})
    except Exception as e:
        logger.error(f"Error getting idea status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_calendar_ideas_for_week(week_number):
    """Get ideas for a specific week (alias for api_calendar_ideas)"""
    return api_calendar_ideas(week_number)
