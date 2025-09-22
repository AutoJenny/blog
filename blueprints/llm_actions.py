# blueprints/llm_actions.py
from flask import Blueprint, render_template, jsonify, request
import logging
import json
import os
import requests
from datetime import datetime
from config.database import db_manager

bp = Blueprint('llm_actions', __name__)
logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'name': 'OpenAI',
                'base_url': 'https://api.openai.com/v1',
                'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
            },
            'ollama': {
                'name': 'Ollama',
                'base_url': 'http://localhost:11434',
                'models': ['llama2', 'codellama', 'mistral']
            }
        }
    
    def get_available_models(self, provider='openai'):
        """Get available models for a provider."""
        try:
            if provider == 'ollama':
                response = requests.get(f"{self.providers[provider]['base_url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = [model['name'] for model in response.json().get('models', [])]
                    return models
            return self.providers.get(provider, {}).get('models', [])
        except Exception as e:
            logger.error(f"Error getting models for {provider}: {e}")
            return []
    
    def execute_llm_request(self, provider, model, messages, api_key=None):
        """Execute LLM request."""
        try:
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
            elif provider == 'ollama':
                data = {
                    'model': model,
                    'messages': messages,
                    'stream': False
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=60
                )
            else:
                return {'error': f'Unknown provider: {provider}'}
            
            if response.status_code == 200:
                result = response.json()
                if provider == 'openai':
                    return {'content': result['choices'][0]['message']['content']}
                elif provider == 'ollama':
                    return {'content': result['message']['content']}
            else:
                return {'error': f'API request failed: {response.status_code} - {response.text}'}
                
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return {'error': str(e)}

# Initialize LLM service
llm_service = LLMService()

@bp.route('/')
def index():
    """Main LLM Actions interface with context support."""
    # Get context parameters from request
    stage = request.args.get('stage', 'planning')
    substage = request.args.get('substage', 'idea')
    step = request.args.get('step', 'basic_idea')
    post_id = request.args.get('post_id', '1')
    step_id = request.args.get('step_id')
    
    # If step_id not provided, try to get it from database
    if not step_id:
        try:
            with db_manager.get_cursor() as cursor:
                # Convert step name from URL format to database format
                db_step_name = step.replace('_', ' ').title()
                
                cursor.execute("""
                    SELECT ws.id as step_id
                    FROM workflow_stage_entity s
                    JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                    JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
                    WHERE s.name ILIKE %s
                    AND ss.name ILIKE %s
                    AND ws.name ILIKE %s
                """, (stage, substage, db_step_name))
                result = cursor.fetchone()
                if result:
                    step_id = result['step_id']
        except Exception as e:
            logger.warning(f"Could not get step_id: {str(e)}")
    
    # Pass context to template
    context = {
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step,
        'current_post_id': post_id,
        'current_step_id': step_id
    }
    
    return render_template('llm_actions/index.html', **context)

@bp.route('/api/step-config/<stage>/<substage>/<step>', methods=['GET'])
def get_step_config(stage, substage, step):
    """Get step configuration for LLM actions."""
    try:
        with db_manager.get_cursor() as cursor:
            # Convert step name from URL format to database format
            db_step_name = step.replace('_', ' ').title()
            
            cursor.execute("""
                SELECT ws.id, ws.name, ws.description, ws.config
                FROM workflow_stage_entity s
                JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
                WHERE s.name ILIKE %s
                AND ss.name ILIKE %s
                AND ws.name ILIKE %s
            """, (stage, substage, db_step_name))
            result = cursor.fetchone()
            
            if result:
                # Handle config - it might already be a dict or a JSON string
                if isinstance(result['config'], dict):
                    config = result['config']
                elif isinstance(result['config'], str):
                    try:
                        config = json.loads(result['config'])
                    except json.JSONDecodeError:
                        config = {}
                else:
                    config = {}
                
                return jsonify({
                    'step_id': result['id'],
                    'step_name': result['name'],
                    'description': result['description'],
                    'config': config
                })
            else:
                return jsonify({'error': 'Step not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting step config: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/providers', methods=['GET'])
def get_providers():
    """Get available LLM providers."""
    try:
        providers = []
        for key, provider in llm_service.providers.items():
            providers.append({
                'id': key,
                'name': provider['name'],
                'base_url': provider['base_url'],
                'models': llm_service.get_available_models(key)
            })
        return jsonify(providers)
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/actions', methods=['GET'])
def get_actions():
    """Get all LLM actions/prompts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT lp.id, lp.name, lp.description, 
                       COALESCE(lp.system_prompt, '') as system_prompt,
                       COALESCE(lp.prompt_text, '') as prompt_text
                FROM llm_prompt lp
                WHERE lp.system_prompt IS NULL OR lp.system_prompt = ''
                ORDER BY lp.name
            """)
            task_prompts = cursor.fetchall()

            return jsonify({
                'task_prompts': [dict(prompt) for prompt in task_prompts]
            })
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/actions/<int:action_id>/execute', methods=['POST'])
def execute_action(action_id):
    """Execute a specific LLM action."""
    try:
        data = request.get_json()
        input_data = data.get('input_data', {})
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'llama2')
        
        # Get action details
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT name, description, prompt_text, system_prompt
                FROM llm_prompt
                WHERE id = %s
            """, (action_id,))
            action = cursor.fetchone()
            
            if not action:
                return jsonify({'error': 'Action not found'}), 404
            
            # Build messages
            messages = []
            if action['system_prompt']:
                messages.append({'role': 'system', 'content': action['system_prompt']})
            
            # Process prompt template with input data
            prompt = action['prompt_text']
            for key, value in input_data.items():
                prompt = prompt.replace(f'{{{key}}}', str(value))
            
            messages.append({'role': 'user', 'content': prompt})
            
            # Execute LLM request
            result = llm_service.execute_llm_request(provider, model, messages)
            
            return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'llm-actions'})