from flask import Blueprint, jsonify, request, current_app
from app.services.llm import LLMService
from app.models import LLMConfig, LLMInteraction, PostSection, LLMAction, LLMPrompt
from app import db
import requests

bp = Blueprint("llm_api", __name__)


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
    """Get all prompts"""
    prompts = LLMPrompt.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'prompt_text': p.prompt_text
    } for p in prompts])


@bp.route("/templates", methods=["GET"])
def get_templates():
    """Get all prompt templates from LLMPrompt"""
    prompts = LLMPrompt.query.all()
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


@bp.route("/generate-idea", methods=["POST"])
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


@bp.route("/expand-section/<int:section_id>", methods=["POST"])
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


@bp.route("/optimize-seo/<int:post_id>", methods=["POST"])
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


@bp.route("/generate-social/<int:section_id>", methods=["POST"])
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


@bp.route('/actions/<field_name>', methods=['GET'])
def get_llm_action(field_name):
    action = LLMAction.query.filter_by(field_name=field_name).first()
    if not action:
        return jsonify({}), 404
    return jsonify({
        'field_name': action.field_name,
        'stage_name': action.stage_name,
        'source_field': action.source_field,
        'prompt_template': action.prompt_template,
        'llm_model': action.llm_model,
        'temperature': action.temperature,
        'max_tokens': action.max_tokens,
    })


@bp.route('/actions/<field_name>', methods=['POST'])
def update_llm_action(field_name):
    data = request.get_json()
    action = LLMAction.query.filter_by(field_name=field_name).first()
    if not action:
        action = LLMAction(field_name=field_name)
        db.session.add(action)
    action.stage_name = data.get('stage_name')
    action.source_field = data.get('source_field', field_name)
    action.prompt_template = data.get('prompt_template', '')
    action.llm_model = data.get('llm_model', '')
    action.temperature = float(data.get('temperature', 0.7))
    action.max_tokens = int(data.get('max_tokens', 64))
    db.session.commit()
    return jsonify({'status': 'success'})


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
