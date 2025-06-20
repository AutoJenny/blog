# MIGRATION: This file is being refactored to use direct SQL (psycopg2) instead of ORM models.

"""Routes for LLM-powered content generation and enhancement."""

print('DEBUG: Loaded app/llm/routes.py from', __file__)
from flask import jsonify, request, current_app, render_template, redirect, url_for
import logging
from app.llm import bp
from app.llm.services import execute_llm_request
import httpx
from app.blog.fields import WORKFLOW_FIELDS
import psycopg2
import psycopg2.extras
from app.database.routes import get_db_conn
import requests

logger = logging.getLogger(__name__)
# All ORM model imports removed. Use direct SQL via psycopg2 for any DB access.

@bp.route("/")
def index():
    """Redirect to config page."""
    return redirect(url_for('llm.config_page'))

@bp.route("/config")
def config_page():
    """LLM configuration interface."""
    return render_template("llm/config.html", config=None)

@bp.route('/templates')
def templates():
    """Show prompt templates"""
    prompts = []  # TODO: Replace with direct SQL query for prompt templates
    logger.info(f"RAW WORKFLOW_FIELDS: {WORKFLOW_FIELDS}")
    def clean_workflow_fields(fields):
        return {
            stage.replace('\n', ' ').replace('\r', ' '): [
                f.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
                for f in field_list
            ]
            for stage, field_list in fields.items()
        }
    clean_fields = clean_workflow_fields(WORKFLOW_FIELDS)
    logger.info(f"CLEANED WORKFLOW_FIELDS: {clean_fields}")
    return render_template('llm/templates.html', prompts=prompts, workflow_fields=clean_fields)

@bp.route('/actions')
def actions():
    """Render the LLM Actions management page."""
    actions = []
    prompts = []
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM llm_action ORDER BY id")
            actions = cur.fetchall()
            cur.execute("SELECT * FROM llm_prompt ORDER BY id")
            prompts = cur.fetchall()
    return render_template(
        'llm/actions.html',
        actions=actions,
        prompts=prompts,
        workflow_fields=WORKFLOW_FIELDS
    )

@bp.route('/actions/<int:action_id>')
def action_detail(action_id):
    action = None
    action_prompt_parts = []
    all_prompt_parts = []
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM llm_action WHERE id = %s
            """, (action_id,))
            action = cur.fetchone()
            cur.execute("""
                SELECT * FROM llm_prompt_part ORDER BY "order", id
            """)
            all_prompt_parts = cur.fetchall()
    return render_template('llm/action_detail.html', action=action, action_prompt_parts=action_prompt_parts, all_prompt_parts=all_prompt_parts)

@bp.route('/api/v1/llm/test', methods=['POST'])
def test_llm_action():
    """Test an LLM action with provided input."""
    try:
        data = request.get_json()
        logger.info(f"[TEST ENDPOINT] Raw request data received: {data}")
        
        if not data:
            logger.error("[TEST ENDPOINT] No request data provided")
            return jsonify({'error': 'No request data provided'}), 400
            
        # Validate required fields
        required_fields = ['prompt', 'model_name', 'input']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"[TEST ENDPOINT] Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            
        # Log individual fields for debugging
        logger.info(f"[TEST ENDPOINT] Prompt template: '{data.get('prompt', '')}'")
        logger.info(f"[TEST ENDPOINT] Input text: '{data.get('input', '')}'")
        logger.info(f"[TEST ENDPOINT] Model name: {data.get('model_name', '')}")
        logger.info(f"[TEST ENDPOINT] Temperature: {data.get('temperature', 0.7)}")
            
        # Get the configuration
        config = None
        if not config:
            logger.error("[TEST ENDPOINT] LLM configuration not found")
            return jsonify({'error': 'LLM configuration not found'}), 500
            
        logger.info(f"[TEST ENDPOINT] Using LLM config: {config}")
            
        # Format the prompt with the input
        try:
            input_text = data['input'].strip()
            prompt_template = data['prompt'].strip()
            
            logger.info(f"[TEST ENDPOINT] Cleaned input: '{input_text}'")
            logger.info(f"[TEST ENDPOINT] Cleaned prompt: '{prompt_template}'")
            
            # Prepare the request
            llm_request = {
                'model_name': data['model_name'],
                'temperature': data.get('temperature', 0.7),
                'max_tokens': data.get('max_tokens', 2000),
                'prompt': prompt_template,
                'input': input_text
            }
            
            logger.info(f"[TEST ENDPOINT] Sending to LLM service: {llm_request}")
            
            # Execute the request
            result = execute_llm_request(llm_request)
            logger.info(f"[TEST ENDPOINT] Received from LLM service: {result}")
            
            if 'error' in result:
                logger.error(f"[TEST ENDPOINT] Error from LLM service: {result['error']}")
                return jsonify({'error': result['error']}), 500
                
            if not result.get('response'):
                logger.error(f"[TEST ENDPOINT] No output generated for request: {llm_request}")
                return jsonify({'error': 'No output generated by the LLM service'}), 500
                
            # Return the response
            logger.info(f"[TEST ENDPOINT] Successfully generated output: {result['response'][:100]}...")
            return jsonify({
                'model_used': result['model_used'],
                'response': result['response']
            }), 200
            
        except Exception as e:
            logger.error(f"[TEST ENDPOINT] Error formatting prompt: {str(e)}", exc_info=True)
            return jsonify({'error': 'Error formatting prompt with input'}), 500
            
    except Exception as e:
        logger.exception("[TEST ENDPOINT] Unexpected error testing LLM action")
        return jsonify({'error': str(e)}), 500

@bp.route('/test')
def test_page():
    """Dead simple prompt testing interface."""
    prompts = []  # TODO: Replace with direct SQL query for prompt templates
    return render_template('llm/test.html', config=None, prompts=prompts)

@bp.route('/api/test', methods=['POST'])
def test_prompt():
    """Test a prompt template with input data."""
    try:
        data = request.get_json()
        logger.info(f"[TEST] Received request: {data}")
        
        # Validate input
        if not data or 'prompt_id' not in data or 'input' not in data:
            logger.error("[TEST] Missing required fields in request")
            return jsonify({'error': 'Missing prompt_id or input'}), 400
            
        # Get the prompt template
        prompt = None  # TODO: Replace with direct SQL query for prompt
        if not prompt:
            logger.error(f"[TEST] Prompt template not found for ID: {data['prompt_id']}")
            return jsonify({'error': 'Prompt template not found'}), 404
            
        # Get LLM config
        config = None
        if not config:
            logger.error("[TEST] LLM configuration not found")
            return jsonify({'error': 'LLM configuration not found'}), 500
            
        # Log what we're about to do
        logger.info(f"[TEST] Template name: {prompt.name}")
        logger.info(f"[TEST] Template text: {prompt.prompt_text}")
        logger.info(f"[TEST] Input data: {data['input']}")
        
        # Validate template has placeholder
        if '{{input}}' not in prompt.prompt_text:
            logger.error(f"[TEST] Template missing {{input}} placeholder: {prompt.prompt_text}")
            return jsonify({'error': 'Invalid prompt template - missing {{input}} placeholder'}), 400
        
        # Combine template and input
        final_prompt = prompt.prompt_text.replace('{{input}}', data['input'])
        logger.info(f"[TEST] Final prompt to send to LLM: {final_prompt}")
        
        # Call LLM
        logger.info(f"[TEST] Calling LLM at {config.api_base} with model {config.model_name}")
        response = httpx.post(
            f"{config.api_base}/api/generate",
            json={
                "model": data.get('model', config.model_name),
                "prompt": final_prompt,
                "stream": False
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            logger.error(f"[TEST] LLM error: {response.text}")
            return jsonify({'error': 'LLM service error'}), 500
            
        result = response.json()
        if 'response' not in result:
            logger.error(f"[TEST] Invalid LLM response: {result}")
            return jsonify({'error': 'Invalid response from LLM'}), 500
            
        logger.info(f"[TEST] Success! Response: {result['response'][:100]}...")
        return jsonify({'response': result['response']}), 200
        
    except Exception as e:
        logger.exception("[TEST] Error")
        return jsonify({'error': str(e)}), 500

@bp.route('/')
def llm_index():
    return render_template('llm/index.html')

@bp.route('/images')
def llm_images():
    return render_template('llm/images.html')

@bp.route('/images/configs')
def llm_images_configs():
    return render_template('llm/images_configs.html')

@bp.route('/images/prompts')
def llm_images_prompts():
    return render_template('llm/images_prompts.html')

@bp.route('/images/previews')
def llm_images_previews():
    return render_template('llm/images_previews.html')

@bp.route('/api/v1/llm/models', methods=['GET'])
def api_llm_models():
    # Fetch models live from Ollama
    try:
        resp = requests.get('http://localhost:11434/api/tags', timeout=3)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for idx, m in enumerate(data.get('models', []), 1):
            models.append({
                'id': idx,
                'name': m.get('name'),
                'provider_id': 1,
                'description': f"Ollama {m.get('name')} (local)"
            })
        return jsonify(models)
    except Exception as e:
        return jsonify([])

@bp.route('/api/v1/llm/providers', methods=['GET'])
def api_llm_providers():
    # Only Ollama local provider for now
    providers = [
        {"id": 1, "name": "Ollama (local)"}
    ]
    return jsonify(providers)

@bp.route('/api/v1/llm/actions/<int:action_id>', methods=['GET'])
def api_llm_action_detail(action_id):
    try:
        logger.info(f"[API] Fetching LLM action detail for id={action_id}")
        action = None
        prompt_parts = []
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM llm_action WHERE id = %s", (action_id,))
                action = cur.fetchone()
                logger.info(f"[API] SQL result for action: {action}")
                if action:
                    cur.execute("""
                        SELECT p.*
                        FROM llm_action_prompt_part l
                        JOIN llm_prompt_part p ON l.prompt_part_id = p.id
                        WHERE l.action_id = %s
                        ORDER BY l.order, l.prompt_part_id
                    """, (action_id,))
                    prompt_parts = cur.fetchall()
                    logger.info(f"[API] SQL result for prompt_parts: {prompt_parts}")
        if not action:
            logger.error(f"[API] Action not found for id={action_id}")
            return jsonify({'error': 'Action not found'}), 404
        # Ensure all required fields are present
        required_fields = ['id', 'field_name', 'llm_model', 'prompt_template', 'temperature', 'max_tokens']
        for field in required_fields:
            if field not in action or action[field] is None:
                logger.error(f"[API] Action missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 500
        action['prompt_parts'] = prompt_parts
        return jsonify({'action': action})
    except Exception as e:
        logger.exception(f"[API] Exception in api_llm_action_detail for id={action_id}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
