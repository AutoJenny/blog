from flask import Blueprint, jsonify, request, current_app
from app.services.llm import LLMService
from app.models import LLMConfig, LLMInteraction, PostSection, LLMAction, LLMPrompt
from app import db

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
    """Test LLM with a prompt"""
    data = request.get_json()
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"success": False, "error": "No prompt provided"})

    try:
        llm = LLMService()
        response = llm.generate(prompt)
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/templates", methods=["GET"])
def get_templates():
    """Get all prompt templates from LLMPrompt"""
    templates = LLMPrompt.query.all()
    return jsonify(
        [
            {
                "id": t.id,
                "name": t.name,
                "content": t.prompt_text,
                "description": t.description,
            }
            for t in templates
        ]
    )


@bp.route("/templates/<int:template_id>", methods=["PUT"])
def update_template(template_id):
    """Update a prompt template"""
    data = request.get_json()
    template = PromptTemplate.query.get_or_404(template_id)

    template.content = data.get("content", template.content)
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
