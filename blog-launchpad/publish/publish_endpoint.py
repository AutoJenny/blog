"""
Publish Endpoint
Flask route handler for publishing posts to clan.com
"""

from flask import Blueprint, jsonify, request
import logging
from config.database import db_manager
from .publish_orchestrator import publish_post_to_clan

logger = logging.getLogger(__name__)

bp = Blueprint('publish', __name__, url_prefix='/api/publish')


@bp.route('/recipe/<int:post_id>', methods=['POST'])
def publish_recipe_post(post_id):
    """
    Publish a recipe post to clan.com.
    Validates that the post is a recipe type before publishing.
    """
    try:
        # Validate post exists and is a recipe type
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, post_type 
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post_row = cursor.fetchone()
            
            if not post_row:
                return jsonify({
                    'success': False,
                    'error': f'Post {post_id} not found'
                }), 404
            
            post_type = post_row.get('post_type')
            if post_type != 'recipe':
                return jsonify({
                    'success': False,
                    'error': f'Post {post_id} is not a recipe post (type: {post_type})'
                }), 400
        
        # Publish the post
        result = publish_post_to_clan(post_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in publish_recipe_post endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500




