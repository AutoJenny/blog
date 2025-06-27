"""Format-related routes for workflow steps."""

from flask import jsonify, request
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
import json
from . import bp

@bp.route('/steps/<int:step_id>/formats', methods=['GET'])
def get_step_formats(step_id):
    """Get format configuration for a workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT wsf.*, 
                       input_fmt.name as input_format_name,
                       input_fmt.format_spec as input_format_spec,
                       output_fmt.name as output_format_name,
                       output_fmt.format_spec as output_format_spec
                FROM workflow_step_format wsf
                LEFT JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                WHERE wsf.step_id = %s
            """, (step_id,))
            formats = cur.fetchall()
            return jsonify([dict(f) for f in formats])

@bp.route('/steps/<int:step_id>/formats/<int:post_id>', methods=['GET'])
def get_step_post_format(step_id, post_id):
    """Get format configuration for a specific post's workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT wsf.*, 
                       input_fmt.name as input_format_name,
                       input_fmt.format_spec as input_format_spec,
                       output_fmt.name as output_format_name,
                       output_fmt.format_spec as output_format_spec
                FROM workflow_step_format wsf
                LEFT JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                WHERE wsf.step_id = %s AND wsf.post_id = %s
            """, (step_id, post_id))
            format = cur.fetchone()
            if not format:
                return jsonify({'error': 'Format configuration not found'}), 404
            return jsonify(dict(format))

@bp.route('/steps/<int:step_id>/formats/<int:post_id>', methods=['PUT'])
def set_step_post_format(step_id, post_id):
    """Set format configuration for a specific post's workflow step."""
    data = request.get_json()
    
    # Validate input
    if not all(k in data for k in ['input_format_id', 'output_format_id']):
        return jsonify({'error': 'Missing required fields'}), 400

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify formats exist
            cur.execute("""
                SELECT COUNT(*) as count FROM llm_format_template
                WHERE id IN (%s, %s)
            """, (data['input_format_id'], data['output_format_id']))
            result = cur.fetchone()
            if result['count'] != 2:
                return jsonify({'error': 'One or both format templates not found'}), 404

            # Verify step exists
            cur.execute("SELECT COUNT(*) as count FROM workflow_step_entity WHERE id = %s", (step_id,))
            result = cur.fetchone()
            if result['count'] == 0:
                return jsonify({'error': 'Workflow step not found'}), 404

            # Verify post exists
            cur.execute("SELECT COUNT(*) as count FROM post WHERE id = %s", (post_id,))
            result = cur.fetchone()
            if result['count'] == 0:
                return jsonify({'error': 'Post not found'}), 404

            # Upsert format configuration
            cur.execute("""
                INSERT INTO workflow_step_format 
                    (step_id, post_id, input_format_id, output_format_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (step_id, post_id) 
                DO UPDATE SET 
                    input_format_id = EXCLUDED.input_format_id,
                    output_format_id = EXCLUDED.output_format_id
                RETURNING *
            """, (step_id, post_id, data['input_format_id'], data['output_format_id']))
            conn.commit()
            
            # Fetch complete format info
            cur.execute("""
                SELECT wsf.*, 
                       input_fmt.name as input_format_name,
                       input_fmt.format_spec as input_format_spec,
                       output_fmt.name as output_format_name,
                       output_fmt.format_spec as output_format_spec
                FROM workflow_step_format wsf
                LEFT JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                WHERE wsf.step_id = %s AND wsf.post_id = %s
            """, (step_id, post_id))
            format = cur.fetchone()
            return jsonify(dict(format))

@bp.route('/steps/<int:step_id>/formats/<int:post_id>', methods=['DELETE'])
def delete_step_post_format(step_id, post_id):
    """Delete format configuration for a specific post's workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                DELETE FROM workflow_step_format
                WHERE step_id = %s AND post_id = %s
                RETURNING id
            """, (step_id, post_id))
            deleted = cur.fetchone()
            if not deleted:
                return jsonify({'error': 'Format configuration not found'}), 404
            
            conn.commit()
            return '', 204

@bp.route('/steps/<int:step_id>/formats', methods=['PUT'])
def set_step_default_format(step_id):
    """Set default format configuration for a workflow step."""
    data = request.get_json()
    
    # Validate input
    if not all(k in data for k in ['input_format_id', 'output_format_id']):
        return jsonify({'error': 'Missing required fields'}), 400

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify formats exist if provided
            if data['input_format_id'] or data['output_format_id']:
                format_ids = [f for f in [data['input_format_id'], data['output_format_id']] if f]
                placeholders = ', '.join(['%s'] * len(format_ids))
                cur.execute(f"""
                    SELECT COUNT(*) as count FROM llm_format_template
                    WHERE id IN ({placeholders})
                """, format_ids)
                result = cur.fetchone()
                if result['count'] != len(format_ids):
                    return jsonify({'error': 'One or more format templates not found'}), 404

            # Verify step exists
            cur.execute("SELECT COUNT(*) as count FROM workflow_step_entity WHERE id = %s", (step_id,))
            result = cur.fetchone()
            if result['count'] == 0:
                return jsonify({'error': 'Workflow step not found'}), 404

            # Update step configuration
            cur.execute("""
                UPDATE workflow_step_entity 
                SET default_input_format_id = %s,
                    default_output_format_id = %s
                WHERE id = %s
                RETURNING id
            """, (data['input_format_id'], data['output_format_id'], step_id))
            conn.commit()
            
            # Fetch complete format info
            cur.execute("""
                SELECT 
                    wse.id as step_id,
                    wse.default_input_format_id as input_format_id,
                    wse.default_output_format_id as output_format_id,
                    input_fmt.name as input_format_name,
                    input_fmt.format_spec as input_format_spec,
                    output_fmt.name as output_format_name,
                    output_fmt.format_spec as output_format_spec
                FROM workflow_step_entity wse
                LEFT JOIN llm_format_template input_fmt ON wse.default_input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wse.default_output_format_id = output_fmt.id
                WHERE wse.id = %s
            """, (step_id,))
            format = cur.fetchone()
            return jsonify(dict(format)) 