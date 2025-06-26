from flask import Blueprint, jsonify, request
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
from datetime import datetime

workflow_bp = Blueprint('workflow', __name__)

@workflow_bp.route('/api/workflow/steps/<int:step_id>/formats', methods=['GET'])
def get_step_formats(step_id):
    """Get format configuration for a workflow step"""
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    wsf.input_format_id,
                    wsf.output_format_id,
                    input_fmt.name as input_format_name,
                    output_fmt.name as output_format_name
                FROM workflow_step_entity wse
                LEFT JOIN workflow_step_format wsf ON wsf.step_id = wse.id
                LEFT JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                WHERE wse.id = %s
            """, (step_id,))
            
            result = cur.fetchone()
            if not result:
                return jsonify({
                    'input_format_id': None,
                    'output_format_id': None,
                    'input_format': None,
                    'output_format': None
                })
            
            return jsonify({
                'input_format_id': result['input_format_id'],
                'output_format_id': result['output_format_id'],
                'input_format': {
                    'id': result['input_format_id'],
                    'name': result['input_format_name']
                } if result['input_format_id'] else None,
                'output_format': {
                    'id': result['output_format_id'],
                    'name': result['output_format_name']
                } if result['output_format_id'] else None
            })

@workflow_bp.route('/api/workflow/steps/<int:step_id>/formats', methods=['PUT'])
def update_step_formats(step_id):
    """Update format configuration for a workflow step"""
    data = request.get_json()
    input_format_id = data.get('input_format_id')
    output_format_id = data.get('output_format_id')
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if format configuration exists
            cur.execute("""
                SELECT id FROM workflow_step_format 
                WHERE step_id = %s
            """, (step_id,))
            
            if cur.fetchone():
                # Update existing configuration
                cur.execute("""
                    UPDATE workflow_step_format 
                    SET input_format_id = %s,
                        output_format_id = %s,
                        updated_at = NOW()
                    WHERE step_id = %s
                    RETURNING id
                """, (input_format_id, output_format_id, step_id))
            else:
                # Create new configuration
                cur.execute("""
                    INSERT INTO workflow_step_format 
                    (step_id, input_format_id, output_format_id, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (step_id, input_format_id, output_format_id))
            
            conn.commit()
            
            # Get updated format information
            cur.execute("""
                SELECT 
                    wsf.input_format_id,
                    wsf.output_format_id,
                    input_fmt.name as input_format_name,
                    output_fmt.name as output_format_name
                FROM workflow_step_format wsf
                LEFT JOIN llm_format_template input_fmt ON wsf.input_format_id = input_fmt.id
                LEFT JOIN llm_format_template output_fmt ON wsf.output_format_id = output_fmt.id
                WHERE wsf.step_id = %s
            """, (step_id,))
            
            result = cur.fetchone()
            return jsonify({
                'input_format_id': result['input_format_id'],
                'output_format_id': result['output_format_id'],
                'input_format': {
                    'id': result['input_format_id'],
                    'name': result['input_format_name']
                } if result['input_format_id'] else None,
                'output_format': {
                    'id': result['output_format_id'],
                    'name': result['output_format_name']
                } if result['output_format_id'] else None
            }) 