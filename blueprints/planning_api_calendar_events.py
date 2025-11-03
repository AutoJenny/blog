"""
Planning Calendar API - Events

Calendar events CRUD endpoints
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging

logger = logging.getLogger(__name__)

def api_calendar_events(year, week_number):
    """Get events for a specific year and week, including events whose advance notice overlaps this week"""
    try:
        from datetime import date, timedelta
        
        with db_manager.get_cursor() as cursor:
            # Check if advance_notice column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_events' AND column_name = 'advance_notice'
            """)
            has_advance_notice = cursor.fetchone() is not None
            advance_notice_field = 'ce.advance_notice' if has_advance_notice else 'NULL::integer as advance_notice'
            
            # Check if important_notes column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_events' AND column_name = 'important_notes'
            """)
            has_event_important_notes = cursor.fetchone() is not None
            event_important_notes_field = 'ce.important_notes' if has_event_important_notes else "'[]'::jsonb as important_notes"
            
            # Calculate the week start and end dates for the requested week
            # Use date.fromisocalendar for ISO week calculation
            week_start_date = date.fromisocalendar(year, week_number, 1)  # Monday
            week_end_date = date.fromisocalendar(year, week_number, 7)     # Sunday
            
            # Build WHERE clause: events that occur in this week OR have advance notice overlapping this week
            params = [year, week_number]
            
            if has_advance_notice:
                # Include events in this week OR events whose advance notice overlaps
                where_clause = """(
                    (ce.year = %s AND ce.week_number = %s)
                    OR (
                        ce.advance_notice IS NOT NULL 
                        AND ce.advance_notice > 0
                        AND ce.start_date IS NOT NULL
                        AND (ce.start_date::date - INTERVAL '1 week' * ce.advance_notice) <= %s
                        AND (ce.start_date::date - INTERVAL '1 day') >= %s
                    )
                )"""
                params.extend([week_end_date, week_start_date])
            else:
                # Only events in this week
                where_clause = "(ce.year = %s AND ce.week_number = %s)"
            
            # Check if newsletter_source_item table exists and has event_recurrence_type column
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'newsletter_source_item' AND column_name = 'event_recurrence_type'
            """)
            has_recurrence_type = cursor.fetchone() is not None
            
            # Join with newsletter_source_item to get recurrence_type
            recurrence_join = ""
            recurrence_field = "NULL::varchar as event_recurrence_type"
            if has_recurrence_type:
                recurrence_join = "LEFT JOIN newsletter_source_item nsi ON ce.id = nsi.calendar_event_id"
                recurrence_field = "nsi.event_recurrence_type"
            
            cursor.execute(f"""
                SELECT ce.id, ce.event_title, ce.event_description, ce.start_date, ce.end_date,
                       ce.is_recurring, ce.priority, ce.tags, ce.content_type, ce.year,
                       {advance_notice_field}, {event_important_notes_field}, ce.created_at, ce.updated_at,
                       EXTRACT(ISODOW FROM ce.start_date)::integer as weekday,
                       {recurrence_field},
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
                {recurrence_join}
                WHERE {where_clause}
                GROUP BY ce.id, ce.event_title, ce.event_description, ce.start_date, ce.end_date,
                         ce.is_recurring, ce.priority, ce.tags, ce.content_type, ce.year,
                         ce.created_at, ce.updated_at, EXTRACT(ISODOW FROM ce.start_date)""" + (", ce.advance_notice" if has_advance_notice else "") + (", ce.important_notes" if has_event_important_notes else "") + (", " + recurrence_field if has_recurrence_type else "") + """
                ORDER BY ce.start_date, ce.priority
            """, tuple(params))
            
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

def api_add_calendar_event():
    """Create a new calendar event."""
    try:
        import json
        from datetime import datetime
        data = _safe_parse_json_request() or {}
        
        if not data.get('event_title'):
            return jsonify({'success': False, 'error': 'Missing field: event_title'}), 400
        if not data.get('start_date'):
            return jsonify({'success': False, 'error': 'Missing field: start_date'}), 400
        if not data.get('end_date'):
            return jsonify({'success': False, 'error': 'Missing field: end_date'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check which columns exist
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_events'
                """)
                existing_columns = {row['column_name'] for row in cursor.fetchall()}
                
                # Calculate week_number from start_date
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                week_number = start_date.isocalendar()[1]
                
                fields = ['event_title', 'start_date', 'end_date', 'year', 'week_number']
                values = [
                    data['event_title'].strip(),
                    data['start_date'],
                    data['end_date'],
                    int(data.get('year', start_date.year)),
                    week_number
                ]
                
                if data.get('event_description') and 'event_description' in existing_columns:
                    fields.append('event_description')
                    values.append(data['event_description'].strip())
                
                if 'is_recurring' in existing_columns:
                    fields.append('is_recurring')
                    values.append(data.get('is_recurring', False))
                
                if data.get('content_type') and 'content_type' in existing_columns:
                    fields.append('content_type')
                    values.append(data['content_type'].strip())
                
                if 'priority' in existing_columns:
                    fields.append('priority')
                    values.append((data.get('priority') or 'random').strip())
                
                if data.get('tags') and 'tags' in existing_columns:
                    fields.append('tags')
                    values.append(json.dumps(data['tags']))
                
                if 'advance_notice' in existing_columns and data.get('advance_notice') is not None:
                    fields.append('advance_notice')
                    values.append(int(data['advance_notice']))
                
                if 'important_notes' in existing_columns and data.get('important_notes') is not None:
                    fields.append('important_notes')
                    values.append(json.dumps(data['important_notes']))
                
                placeholders = ', '.join(['%s'] * len(values))
                field_names = ', '.join(fields)
                
                cursor.execute(
                    f"INSERT INTO calendar_events ({field_names}) VALUES ({placeholders}) RETURNING id, event_title, start_date, end_date, year",
                    values
                )
                row = cursor.fetchone()
                event_id = row['id']
                
                # Handle categories
                if data.get('categories'):
                    for cat_id in data['categories']:
                        cursor.execute(
                            "INSERT INTO calendar_event_categories (event_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (event_id, int(cat_id))
                        )
                
                conn.commit()
        
        return jsonify({'success': True, 'event': row})
    except Exception as e:
        logger.error(f"Error adding calendar event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_update_calendar_event(event_id: int):
    """Update an existing calendar event."""
    try:
        import json
        from datetime import datetime
        data = _safe_parse_json_request() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check which columns exist
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_events'
                """)
                existing_columns = {row['column_name'] for row in cursor.fetchall()}
                
                fields = []
                values = []
                
                updatable_fields = [
                    'event_title', 'event_description', 'start_date', 'end_date', 'year',
                    'content_type', 'priority', 'is_recurring', 'advance_notice', 'important_notes'
                ]
                
                for col in updatable_fields:
                    if col in data and col in existing_columns:
                        fields.append(col)
                        if col in ('is_recurring',):
                            values.append(bool(data[col]))
                        elif col == 'year':
                            values.append(int(data[col]))
                        elif col == 'advance_notice':
                            values.append(int(data[col]) if data[col] else None)
                        elif col == 'important_notes':
                            values.append(json.dumps(data[col]) if data[col] else json.dumps([]))
                        elif col in ('start_date', 'end_date'):
                            values.append(data[col])
                        else:
                            values.append(data[col].strip() if data[col] else None)
                
                # Handle tags as JSONB
                if 'tags' in data and 'tags' in existing_columns:
                    fields.append('tags')
                    values.append(json.dumps(data['tags']) if data['tags'] else json.dumps([]))
                
                # Update week_number if start_date changed
                if 'start_date' in data and 'start_date' in [f for f in fields]:
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                    week_number = start_date.isocalendar()[1]
                    if 'week_number' in existing_columns:
                        fields.append('week_number')
                        values.append(week_number)
                
                if not fields:
                    return jsonify({'success': False, 'error': 'No fields provided'}), 400
                
                set_clause = ", ".join(f"{c} = %s" for c in fields)
                values.append(event_id)
                
                cursor.execute(f"UPDATE calendar_events SET {set_clause} WHERE id = %s RETURNING id", values)
                row = cursor.fetchone()
                
                if not row:
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                # Update categories
                if 'categories' in data:
                    cursor.execute("DELETE FROM calendar_event_categories WHERE event_id = %s", (event_id,))
                    for cat_id in data['categories']:
                        cursor.execute(
                            "INSERT INTO calendar_event_categories (event_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (event_id, int(cat_id))
                        )
                
                conn.commit()
        
        return jsonify({'success': True, 'event': {'id': event_id}})
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_delete_calendar_event(event_id: int):
    """Delete a calendar event."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM calendar_events WHERE id = %s RETURNING id", (event_id,))
                row = cursor.fetchone()
                conn.commit()
        if not row:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_convert_event_to_idea(event_id: int):
    """Convert an event to an idea atomically: create idea, copy categories, update schedule, delete event."""
    try:
        import json
        data = _safe_parse_json_request() or {}
        
        if not data.get('idea_title'):
            return jsonify({'success': False, 'error': 'Missing field: idea_title'}), 400
        if not data.get('week_number'):
            data['week_number'] = _current_iso_week()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Get event data and categories first
                cursor.execute("""
                    SELECT ce.*, 
                           COALESCE(json_agg(cc.id), '[]'::json) as category_ids
                    FROM calendar_events ce
                    LEFT JOIN calendar_event_categories cec ON ce.id = cec.event_id
                    LEFT JOIN calendar_categories cc ON cec.category_id = cc.id
                    WHERE ce.id = %s
                    GROUP BY ce.id
                """, (event_id,))
                event_row = cursor.fetchone()
                
                if not event_row:
                    return jsonify({'success': False, 'error': 'Event not found'}), 404
                
                # Parse category IDs from the JSON aggregate
                category_ids = []
                try:
                    cat_json = event_row['category_ids']
                    if isinstance(cat_json, list):
                        category_ids = [c for c in cat_json if c]
                    elif cat_json:
                        category_ids = json.loads(cat_json) if isinstance(cat_json, str) else cat_json
                except Exception:
                    pass
                
                # 2. Check which columns exist for calendar_ideas
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_ideas'
                """)
                existing_columns = {row['column_name'] for row in cursor.fetchall()}
                
                # 3. Create the idea using form data (prefer form data over event data)
                fields = ['week_number', 'idea_title']
                values = [
                    int(data.get('week_number', event_row.get('week_number', _current_iso_week()))),
                    data['idea_title'].strip()
                ]
                
                # Map form fields to idea fields
                if data.get('idea_description') and 'idea_description' in existing_columns:
                    fields.append('idea_description')
                    values.append(data['idea_description'].strip())
                elif event_row.get('event_description') and 'idea_description' in existing_columns:
                    fields.append('idea_description')
                    values.append(event_row['event_description'].strip() if event_row['event_description'] else None)
                
                if data.get('seasonal_context') and 'seasonal_context' in existing_columns:
                    fields.append('seasonal_context')
                    values.append(data['seasonal_context'].strip())
                
                if data.get('content_type') and 'content_type' in existing_columns:
                    fields.append('content_type')
                    values.append(data['content_type'].strip())
                elif event_row.get('content_type') and 'content_type' in existing_columns:
                    fields.append('content_type')
                    values.append(event_row['content_type'].strip() if event_row['content_type'] else None)
                
                if 'priority' in existing_columns:
                    fields.append('priority')
                    values.append((data.get('priority') or event_row.get('priority') or 'random').strip())
                
                if 'is_recurring' in existing_columns:
                    fields.append('is_recurring')
                    values.append(data.get('is_recurring', True))  # Ideas default to recurring
                
                if 'can_span_weeks' in existing_columns:
                    fields.append('can_span_weeks')
                    values.append(data.get('can_span_weeks', event_row.get('can_span_weeks', False)))
                
                if 'max_weeks' in existing_columns:
                    fields.append('max_weeks')
                    values.append(int(data.get('max_weeks', event_row.get('max_weeks', 1))))
                
                if 'item_classification' in existing_columns:
                    fields.append('item_classification')
                    # When converting event to idea, always set as 'idea' (not 'theme')
                    values.append('idea')
                
                if 'is_evergreen' in existing_columns:
                    fields.append('is_evergreen')
                    values.append(data.get('is_evergreen', False))
                
                if data.get('evergreen_frequency') and 'evergreen_frequency' in existing_columns:
                    fields.append('evergreen_frequency')
                    values.append(data['evergreen_frequency'].strip())
                
                if data.get('evergreen_notes') and 'evergreen_notes' in existing_columns:
                    fields.append('evergreen_notes')
                    values.append(data['evergreen_notes'].strip())
                
                if data.get('tags') and 'tags' in existing_columns:
                    fields.append('tags')
                    values.append(json.dumps(data['tags']))
                elif event_row.get('tags') and 'tags' in existing_columns:
                    fields.append('tags')
                    values.append(json.dumps(event_row['tags']) if isinstance(event_row['tags'], (dict, list)) else event_row['tags'])
                
                if data.get('sources') and 'sources' in existing_columns:
                    fields.append('sources')
                    values.append(json.dumps(data['sources']))
                
                placeholders = ', '.join(['%s'] * len(values))
                field_names = ', '.join(fields)
                
                # 4. Insert the new idea
                cursor.execute(
                    f"INSERT INTO calendar_ideas ({field_names}) VALUES ({placeholders}) RETURNING id, week_number, idea_title",
                    values
                )
                idea_row = cursor.fetchone()
                new_idea_id = idea_row['id']
                
                # 5. Copy categories from event to idea (use form categories if provided, else event categories)
                categories_to_use = data.get('categories', category_ids)
                if categories_to_use:
                    for cat_id in categories_to_use:
                        cursor.execute(
                            "INSERT INTO calendar_idea_categories (idea_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (new_idea_id, int(cat_id))
                        )
                
                # 6. Update calendar_schedule entries to reference the new idea instead of the event
                #    Only if calendar_schedule has an event_id column in this deployment
                cursor.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'calendar_schedule' AND column_name = 'event_id'
                """)
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE calendar_schedule 
                        SET idea_id = %s, event_id = NULL, updated_at = NOW()
                        WHERE event_id = %s
                    """, (new_idea_id, event_id))
                
                # 7. Delete the event (cascades will clean up calendar_event_categories)
                cursor.execute("DELETE FROM calendar_events WHERE id = %s", (event_id,))
                
                conn.commit()
        
        return jsonify({'success': True, 'idea': idea_row})
    except Exception as e:
        logger.error(f"Error converting event to idea: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


