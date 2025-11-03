"""
Planning Calendar API - Social Focus

Weekly social focus endpoints
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging

logger = logging.getLogger(__name__)

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


