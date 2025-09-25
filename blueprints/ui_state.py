"""
UI State Management Blueprint
Handles persistent state storage for UI components
Replaces localStorage, sessionStorage, and in-memory state
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import json
from datetime import datetime

ui_state_bp = Blueprint('ui_state', __name__, url_prefix='/api/ui')

@ui_state_bp.route('/selection-state', methods=['GET'])
def get_selection_state():
    """Get selection state for a user/page"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        selection_type = request.args.get('selection_type')
        
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT id, user_id, page_type, selection_type, selected_id, 
                       selected_data, created_at, updated_at
                FROM ui_selection_state
                WHERE user_id = %s
            """
            params = [user_id]
            
            if page_type:
                query += " AND page_type = %s"
                params.append(page_type)
            
            if selection_type:
                query += " AND selection_type = %s"
                params.append(selection_type)
            
            query += " ORDER BY updated_at DESC"
            
            cursor.execute(query, params)
            selections = cursor.fetchall()
            
            return jsonify({
                'selections': [
                    {
                        'id': s['id'],
                        'user_id': s['user_id'],
                        'page_type': s['page_type'],
                        'selection_type': s['selection_type'],
                        'selected_id': s['selected_id'],
                        'selected_data': s['selected_data'],
                        'created_at': s['created_at'].isoformat() if s['created_at'] else None,
                        'updated_at': s['updated_at'].isoformat() if s['updated_at'] else None
                    }
                    for s in selections
                ]
            })
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/selection-state', methods=['POST'])
def set_selection_state():
    """Set selection state"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        page_type = data.get('page_type')
        selection_type = data.get('selection_type')
        selected_id = data.get('selected_id')
        selected_data = data.get('selected_data')
        
        if not page_type or not selection_type:
            return jsonify({'error': True, 'message': 'page_type and selection_type are required'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ui_selection_state 
                (user_id, page_type, selection_type, selected_id, selected_data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, page_type, selection_type) 
                DO UPDATE SET 
                    selected_id = EXCLUDED.selected_id,
                    selected_data = EXCLUDED.selected_data,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, page_type, selection_type, selected_id, 
                  json.dumps(selected_data) if selected_data else None))
            
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/selection-state', methods=['DELETE'])
def clear_selection_state():
    """Clear selection state"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        selection_type = request.args.get('selection_type')
        
        with db_manager.get_cursor() as cursor:
            query = "DELETE FROM ui_selection_state WHERE user_id = %s"
            params = [user_id]
            
            if page_type:
                query += " AND page_type = %s"
                params.append(page_type)
            
            if selection_type:
                query += " AND selection_type = %s"
                params.append(selection_type)
            
            cursor.execute(query, params)
            
            return jsonify({'success': True, 'deleted': cursor.rowcount})
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/ui-state', methods=['GET'])
def get_ui_state():
    """Get UI state for a user/page"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        state_key = request.args.get('state_key')
        
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT id, user_id, page_type, state_key, state_data, 
                       created_at, updated_at
                FROM ui_ui_state
                WHERE user_id = %s
            """
            params = [user_id]
            
            if page_type:
                query += " AND page_type = %s"
                params.append(page_type)
            
            if state_key:
                query += " AND state_key = %s"
                params.append(state_key)
            
            query += " ORDER BY updated_at DESC"
            
            cursor.execute(query, params)
            ui_states = cursor.fetchall()
            
            return jsonify({
                'ui_states': [
                    {
                        'id': s['id'],
                        'user_id': s['user_id'],
                        'page_type': s['page_type'],
                        'state_key': s['state_key'],
                        'state_data': s['state_data'],
                        'created_at': s['created_at'].isoformat() if s['created_at'] else None,
                        'updated_at': s['updated_at'].isoformat() if s['updated_at'] else None
                    }
                    for s in ui_states
                ]
            })
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/ui-state', methods=['POST'])
def set_ui_state():
    """Set UI state"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        page_type = data.get('page_type')
        state_key = data.get('state_key')
        state_data = data.get('state_data')
        
        if not page_type or not state_key:
            return jsonify({'error': True, 'message': 'page_type and state_key are required'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ui_ui_state 
                (user_id, page_type, state_key, state_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, page_type, state_key) 
                DO UPDATE SET 
                    state_data = EXCLUDED.state_data,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, page_type, state_key, json.dumps(state_data)))
            
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/workflow-state', methods=['GET'])
def get_workflow_state():
    """Get workflow state for a user/page"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        workflow_id = request.args.get('workflow_id')
        
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT id, user_id, page_type, workflow_id, state_data, 
                       created_at, updated_at
                FROM ui_workflow_state
                WHERE user_id = %s
            """
            params = [user_id]
            
            if page_type:
                query += " AND page_type = %s"
                params.append(page_type)
            
            if workflow_id:
                query += " AND workflow_id = %s"
                params.append(workflow_id)
            
            query += " ORDER BY updated_at DESC"
            
            cursor.execute(query, params)
            workflow_states = cursor.fetchall()
            
            return jsonify({
                'workflow_states': [
                    {
                        'id': s['id'],
                        'user_id': s['user_id'],
                        'page_type': s['page_type'],
                        'workflow_id': s['workflow_id'],
                        'state_data': s['state_data'],
                        'created_at': s['created_at'].isoformat() if s['created_at'] else None,
                        'updated_at': s['updated_at'].isoformat() if s['updated_at'] else None
                    }
                    for s in workflow_states
                ]
            })
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/workflow-state', methods=['POST'])
def set_workflow_state():
    """Set workflow state"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        page_type = data.get('page_type')
        workflow_id = data.get('workflow_id')
        state_data = data.get('state_data')
        
        if not page_type or not workflow_id:
            return jsonify({'error': True, 'message': 'page_type and workflow_id are required'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ui_workflow_state 
                (user_id, page_type, workflow_id, state_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, page_type, workflow_id) 
                DO UPDATE SET 
                    state_data = EXCLUDED.state_data,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, page_type, workflow_id, json.dumps(state_data)))
            
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/queue-state', methods=['GET'])
def get_queue_state():
    """Get queue state for a user/page"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        queue_type = request.args.get('queue_type')
        
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT id, user_id, page_type, queue_type, state_data, 
                       created_at, updated_at
                FROM ui_queue_state
                WHERE user_id = %s
            """
            params = [user_id]
            
            if page_type:
                query += " AND page_type = %s"
                params.append(page_type)
            
            if queue_type:
                query += " AND queue_type = %s"
                params.append(queue_type)
            
            query += " ORDER BY updated_at DESC"
            
            cursor.execute(query, params)
            queue_states = cursor.fetchall()
            
            return jsonify({
                'queue_states': [
                    {
                        'id': s['id'],
                        'user_id': s['user_id'],
                        'page_type': s['page_type'],
                        'queue_type': s['queue_type'],
                        'state_data': s['state_data'],
                        'created_at': s['created_at'].isoformat() if s['created_at'] else None,
                        'updated_at': s['updated_at'].isoformat() if s['updated_at'] else None
                    }
                    for s in queue_states
                ]
            })
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/queue-state', methods=['POST'])
def set_queue_state():
    """Set queue state"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        page_type = data.get('page_type')
        queue_type = data.get('queue_type')
        state_data = data.get('state_data')
        
        if not page_type or not queue_type:
            return jsonify({'error': True, 'message': 'page_type and queue_type are required'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ui_queue_state 
                (user_id, page_type, queue_type, state_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, page_type, queue_type) 
                DO UPDATE SET 
                    state_data = EXCLUDED.state_data,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, page_type, queue_type, json.dumps(state_data)))
            
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/state', methods=['GET'])
def get_all_state():
    """Get all state for a user/page"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        
        with db_manager.get_cursor() as cursor:
            result = {
                'user_id': user_id,
                'page_type': page_type,
                'selections': [],
                'ui_states': [],
                'workflow_states': [],
                'queue_states': []
            }
            
            # Get selections
            if page_type:
                cursor.execute("""
                    SELECT * FROM ui_selection_state 
                    WHERE user_id = %s AND page_type = %s
                """, (user_id, page_type))
            else:
                cursor.execute("""
                    SELECT * FROM ui_selection_state 
                    WHERE user_id = %s
                """, (user_id,))
            
            result['selections'] = [dict(row) for row in cursor.fetchall()]
            
            # Get UI states
            if page_type:
                cursor.execute("""
                    SELECT * FROM ui_ui_state 
                    WHERE user_id = %s AND page_type = %s
                """, (user_id, page_type))
            else:
                cursor.execute("""
                    SELECT * FROM ui_ui_state 
                    WHERE user_id = %s
                """, (user_id,))
            
            result['ui_states'] = [dict(row) for row in cursor.fetchall()]
            
            # Get workflow states
            if page_type:
                cursor.execute("""
                    SELECT * FROM ui_workflow_state 
                    WHERE user_id = %s AND page_type = %s
                """, (user_id, page_type))
            else:
                cursor.execute("""
                    SELECT * FROM ui_workflow_state 
                    WHERE user_id = %s
                """, (user_id,))
            
            result['workflow_states'] = [dict(row) for row in cursor.fetchall()]
            
            # Get queue states
            if page_type:
                cursor.execute("""
                    SELECT * FROM ui_queue_state 
                    WHERE user_id = %s AND page_type = %s
                """, (user_id, page_type))
            else:
                cursor.execute("""
                    SELECT * FROM ui_queue_state 
                    WHERE user_id = %s
                """, (user_id,))
            
            result['queue_states'] = [dict(row) for row in cursor.fetchall()]
            
            return jsonify(result)
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500

@ui_state_bp.route('/state', methods=['DELETE'])
def clear_all_state():
    """Clear all state for a user/page"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        page_type = request.args.get('page_type')
        
        with db_manager.get_cursor() as cursor:
            deleted_counts = {}
            
            # Clear selections
            if page_type:
                cursor.execute("DELETE FROM ui_selection_state WHERE user_id = %s AND page_type = %s", (user_id, page_type))
            else:
                cursor.execute("DELETE FROM ui_selection_state WHERE user_id = %s", (user_id,))
            deleted_counts['selections'] = cursor.rowcount
            
            # Clear UI states
            if page_type:
                cursor.execute("DELETE FROM ui_ui_state WHERE user_id = %s AND page_type = %s", (user_id, page_type))
            else:
                cursor.execute("DELETE FROM ui_ui_state WHERE user_id = %s", (user_id,))
            deleted_counts['ui_states'] = cursor.rowcount
            
            # Clear workflow states
            if page_type:
                cursor.execute("DELETE FROM ui_workflow_state WHERE user_id = %s AND page_type = %s", (user_id, page_type))
            else:
                cursor.execute("DELETE FROM ui_workflow_state WHERE user_id = %s", (user_id,))
            deleted_counts['workflow_states'] = cursor.rowcount
            
            # Clear queue states
            if page_type:
                cursor.execute("DELETE FROM ui_queue_state WHERE user_id = %s AND page_type = %s", (user_id, page_type))
            else:
                cursor.execute("DELETE FROM ui_queue_state WHERE user_id = %s", (user_id,))
            deleted_counts['queue_states'] = cursor.rowcount
            
            return jsonify({'success': True, 'deleted': deleted_counts})
            
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500
