from flask import Blueprint, jsonify, request
from app.db import get_db_conn
import psycopg2.extras
import json

from . import bp

@bp.route('/steps', methods=['GET'])
def get_all_steps():
    """Get all workflow steps with their stage and substage information."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT 
                wse.id,
                wse.name as step_name,
                wse.description,
                wse.step_order,
                wsse.name as substage_name,
                wsse.sub_stage_order,
                wst.name as stage_name,
                wst.stage_order
            FROM workflow_step_entity wse
            JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
            JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
            ORDER BY wst.stage_order, wsse.sub_stage_order, wse.step_order
        """)
        steps = cur.fetchall()
        
        return jsonify([{
            'id': step['id'],
            'step_name': step['step_name'],
            'description': step['description'],
            'step_order': step['step_order'],
            'substage_name': step['substage_name'],
            'sub_stage_order': step['sub_stage_order'],
            'stage_name': step['stage_name'],
            'stage_order': step['stage_order']
        } for step in steps])

@bp.route('/steps', methods=['POST'])
def create_step():
    """Create a new workflow step."""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('sub_stage_id'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get the current max step_order for this substage
        cur.execute("""
            SELECT COALESCE(MAX(step_order), 0)
            FROM workflow_step_entity
            WHERE sub_stage_id = %s
        """, (data['sub_stage_id'],))
        max_order = cur.fetchone()[0]
        
        # Create the new step
        cur.execute("""
            INSERT INTO workflow_step_entity (
                sub_stage_id, name, description, step_order, config
            ) VALUES (
                %s, %s, %s, %s, %s::jsonb
            ) RETURNING id, name, description, step_order, config
        """, (
            data['sub_stage_id'],
            data['name'],
            data.get('description', ''),
            max_order + 1,
            json.dumps(data.get('config', {}))
        ))
        
        new_step = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'id': new_step['id'],
            'name': new_step['name'],
            'description': new_step['description'],
            'step_order': new_step['step_order'],
            'config': new_step['config']
        }), 201

@bp.route('/steps/<int:step_id>', methods=['PUT'])
def update_step(step_id):
    """Update a workflow step."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get the current step
        cur.execute("""
            SELECT id, sub_stage_id, step_order
            FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        step = cur.fetchone()
        
        if not step:
            return jsonify({'error': 'Step not found'}), 404
            
        # If moving to a different substage, handle reordering
        if 'sub_stage_id' in data and data['sub_stage_id'] != step['sub_stage_id']:
            # Update order in old substage
            cur.execute("""
                UPDATE workflow_step_entity
                SET step_order = step_order - 1
                WHERE sub_stage_id = %s
                AND step_order > %s
            """, (step['sub_stage_id'], step['step_order']))
            
            # Get max order in new substage
            cur.execute("""
                SELECT COALESCE(MAX(step_order), 0)
                FROM workflow_step_entity
                WHERE sub_stage_id = %s
            """, (data['sub_stage_id'],))
            max_order = cur.fetchone()[0]
            data['step_order'] = max_order + 1
            
        # If changing order within same substage
        elif 'step_order' in data and data['step_order'] != step['step_order']:
            new_order = data['step_order']
            old_order = step['step_order']
            
            if new_order > old_order:
                # Moving down: decrement steps in between
                cur.execute("""
                    UPDATE workflow_step_entity
                    SET step_order = step_order - 1
                    WHERE sub_stage_id = %s
                    AND step_order > %s
                    AND step_order <= %s
                """, (step['sub_stage_id'], old_order, new_order))
            else:
                # Moving up: increment steps in between
                cur.execute("""
                    UPDATE workflow_step_entity
                    SET step_order = step_order + 1
                    WHERE sub_stage_id = %s
                    AND step_order >= %s
                    AND step_order < %s
                """, (step['sub_stage_id'], new_order, old_order))
        
        # Update the step
        update_fields = []
        update_values = []
        for field in ['name', 'description', 'sub_stage_id', 'step_order']:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        if 'config' in data:
            update_fields.append("config = %s::jsonb")
            update_values.append(json.dumps(data['config']))
        
        if update_fields:
            update_values.append(step_id)
            cur.execute(f"""
                UPDATE workflow_step_entity
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, description, step_order, config
            """, update_values)
            
            updated_step = cur.fetchone()
            conn.commit()
            
            return jsonify({
                'id': updated_step['id'],
                'name': updated_step['name'],
                'description': updated_step['description'],
                'step_order': updated_step['step_order'],
                'config': updated_step['config']
            })
        
        return jsonify({'error': 'No fields to update'}), 400

@bp.route('/steps/<int:step_id>', methods=['GET'])
def get_step(step_id):
    """Get a workflow step by ID."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, name, description, sub_stage_id, step_order, config
            FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        step = cur.fetchone()
        
        if not step:
            return jsonify({'error': 'Step not found'}), 404
            
        return jsonify({
            'id': step['id'],
            'name': step['name'],
            'description': step['description'],
            'subStageId': step['sub_stage_id'],
            'stepOrder': step['step_order'],
            'config': step['config']
        })

@bp.route('/steps/<int:step_id>', methods=['DELETE'])
def delete_step(step_id):
    """Delete a workflow step."""
    with get_db_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get the step's current order and substage
        cur.execute("""
            SELECT step_order, sub_stage_id
            FROM workflow_step_entity
            WHERE id = %s
        """, (step_id,))
        step = cur.fetchone()
        
        if not step:
            return jsonify({'error': 'Step not found'}), 404
            
        # Delete related records first
        cur.execute("""
            DELETE FROM post_workflow_step_action
            WHERE step_id = %s
        """, (step_id,))
        
        cur.execute("""
            DELETE FROM workflow_step_input
            WHERE step_id = %s
        """, (step_id,))
            
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
        """, (step['sub_stage_id'], step['step_order']))
        
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