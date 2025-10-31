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
            # Check if sources column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'sources'
            """)
            has_sources = cursor.fetchone() is not None
            sources_field = 'ci.sources' if has_sources else "'[]'::jsonb as sources"
            
            # Check if item_classification column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'item_classification'
            """)
            has_classification = cursor.fetchone() is not None
            classification_field = 'ci.item_classification' if has_classification else "'idea'::varchar as item_classification"
            
            cursor.execute(f"""
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, {sources_field}, {classification_field}, ci.created_at, ci.updated_at,
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
                         ci.evergreen_notes, ci.created_at, ci.updated_at""" + (", ci.item_classification" if has_classification else "")
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
            # Check if item_classification column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'item_classification'
            """)
            has_classification = cursor.fetchone() is not None
            classification_field = 'ci.item_classification' if has_classification else "'idea'::varchar as item_classification"
            
            cursor.execute(f"""
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, ci.sources, {classification_field}, ci.created_at, ci.updated_at,
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
                         ci.evergreen_notes, ci.created_at, ci.updated_at""" + (", ci.item_classification" if has_classification else "") + """
            """, (idea_id,))
            
            idea = cursor.fetchone()
            if not idea:
                return jsonify({'success': False, 'error': 'Idea not found'}), 404
            
            return jsonify({'success': True, 'idea': idea})
            
    except Exception as e:
        logger.error(f"Error fetching calendar idea: {e}")
        return jsonify({'error': str(e)}), 500

def _safe_parse_json_request():
    """Parse JSON body without triggering 'Body is disturbed or locked' errors.
    Uses Flask's get_json which handles stream caching internally - safest approach.
    """
    # Use get_json with silent=True (without force=True to avoid stream issues)
    # silent=True returns None on error instead of raising
    # Content-Type: application/json is set by the client, so force shouldn't be needed
    try:
        data = request.get_json(silent=True)
        if data is not None and isinstance(data, dict):
            return data
        # If we got something but it's not a dict, return empty dict
        return {}
    except RuntimeError as e:
        # "Body is disturbed or locked" is a RuntimeError from Flask
        # If this happens, log it and try to access cached data
        if 'disturbed' in str(e).lower() or 'locked' in str(e).lower():
            logger.warning(f"Request body already consumed, trying cached JSON: {e}")
            # Try to access Flask's internal cache
            if hasattr(request, '_cached_json') and request._cached_json:
                return request._cached_json if isinstance(request._cached_json, dict) else {}
        logger.error(f"Error parsing JSON request: {e}", exc_info=True)
        return {}
    except Exception as e:
        # Any other error
        logger.error(f"Error parsing JSON request: {e}", exc_info=True)
        return {}


def _current_iso_week():
    from datetime import datetime
    return datetime.utcnow().isocalendar().week


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


def api_add_calendar_idea():
    """Create a new week idea and persist it to calendar_ideas."""
    try:
        import json
        data = _safe_parse_json_request() or {}
        # Apply backend defaults so client doesn't have to supply everything
        if not data.get('idea_title'):
            return jsonify({'success': False, 'error': 'Missing field: idea_title'}), 400
        if not data.get('week_number'):
            data['week_number'] = _current_iso_week()

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check which columns exist
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_ideas'
                """)
                existing_columns = {row['column_name'] for row in cursor.fetchall()}
                
                # Prepare all fields
                fields = ['week_number', 'idea_title']
                values = [
                    int(data['week_number']),
                    data['idea_title'].strip()
                ]
                
                if data.get('idea_description') and 'idea_description' in existing_columns:
                    fields.append('idea_description')
                    values.append(data['idea_description'].strip())
                
                if data.get('seasonal_context') and 'seasonal_context' in existing_columns:
                    fields.append('seasonal_context')
                    values.append(data['seasonal_context'].strip())
                
                if data.get('content_type') and 'content_type' in existing_columns:
                    fields.append('content_type')
                    values.append(data['content_type'].strip())
                
                if 'priority' in existing_columns:
                    fields.append('priority')
                    values.append((data.get('priority') or 'random').strip())
                
                if 'is_recurring' in existing_columns:
                    fields.append('is_recurring')
                    values.append(data.get('is_recurring', True))
                
                if 'can_span_weeks' in existing_columns:
                    fields.append('can_span_weeks')
                    values.append(data.get('can_span_weeks', False))
                
                if 'max_weeks' in existing_columns:
                    fields.append('max_weeks')
                    values.append(int(data.get('max_weeks', 1)))
                
                if 'item_classification' in existing_columns:
                    fields.append('item_classification')
                    # Default to 'idea' unless explicitly set to 'theme'
                    values.append((data.get('item_classification') or 'idea').strip())
                
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
                
                if data.get('sources') and 'sources' in existing_columns:
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
        data = _safe_parse_json_request() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check which columns exist
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'calendar_ideas'
                """)
                existing_columns = {row['column_name'] for row in cursor.fetchall()}
                
                fields = []
                values = []
                
                # Update all possible fields (only if column exists)
                updatable_fields = [
                    'idea_title', 'idea_description', 'seasonal_context', 'content_type',
                    'priority', 'week_number', 'is_recurring', 'can_span_weeks', 'max_weeks',
                    'is_evergreen', 'evergreen_frequency', 'evergreen_notes', 'item_classification'
                ]
                
                for col in updatable_fields:
                    if col in data and col in existing_columns:
                        fields.append(col)
                        if col in ('is_recurring', 'can_span_weeks', 'is_evergreen'):
                            values.append(bool(data[col]))
                        elif col == 'max_weeks':
                            values.append(int(data[col]) if data[col] else 1)
                        elif col == 'week_number':
                            values.append(int(data[col]))
                        elif col == 'item_classification':
                            # Ensure it's either 'theme' or 'idea'
                            val = (data[col] or 'idea').strip().lower()
                            values.append('theme' if val == 'theme' else 'idea')
                        else:
                            values.append(data[col].strip() if data[col] else None)
                
                # Handle tags and sources as JSONB (only if columns exist)
                if 'tags' in data and 'tags' in existing_columns:
                    fields.append('tags')
                    values.append(json.dumps(data['tags']) if data['tags'] else json.dumps([]))
                
                if 'sources' in data and 'sources' in existing_columns:
                    fields.append('sources')
                    values.append(json.dumps(data['sources']) if data['sources'] else json.dumps([]))
                
                if not fields:
                    return jsonify({'success': False, 'error': 'No fields provided'}), 400

                set_clause = ", ".join(f"{c} = %s" for c in fields)
                values.append(idea_id)

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
