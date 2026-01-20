"""
Planning Calendar API - Ideas

Calendar ideas CRUD endpoints
"""

from flask import jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging

logger = logging.getLogger(__name__)

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
            
            # Check if important_notes column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'calendar_ideas' AND column_name = 'important_notes'
            """)
            has_important_notes = cursor.fetchone() is not None
            important_notes_field = 'ci.important_notes' if has_important_notes else "'[]'::jsonb as important_notes"
            
            # Build GROUP BY clause with optional item_classification, important_notes, and sources
            group_by_fields = """ci.id, ci.week_number, ci.idea_title, ci.idea_description, 
                         ci.seasonal_context, ci.content_type, ci.priority, ci.tags,
                         ci.is_recurring, ci.can_span_weeks, ci.max_weeks, ci.is_evergreen,
                         ci.evergreen_frequency, ci.last_used_date, ci.usage_count,
                         ci.evergreen_notes, ci.created_at, ci.updated_at"""
            if has_sources:
                group_by_fields += ", ci.sources"
            if has_classification:
                group_by_fields += ", ci.item_classification"
            if has_important_notes:
                group_by_fields += ", ci.important_notes"
            
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
def api_calendar_ideas_for_week(week_number):
    """Get ideas for a specific week (alias for api_calendar_ideas)"""
    return api_calendar_ideas(week_number)
