"""Post development API."""

from flask import Blueprint, jsonify, request, current_app
from app.database import get_db_conn

bp = Blueprint('post', __name__)

@bp.route('/post/<int:post_id>/development', methods=['GET'])
def get_post_development(post_id):
    """Get post development fields."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM post_development WHERE post_id = %s
                """, (post_id,))
                fields = dict(cur.fetchone() or {})
                return jsonify(fields)
    except Exception as e:
        current_app.logger.error(f"Error getting post development fields for post {post_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/post/<int:post_id>/development', methods=['PATCH'])
def update_post_development(post_id):
    """Update post development fields."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Build update query
        fields = []
        values = []
        for field, value in data.items():
            fields.append(f"{field} = %s")
            values.append(value)
        values.append(post_id)
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE post_development 
                    SET {', '.join(fields)}
                    WHERE post_id = %s
                """, tuple(values))
                conn.commit()
                return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error updating post development fields for post {post_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500 