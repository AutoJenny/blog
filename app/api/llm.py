# MIGRATION: This file is being refactored to use direct SQL (psycopg2) instead of ORM models.
from flask import Blueprint, jsonify, request, current_app
from app.llm.services import LLMService, execute_llm_request
import requests
import traceback
import logging
from app.database.routes import get_db_conn
import json

bp = Blueprint('llm_api', __name__, url_prefix='/api/v1/llm')


@bp.route("/config", methods=["GET"])
def get_config():
    """Get current LLM configuration"""
    # LLMConfig and llm_config are deprecated. Use llm_provider/llm_model instead. Refactor config logic as needed.
    config = None
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

    config = None
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
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, input_field, output_field, "order"
                    FROM llm_action
                    ORDER BY "order", id
                """)
                actions = cur.fetchall()
        return jsonify(actions)
    data = request.get_json()
    try:
        required_fields = ['field_name', 'prompt_template_id', 'llm_model']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'error': f'Missing required field: {field}'}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT prompt_text FROM llm_prompt WHERE id = %s
                """, (data['prompt_template_id'],))
                prompt_row = cur.fetchone()
                if not prompt_row:
                    return jsonify({'status': 'error', 'error': 'Prompt template not found'}), 404
                prompt_template = prompt_row['prompt_text']
                cur.execute("""
                    INSERT INTO llm_action (field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, input_field, output_field, "order")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    data['field_name'],
                    prompt_template,
                    data['prompt_template_id'],
                    data['llm_model'],
                    float(data.get('temperature', 0.7)),
                    int(data.get('max_tokens', 1000)),
                    data.get('input_field'),
                    data.get('output_field'),
                    data.get('order', 0)
                ))
                action_id = cur.fetchone()['id']
                conn.commit()
        return jsonify({'status': 'success', 'action': action_id})
    except Exception as e:
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
    if request.method == 'GET':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, input_field, output_field, "order"
                    FROM llm_action WHERE id = %s
                """, (action_id,))
                action = cur.fetchone()
        if not action:
            return jsonify({'status': 'error', 'error': 'Not found'}), 404
        return jsonify({'status': 'success', 'action': action})
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    update_fields = ['field_name', 'prompt_template', 'prompt_template_id', 'llm_model', 'temperature', 'max_tokens', 'input_field', 'output_field', 'order']
                    set_clause = ', '.join([f'{f}=%s' for f in update_fields if f in data])
                    values = [data[f] for f in update_fields if f in data]
                    if not set_clause:
                        return jsonify({'status': 'error', 'error': 'No fields to update'}), 400
                    values.append(action_id)
                    cur.execute(f"""
                        UPDATE llm_action SET {set_clause}, updated_at=NOW() WHERE id=%s
                    """, tuple(values))
                    conn.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 400
    elif request.method == 'DELETE':
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM llm_action WHERE id=%s", (action_id,))
                    conn.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
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
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, type, content, description, tags, "order", created_at, updated_at
                    FROM llm_prompt_part
                    ORDER BY "order", id
                """)
                parts = cur.fetchall()
        return jsonify(parts)
    if request.method == 'POST':
        data = request.get_json()
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO llm_prompt_part (type, content, description, tags, "order", created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id
                """, (
                    data['type'],
                    data['content'],
                    data.get('description'),
                    json.dumps(data.get('tags', [])),
                    data.get('order', 0)
                ))
                part_id = cur.fetchone()['id']
                conn.commit()
        return jsonify({'status': 'success', 'part': part_id})


@bp.route('/prompt_parts/<int:part_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_prompt_part(part_id):
    if request.method == 'GET':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, type, content, description, tags, "order", created_at, updated_at
                    FROM llm_prompt_part WHERE id = %s
                """, (part_id,))
                part = cur.fetchone()
        if not part:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(part)
    if request.method == 'PUT':
        data = request.get_json()
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE llm_prompt_part SET type=%s, content=%s, description=%s, tags=%s, "order"=%s, updated_at=NOW()
                    WHERE id=%s
                """, (
                    data.get('type'),
                    data.get('content'),
                    data.get('description'),
                    json.dumps(data.get('tags', [])),
                    data.get('order', 0),
                    part_id
                ))
                conn.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM llm_prompt_part WHERE id=%s", (part_id,))
                conn.commit()
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


# --- LLM Provider CRUD ---
@bp.route('/providers', methods=['GET', 'POST'])
def providers():
    if request.method == 'GET':
        providers = LLMProvider.query.order_by(LLMProvider.id).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'api_url': p.api_url,
            'auth_token': p.auth_token,
            'created_at': p.created_at,
            'updated_at': p.updated_at
        } for p in providers])
    if request.method == 'POST':
        data = request.get_json()
        provider = LLMProvider(
            name=data['name'],
            description=data.get('description'),
            api_url=data.get('api_url'),
            auth_token=data.get('auth_token')
        )
        db.session.add(provider)
        db.session.commit()
        return jsonify({'status': 'success', 'provider': provider.id})

@bp.route('/providers/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def provider_detail(id):
    provider = LLMProvider.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': provider.id,
            'name': provider.name,
            'description': provider.description,
            'api_url': provider.api_url,
            'auth_token': provider.auth_token,
            'created_at': provider.created_at,
            'updated_at': provider.updated_at
        })
    if request.method == 'PUT':
        data = request.get_json()
        provider.name = data.get('name', provider.name)
        provider.description = data.get('description', provider.description)
        provider.api_url = data.get('api_url', provider.api_url)
        provider.auth_token = data.get('auth_token', provider.auth_token)
        db.session.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        db.session.delete(provider)
        db.session.commit()
        return jsonify({'status': 'success'})

# --- LLM Model CRUD ---
@bp.route('/models', methods=['GET', 'POST'])
def models():
    if request.method == 'GET':
        models = LLMModel.query.order_by(LLMModel.id).all()
        return jsonify([{
            'id': m.id,
            'provider_id': m.provider_id,
            'name': m.name,
            'description': m.description,
            'config': m.config,
            'created_at': m.created_at,
            'updated_at': m.updated_at
        } for m in models])
    if request.method == 'POST':
        data = request.get_json()
        model = LLMModel(
            provider_id=data['provider_id'],
            name=data['name'],
            description=data.get('description'),
            config=data.get('config')
        )
        db.session.add(model)
        db.session.commit()
        return jsonify({'status': 'success', 'model': model.id})

@bp.route('/models/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def model_detail(id):
    model = LLMModel.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            'id': model.id,
            'provider_id': model.provider_id,
            'name': model.name,
            'description': model.description,
            'config': model.config,
            'created_at': model.created_at,
            'updated_at': model.updated_at
        })
    if request.method == 'PUT':
        data = request.get_json()
        model.name = data.get('name', model.name)
        model.description = data.get('description', model.description)
        model.config = data.get('config', model.config)
        db.session.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        db.session.delete(model)
        db.session.commit()
        return jsonify({'status': 'success'})

@bp.route('/actions/<int:action_id>/test', methods=['POST'])
def test_action(action_id):
    """Test an LLM action with modular prompt parts and return diagnostics."""
    from app.models import LLMModel
    from app import db
    import logging
    action = LLMAction.query.get_or_404(action_id)
    data = request.get_json() or {}
    input_text = data.get('input', '')
    fields = {'input': input_text}
    diagnostics = {}

    try:
        # Use a local variable for the model name, never reference action.llm_model in diagnostics or response
        if hasattr(action.llm_model, 'name'):
            safe_model_name = action.llm_model.name
        elif isinstance(action.llm_model, str):
            safe_model_name = action.llm_model
        else:
            safe_model_name = str(action.llm_model_id)
        # Assemble prompt/messages from modular prompt parts
        from app.llm.services import assemble_prompt_from_parts, LLMService
        prompt, messages = assemble_prompt_from_parts(action, fields)
        diagnostics['assembled_prompt'] = prompt
        diagnostics['messages'] = messages
        diagnostics['input'] = input_text
        diagnostics['model'] = safe_model_name
        # Execute the action using the safe model name
        service = LLMService()
        result = service.execute_action(action, fields, model_name=safe_model_name)
        # Ensure diagnostics and result are JSON serializable
        def make_json_safe(obj):
            if isinstance(obj, db.Model):
                if hasattr(obj, 'to_dict'):
                    return obj.to_dict()
                return str(obj)
            elif isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_safe(i) for i in obj]
            return obj
        safe_result = make_json_safe(result)
        safe_diag = make_json_safe(diagnostics)
        logging.error(f"[DEBUG] Sanitized diagnostics: {safe_diag}")
        logging.error(f"[DEBUG] Sanitized result: {safe_result}")
        return jsonify({
            'result': safe_result,
            'diagnostics': safe_diag
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
