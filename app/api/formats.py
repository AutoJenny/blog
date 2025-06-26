from flask import Blueprint, jsonify, request
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
from datetime import datetime
import jsonschema
import json

formats_bp = Blueprint('formats', __name__)

@formats_bp.route('/api/formats/templates', methods=['GET'])
def get_format_templates():
    """Get all format templates"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, format_type, format_spec, created_at, updated_at 
                FROM llm_format_template 
                ORDER BY name
            """)
            templates = cur.fetchall()
            return jsonify([dict(t) for t in templates])

@formats_bp.route('/api/formats/templates/<int:template_id>', methods=['GET'])
def get_format_template(template_id):
    """Get a specific format template"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, format_type, format_spec, created_at, updated_at 
                FROM llm_format_template 
                WHERE id = %s
            """, (template_id,))
            template = cur.fetchone()
            if not template:
                return jsonify({'error': 'Format template not found'}), 404
            return jsonify(dict(template))

@formats_bp.route('/api/formats/templates', methods=['POST'])
def create_format_template():
    """Create a new format template"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'format_type', 'format_spec']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Validate format_type
    if data['format_type'] not in ['input', 'output']:
        return jsonify({'error': 'format_type must be either "input" or "output"'}), 400

    # Validate format_spec is valid JSON Schema
    try:
        spec = json.loads(data['format_spec'])
        jsonschema.Draft7Validator.check_schema(spec)
    except (json.JSONDecodeError, jsonschema.exceptions.SchemaError) as e:
        return jsonify({'error': f'Invalid JSON Schema: {str(e)}'}), 400

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO llm_format_template (name, format_type, format_spec)
                VALUES (%s, %s, %s)
                RETURNING id, name, format_type, format_spec, created_at, updated_at
            """, (data['name'], data['format_type'], data['format_spec']))
            conn.commit()
            template = cur.fetchone()
            return jsonify(dict(template)), 201

@formats_bp.route('/api/formats/templates/<int:template_id>', methods=['PATCH'])
def update_format_template(template_id):
    """Update a format template"""
    data = request.get_json()
    
    # Validate format_type if provided
    if 'format_type' in data and data['format_type'] not in ['input', 'output']:
        return jsonify({'error': 'format_type must be either "input" or "output"'}), 400

    # Validate format_spec if provided
    if 'format_spec' in data:
        try:
            spec = json.loads(data['format_spec'])
            jsonschema.Draft7Validator.check_schema(spec)
        except (json.JSONDecodeError, jsonschema.exceptions.SchemaError) as e:
            return jsonify({'error': f'Invalid JSON Schema: {str(e)}'}), 400

    # Build update query
    update_fields = []
    params = []
    for field in ['name', 'format_type', 'format_spec']:
        if field in data:
            update_fields.append(f"{field} = %s")
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400

    params.append(template_id)
    update_sql = f"""
        UPDATE llm_format_template 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, name, format_type, format_spec, created_at, updated_at
    """

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(update_sql, params)
            if cur.rowcount == 0:
                return jsonify({'error': 'Format template not found'}), 404
            conn.commit()
            template = cur.fetchone()
            return jsonify(dict(template))

@formats_bp.route('/api/formats/templates/<int:template_id>', methods=['DELETE'])
def delete_format_template(template_id):
    """Delete a format template"""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM llm_format_template WHERE id = %s", (template_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Format template not found'}), 404
            conn.commit()
            return '', 204

@formats_bp.route('/api/formats/validate', methods=['POST'])
def validate_format():
    """Validate data against a format specification"""
    data = request.get_json()
    
    # Validate required fields
    if 'format_spec' not in data or 'test_data' not in data:
        return jsonify({'error': 'Missing required fields: format_spec and test_data'}), 400

    try:
        # Parse and validate schema
        schema = json.loads(data['format_spec'])
        jsonschema.Draft7Validator.check_schema(schema)
        validator = jsonschema.Draft7Validator(schema)
        
        # Validate test data against schema
        errors = []
        for error in validator.iter_errors(data['test_data']):
            errors.append(f"{' -> '.join(str(p) for p in error.path)}: {error.message}")
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 400
    except jsonschema.exceptions.SchemaError as e:
        return jsonify({'error': f'Invalid JSON Schema: {str(e)}'}), 400 