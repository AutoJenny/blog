"""
Planning Post Metadata API
Endpoints for managing post metadata (subtitle, required ideas, etc.)
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('planning_api_post_metadata', __name__, url_prefix='/planning/api/posts')

@bp.route('/<int:post_id>/subtitle', methods=['GET', 'POST'])
def api_post_subtitle(post_id):
    """Get or update post subtitle"""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT subtitle
                    FROM post
                    WHERE id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Post not found'}), 404
                
                return jsonify({
                    'success': True,
                    'subtitle': result.get('subtitle') or ''
                })
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            subtitle = data.get('subtitle', '').strip()
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE post
                    SET subtitle = %s, updated_at = NOW()
                    WHERE id = %s
                """, (subtitle[:200] if subtitle else None, post_id))
                
                if cursor.rowcount == 0:
                    return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'subtitle': subtitle
            })
            
    except Exception as e:
        logger.error(f"Error handling subtitle for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:post_id>/required-ideas', methods=['GET', 'POST'])
def api_post_required_ideas(post_id):
    """Get or update required ideas to include (stored in embedding_overrides)"""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT embedding_overrides
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({
                        'success': True,
                        'required_ideas': []
                    })
                
                overrides = result.get('embedding_overrides') or {}
                if isinstance(overrides, str):
                    try:
                        overrides = json.loads(overrides)
                    except:
                        overrides = {}
                
                required_ideas = overrides.get('required_ideas', [])
                if not isinstance(required_ideas, list):
                    required_ideas = []
                
                return jsonify({
                    'success': True,
                    'required_ideas': required_ideas
                })
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            required_ideas = data.get('required_ideas', [])
            
            if not isinstance(required_ideas, list):
                return jsonify({'success': False, 'error': 'required_ideas must be an array'}), 400
            
            with db_manager.get_cursor() as cursor:
                # Get existing embedding_overrides
                cursor.execute("""
                    SELECT embedding_overrides
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                # Parse existing overrides
                overrides = {}
                if result and result.get('embedding_overrides'):
                    existing = result.get('embedding_overrides')
                    if isinstance(existing, str):
                        try:
                            overrides = json.loads(existing)
                        except:
                            overrides = {}
                    elif isinstance(existing, dict):
                        overrides = existing
                
                # Update required_ideas
                overrides['required_ideas'] = required_ideas
                
                # Ensure post_development record exists
                cursor.execute("""
                    SELECT id FROM post_development WHERE post_id = %s
                """, (post_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO post_development (post_id, embedding_overrides, updated_at)
                        VALUES (%s, %s, NOW())
                    """, (post_id, json.dumps(overrides)))
                else:
                    cursor.execute("""
                        UPDATE post_development
                        SET embedding_overrides = %s, updated_at = NOW()
                        WHERE post_id = %s
                    """, (json.dumps(overrides), post_id))
            
            return jsonify({
                'success': True,
                'required_ideas': required_ideas
            })
            
    except Exception as e:
        logger.error(f"Error handling required ideas for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
