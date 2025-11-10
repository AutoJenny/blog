"""
Authoring API - Styles Management

Handles post-wide image styles for the authoring stage.
Keeps file size under 300 lines as per user requirements.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('authoring_styles', __name__, url_prefix='/authoring')


def _get_post_extra_settings(cursor, post_id):
    """Get post extra_settings with fallback to empty dict"""
    cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
    row = cursor.fetchone()
    return row['extra_settings'] if row and row['extra_settings'] else {}


@bp.route('/api/posts/<int:post_id>/styles', methods=['GET'])
def api_list_post_styles(post_id):
    """List all styles for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            active_index = imaging.get('activeIndex', 0)
            
            # If no styles found for the post, return a permanent system default (do NOT persist per-post)
            if not styles:
                # Try to get default style from taxonomy first
                from utils.taxonomy_helpers import get_default_image_style
                taxonomy_style = get_default_image_style(post_id)
                
                if taxonomy_style:
                    styles = [taxonomy_style]
                    logger.info(f"Using taxonomy default image style: {taxonomy_style.get('name', 'Unknown')}")
                else:
                    # Fallback to permanent system default (Watercolour and Pen & Ink)
                    styles = [{
                        'name': 'Watercolour and Pen & Ink',
                        'style_json': {
                            'medium': 'watercolour and pen and ink',
                            'technique': 'brushstrokes fading out by ending towards the edges of the image',
                            'palette': ['ochres', 'siennas', 'umbers', 'celestial blues', 'golds'],
                            'composition': 'rule-of-thirds with negative space',
                            'lighting': 'soft, ethereal, golden hour',
                            'constraints': ['no text', 'no watermark in frame', 'edges fade to white'],
                            'negatives': ['hyperrealism', 'sharp edges', 'solid borders']
                        }
                    }]
                    logger.info("Using system default image style (no taxonomy default found)")
                active_index = 0
            
            return jsonify({
                'success': True,
                'styles': styles,
                'activeIndex': active_index,
                'count': len(styles)
            })
    except Exception as e:
        logger.error(f"Error listing post styles: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/styles/active', methods=['GET'])
def api_get_active_style(post_id):
    """Get the currently active style for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            active_index = imaging.get('activeIndex', 0)
            
            active_style = None
            if styles and 0 <= active_index < len(styles):
                active_style = styles[active_index]
            
            # If no saved styles, check taxonomy default
            if not active_style:
                from utils.taxonomy_helpers import get_default_image_style
                taxonomy_style = get_default_image_style(post_id)
                if taxonomy_style:
                    active_style = taxonomy_style
                    logger.info(f"Using taxonomy default image style for active: {taxonomy_style.get('name', 'Unknown')}")
            
            return jsonify({
                'success': True,
                'active_style': active_style,
                'active_index': active_index if active_style else -1
            })
    except Exception as e:
        logger.error(f"Error getting active style: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/styles', methods=['POST'])
def api_create_style(post_id):
    """Create a new style for a post"""
    try:
        data = request.get_json()
        style_name = data.get('name')
        style_json = data.get('style_json', {})
        activate = data.get('activate', True)
        
        if not style_name:
            return jsonify({'error': 'Style name is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            
            # Initialize imaging settings if not present
            if 'imaging' not in extra_settings:
                extra_settings['imaging'] = {}
            if 'styles' not in extra_settings['imaging']:
                extra_settings['imaging']['styles'] = []
            
            # Create new style
            new_style = {
                'name': style_name,
                'style_json': style_json
            }
            
            # Add to styles array
            extra_settings['imaging']['styles'].append(new_style)
            
            # Set as active if requested
            if activate:
                extra_settings['imaging']['activeIndex'] = len(extra_settings['imaging']['styles']) - 1
            
            # Save to database
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s 
                WHERE id = %s
            """, (json.dumps(extra_settings), post_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Style created successfully',
                'style': new_style,
                'active_index': extra_settings['imaging']['activeIndex']
            })
            
    except Exception as e:
        logger.error(f"Error creating style: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/styles/<int:style_index>/activate', methods=['POST'])
def api_activate_style(post_id, style_index):
    """Activate a specific style by index"""
    try:
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            
            if not styles or style_index < 0 or style_index >= len(styles):
                return jsonify({'error': 'Invalid style index'}), 400
            
            # Update active index
            extra_settings['imaging']['activeIndex'] = style_index
            
            # Save to database
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s 
                WHERE id = %s
            """, (json.dumps(extra_settings), post_id))
            
            cursor.connection.commit()
            
            active_style = styles[style_index]
            return jsonify({
                'success': True,
                'message': 'Style activated successfully',
                'active_style': active_style,
                'active_index': style_index
            })
            
    except Exception as e:
        logger.error(f"Error activating style: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ui/preferences', methods=['GET', 'POST'])
def api_ui_preferences():
    """Get or save UI preferences for accordion states"""
    try:
        if request.method == 'GET':
            # Get preferences from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT preference_key, preference_value FROM ui_user_preferences 
                    WHERE user_id = 1 AND category = 'image_prompts'
                """)
                rows = cursor.fetchall()
                
                preferences = {}
                for row in rows:
                    try:
                        preferences[row['preference_key']] = json.loads(row['preference_value'])
                    except (json.JSONDecodeError, TypeError):
                        preferences[row['preference_key']] = row['preference_value']
                
                return jsonify({
                    'success': True,
                    'preferences': preferences
                })
        
        elif request.method == 'POST':
            data = request.get_json()
            preferences = data.get('preferences', {})
            
            # Save preferences to database
            with db_manager.get_cursor() as cursor:
                for key, value in preferences.items():
                    cursor.execute("""
                        INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category)
                        VALUES (1, %s, %s, 'json', 'image_prompts')
                        ON CONFLICT (user_id, preference_key) 
                        DO UPDATE SET preference_value = %s, updated_at = CURRENT_TIMESTAMP
                    """, (key, json.dumps(value), json.dumps(value)))
                
                return jsonify({
                    'success': True,
                    'message': 'Preferences saved successfully'
                })
                
    except Exception as e:
        logger.error(f"Error handling UI preferences: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/ui/preferences/<preference_key>', methods=['GET', 'POST'])
def api_ui_preference(preference_key):
    """Get or save individual UI preference"""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE user_id = 1 AND preference_key = %s
                """, (preference_key,))
                row = cursor.fetchone()
                
                if row:
                    try:
                        value = json.loads(row['preference_value'])
                    except (json.JSONDecodeError, TypeError):
                        value = row['preference_value']
                    return jsonify({'success': True, 'value': value})
                else:
                    return jsonify({'success': True, 'value': None})
        
        elif request.method == 'POST':
            data = request.get_json()
            value = data.get('value')
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category)
                    VALUES (1, %s, %s, 'json', 'image_prompts')
                    ON CONFLICT (user_id, preference_key) 
                    DO UPDATE SET preference_value = %s, updated_at = CURRENT_TIMESTAMP
                """, (preference_key, json.dumps(value), json.dumps(value)))
                
                return jsonify({'success': True, 'message': 'Preference saved'})
                
    except Exception as e:
        logger.error(f"Error handling UI preference: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
