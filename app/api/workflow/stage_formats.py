"""Stage format endpoints for workflow API."""

from flask import Blueprint, jsonify, request
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

stage_formats_bp = Blueprint('stage_formats', __name__)

@stage_formats_bp.route('/api/workflow/stages/<int:stage_id>/format', methods=['GET'])
def get_stage_format(stage_id):
    """Get format configuration for a stage"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First check if stage exists
            cur.execute("""
                SELECT id, name FROM workflow_stage_entity 
                WHERE id = %s
            """, (stage_id,))
            stage = cur.fetchone()
            if not stage:
                return jsonify({
                    'error': {
                        'code': 'STAGE_NOT_FOUND',
                        'message': 'Stage not found',
                        'details': {'stage_id': stage_id}
                    }
                }), 404
            
            # Get stage format configuration
            cur.execute("""
                SELECT wsf.template_id, wsf.config, wft.name as template_name
                FROM workflow_stage_format wsf
                JOIN workflow_format_template wft ON wsf.template_id = wft.id
                WHERE wsf.stage_id = %s
            """, (stage_id,))
            stage_format = cur.fetchone()
            
            if not stage_format:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'No format configuration found for stage',
                        'details': {'stage_id': stage_id}
                    }
                }), 404
            
            return jsonify({
                'template_id': stage_format['template_id'],
                'template_name': stage_format['template_name'],
                'config': stage_format['config']
            })

@stage_formats_bp.route('/api/workflow/stages/<int:stage_id>/format', methods=['POST'])
def update_stage_format(stage_id):
    """Update format configuration for a stage"""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'template_id' not in data:
        return jsonify({
            'error': {
                'code': 'MISSING_TEMPLATE_ID',
                'message': 'template_id is required',
                'details': {}
            }
        }), 400
    
    template_id = data['template_id']
    config = data.get('config', {})
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if stage exists
            cur.execute("""
                SELECT id, name FROM workflow_stage_entity 
                WHERE id = %s
            """, (stage_id,))
            stage = cur.fetchone()
            if not stage:
                return jsonify({
                    'error': {
                        'code': 'STAGE_NOT_FOUND',
                        'message': 'Stage not found',
                        'details': {'stage_id': stage_id}
                    }
                }), 404
            
            # Check if template exists
            cur.execute("""
                SELECT id, name FROM workflow_format_template 
                WHERE id = %s
            """, (template_id,))
            template = cur.fetchone()
            if not template:
                return jsonify({
                    'error': {
                        'code': 'TEMPLATE_NOT_FOUND',
                        'message': 'Format template not found',
                        'details': {'template_id': template_id}
                    }
                }), 404
            
            # Check if stage format already exists
            cur.execute("""
                SELECT id FROM workflow_stage_format 
                WHERE stage_id = %s
            """, (stage_id,))
            existing = cur.fetchone()
            
            if existing:
                # Update existing stage format
                cur.execute("""
                    UPDATE workflow_stage_format 
                    SET template_id = %s, config = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE stage_id = %s
                    RETURNING id
                """, (template_id, json.dumps(config), stage_id))
            else:
                # Create new stage format
                cur.execute("""
                    INSERT INTO workflow_stage_format (stage_id, template_id, config)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (stage_id, template_id, json.dumps(config)))
            
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Stage format updated successfully'
            })

@stage_formats_bp.route('/api/workflow/stages/<int:stage_id>/format', methods=['DELETE'])
def delete_stage_format(stage_id):
    """Delete format configuration for a stage"""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Check if stage format exists
            cur.execute("""
                SELECT id FROM workflow_stage_format 
                WHERE stage_id = %s
            """, (stage_id,))
            stage_format = cur.fetchone()
            
            if not stage_format:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'No format configuration found for stage',
                        'details': {'stage_id': stage_id}
                    }
                }), 404
            
            # Delete the stage format
            cur.execute("""
                DELETE FROM workflow_stage_format 
                WHERE stage_id = %s
            """, (stage_id,))
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Stage format deleted successfully'
            })

@stage_formats_bp.route('/api/workflow/stages/<int:stage_id>/format/validate', methods=['POST'])
def validate_stage_format(stage_id):
    """Validate data against stage format configuration"""
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
            # Get stage format configuration
            cur.execute("""
                SELECT wsf.template_id, wsf.config, wft.fields
                FROM workflow_stage_format wsf
                JOIN workflow_format_template wft ON wsf.template_id = wft.id
                WHERE wsf.stage_id = %s
            """, (stage_id,))
            stage_format = cur.fetchone()
            
            if not stage_format:
                return jsonify({
                    'error': {
                        'code': 'FORMAT_NOT_FOUND',
                        'message': 'No format configuration found for stage',
                        'details': {'stage_id': stage_id}
                    }
                }), 404
            
            # Extract fields from template
            fields_data = stage_format['fields']
            if isinstance(fields_data, str):
                fields_data = json.loads(fields_data)
            
            # Convert fields to schema for validation
            if isinstance(fields_data, dict) and 'schema' in fields_data:
                schema = fields_data['schema']
                if isinstance(schema, dict) and 'properties' in schema:
                    # Validate test data against schema
                    errors = []
                    properties = schema['properties']
                    required = schema.get('required', [])
                    
                    # Check required fields
                    for field_name in required:
                        if field_name not in test_data:
                            errors.append(f"Missing required field: {field_name}")
                    
                    # Check field types
                    for field_name, field_value in test_data.items():
                        if field_name in properties:
                            field_spec = properties[field_name]
                            if isinstance(field_spec, dict):
                                expected_type = field_spec.get('type', 'string')
                                # Basic type validation
                                if expected_type == 'string' and not isinstance(field_value, str):
                                    errors.append(f"Field '{field_name}' must be a string")
                                elif expected_type == 'number' and not isinstance(field_value, (int, float)):
                                    errors.append(f"Field '{field_name}' must be a number")
                                elif expected_type == 'array' and not isinstance(field_value, list):
                                    errors.append(f"Field '{field_name}' must be an array")
                                elif expected_type == 'object' and not isinstance(field_value, dict):
                                    errors.append(f"Field '{field_name}' must be an object")
                    
                    return jsonify({
                        'valid': len(errors) == 0,
                        'errors': errors
                    })
            
            # Fallback: return valid if no schema found
            return jsonify({
                'valid': True,
                'errors': []
            }) 