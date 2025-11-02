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
            
            # Build GROUP BY clause with optional item_classification
            group_by_fields = """ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                         ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                         ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                         ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                         ci.evergreen_notes, ci.created_at, ci.updated_at"""
            if has_classification:
                group_by_fields += ", ci.item_classification"
            
            # Check if important_notes column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'important_notes'
            """)
            has_important_notes = cursor.fetchone() is not None
            important_notes_field = 'ci.important_notes' if has_important_notes else "'[]'::jsonb as important_notes"
            
            cursor.execute(f"""
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, {sources_field}, {classification_field}, {important_notes_field}, ci.created_at, ci.updated_at,
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
                  AND NOT EXISTS (
                      SELECT 1 FROM calendar_themes ct WHERE ct.id = ci.id
                  )
                GROUP BY {group_by_fields}
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

def api_calendar_schedule(year, week_number):
    """Get schedule for a specific year and week"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if calendar_themes table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_themes'
                )
            """)
            has_themes_table = cursor.fetchone()['exists']
            
            # Include theme_id and theme data if themes table exists
            if has_themes_table:
                cursor.execute("""
                    SELECT cs.id, cs.post_id, cs.idea_id, cs.theme_id, cs.year, cs.week_number, cs.scheduled_date,
                           cs.created_at, cs.updated_at,
                           p.title as post_title, p.status as post_status,
                           pd.idea_seed as post_idea_seed,
                           ct.theme_title, ct.id as calendar_theme_id
                    FROM calendar_schedule cs
                    LEFT JOIN post p ON cs.post_id = p.id
                    LEFT JOIN post_development pd ON p.id = pd.post_id
                    LEFT JOIN calendar_themes ct ON cs.theme_id = ct.id
                    WHERE cs.year = %s AND cs.week_number = %s
                    ORDER BY cs.scheduled_date
                """, (year, week_number))
            else:
                # Fallback if themes table doesn't exist yet
                cursor.execute("""
                    SELECT cs.id, cs.post_id, cs.idea_id, cs.year, cs.week_number, cs.scheduled_date,
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
            
            # Check if important_notes column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'important_notes'
            """)
            has_important_notes = cursor.fetchone() is not None
            important_notes_field = 'ci.important_notes' if has_important_notes else "'[]'::jsonb as important_notes"
            
            # Check if sources column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'sources'
            """)
            has_sources = cursor.fetchone() is not None
            sources_field = 'ci.sources' if has_sources else "'[]'::jsonb as sources"
            
            cursor.execute(f"""
                SELECT ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                       ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                       ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                       ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                       ci.evergreen_notes, {sources_field}, {classification_field}, {important_notes_field}, ci.created_at, ci.updated_at,
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
                         ci.evergreen_notes, ci.created_at, ci.updated_at""" + (", ci.sources" if has_sources else "") + (", ci.item_classification" if has_classification else "") + (", ci.important_notes" if has_important_notes else "") + """
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


def api_weekly_social_focus():
    """Get all weekly social focus entries"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, day_of_week, social_focus, format, purpose, example, is_active,
                       created_at, updated_at
                FROM weekly_social_focus
                WHERE is_active = TRUE
                ORDER BY day_of_week
            """)
            
            focuses = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'focuses': focuses
            })
            
    except Exception as e:
        logger.error(f"Error fetching weekly social focus: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_weekly_social_focus_day(day_of_week):
    """Get social focus for a specific day (1-7)"""
    try:
        if day_of_week < 1 or day_of_week > 7:
            return jsonify({'success': False, 'error': 'day_of_week must be between 1 and 7'}), 400
            
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, day_of_week, social_focus, format, purpose, example, is_active,
                       created_at, updated_at
                FROM weekly_social_focus
                WHERE day_of_week = %s AND is_active = TRUE
            """, (day_of_week,))
            
            focus = cursor.fetchone()
            
            if not focus:
                return jsonify({'success': False, 'error': 'Social focus not found for this day'}), 404
                
            return jsonify({
                'success': True,
                'focus': focus
            })
            
    except Exception as e:
        logger.error(f"Error fetching social focus for day {day_of_week}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_add_weekly_social_focus():
    """Create a new weekly social focus"""
    try:
        data = _safe_parse_json_request() or {}
        day_of_week = data.get('day_of_week')
        social_focus = data.get('social_focus')
        format_val = data.get('format')
        purpose = data.get('purpose')
        example = data.get('example')
        
        if not day_of_week or not social_focus:
            return jsonify({'success': False, 'error': 'day_of_week and social_focus are required'}), 400
            
        if day_of_week < 1 or day_of_week > 7:
            return jsonify({'success': False, 'error': 'day_of_week must be between 1 and 7'}), 400
            
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if entry already exists for this day
                cursor.execute("""
                    SELECT id FROM weekly_social_focus WHERE day_of_week = %s
                """, (day_of_week,))
                
                if cursor.fetchone():
                    return jsonify({'success': False, 'error': 'Social focus already exists for this day'}), 400
                
                cursor.execute("""
                    INSERT INTO weekly_social_focus (day_of_week, social_focus, format, purpose, example)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, day_of_week, social_focus, format, purpose, example, is_active,
                              created_at, updated_at
                """, (day_of_week, social_focus, format_val, purpose, example))
                
                result = cursor.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'focus': result
                })
                
    except Exception as e:
        logger.error(f"Error creating weekly social focus: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_update_weekly_social_focus(focus_id):
    """Update an existing weekly social focus"""
    try:
        data = _safe_parse_json_request() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if focus exists
                cursor.execute("SELECT id FROM weekly_social_focus WHERE id = %s", (focus_id,))
                if not cursor.fetchone():
                    return jsonify({'success': False, 'error': 'Social focus not found'}), 404
                
                # Build update query dynamically based on provided fields
                updates = []
                values = []
                
                if 'social_focus' in data:
                    updates.append('social_focus = %s')
                    values.append(data['social_focus'])
                if 'format' in data:
                    updates.append('format = %s')
                    values.append(data['format'])
                if 'purpose' in data:
                    updates.append('purpose = %s')
                    values.append(data['purpose'])
                if 'example' in data:
                    updates.append('example = %s')
                    values.append(data['example'])
                if 'is_active' in data:
                    updates.append('is_active = %s')
                    values.append(data['is_active'])
                    
                if not updates:
                    return jsonify({'success': False, 'error': 'No fields to update'}), 400
                    
                updates.append('updated_at = NOW()')
                values.append(focus_id)
                
                cursor.execute(f"""
                    UPDATE weekly_social_focus
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING id, day_of_week, social_focus, format, purpose, example, is_active,
                              created_at, updated_at
                """, values)
                
                result = cursor.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'focus': result
                })
                
    except Exception as e:
        logger.error(f"Error updating weekly social focus: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def api_delete_weekly_social_focus(focus_id):
    """Delete (deactivate) a weekly social focus"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE weekly_social_focus
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                """, (focus_id,))
                
                result = cursor.fetchone()
                conn.commit()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Social focus not found'}), 404
                    
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error deleting weekly social focus: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
                
                if 'important_notes' in existing_columns and data.get('important_notes') is not None:
                    fields.append('important_notes')
                    values.append(json.dumps(data['important_notes']))

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
                    'is_evergreen', 'evergreen_frequency', 'evergreen_notes', 'item_classification', 'important_notes'
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
                        elif col == 'important_notes':
                            values.append(json.dumps(data[col]) if data[col] else json.dumps([]))
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

def api_select_theme_idea():
    """Select a theme/idea for a specific week/year by saving to calendar_schedule.
    This allows themes to persist their selection before a post is created.
    """
    try:
        from flask import request
        data = _safe_parse_json_request() or {}
        idea_id = data.get('idea_id')
        year = data.get('year')
        week_number = data.get('week_number')
        
        if not idea_id:
            return jsonify({'success': False, 'error': 'idea_id is required'}), 400
        if not year or not week_number:
            return jsonify({'success': False, 'error': 'year and week_number are required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Verify idea exists
                cursor.execute("SELECT id, item_classification FROM calendar_ideas WHERE id = %s", (idea_id,))
                idea = cursor.fetchone()
                if not idea:
                    return jsonify({'success': False, 'error': 'Idea not found'}), 404
                
                # Check if there's already a schedule entry for this week/year
                cursor.execute("""
                    SELECT id, idea_id, post_id 
                    FROM calendar_schedule 
                    WHERE year = %s AND week_number = %s
                    LIMIT 1
                """, (year, week_number))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing schedule entry to use this idea_id
                    # Don't overwrite post_id if it exists (preserve existing post association)
                    cursor.execute("""
                        UPDATE calendar_schedule 
                        SET idea_id = %s, updated_at = NOW()
                        WHERE id = %s
                        RETURNING id, idea_id, post_id
                    """, (idea_id, existing['id']))
                else:
                    # Create new schedule entry with idea_id but no post_id yet
                    cursor.execute("""
                        INSERT INTO calendar_schedule (year, week_number, idea_id, status, created_at, updated_at)
                        VALUES (%s, %s, %s, 'planned', NOW(), NOW())
                        RETURNING id, idea_id, post_id
                    """, (year, week_number, idea_id))
                
                result = cursor.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'schedule_id': result['id'],
                    'idea_id': result['idea_id'],
                    'post_id': result['post_id']
                })
    except Exception as e:
        logger.error(f"Error selecting theme/idea: {e}")
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

def api_calendar_ideas_for_week(week_number):
    """Get ideas for a specific week (alias for api_calendar_ideas)"""
    return api_calendar_ideas(week_number)

def api_schedule_update_theme_to_idea():
    """Update schedule entries to convert theme_id to idea_id"""
    try:
        data = request.get_json() or {}
        theme_id = data.get('theme_id')
        idea_id = data.get('idea_id')
        
        if not theme_id or not idea_id:
            return jsonify({'success': False, 'error': 'Missing theme_id or idea_id'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update schedule entries: set idea_id and clear theme_id
                cursor.execute("""
                    UPDATE calendar_schedule
                    SET idea_id = %s, theme_id = NULL, updated_at = NOW()
                    WHERE theme_id = %s
                """, (idea_id, theme_id))
                
                updated_count = cursor.rowcount
                conn.commit()
                
        return jsonify({'success': True, 'updated_count': updated_count})
    except Exception as e:
        logger.error(f"Error updating schedule theme to idea: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
