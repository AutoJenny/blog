import json
import jsonschema
from typing import Dict, Any, Optional, Tuple, Union
from flask import current_app
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor

class FormatValidator:
    """Validator for workflow step format specifications."""

    @staticmethod
    def get_format_spec(format_id: int) -> Optional[Dict[str, Any]]:
        """Get format specification from database."""
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT format_spec, format_type
                    FROM llm_format_template
                    WHERE id = %s
                """, (format_id,))
                result = cur.fetchone()
                if not result:
                    return None
                return {
                    'spec': json.loads(result['format_spec']),
                    'type': result['format_type']
                }

    @staticmethod
    def get_step_formats(step_id: int, post_id: int) -> Optional[Dict[str, Any]]:
        """Get input and output format specifications for a workflow step."""
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        input_fmt.format_spec as input_spec,
                        output_fmt.format_spec as output_spec
                    FROM workflow_step_format wsf
                    JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                    JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                    WHERE wsf.step_id = %s AND wsf.post_id = %s
                """, (step_id, post_id))
                result = cur.fetchone()
                if not result:
                    return None
                return {
                    'input': json.loads(result['input_spec']),
                    'output': json.loads(result['output_spec'])
                }

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

# Create validation endpoints
from flask import Blueprint, jsonify, request

bp = Blueprint('format_validator', __name__)

@bp.route('/api/formats/validate/<int:format_id>', methods=['POST'])
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