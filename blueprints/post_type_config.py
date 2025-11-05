"""
Post Type Configuration API
Manages publication scheduling configuration for different post types.
"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('post_type_config', __name__, url_prefix='/api/post-type-config')

def get_publication_day_for_post_type(post_type: str, cursor=None):
    """
    Get default publication day for a post type.
    Returns day of week (1=Monday, 7=Sunday) or None if not found.
    """
    if cursor is None:
        with db_manager.get_cursor() as cursor:
            return get_publication_day_for_post_type(post_type, cursor)
    
    cursor.execute("""
        SELECT default_publication_day, default_publication_time, timezone
        FROM post_type_config
        WHERE post_type = %s AND is_active = TRUE
    """, (post_type,))
    
    result = cursor.fetchone()
    if result:
        if isinstance(result, dict):
            return {
                'day': result['default_publication_day'],
                'time': str(result['default_publication_time']),
                'timezone': result['timezone']
            }
        else:
            return {
                'day': result[0],
                'time': str(result[1]),
                'timezone': result[2]
            }
    return None

@bp.route('/<post_type>', methods=['GET'])
def get_post_type_config(post_type):
    """Get configuration for a specific post type."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT post_type, default_publication_day, default_publication_time,
                       timezone, is_active, description
                FROM post_type_config
                WHERE post_type = %s
            """, (post_type,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({
                    'success': False,
                    'error': f'Post type "{post_type}" not found'
                }), 404
            
            if isinstance(result, dict):
                config = {
                    'post_type': result['post_type'],
                    'default_publication_day': result['default_publication_day'],
                    'default_publication_time': str(result['default_publication_time']),
                    'timezone': result['timezone'],
                    'is_active': result['is_active'],
                    'description': result['description']
                }
            else:
                config = {
                    'post_type': result[0],
                    'default_publication_day': result[1],
                    'default_publication_time': str(result[2]),
                    'timezone': result[3],
                    'is_active': result[4],
                    'description': result[5]
                }
            
            return jsonify({
                'success': True,
                'config': config
            })
            
    except Exception as e:
        logger.error(f"Error fetching post type config: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('', methods=['GET'])
def get_all_post_type_configs():
    """Get all post type configurations."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT post_type, default_publication_day, default_publication_time,
                       timezone, is_active, description
                FROM post_type_config
                ORDER BY post_type
            """)
            
            results = cursor.fetchall()
            configs = []
            
            for result in results:
                if isinstance(result, dict):
                    configs.append({
                        'post_type': result['post_type'],
                        'default_publication_day': result['default_publication_day'],
                        'default_publication_time': str(result['default_publication_time']),
                        'timezone': result['timezone'],
                        'is_active': result['is_active'],
                        'description': result['description']
                    })
                else:
                    configs.append({
                        'post_type': result[0],
                        'default_publication_day': result[1],
                        'default_publication_time': str(result[2]),
                        'timezone': result[3],
                        'is_active': result[4],
                        'description': result[5]
                    })
            
            return jsonify({
                'success': True,
                'configs': configs
            })
            
    except Exception as e:
        logger.error(f"Error fetching post type configs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<post_type>', methods=['PUT'])
def update_post_type_config(post_type):
    """Update configuration for a specific post type."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE post_type_config
                    SET default_publication_day = %s,
                        default_publication_time = %s,
                        timezone = %s,
                        is_active = %s,
                        description = %s,
                        updated_at = NOW()
                    WHERE post_type = %s
                    RETURNING post_type
                """, (
                    data.get('default_publication_day'),
                    data.get('default_publication_time'),
                    data.get('timezone'),
                    data.get('is_active', True),
                    data.get('description'),
                    post_type
                ))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({
                        'success': False,
                        'error': f'Post type "{post_type}" not found'
                    }), 404
                
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f'Updated configuration for post type "{post_type}"'
                })
                
    except Exception as e:
        logger.error(f"Error updating post type config: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Export the helper function for use in other modules
__all__ = ['get_publication_day_for_post_type']

