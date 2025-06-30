"""LLM actions API."""

from flask import Blueprint, jsonify, request, current_app
from app.database import get_db_conn
from app.services.llm import execute_llm_request

bp = Blueprint('llm_actions', __name__)

@bp.route('/actions', methods=['GET'])
def get_actions():
    """Get all LLM actions for a substage."""
    substage = request.args.get('substage')
    if not substage:
        return jsonify({'error': 'No substage provided'}), 400
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.* 
                    FROM llm_action a
                    JOIN workflow_sub_stage_entity s ON s.id = a.substage_id
                    WHERE s.name = %s
                    ORDER BY a.order
                """, (substage,))
                actions = [dict(row) for row in cur.fetchall()]
                return jsonify(actions)
    except Exception as e:
        current_app.logger.error(f"Error getting actions for substage {substage}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/actions/<int:action_id>/execute', methods=['POST'])
def execute_action(action_id):
    """Execute an LLM action."""
    try:
        # Get action configuration
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM llm_action WHERE id = %s
                """, (action_id,))
                action = cur.fetchone()
                if not action:
                    return jsonify({'error': 'Action not found'}), 404
        
        # Get input data
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({'error': 'No input provided'}), 400
        
        # Get LLM provider and settings
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, type, api_url, auth_token 
                    FROM llm_provider 
                    WHERE is_active = true 
                    LIMIT 1
                """)
                provider = cur.fetchone()
                if not provider:
                    return jsonify({'error': 'No active LLM provider found'}), 500
                cur.execute("""
                    SELECT name FROM llm_model WHERE name = %s AND provider_id = %s
                """, (action['llm_model'], provider['id']))
                model = cur.fetchone()
                if not model:
                    return jsonify({'error': 'Model not found for this provider'}), 500
        
        # Format prompt
        prompt = action['prompt_template']
        if '[data:input]' in prompt:
            prompt = prompt.replace('[data:input]', data['input'])
        else:
            prompt = prompt.format(input=data['input'])
        
        # Call LLM
        try:
            response = execute_llm_request(
                provider=provider['type'],
                model=model['name'],
                prompt=prompt,
                temperature=action.get('temperature', 0.7),
                max_tokens=action.get('max_tokens', 1000),
                api_key=provider['auth_token'],
                api_endpoint=provider['api_url']
            )
            current_app.logger.debug(f"Raw LLM response: {response}")
        except Exception as e:
            current_app.logger.error(f"Error in execute_llm_request: {str(e)}")
            raise
        
        # Process output
        result = {'output': response['result']}
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Error executing action {action_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/actions/<int:action_id>/test', methods=['POST'])
@jwt_required()
def test_action(action_id):
    """Test an LLM action with the provided input."""
    try:
        # Get action configuration
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM llm_action WHERE id = %s
                """, (action_id,))
                action = cur.fetchone()
                if not action:
                    return jsonify({'error': 'Action not found'}), 404

        # Get input data
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({'error': 'No input provided'}), 400

        # Validate input fields
        input_data = data['input']
        if 'idea_seed' not in input_data:
            return jsonify({'error': 'Missing required input field: idea_seed'}), 400

        # Get LLM provider and settings
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, type, api_url, auth_token 
                    FROM llm_provider 
                    WHERE is_active = true 
                    LIMIT 1
                """)
                provider = cur.fetchone()
                if not provider:
                    return jsonify({'error': 'No active LLM provider found'}), 500
                cur.execute("""
                    SELECT name FROM llm_model WHERE name = %s AND provider_id = %s
                """, (action['llm_model'], provider['id']))
                model = cur.fetchone()
                if not model:
                    return jsonify({'error': 'Model not found for this provider'}), 500

        # Format prompt
        prompt = action['prompt_template']
        if '[data:idea_seed]' in prompt:
            prompt = prompt.replace('[data:idea_seed]', input_data['idea_seed'])
        else:
            prompt = prompt.format(**input_data)

        # Call LLM
        try:
            response = execute_llm_request(
                provider=provider['type'],
                model=model['name'],
                prompt=prompt,
                temperature=action.get('temperature', 0.7),
                max_tokens=action.get('max_tokens', 1000),
                api_key=provider['auth_token'],
                api_endpoint=provider['api_url']
            )
            current_app.logger.debug(f"Raw LLM response: {response}")
        except Exception as e:
            current_app.logger.error(f"Error in execute_llm_request: {str(e)}")
            raise

        # Process output
        result = {'result': response['result']}
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error testing action {action_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500 