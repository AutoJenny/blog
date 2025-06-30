import json
import jsonschema
import psycopg2
import re
from typing import Dict, Any, Optional, Tuple, Union, List
from flask import current_app
from psycopg2.extras import RealDictCursor

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

def _extract_references_from_text(text: str) -> List[str]:
    """Extract all [data:field_name] references from text."""
    pattern = r'\[data:([a-zA-Z0-9_]+)\]'
    return re.findall(pattern, text)

def _validate_references(text: str, available_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that all [data:field_name] references in text exist in available_data."""
    references = _extract_references_from_text(text)
    missing_refs = []
    
    for ref in references:
        if ref not in available_data:
            missing_refs.append(ref)
    
    return len(missing_refs) == 0, missing_refs

def get_db_conn():
    """Get database connection, handling both Flask and standalone contexts."""
    try:
        # Try Flask context first
        from app.db import get_db_conn as flask_get_db_conn
        return flask_get_db_conn()
    except RuntimeError:
        # Fall back to direct connection
        return psycopg2.connect("postgresql://nickfiddes@localhost:5432/blog")

class FormatValidator:
    """Validator for workflow step format specifications."""

    @staticmethod
    def get_format_spec(format_id: int) -> Optional[Dict[str, Any]]:
        """Get format specification from database."""
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT fields, format_type
                    FROM workflow_format_template
                    WHERE id = %s
                """, (format_id,))
                result = cur.fetchone()
                if not result:
                    return None
                
                # Handle both string and dict formats
                fields_data = result['fields']
                if isinstance(fields_data, str):
                    fields_data = json.loads(fields_data)
                
                # Convert fields array to schema
                schema = _extract_schema_from_fields(fields_data)
                
                return {
                    'spec': schema,
                    'type': result['format_type'] if 'format_type' in result else None
                }
        finally:
            conn.close()

    @staticmethod
    def get_step_formats(step_id: int, post_id: int) -> Optional[Dict[str, Any]]:
        """Get input and output format specifications for a workflow step."""
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        input_fmt.fields as input_spec,
                        output_fmt.fields as output_spec
                    FROM workflow_step_format wsf
                    JOIN workflow_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                    JOIN workflow_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                    WHERE wsf.step_id = %s AND wsf.post_id = %s
                """, (step_id, post_id))
                result = cur.fetchone()
                if not result:
                    return None
                
                # Handle both string and dict formats
                input_fields = result['input_spec']
                output_fields = result['output_spec']
                
                if isinstance(input_fields, str):
                    input_fields = json.loads(input_fields)
                if isinstance(output_fields, str):
                    output_fields = json.loads(output_fields)
                
                return {
                    'input': _extract_schema_from_fields(input_fields),
                    'output': _extract_schema_from_fields(output_fields)
                }
        finally:
            conn.close()

    @staticmethod
    def validate_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate data against a JSON schema."""
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def validate_references(text: str, available_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that all [data:field_name] references in text exist in available_data."""
        return _validate_references(text, available_data)

    def validate_format(self, format_id: int, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate data against a format template."""
        format_info = self.get_format_spec(format_id)
        if not format_info:
            return False, "Format template not found"
        
        return self.validate_data(data, format_info['spec'])

    def validate_step_input(self, step_id: int, post_id: int, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate input data for a workflow step."""
        formats = self.get_step_formats(step_id, post_id)
        if not formats:
            return False, "Format configuration not found for step"
        
        return self.validate_data(data, formats['input'])

    def validate_step_output(self, step_id: int, post_id: int, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate output data for a workflow step."""
        formats = self.get_step_formats(step_id, post_id)
        if not formats:
            return False, "Format configuration not found for step"
        
        return self.validate_data(data, formats['output'])

    def validate_step_prompts(self, step_id: int, post_id: int, system_prompt: str, task_prompt: str, available_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that all references in step prompts exist in available data."""
        errors = []
        
        # Validate system prompt references
        is_valid, missing_refs = self.validate_references(system_prompt, available_data)
        if not is_valid:
            errors.extend([f"System prompt missing reference: {ref}" for ref in missing_refs])
        
        # Validate task prompt references
        is_valid, missing_refs = self.validate_references(task_prompt, available_data)
        if not is_valid:
            errors.extend([f"Task prompt missing reference: {ref}" for ref in missing_refs])
        
        return len(errors) == 0, errors

# Create validation endpoints
from flask import Blueprint, jsonify, request

bp = Blueprint('format_validator', __name__)

@bp.route('/api/workflow/formats/validate/<int:format_id>', methods=['POST'])
def validate_format_data(format_id: int):
    """Validate data against a format template."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    validator = FormatValidator()
    is_valid, error = validator.validate_format(format_id, data)
    
    if is_valid:
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False, 'error': error}), 400

@bp.route('/api/workflow/steps/<int:step_id>/formats/<int:post_id>/validate/input', methods=['POST'])
def validate_step_input_data(step_id: int, post_id: int):
    """Validate input data for a workflow step."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    validator = FormatValidator()
    is_valid, error = validator.validate_step_input(step_id, post_id, data)
    
    if is_valid:
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False, 'error': error}), 400

@bp.route('/api/workflow/steps/<int:step_id>/formats/<int:post_id>/validate/output', methods=['POST'])
def validate_step_output_data(step_id: int, post_id: int):
    """Validate output data for a workflow step."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    validator = FormatValidator()
    is_valid, error = validator.validate_step_output(step_id, post_id, data)
    
    if is_valid:
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False, 'error': error}), 400

@bp.route('/api/workflow/steps/<int:step_id>/formats/<int:post_id>/validate/references', methods=['POST'])
def validate_step_references(step_id: int, post_id: int):
    """Validate that all references in step prompts exist in available data."""
    data = request.get_json()
    if not data or 'system_prompt' not in data or 'task_prompt' not in data or 'available_data' not in data:
        return jsonify({'error': 'Missing required fields: system_prompt, task_prompt, available_data'}), 400

    validator = FormatValidator()
    is_valid, errors = validator.validate_step_prompts(
        step_id, 
        post_id, 
        data['system_prompt'], 
        data['task_prompt'], 
        data['available_data']
    )
    
    if is_valid:
        return jsonify({'valid': True, 'errors': []})
    else:
        return jsonify({'valid': False, 'errors': errors}), 400 