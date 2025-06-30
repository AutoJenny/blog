from flask import jsonify, request
from app.db import get_db_conn
from psycopg2.extras import DictCursor
from app.api.workflow.decorators import validate_post_id, validate_step_id
from . import bp

# Format template endpoints
@bp.route('/formats', methods=['GET'])
def get_format_templates():
    """Get all format templates."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT id, name, description, fields, llm_instructions, created_at, updated_at
                FROM workflow_format_template
                ORDER BY name
            """)
            templates = [dict(row) for row in cur.fetchall()]
            return jsonify(templates)

@bp.route('/formats/<int:format_id>', methods=['GET'])
def get_format_template(format_id):
    """Get a specific format template."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT id, name, description, fields, llm_instructions, created_at, updated_at
                FROM workflow_format_template
                WHERE id = %s
            """, (format_id,))
            template = cur.fetchone()
            if not template:
                return jsonify({'error': 'Format template not found'}), 404
            return jsonify(dict(template))

@bp.route('/formats', methods=['POST'])
def create_format_template():
    """Create a new format template."""
    data = request.get_json()
    required_fields = ['name', 'fields']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    # Ensure llm_instructions is present
    if 'llm_instructions' not in data:
        data['llm_instructions'] = ''
    
    # Debug: Print the data dictionary
    print(f"DEBUG: Creating format template with data: {data}")
    print(f"DEBUG: llm_instructions value: '{data.get('llm_instructions', 'NOT_FOUND')}'")
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                INSERT INTO workflow_format_template (
                    name, description, fields, llm_instructions
                ) VALUES (
                    %(name)s, %(description)s, %(fields)s, %(llm_instructions)s
                ) RETURNING id
            """, data)
            format_id = cur.fetchone()['id']
            conn.commit()
            return jsonify({'id': format_id}), 201

@bp.route('/formats/<int:format_id>', methods=['PUT'])
def update_format_template(format_id):
    """Update a format template."""
    data = request.get_json()
    # Ensure llm_instructions is present
    if 'llm_instructions' not in data:
        data['llm_instructions'] = ''
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT id FROM workflow_format_template WHERE id = %s", (format_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Format template not found'}), 404
            cur.execute("""
                UPDATE workflow_format_template SET
                    name = COALESCE(%(name)s, name),
                    description = COALESCE(%(description)s, description),
                    fields = COALESCE(%(fields)s, fields),
                    llm_instructions = COALESCE(%(llm_instructions)s, llm_instructions)
                WHERE id = %(id)s
            """, {**data, 'id': format_id})
            conn.commit()
            return jsonify({'message': 'Format template updated'})

# Step format mapping endpoints
@bp.route('/steps/<int:step_id>/format', methods=['GET'])
@validate_step_id
def get_step_format(step_id):
    """Get the format template for a workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT f.* 
                FROM workflow_format_template f
                JOIN workflow_step_format wsf ON f.id = wsf.format_template_id
                WHERE wsf.step_id = %s
            """, (step_id,))
            format = cur.fetchone()
            if not format:
                return jsonify({'error': 'No format template found for step'}), 404
            return jsonify(dict(format))

@bp.route('/steps/<int:step_id>/format', methods=['PUT'])
@validate_step_id
def set_step_format(step_id):
    """Set or update the format template for a workflow step."""
    data = request.get_json()
    if 'format_template_id' not in data:
        return jsonify({'error': 'Missing format_template_id'}), 400
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Check if format template exists
            cur.execute("""
                SELECT id FROM workflow_format_template 
                WHERE id = %s
            """, (data['format_template_id'],))
            if not cur.fetchone():
                return jsonify({'error': 'Format template not found'}), 404
            
            # Upsert format mapping
            cur.execute("""
                INSERT INTO workflow_step_format (step_id, format_template_id)
                VALUES (%s, %s)
                ON CONFLICT (step_id) 
                DO UPDATE SET format_template_id = EXCLUDED.format_template_id
            """, (step_id, data['format_template_id']))
            conn.commit()
            return jsonify({'message': 'Step format updated'})

@bp.route('/steps/<int:step_id>/format', methods=['DELETE'])
@validate_step_id
def remove_step_format(step_id):
    """Remove the format template from a workflow step."""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                DELETE FROM workflow_step_format
                WHERE step_id = %s
            """, (step_id,))
            conn.commit()
            return jsonify({'message': 'Step format removed'})

# Format validation endpoints
@bp.route('/formats/validate', methods=['POST'])
def validate_format():
    """Validate content against a format template."""
    data = request.get_json()
    required_fields = ['format_id', 'content', 'direction']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    if data['direction'] not in ['input', 'output']:
        return jsonify({'error': 'Direction must be either "input" or "output"'}), 400
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Get format template
            cur.execute("""
                SELECT fields, llm_instructions
                FROM workflow_format_template
                WHERE id = %s
            """, (data['format_id'],))
            template = cur.fetchone()
            if not template:
                return jsonify({'error': 'Format template not found'}), 404
            
            # Basic format validation
            schema = template['fields']
            format_type = template['llm_instructions']
            
            # For now, just check if JSON content matches format type
            if format_type == 'json':
                try:
                    import json
                    content = data['content'] if isinstance(data['content'], dict) else json.loads(data['content'])
                    # TODO: Add proper JSON schema validation
                    return jsonify({
                        'valid': True,
                        'format': format_type,
                        'schema': schema
                    })
                except json.JSONDecodeError:
                    return jsonify({
                        'valid': False,
                        'error': 'Invalid JSON content'
                    }), 400
            else:
                # For text format, just ensure it's a string
                return jsonify({
                    'valid': isinstance(data['content'], str),
                    'format': format_type,
                    'schema': schema
                }) 