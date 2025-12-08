"""
Calendar Themes API

DEPRECATED: The old week_number-based theme system is deprecated.
NEW SYSTEM: Themes now use cyclic position-based logic.

This API has been updated to use the new cyclic system for consistency
with the scheduling calendar. The week_number parameter is now used
to calculate which theme appears via cyclic logic, not direct lookup.
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from utils.calendar_resolver import resolve_item_for_week
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('planning_api_themes', __name__)

@bp.route('/api/calendar/themes/week/<int:week_number>')
def api_calendar_themes(week_number):
    """
    Get theme for a specific week number using NEW cyclic system.
    
    DEPRECATED: Old system queried calendar_themes WHERE week_number = X
    NEW SYSTEM: Uses cyclic position logic to determine which theme appears
    
    Returns the theme that appears in this week based on cyclic calculation,
    matching what the scheduling calendar shows.
    """
    try:
        # Get current year (or use request parameter if provided)
        year = request.args.get('year', type=int)
        if not year:
            year = datetime.utcnow().isocalendar()[0]
        
        # Use new cyclic system to get theme for this week
        theme = resolve_item_for_week("theme", year, week_number)
        
        if theme:
            # Format response to match old API structure for backward compatibility
            theme_data = {
                'id': theme.get('id'),
                'week_number': week_number,  # Keep for backward compatibility
                'theme_title': theme.get('theme_title'),
                'theme_description': theme.get('theme_description'),
                'position': theme.get('position'),
                '_from_cyclic_system': True,
                '_override': theme.get('_override', False)
            }
            
            return jsonify({
                'success': True,
                'week_number': week_number,
                'themes': [theme_data],  # Return as array for backward compatibility
                '_deprecated_note': 'This endpoint now uses cyclic system. week_number parameter is used for cyclic calculation, not direct lookup.'
            })
        else:
            # No theme found via cyclic system
            return jsonify({
                'success': True,
                'week_number': week_number,
                'themes': [],
                '_deprecated_note': 'This endpoint now uses cyclic system. week_number parameter is used for cyclic calculation, not direct lookup.'
            })
            
    except Exception as e:
        logger.error(f"Error fetching calendar themes: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/themes/<int:theme_id>')
def api_get_calendar_theme(theme_id):
    """Get a single calendar theme by ID"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ct.id, ct.week_number, ct.theme_title, ct.theme_description,
                       ct.seasonal_context, ct.priority, ct.tags,
                       ct.is_recurring, ct.can_span_weeks, ct.max_weeks,
                       ct.is_evergreen, ct.evergreen_frequency, ct.last_used_date,
                       ct.usage_count, ct.evergreen_notes, ct.sources, ct.important_notes,
                       ct.created_at, ct.updated_at,
                       '[]'::json as categories
                FROM calendar_themes ct
                WHERE ct.id = %s
            """, (theme_id,))
            
            theme = cursor.fetchone()
            if not theme:
                return jsonify({'success': False, 'error': 'Theme not found'}), 404
            
            return jsonify({'success': True, 'theme': theme})
            
    except Exception as e:
        logger.error(f"Error fetching calendar theme: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calendar/themes', methods=['POST'])
def api_add_calendar_theme():
    """Create a new calendar theme"""
    try:
        import json
        data = request.get_json() or {}
        
        if not data.get('theme_title'):
            return jsonify({'success': False, 'error': 'Missing field: theme_title'}), 400
        if not data.get('week_number'):
            from datetime import datetime
            data['week_number'] = datetime.utcnow().isocalendar()[1]
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                fields = ['week_number', 'theme_title']
                values = [
                    int(data['week_number']),
                    data['theme_title'].strip()
                ]
                
                if data.get('theme_description'):
                    fields.append('theme_description')
                    values.append(data['theme_description'].strip())
                
                if data.get('seasonal_context'):
                    fields.append('seasonal_context')
                    values.append(data['seasonal_context'].strip())
                
                if data.get('priority'):
                    fields.append('priority')
                    values.append(data['priority'].strip())
                else:
                    fields.append('priority')
                    values.append('random')
                
                if 'tags' in data:
                    fields.append('tags')
                    values.append(json.dumps(data['tags']) if data['tags'] else json.dumps([]))
                
                if 'is_recurring' in data:
                    fields.append('is_recurring')
                    values.append(bool(data['is_recurring']))
                
                if 'can_span_weeks' in data:
                    fields.append('can_span_weeks')
                    values.append(bool(data['can_span_weeks']))
                
                if 'max_weeks' in data:
                    fields.append('max_weeks')
                    values.append(int(data['max_weeks']) if data['max_weeks'] else 1)
                
                if 'is_evergreen' in data:
                    fields.append('is_evergreen')
                    values.append(bool(data['is_evergreen']))
                
                if 'evergreen_frequency' in data and data.get('is_evergreen'):
                    fields.append('evergreen_frequency')
                    values.append(data['evergreen_frequency'].strip() if data['evergreen_frequency'] else 'low-frequency')
                
                if 'evergreen_notes' in data and data.get('is_evergreen'):
                    fields.append('evergreen_notes')
                    values.append(data['evergreen_notes'].strip())
                
                if 'sources' in data:
                    fields.append('sources')
                    values.append(json.dumps(data['sources']) if data['sources'] else json.dumps([]))
                
                if 'important_notes' in data:
                    fields.append('important_notes')
                    values.append(json.dumps(data['important_notes']) if data['important_notes'] else json.dumps([]))
                
                placeholders = ', '.join(['%s'] * len(values))
                field_names = ', '.join(fields)
                
                cursor.execute(
                    f"INSERT INTO calendar_themes ({field_names}) VALUES ({placeholders}) RETURNING id, week_number, theme_title",
                    values
                )
                row = cursor.fetchone()
                theme_id = row['id']
                
                conn.commit()
                
        return jsonify({'success': True, 'theme': row})
    except Exception as e:
        logger.error(f"Error adding calendar theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/calendar/themes/<int:theme_id>', methods=['PUT'])
def api_update_calendar_theme(theme_id):
    """Update an existing calendar theme"""
    try:
        import json
        data = request.get_json() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                fields = []
                values = []
                
                if 'theme_title' in data:
                    fields.append('theme_title')
                    values.append(data['theme_title'].strip())
                
                if 'theme_description' in data:
                    fields.append('theme_description')
                    values.append(data['theme_description'].strip() if data['theme_description'] else None)
                
                if 'week_number' in data:
                    fields.append('week_number')
                    values.append(int(data['week_number']))
                
                if 'seasonal_context' in data:
                    fields.append('seasonal_context')
                    values.append(data['seasonal_context'].strip() if data['seasonal_context'] else None)
                
                if 'priority' in data:
                    fields.append('priority')
                    values.append(data['priority'].strip())
                
                if 'tags' in data:
                    fields.append('tags')
                    values.append(json.dumps(data['tags']) if data['tags'] else json.dumps([]))
                
                if 'is_recurring' in data:
                    fields.append('is_recurring')
                    values.append(bool(data['is_recurring']))
                
                if 'can_span_weeks' in data:
                    fields.append('can_span_weeks')
                    values.append(bool(data['can_span_weeks']))
                
                if 'max_weeks' in data:
                    fields.append('max_weeks')
                    values.append(int(data['max_weeks']) if data['max_weeks'] else 1)
                
                if 'is_evergreen' in data:
                    fields.append('is_evergreen')
                    values.append(bool(data['is_evergreen']))
                
                if 'evergreen_frequency' in data:
                    fields.append('evergreen_frequency')
                    values.append(data['evergreen_frequency'].strip() if data['evergreen_frequency'] else 'low-frequency')
                
                if 'evergreen_notes' in data:
                    fields.append('evergreen_notes')
                    values.append(data['evergreen_notes'].strip() if data['evergreen_notes'] else None)
                
                if 'sources' in data:
                    fields.append('sources')
                    values.append(json.dumps(data['sources']) if data['sources'] else json.dumps([]))
                
                if 'important_notes' in data:
                    fields.append('important_notes')
                    values.append(json.dumps(data['important_notes']) if data['important_notes'] else json.dumps([]))
                
                if not fields:
                    return jsonify({'success': False, 'error': 'No fields provided'}), 400
                
                fields.append('updated_at')
                values.append('NOW()')
                
                set_clause = ", ".join(f"{f} = %s" if f != 'updated_at' else f"{f} = NOW()" for f in fields)
                values_without_updated = [v for i, v in enumerate(values) if fields[i] != 'updated_at']
                values_without_updated.append(theme_id)
                
                cursor.execute(f"UPDATE calendar_themes SET {set_clause} WHERE id = %s RETURNING id", values_without_updated)
                row = cursor.fetchone()
                
                if not row:
                    return jsonify({'success': False, 'error': 'Theme not found'}), 404
                
                conn.commit()
                
        return jsonify({'success': True, 'theme': {'id': theme_id}})
    except Exception as e:
        logger.error(f"Error updating calendar theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/calendar/themes/<int:theme_id>', methods=['DELETE'])
def api_delete_calendar_theme(theme_id):
    """Delete a calendar theme"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if theme exists
                cursor.execute("SELECT id FROM calendar_themes WHERE id = %s", (theme_id,))
                if not cursor.fetchone():
                    return jsonify({'success': False, 'error': 'Theme not found'}), 404
                
                # Delete theme (cascade will handle schedule entries if foreign key is set up)
                cursor.execute("DELETE FROM calendar_themes WHERE id = %s", (theme_id,))
                conn.commit()
                
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting calendar theme: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

