"""Post format endpoints for workflow API."""

from flask import Blueprint, jsonify, request
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
import json

post_formats_bp = Blueprint('post_formats', __name__)

@post_formats_bp.route('/api/workflow/posts/<int:post_id>/format', methods=['GET'])
def get_post_format(post_id):
    """Get format data for a post"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            post = cur.fetchone()
            if not post:
                return jsonify({
                    'error': {
                        'code': 'POST_NOT_FOUND',
                        'message': 'Post not found',
                        'details': {'post_id': post_id}
                    }
                }), 404
            # Get post format
            cur.execute("""
                SELECT wpf.template_id, wpf.data, wft.name as template_name
                FROM workflow_post_format wpf
                JOIN workflow_format_template wft ON wpf.template_id = wft.id
                WHERE wpf.post_id = %s
            """, (post_id,))
            post_format = cur.fetchone()
            if not post_format:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'No format data found for post',
                        'details': {'post_id': post_id}
                    }
                }), 404
            return jsonify({
                'template_id': post_format['template_id'],
                'template_name': post_format['template_name'],
                'data': post_format['data']
            })

@post_formats_bp.route('/api/workflow/posts/<int:post_id>/format', methods=['POST'])
def update_post_format(post_id):
    """Update format data for a post"""
    data = request.get_json()
    if not data or 'template_id' not in data:
        return jsonify({
            'error': {
                'code': 'MISSING_TEMPLATE_ID',
                'message': 'template_id is required',
                'details': {}
            }
        }), 400
    template_id = data['template_id']
    format_data = data.get('data', {})
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if post exists
            cur.execute("SELECT id FROM post WHERE id = %s", (post_id,))
            post = cur.fetchone()
            if not post:
                return jsonify({
                    'error': {
                        'code': 'POST_NOT_FOUND',
                        'message': 'Post not found',
                        'details': {'post_id': post_id}
                    }
                }), 404
            # Check if template exists
            cur.execute("SELECT id FROM workflow_format_template WHERE id = %s", (template_id,))
            template = cur.fetchone()
            if not template:
                return jsonify({
                    'error': {
                        'code': 'TEMPLATE_NOT_FOUND',
                        'message': 'Format template not found',
                        'details': {'template_id': template_id}
                    }
                }), 404
            # Check if post format already exists
            cur.execute("SELECT id FROM workflow_post_format WHERE post_id = %s", (post_id,))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE workflow_post_format
                    SET template_id = %s, data = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s
                    RETURNING id
                """, (template_id, json.dumps(format_data), post_id))
            else:
                cur.execute("""
                    INSERT INTO workflow_post_format (post_id, template_id, data)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (post_id, template_id, json.dumps(format_data)))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Post format updated successfully'})

@post_formats_bp.route('/api/workflow/posts/<int:post_id>/format/validate', methods=['POST'])
def validate_post_format(post_id):
    """Validate data against post format configuration"""
    data = request.get_json()
    if not data or 'test_data' not in data:
        return jsonify({
            'error': {
                'code': 'MISSING_TEST_DATA',
                'message': 'test_data is required',
                'details': {}
            }
        }), 400
    test_data = data['test_data']
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT wpf.template_id, wpf.data, wft.fields
                FROM workflow_post_format wpf
                JOIN workflow_format_template wft ON wpf.template_id = wft.id
                WHERE wpf.post_id = %s
            """, (post_id,))
            post_format = cur.fetchone()
            if not post_format:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'No format data found for post',
                        'details': {'post_id': post_id}
                    }
                }), 404
            fields_data = post_format['fields']
            if isinstance(fields_data, str):
                fields_data = json.loads(fields_data)
            if isinstance(fields_data, dict) and 'schema' in fields_data:
                schema = fields_data['schema']
                if isinstance(schema, dict) and 'properties' in schema:
                    errors = []
                    properties = schema['properties']
                    required = schema.get('required', [])
                    for field_name in required:
                        if field_name not in test_data:
                            errors.append(f"Missing required field: {field_name}")
                    for field_name, field_value in test_data.items():
                        if field_name in properties:
                            field_spec = properties[field_name]
                            if isinstance(field_spec, dict):
                                expected_type = field_spec.get('type', 'string')
                                if expected_type == 'string' and not isinstance(field_value, str):
                                    errors.append(f"Field '{field_name}' must be a string")
                                elif expected_type == 'number' and not isinstance(field_value, (int, float)):
                                    errors.append(f"Field '{field_name}' must be a number")
                                elif expected_type == 'array' and not isinstance(field_value, list):
                                    errors.append(f"Field '{field_name}' must be an array")
                                elif expected_type == 'object' and not isinstance(field_value, dict):
                                    errors.append(f"Field '{field_name}' must be an object")
                    return jsonify({'valid': len(errors) == 0, 'errors': errors})
            return jsonify({'valid': True, 'errors': []}) 