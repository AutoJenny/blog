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
                SELECT id, name, description, version, type, 
                       input_format, output_format, input_schema, 
                       output_schema, output_rules, examples, notes
                FROM llm_format_template
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
                SELECT id, name, description, version, type, 
                       input_format, output_format, input_schema, 
                       output_schema, output_rules, examples, notes
                FROM llm_format_template
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
    required_fields = ['name', 'version', 'type', 'output_format']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                INSERT INTO llm_format_template (
                    name, description, version, type, input_format,
                    input_schema, input_instructions, output_format,
                    output_schema, output_rules, examples, notes
                ) VALUES (
                    %(name)s, %(description)s, %(version)s, %(type)s,
                    %(input_format)s, %(input_schema)s, %(input_instructions)s,
                    %(output_format)s, %(output_schema)s, %(output_rules)s,
                    %(examples)s, %(notes)s
                ) RETURNING id
            """, data)
            format_id = cur.fetchone()['id']
            conn.commit()
            return jsonify({'id': format_id}), 201

@bp.route('/formats/<int:format_id>', methods=['PUT'])
def update_format_template(format_id):
    """Update a format template."""
    data = request.get_json()
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Check if template exists
            cur.execute("SELECT id FROM llm_format_template WHERE id = %s", (format_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Format template not found'}), 404
            
            # Update template
            cur.execute("""
                UPDATE llm_format_template SET
                    name = COALESCE(%(name)s, name),
                    description = COALESCE(%(description)s, description),
                    version = COALESCE(%(version)s, version),
                    type = COALESCE(%(type)s, type),
                    input_format = COALESCE(%(input_format)s, input_format),
                    input_schema = COALESCE(%(input_schema)s, input_schema),
                    input_instructions = COALESCE(%(input_instructions)s, input_instructions),
                    output_format = COALESCE(%(output_format)s, output_format),
                    output_schema = COALESCE(%(output_schema)s, output_schema),
                    output_rules = COALESCE(%(output_rules)s, output_rules),
                    examples = COALESCE(%(examples)s, examples),
                    notes = COALESCE(%(notes)s, notes)
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
                FROM llm_format_template f
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
                SELECT id FROM llm_format_template 
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
                SELECT input_schema, output_schema, input_format, output_format
                FROM llm_format_template
                WHERE id = %s
            """, (data['format_id'],))
            template = cur.fetchone()
            if not template:
                return jsonify({'error': 'Format template not found'}), 404
            
            # Basic format validation
            schema = template[f'{data["direction"]}_schema']
            format_type = template[f'{data["direction"]}_format']
            
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