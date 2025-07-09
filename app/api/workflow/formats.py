"""Format-related routes for workflow API."""

from flask import Blueprint, jsonify, request
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
from datetime import datetime
import jsonschema
import json

formats_bp = Blueprint('formats', __name__)

@formats_bp.route('/api/workflow/formats/templates', methods=['GET'])
def get_format_templates():
    """Get all format templates"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, description, fields, llm_instructions, created_at, updated_at 
                FROM workflow_format_template 
                ORDER BY name
            """)
            templates = cur.fetchall()
            
            # Transform response to match API specification
            formatted_templates = []
            for template in templates:
                fields_data = template['fields']
                # Extract format_type from fields JSONB
                if isinstance(fields_data, str):
                    fields_data_obj = json.loads(fields_data)
                else:
                    fields_data_obj = fields_data
                format_type = fields_data_obj.get('type', 'output') if isinstance(fields_data_obj, dict) else 'output'
                formatted_template = {
                    'id': template['id'],
                    'name': template['name'],
                    'description': template['description'],
                    'fields': _extract_fields_from_jsonb(fields_data),
                    'format_type': format_type,
                    'llm_instructions': template.get('llm_instructions', '')
                }
                formatted_templates.append(formatted_template)
            
            return jsonify(formatted_templates)

@formats_bp.route('/api/workflow/formats/templates/<int:template_id>', methods=['GET'])
def get_format_template(template_id):
    """Get a specific format template"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, description, fields, llm_instructions, created_at, updated_at 
                FROM workflow_format_template 
                WHERE id = %s
            """, (template_id,))
            template = cur.fetchone()
            if not template:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'Format template not found',
                        'details': {'template_id': template_id}
                    }
                }), 404
            fields_data = template['fields']
            if isinstance(fields_data, str):
                fields_data_obj = json.loads(fields_data)
            else:
                fields_data_obj = fields_data
            format_type = fields_data_obj.get('type', 'output') if isinstance(fields_data_obj, dict) else 'output'
            formatted_template = {
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'fields': _extract_fields_from_jsonb(fields_data),
                'format_type': format_type,
                'llm_instructions': template.get('llm_instructions', '')
            }
            return jsonify(formatted_template)

@formats_bp.route('/api/workflow/formats/templates', methods=['POST'])
def create_format_template():
    """Create a new format template"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'description', 'fields']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': f'Missing required field: {field}',
                    'details': {'field': field}
                }
            }), 400

    # Validate fields structure - allow empty arrays for HTML/text templates
    if not isinstance(data['fields'], list):
        return jsonify({
            'error': {
                'code': 'INVALID_FIELDS',
                'message': 'Fields must be an array',
                'details': {'fields': data['fields']}
            }
        }), 400
    
    # Allow empty arrays for output templates (HTML/text output)
    format_type = data.get('format_type', 'output')
    if format_type == 'output' and len(data['fields']) == 0:
        # Empty array is allowed for output templates (HTML/text)
        pass
    elif len(data['fields']) == 0:
        return jsonify({
            'error': {
                'code': 'EMPTY_FIELDS',
                'message': 'Fields array cannot be empty for input or bidirectional templates',
                'details': {'fields': data['fields']}
            }
        }), 400

    # Get format_type (default to 'output' if not provided)
    format_type = data.get('format_type', 'output')
    if format_type not in ['input', 'output', 'bidirectional']:
        return jsonify({
            'error': {
                'code': 'INVALID_FORMAT_TYPE',
                'message': 'format_type must be one of: input, output, bidirectional',
                'details': {'format_type': format_type}
            }
        }), 400

    # Get llm_instructions (default to empty string if not provided)
    llm_instructions = data.get('llm_instructions', '')

    # Convert fields to JSONB format for storage
    fields_jsonb = _convert_fields_to_jsonb(data['fields'], format_type)

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO workflow_format_template (name, description, fields, llm_instructions)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, description, fields, llm_instructions, created_at, updated_at
            """, (data['name'], data['description'], json.dumps(fields_jsonb), llm_instructions))
            conn.commit()
            template = cur.fetchone()
            
            # Transform response to match API specification
            formatted_template = {
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'fields': _extract_fields_from_jsonb(template['fields']),
                'format_type': format_type,
                'llm_instructions': template.get('llm_instructions', '')
            }
            return jsonify(formatted_template), 201

@formats_bp.route('/api/workflow/formats/templates/<int:template_id>', methods=['PUT'])
def update_format_template(template_id):
    """Update a format template"""
    data = request.get_json()
    
    # Build update query
    update_fields = []
    params = []
    format_type = None
    
    for field in ['name', 'description', 'fields', 'llm_instructions']:
        if field in data:
            if field == 'fields':
                # Get format_type for conversion
                format_type = data.get('format_type', 'output')
                if format_type not in ['input', 'output', 'bidirectional']:
                    return jsonify({
                        'error': {
                            'code': 'INVALID_FORMAT_TYPE',
                            'message': 'format_type must be one of: input, output, bidirectional',
                            'details': {'format_type': format_type}
                        }
                    }), 400
                # Convert fields to JSONB format for storage
                fields_jsonb = _convert_fields_to_jsonb(data['fields'], format_type)
                update_fields.append(f"{field} = %s")
                params.append(json.dumps(fields_jsonb))
            else:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
    
    if not update_fields:
        return jsonify({
            'error': {
                'code': 'NO_FIELDS_TO_UPDATE',
                'message': 'No fields to update',
                'details': {}
            }
        }), 400

    params.append(template_id)
    update_sql = f"""
        UPDATE workflow_format_template 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, name, description, fields, llm_instructions, created_at, updated_at
    """

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(update_sql, params)
            if cur.rowcount == 0:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'Format template not found',
                        'details': {'template_id': template_id}
                    }
                }), 404
            conn.commit()
            template = cur.fetchone()
            
            # Transform response to match API specification
            fields_data = template['fields']
            if isinstance(fields_data, str):
                fields_data_obj = json.loads(fields_data)
            else:
                fields_data_obj = fields_data
            format_type = fields_data_obj.get('type', 'output') if isinstance(fields_data_obj, dict) else 'output'
            formatted_template = {
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'fields': _extract_fields_from_jsonb(template['fields']),
                'format_type': format_type,
                'llm_instructions': template.get('llm_instructions', '')
            }
            return jsonify(formatted_template)

@formats_bp.route('/api/workflow/formats/templates/<int:template_id>', methods=['DELETE'])
def delete_format_template(template_id):
    """Delete a format template"""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM workflow_format_template WHERE id = %s", (template_id,))
            if cur.rowcount == 0:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'Format template not found',
                        'details': {'template_id': template_id}
                    }
                }), 404
            conn.commit()
            return jsonify({'status': 'success'})

@formats_bp.route('/api/workflow/formats/validate', methods=['POST'])
def validate_format():
    """Validate data against a format specification"""
    data = request.get_json()
    
    # Validate required fields
    if 'fields' not in data or 'test_data' not in data:
        return jsonify({
            'error': {
                'code': 'MISSING_FIELDS',
                'message': 'Missing required fields: fields and test_data',
                'details': {}
            }
        }), 400

    try:
        # Extract schema from fields
        schema = _extract_schema_from_fields(data['fields'])
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
        return jsonify({
            'error': {
                'code': 'INVALID_JSON',
                'message': f'Invalid JSON: {str(e)}',
                'details': {}
            }
        }), 400
    except jsonschema.exceptions.SchemaError as e:
        return jsonify({
            'error': {
                'code': 'INVALID_SCHEMA',
                'message': f'Invalid JSON Schema: {str(e)}',
                'details': {}
            }
        }), 400

def _extract_fields_from_jsonb(fields_jsonb):
    """Extract fields array from JSONB storage format (supports both array and schema dict)."""
    if isinstance(fields_jsonb, str):
        fields_data = json.loads(fields_jsonb)
    else:
        fields_data = fields_jsonb

    # If already a list, return as-is (new format)
    if isinstance(fields_data, list):
        return fields_data

    # If old schema dict, extract as before
    if isinstance(fields_data, dict) and 'schema' in fields_data:
        schema = fields_data['schema']
        if isinstance(schema, dict) and 'properties' in schema:
            fields = []
            for field_name, field_spec in schema['properties'].items():
                if not isinstance(field_spec, dict):
                    continue
                field = {
                    'name': field_name,
                    'type': field_spec.get('type', 'string'),
                    'required': field_name in schema.get('required', [])
                }
                if 'description' in field_spec:
                    field['description'] = field_spec['description']
                fields.append(field)
            return fields

    # Fallback: return empty array
    return []

def _convert_fields_to_jsonb(fields_array, format_type='output'):
    """Convert API specification fields array to JSONB storage format"""
    # Handle empty arrays for output templates (HTML/text)
    if len(fields_array) == 0 and format_type == 'output':
        return {
            'type': format_type,
            'schema': {
                'type': 'object',
                'properties': {}
            }
        }
    
    # Convert fields array to schema format
    properties = {}
    required = []
    
    for field in fields_array:
        field_name = field['name']
        field_type = field.get('type', 'string')
        
        properties[field_name] = {
            'type': field_type
        }
        
        if field.get('required', False):
            required.append(field_name)
        
        if 'description' in field:
            properties[field_name]['description'] = field['description']
    
    schema = {
        'type': 'object',
        'properties': properties
    }
    
    if required:
        schema['required'] = required
    
    return {
        'type': format_type,
        'schema': schema
    }

def _extract_schema_from_fields(fields_array):
    """Extract JSON schema from fields array"""
    # Convert fields array to schema format
    properties = {}
    required = []
    
    for field in fields_array:
        field_name = field['name']
        field_type = field.get('type', 'string')
        
        properties[field_name] = {
            'type': field_type
        }
        
        if field.get('required', False):
            required.append(field_name)
        
        if 'description' in field:
            properties[field_name]['description'] = field['description']
    
    schema = {
        'type': 'object',
        'properties': properties
    }
    
    if required:
        schema['required'] = required
    
    return schema 