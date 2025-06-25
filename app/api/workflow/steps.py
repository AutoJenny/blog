from flask import Blueprint, jsonify, request
from app.db import get_db_conn
import psycopg2.extras

bp = Blueprint('workflow_steps', __name__)

@bp.route('/steps/<int:step_id>', methods=['GET'])
def get_step(step_id):
    """Get a workflow step by ID."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, name, config, sub_stage_id
            FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        step = cur.fetchone()
        
        if not step:
            return jsonify({'error': 'Step not found'}), 404
            
        return jsonify({
            'id': step['id'],
            'name': step['name'],
            'config': step['config'],
            'substageId': step['sub_stage_id']
        })

@bp.route('/steps', methods=['POST'])
def create_step():
    """Create a new workflow step."""
    data = request.get_json()
    
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get the current max step_order for the substage
        cur.execute("""
            SELECT COALESCE(MAX(step_order), 0) + 1 as next_order
            FROM workflow_step_entity
            WHERE sub_stage_id = %s
        """, (data['substageId'],))
        next_order = cur.fetchone()['next_order']
        
        # Insert the new step
        cur.execute("""
            INSERT INTO workflow_step_entity (name, config, sub_stage_id, step_order)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (data['name'], data['config'], data['substageId'], next_order))
        
        step_id = cur.fetchone()['id']
        conn.commit()
        
        return jsonify({'id': step_id}), 201

@bp.route('/steps/<int:step_id>', methods=['PUT'])
def update_step(step_id):
    """Update a workflow step."""
    data = request.get_json()
    
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            UPDATE workflow_step_entity
            SET name = %s, config = %s
            WHERE id = %s
            RETURNING id
        """, (data['name'], data['config'], step_id))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Step not found'}), 404
            
        conn.commit()
        return jsonify({'id': step_id})

@bp.route('/steps/<int:step_id>', methods=['DELETE'])
def delete_step(step_id):
    """Delete a workflow step."""
    with get_db_conn() as conn:
        cur = conn.cursor()
        
        # Get the step's current order and substage
        cur.execute("""
            SELECT step_order, sub_stage_id
            FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        step = cur.fetchone()
        
        if not step:
            return jsonify({'error': 'Step not found'}), 404
            
        # Delete the step
        cur.execute("""
            DELETE FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        
        # Update the order of remaining steps
        cur.execute("""
            UPDATE workflow_step_entity
            SET step_order = step_order - 1
            WHERE sub_stage_id = %s
            AND step_order > %s
        """, (step[1], step[0]))
        
        conn.commit()
        return '', 204

@bp.route('/reorder-steps', methods=['POST'])
def reorder_steps():
    """Reorder workflow steps."""
    data = request.get_json()
    step_id = data['stepId']
    new_index = data['newIndex']
    
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get the current step's info
        cur.execute("""
            SELECT step_order, sub_stage_id
            FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        step = cur.fetchone()
        
        if not step:
            return jsonify({'error': 'Step not found'}), 404
            
        old_index = step['step_order']
        substage_id = step['sub_stage_id']
        
        # Update the orders
        if old_index < new_index:
            # Moving down: decrease order of steps in between
            cur.execute("""
                UPDATE workflow_step_entity
                SET step_order = step_order - 1
                WHERE sub_stage_id = %s
                AND step_order > %s AND step_order <= %s
            """, (substage_id, old_index, new_index))
        else:
            # Moving up: increase order of steps in between
            cur.execute("""
                UPDATE workflow_step_entity
                SET step_order = step_order + 1
                WHERE sub_stage_id = %s
                AND step_order >= %s AND step_order < %s
            """, (substage_id, new_index, old_index))
        
        # Set the new order for the moved step
        cur.execute("""
            UPDATE workflow_step_entity
            SET step_order = %s
            WHERE id = %s
        """, (new_index, step_id))
        
        conn.commit()
        return jsonify({'success': True}) 