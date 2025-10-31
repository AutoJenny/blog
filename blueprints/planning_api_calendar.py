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
                       ci.evergreen_notes, ci.sources, ci.created_at, ci.updated_at,
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
                         ci.evergreen_notes, ci.sources, ci.created_at, ci.updated_at
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

def api_get_calendar_idea(idea_id):
    """Get a single calendar idea by ID with full details."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, ci.sources, ci.created_at, ci.updated_at,
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
                WHERE ci.id = %s
                GROUP BY ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                         ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                         ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                         ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                         ci.evergreen_notes, ci.created_at, ci.updated_at
            """, (idea_id,))
            
            idea = cursor.fetchone()
            if not idea:
                return jsonify({'success': False, 'error': 'Idea not found'}), 404
            
            return jsonify({'success': True, 'idea': idea})
            
    except Exception as e:
        logger.error(f"Error fetching calendar idea: {e}")
        return jsonify({'error': str(e)}), 500

def api_add_calendar_idea():
    """Create a new week idea and persist it to calendar_ideas."""
    try:
        import json
        data = request.get_json(force=True) or {}
        required = ['idea_title', 'week_number']
        for f in required:
            if not data.get(f):
                return jsonify({'success': False, 'error': f'Missing field: {f}'}), 400

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare all fields
                fields = ['week_number', 'idea_title']
                values = [
                    int(data['week_number']),
                    data['idea_title'].strip()
                ]
                
                if data.get('idea_description'):
                    fields.append('idea_description')
                    values.append(data['idea_description'].strip())
                
                if data.get('seasonal_context'):
                    fields.append('seasonal_context')
                    values.append(data['seasonal_context'].strip())
                
                if data.get('content_type'):
                    fields.append('content_type')
                    values.append(data['content_type'].strip())
                
                fields.append('priority')
                values.append((data.get('priority') or 'random').strip())
                
                fields.append('is_recurring')
                values.append(data.get('is_recurring', True))
                
                fields.append('can_span_weeks')
                values.append(data.get('can_span_weeks', False))
                
                fields.append('max_weeks')
                values.append(int(data.get('max_weeks', 1)))
                
                fields.append('is_evergreen')
                values.append(data.get('is_evergreen', False))
                
                if data.get('evergreen_frequency'):
                    fields.append('evergreen_frequency')
                    values.append(data['evergreen_frequency'].strip())
                
                if data.get('evergreen_notes'):
                    fields.append('evergreen_notes')
                    values.append(data['evergreen_notes'].strip())
                
                if data.get('tags'):
                    fields.append('tags')
                    values.append(json.dumps(data['tags']))
                
                if data.get('sources'):
                    fields.append('sources')
                    values.append(json.dumps(data['sources']))

                placeholders = ', '.join(['%s'] * len(values))
                field_names = ', '.join(fields)
                return_fields = 'id, week_number, idea_title'
                
                cursor.execute(
                    f"INSERT INTO calendar_ideas ({field_names}) VALUES ({placeholders}) RETURNING {return_fields}",
                    values
                )
                row = cursor.fetchone()
                idea_id = row['id']
                
                # Handle categories
                if data.get('categories'):
                    for cat_id in data['categories']:
                        cursor.execute(
                            "INSERT INTO calendar_idea_categories (idea_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (idea_id, int(cat_id))
                        )
                
                conn.commit()

        return jsonify({'success': True, 'idea': row})
    except Exception as e:
        logger.error(f"Error adding calendar idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_update_calendar_idea(idea_id: int):
    """Update an existing week idea."""
    try:
        import json
        data = request.get_json(force=True) or {}
        fields = []
        values = []
        
        # Update all possible fields
        updatable_fields = [
            'idea_title', 'idea_description', 'seasonal_context', 'content_type',
            'priority', 'week_number', 'is_recurring', 'can_span_weeks', 'max_weeks',
            'is_evergreen', 'evergreen_frequency', 'evergreen_notes'
        ]
        
        for col in updatable_fields:
            if col in data:
                fields.append(col)
                if col in ('is_recurring', 'can_span_weeks', 'is_evergreen'):
                    values.append(bool(data[col]))
                elif col == 'max_weeks':
                    values.append(int(data[col]) if data[col] else 1)
                elif col == 'week_number':
                    values.append(int(data[col]))
                else:
                    values.append(data[col].strip() if data[col] else None)
        
        # Handle tags and sources as JSONB
        if 'tags' in data:
            fields.append('tags')
            values.append(json.dumps(data['tags']) if data['tags'] else json.dumps([]))
        
        if 'sources' in data:
            fields.append('sources')
            values.append(json.dumps(data['sources']) if data['sources'] else json.dumps([]))
        
        if not fields:
            return jsonify({'success': False, 'error': 'No fields provided'}), 400

        set_clause = ", ".join(f"{c} = %s" for c in fields)
        values.append(idea_id)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE calendar_ideas SET {set_clause} WHERE id = %s RETURNING id", values)
                row = cursor.fetchone()
                
                if not row:
                    return jsonify({'success': False, 'error': 'Idea not found'}), 404
                
                # Update categories
                if 'categories' in data:
                    # Remove all existing category links
                    cursor.execute("DELETE FROM calendar_idea_categories WHERE idea_id = %s", (idea_id,))
                    # Add new category links
                    for cat_id in data['categories']:
                        cursor.execute(
                            "INSERT INTO calendar_idea_categories (idea_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (idea_id, int(cat_id))
                        )
                
                conn.commit()
        
        return jsonify({'success': True, 'idea': {'id': idea_id}})
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
