from flask import Blueprint, jsonify, request, current_app
from app.llm.services import LLMService, execute_llm_request
from app.models import LLMConfig, LLMInteraction, PostSection, LLMAction, LLMPrompt, LLMActionHistory, PostDevelopment, LLMPromptPart, LLMActionPromptPart
from app import db
import requests
import traceback

bp = Blueprint('llm_api', __name__, url_prefix='/api/v1/llm')


@bp.route("/config", methods=["GET"])
def get_config():
    """Get current LLM configuration"""
    config = LLMConfig.query.first()
    if not config:
        return jsonify(
            {
                "provider_type": "ollama",
                "model_name": "mistral",
                "api_base": "http://localhost:11434",
            }
        )
    return jsonify(
        {
            "provider_type": config.provider_type,
            "model_name": config.model_name,
            "api_base": config.api_base,
        }
    )


@bp.route("/config", methods=["POST"])
def update_config():
    """Update LLM configuration"""
    data = request.get_json()

    config = LLMConfig.query.first()
    if not config:
        config = LLMConfig()
        db.session.add(config)

    config.provider_type = data.get("provider_type", config.provider_type)
    config.model_name = data.get("model_name", config.model_name)
    config.api_base = data.get("api_base", config.api_base)

    # Handle provider authentication
    if "auth_token" in data and data["auth_token"]:
        config.auth_token = data["auth_token"]

    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})


@bp.route("/test", methods=["POST"])
def test_llm():
    """Test an LLM prompt"""
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        llm = LLMService()
        result = llm.generate(data["prompt"], model_name=data.get("model_name"))
        return jsonify(result)
    except RuntimeError as e:
        if "timed out" in str(e).lower():
            current_app.logger.error(f"LLM test timeout: {e}")
            return jsonify({
                "error": "Request timed out. This could be because:\n"
                "1. The model is not loaded and loading took too long\n"
                "2. The generation request itself took too long\n"
                "Try preloading the model first or using a different model."
            }), 504  # Gateway Timeout
        current_app.logger.error(f"LLM test runtime error: {e}")
        return jsonify({"error": str(e)}), 500
    except requests.exceptions.Timeout:
        current_app.logger.error("LLM test explicit timeout")
        return jsonify({
            "error": "Request timed out while waiting for the LLM service"
        }), 504
    except Exception as e:
        current_app.logger.error(f"Unexpected error in LLM test: {type(e).__name__}: {e}")
        return jsonify({
            "error": f"An unexpected error occurred: {type(e).__name__}"
        }), 500


@bp.route('/prompts', methods=['GET'])
def get_prompts():
    """Get all prompts, ordered by 'order' (NULLs last), then id."""
    prompts = LLMPrompt.query.order_by(LLMPrompt.order.is_(None), LLMPrompt.order, LLMPrompt.id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'prompt_text': p.prompt_text
    } for p in prompts])


@bp.route("/templates", methods=["GET"])
def get_templates():
    """Get all prompt templates from LLMPrompt, ordered by 'order' (NULLs last), then id."""
    prompts = LLMPrompt.query.order_by(LLMPrompt.order.is_(None), LLMPrompt.order, LLMPrompt.id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'prompt_text': p.prompt_text
    } for p in prompts])


@bp.route("/templates/<int:template_id>", methods=["PUT"])
def update_template(template_id):
    """Update a prompt template"""
    data = request.get_json()
    template = PromptTemplate.query.get_or_404(template_id)

    template.prompt_text = data.get("prompt_text", template.prompt_text)
    template.description = data.get("description", template.description)

    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})


@bp.route('/generate-idea', methods=['POST'])
def generate_idea():
    data = request.get_json() or {}
    # Create LLMInteraction record
    interaction = LLMInteraction()
    interaction.input_text = data.get("topic", "dummy")
    db.session.add(interaction)
    db.session.commit()
    return jsonify(
        {
            "title": "Test Title",
            "outline": ["Point 1", "Point 2"],
            "keywords": ["test", "blog"],
        }
    )


@bp.route('/expand-section/<int:section_id>', methods=['POST'])
def expand_section(section_id):
    data = request.get_json() or {}
    section = PostSection.query.get(section_id)
    if section:
        section.content = "Expanded content"
        db.session.commit()
    return jsonify(
        {
            "content": "Expanded content",
            "keywords": ["expanded", "test"],
            "social_media_snippets": {"twitter": "Test tweet"},
        }
    )


@bp.route('/optimize-seo/<int:post_id>', methods=['POST'])
def optimize_seo(post_id):
    data = request.get_json() or {}
    # Return dummy data for test
    return jsonify(
        {
            "suggestions": {
                "title_suggestions": ["Better Title"],
                "meta_description": "Optimized description",
                "keyword_suggestions": ["seo", "optimization"],
            }
        }
    )


@bp.route('/generate-social/<int:section_id>', methods=['POST'])
def generate_social(section_id):
    data = request.get_json() or {}
    section = PostSection.query.get(section_id)
    if section:
        section.social_media_snippets = {
            "twitter": "Test tweet",
            "instagram": "Test instagram post",
        }
        db.session.commit()
    return jsonify({"twitter": "Test tweet", "instagram": "Test instagram post"})


@bp.route('/actions', methods=['GET', 'POST'])
def handle_actions():
    """Handle LLM actions list and creation."""
    if request.method == 'GET':
        actions = LLMAction.query.all()
        return jsonify([action.to_dict() for action in actions])
    
    data = request.get_json()
    try:
        # Validate required fields
        required_fields = ['field_name', 'prompt_template_id', 'llm_model']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'error': f'Missing required field: {field}'}), 400
        
        # Get the prompt template
        prompt_template = LLMPrompt.query.get_or_404(data['prompt_template_id'])
        
        # Create the action
        action = LLMAction(
            field_name=data['field_name'],
            prompt_template=prompt_template.prompt_text,
            prompt_template_id=prompt_template.id,
            llm_model=data['llm_model'],
            temperature=float(data.get('temperature', 0.7)),
            max_tokens=int(data.get('max_tokens', 1000))
        )
        
        db.session.add(action)
        db.session.commit()
        
        current_app.logger.info(f"Created new LLM action: {action.to_dict()}")
        return jsonify({'status': 'success', 'action': action.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error creating action: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400


@bp.route('/prompts', methods=['POST'])
def create_prompt():
    data = request.get_json()
    name = data.get('name')
    prompt_text = data.get('prompt_text')
    if not name or not prompt_text:
        return jsonify({'success': False, 'error': 'Name and prompt_text required'}), 400
    prompt = LLMPrompt(name=name, prompt_text=prompt_text, description=data.get('description', ''))
    db.session.add(prompt)
    db.session.commit()
    return jsonify({'success': True, 'prompt': {'id': prompt.id, 'name': prompt.name, 'prompt_text': prompt.prompt_text, 'description': prompt.description}})


@bp.route('/models/ollama', methods=['GET'])
def get_ollama_models():
    try:
        tags_resp = requests.get('http://localhost:11434/api/tags', timeout=3)
        tags_data = tags_resp.json()
        all_models = [m['name'] for m in tags_data.get('models', [])]
        ps_resp = requests.get('http://localhost:11434/api/ps', timeout=3)
        ps_data = ps_resp.json()
        loaded_models = [m['name'] for m in ps_data.get('models', [])]
        return jsonify({'models': all_models, 'loaded': loaded_models})
    except Exception as e:
        return jsonify({'models': [], 'loaded': [], 'error': str(e)}), 500


@bp.route('/preload', methods=['POST'])
def preload_model():
    data = request.get_json()
    model = data.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'No model specified'}), 400
    try:
        # Send a dummy prompt to load the model
        r = requests.post('http://localhost:11434/api/generate', json={
            'model': model,
            'prompt': '',
            'stream': False
        }, timeout=60)
        r.raise_for_status()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """Update an existing prompt"""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('prompt_text'):
        return jsonify({'success': False, 'error': 'Name and prompt_text required'}), 400
    
    prompt = LLMPrompt.query.get_or_404(prompt_id)
    prompt.name = data['name']
    prompt.description = data.get('description', '')
    prompt.prompt_text = data['prompt_text']
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'prompt': {
            'id': prompt.id,
            'name': prompt.name,
            'description': prompt.description,
            'prompt_text': prompt.prompt_text
        }})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """Delete a prompt"""
    prompt = LLMPrompt.query.get_or_404(prompt_id)
    try:
        db.session.delete(prompt)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """Get a single prompt by ID"""
    prompt = LLMPrompt.query.get_or_404(prompt_id)
    return jsonify({
        'id': prompt.id,
        'name': prompt.name,
        'description': prompt.description,
        'prompt_text': prompt.prompt_text
    })


@bp.route('/actions/<int:action_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_action(action_id):
    """Handle individual LLM action operations."""
    action = LLMAction.query.get_or_404(action_id)
    
    if request.method == 'GET':
        try:
            return jsonify({'status': 'success', 'action': action.to_dict()})
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 400
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Update action fields
        for field in ['field_name', 'prompt_template', 'llm_model', 'temperature', 'max_tokens']:
            if field in data:
                setattr(action, field, data[field])
        if 'prompt_template_id' in data:
            prompt_template = LLMPrompt.query.get_or_404(data['prompt_template_id'])
            action.prompt_template_id = prompt_template.id
            action.prompt_template = prompt_template.prompt_text
        
        try:
            db.session.commit()
            return jsonify({'status': 'success', 'action': action.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(action)
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'error': str(e)}), 400


@bp.route('/actions/<int:action_id>/execute', methods=['POST'])
def execute_action(action_id):
    """Execute an LLM action with robust debug logging."""
    action = LLMAction.query.get_or_404(action_id)
    data = request.get_json()
    current_app.logger.debug(f"[LLM EXECUTE] Action ID: {action_id}, Incoming data: {data}")
    
    if not data or 'input_text' not in data:
        current_app.logger.warning(f"[LLM EXECUTE] No input_text provided for action {action_id}.")
        return jsonify({'error': 'No input text provided'}), 400
    
    try:
        post_id = data.get('post_id')
        fields = {'input': data['input_text']}
        # If post_id is provided, fetch all PostDevelopment fields
        if post_id:
            dev = PostDevelopment.query.filter_by(post_id=post_id).first()
            if dev:
                for c in dev.__table__.columns:
                    if c.name not in ['id', 'post_id']:
                        fields[c.name] = getattr(dev, c.name)
        # PATCH: Merge in section_fields if provided
        section_fields = data.get('section_fields')
        if section_fields and isinstance(section_fields, dict):
            fields.update(section_fields)
        current_app.logger.debug(f"[LLM EXECUTE] Final fields for action {action_id}: {fields}")
        llm = LLMService()
        result = llm.execute_action(
            action=action,
            fields=fields,
            post_id=post_id
        )
        current_app.logger.info(f"[LLM EXECUTE] Action {action_id} executed successfully.")
        return jsonify(result)
    except ValueError as e:
        current_app.logger.error(f"[LLM EXECUTE] ValueError executing action {action_id}: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"[LLM EXECUTE] Exception executing action {action_id}: {str(e)}\n{traceback.format_exc()} | Data: {data}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/actions/<int:action_id>/history')
def action_history(action_id):
    """Get the history for a specific LLM action."""
    action = LLMAction.query.get_or_404(action_id)
    history = LLMActionHistory.query.filter_by(action_id=action_id).order_by(LLMActionHistory.created_at.desc()).all()
    return jsonify({
        'action': action.to_dict(),
        'history': [h.to_dict() for h in history]
    })


@bp.route('/actions/debug/list_templates', methods=['GET'])
def debug_list_llm_templates():
    """Debug: List all LLMAction prompt templates."""
    actions = LLMAction.query.all()
    return jsonify([
        {
            'id': a.id,
            'field_name': a.field_name,
            'prompt_template': a.prompt_template
        } for a in actions
    ])


@bp.route('/prompts/order', methods=['POST'])
def update_prompt_order():
    """Update the order of prompt templates."""
    data = request.get_json()
    ids = data.get('order', [])
    if not isinstance(ids, list):
        return jsonify({'success': False, 'error': 'Invalid order list'}), 400
    try:
        for idx, prompt_id in enumerate(ids):
            prompt = LLMPrompt.query.get(int(prompt_id))
            if prompt:
                prompt.order = idx
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/actions/order', methods=['POST'])
def update_action_order():
    """Update the order of LLM actions."""
    data = request.get_json()
    ids = data.get('order', [])
    if not isinstance(ids, list):
        return jsonify({'success': False, 'error': 'Invalid order list'}), 400
    try:
        for idx, action_id in enumerate(ids):
            action = LLMAction.query.get(int(action_id))
            if action:
                action.order = idx
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/prompt_parts', methods=['GET', 'POST'])
def handle_prompt_parts():
    if request.method == 'GET':
        parts = LLMPromptPart.query.order_by(LLMPromptPart.order, LLMPromptPart.id).all()
        return jsonify([{
            'id': p.id,
            'type': p.type,
            'content': p.content,
            'description': p.description,
            'tags': p.tags,
            'order': p.order,
            'created_at': p.created_at,
            'updated_at': p.updated_at
        } for p in parts])
    if request.method == 'POST':
        data = request.get_json()
        part = LLMPromptPart(
            type=data['type'],
            content=data['content'],
            description=data.get('description'),
            tags=data.get('tags', []),
            order=data.get('order', 0)
        )
        db.session.add(part)
        db.session.commit()
        return jsonify({'status': 'success', 'part': part.id})


@bp.route('/prompt_parts/<int:part_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_prompt_part(part_id):
    part = LLMPromptPart.query.get_or_404(part_id)
    if request.method == 'GET':
        return jsonify({
            'id': part.id,
            'type': part.type,
            'content': part.content,
            'description': part.description,
            'tags': part.tags,
            'order': part.order,
            'created_at': part.created_at,
            'updated_at': part.updated_at
        })
    if request.method == 'PUT':
        data = request.get_json()
        part.type = data.get('type', part.type)
        part.content = data.get('content', part.content)
        part.description = data.get('description', part.description)
        part.tags = data.get('tags', part.tags)
        part.order = data.get('order', part.order)
        db.session.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        db.session.delete(part)
        db.session.commit()
        return jsonify({'status': 'success'})


@bp.route('/actions/<int:action_id>/prompt_parts', methods=['GET', 'POST'])
def action_prompt_parts(action_id):
    if request.method == 'GET':
        links = LLMActionPromptPart.query.filter_by(action_id=action_id).order_by(LLMActionPromptPart.order).all()
        return jsonify([{
            'prompt_part_id': l.prompt_part_id,
            'order': l.order,
            'type': l.prompt_part.type,
            'content': l.prompt_part.content,
            'description': l.prompt_part.description,
            'tags': l.prompt_part.tags
        } for l in links])
    if request.method == 'POST':
        data = request.get_json()
        link = LLMActionPromptPart(
            action_id=action_id,
            prompt_part_id=data['prompt_part_id'],
            order=data.get('order', 0)
        )
        db.session.add(link)
        db.session.commit()
        return jsonify({'status': 'success'})


@bp.route('/actions/<int:action_id>/prompt_parts/<int:part_id>', methods=['PUT', 'DELETE'])
def update_action_prompt_part(action_id, part_id):
    link = LLMActionPromptPart.query.filter_by(action_id=action_id, prompt_part_id=part_id).first_or_404()
    if request.method == 'PUT':
        data = request.get_json()
        link.order = data.get('order', link.order)
        db.session.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        db.session.delete(link)
        db.session.commit()
        return jsonify({'status': 'success'})
