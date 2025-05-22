"""Routes for LLM-powered content generation and enhancement."""

from flask import jsonify, request, current_app, render_template, redirect, url_for
import logging
from app.models import Post, PostSection, LLMPrompt, LLMInteraction, LLMConfig, db, LLMAction, LLMActionHistory
from datetime import datetime
from app.llm import bp
from app.llm.services import execute_llm_request
import httpx
from app.blog.fields import WORKFLOW_FIELDS

logger = logging.getLogger(__name__)

@bp.route("/")
def index():
    """Redirect to config page."""
    return redirect(url_for('llm.config_page'))

@bp.route("/config")
def config_page():
    """LLM configuration interface."""
    config = LLMConfig.query.first()
    return render_template("llm/config.html", config=config)

@bp.route('/templates')
def templates():
    """Show prompt templates"""
    prompts = LLMPrompt.query.order_by(LLMPrompt.order.is_(None), LLMPrompt.order, LLMPrompt.id).all()
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
    actions = [action.to_dict() for action in LLMAction.query.all()]
    logger.info(f"[ACTIONS] Loaded {len(actions)} actions: {actions}")
    prompts = LLMPrompt.query.order_by(LLMPrompt.order.is_(None), LLMPrompt.order, LLMPrompt.id).all()
    config = LLMConfig.query.first()
    if not config:
        config = LLMConfig(
            provider_type="ollama",
            model_name="mistral",
            api_base="http://localhost:11434"
        )
        db.session.add(config)
        db.session.commit()
    return render_template(
        'llm/actions.html',
        actions=actions,
        prompts=prompts,
        config=config,
        workflow_fields=WORKFLOW_FIELDS
    )

@bp.route('/actions/<int:action_id>')
def action_detail(action_id):
    action = LLMAction.query.get_or_404(action_id)
    return render_template('llm/action_detail.html', action=action)

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
        config = LLMConfig.query.first()
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
    config = LLMConfig.query.first()
    prompts = LLMPrompt.query.all()
    return render_template('llm/test.html', config=config, prompts=prompts)

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
        prompt = LLMPrompt.query.get(data['prompt_id'])
        if not prompt:
            logger.error(f"[TEST] Prompt template not found for ID: {data['prompt_id']}")
            return jsonify({'error': 'Prompt template not found'}), 404
            
        # Get LLM config
        config = LLMConfig.query.first()
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
