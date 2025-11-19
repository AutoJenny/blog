"""UI preferences API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register UI preferences API routes"""
    
    @bp.route('/api/ui/preferences/<key>', methods=['GET', 'POST'])
    def api_ui_preferences(key):
        """Handle UI preferences for header stage"""
        try:
            if request.method == 'GET':
                # Get preference value
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT preference_value FROM ui_user_preferences 
                        WHERE user_id = 0 AND preference_key = %s
                    """, (key,))
                    result = cursor.fetchone()
                    
                    if result:
                        return jsonify({
                            'success': True,
                            'value': result['preference_value']
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'value': None
                        })
            
            elif request.method == 'POST':
                # Save preference value
                data = request.get_json()
                value = data.get('value')
                
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, created_at, updated_at)
                        VALUES (0, %s, %s, 'string', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id, preference_key) 
                        DO UPDATE SET preference_value = %s, updated_at = CURRENT_TIMESTAMP
                    """, (key, value, value))
                
                return jsonify({
                    'success': True,
                    'message': 'Preference saved'
                })
                
        except Exception as e:
            logger.error(f"Error handling UI preference {key}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to handle preference: {str(e)}'
            }), 500

