# MIGRATION: This file is being refactored to use direct SQL (psycopg2) instead of ORM models.
from flask import Blueprint, jsonify, request, current_app
from app.llm.services import LLMService, execute_llm_request
import requests
import traceback
import logging
from app.database.routes import get_db_conn
import json
from jinja2 import Template
import subprocess
import socket
import time
import re

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
    current_app.logger.error(f"[LLM TEST] Incoming payload: {data}")
    if not data or "prompt" not in data or not data.get("prompt"):
        current_app.logger.error("[LLM TEST] No prompt provided or prompt is empty")
        return jsonify({"error": "No prompt provided"}), 400
    if "model_name" not in data or not data.get("model_name"):
        current_app.logger.error("[LLM TEST] No model_name provided or model_name is empty")
        return jsonify({"error": "No model_name provided"}), 400
    if "provider_type" not in data or not data.get("provider_type"):
        current_app.logger.error("[LLM TEST] No provider_type provided or provider_type is empty")
        return jsonify({"error": "No provider_type provided"}), 400
    try:
        llm = LLMService()
        llm.config = data.get("provider_type")  # Set provider type (e.g., 'ollama')
        # PATCH: Set api_url for Ollama
        if llm.config == "ollama":
            llm.api_url = data.get("api_base") or "http://localhost:11434"
        # PATCH: Combine prompt and input for test
        prompt = data["prompt"]
        if "input" in data and data["input"]:
            if "{{input}}" in prompt:
                from jinja2 import Template
                prompt = Template(prompt).render(input=data["input"])
            else:
                prompt = f"{prompt}\n\n{data['input']}"
        result = llm.generate(
            prompt,
            model_name=data.get("model_name"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 1000)
        )
        return jsonify({"response": result})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        current_app.logger.error(f"[LLM TEST] Exception: {e}\n{tb}")
        return jsonify({"error": f"{type(e).__name__}: {e}", "traceback": tb}), 500


@bp.route('/prompts', methods=['GET'])
def get_prompts():
    """Get all prompts, ordered by 'order' (NULLs last), then id."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, name, prompt_text
                FROM llm_prompt
                ORDER BY ("order" IS NULL), "order", id
            ''')
            prompts = cur.fetchall()
    return jsonify([
        {
            'id': p['id'],
            'name': p['name'],
            'prompt_text': p['prompt_text']
        } for p in prompts
    ])


@bp.route("/templates", methods=["GET"])
def get_templates():
    """Get all prompt templates from llm_prompt, ordered by 'order' (NULLs last), then id."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, name, prompt_text
                FROM llm_prompt
                ORDER BY ("order" IS NULL), "order", id
            ''')
            prompts = cur.fetchall()
    return jsonify([
        {
            'id': p['id'],
            'name': p['name'],
            'prompt_text': p['prompt_text']
        } for p in prompts
    ])


@bp.route("/templates/<int:template_id>", methods=["PUT"])
def update_template(template_id):
    """Update a prompt template"""
    data = request.get_json()
    template = PromptTemplate.query.get_or_404(template_id)

    template.prompt_text = data.get("prompt_text", template.prompt_text)

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
        prompt_parts = data.get('prompt_parts', [])
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                prompt_template_id = int(data['prompt_template_id'])
                cur.execute("""
                    SELECT prompt_text FROM llm_prompt WHERE id = %s
                """, (prompt_template_id,))
                prompt_row = cur.fetchone()
                if not prompt_row:
                    return jsonify({'status': 'error', 'error': 'Prompt template not found'}), 404
                prompt_template = prompt_row['prompt_text']
                # Insert action
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
    description = data.get('description', '')
    if not name or not prompt_text:
        return jsonify({'success': False, 'error': 'Name and prompt_text required'}), 400
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO llm_prompt (name, prompt_text, description, created_at, updated_at, "order")
                    VALUES (%s, %s, %s, NOW(), NOW(), 0)
                    RETURNING id
                ''', (name, prompt_text, description))
                new_id = cur.fetchone()['id']
                conn.commit()
        return jsonify({'success': True, 'prompt': {'id': new_id, 'name': name, 'prompt_text': prompt_text, 'description': description}})
    except Exception as e:
        import traceback
        current_app.logger.error(f"[CREATE PROMPT ERROR] {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': repr(e), 'traceback': traceback.format_exc()}), 500


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
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE llm_prompt SET name=%s, prompt_text=%s, updated_at=NOW() WHERE id=%s
                ''', (data['name'], data['prompt_text'], prompt_id))
                conn.commit()
        return jsonify({'success': True, 'prompt': {
            'id': prompt_id,
            'name': data['name'],
            'prompt_text': data['prompt_text']
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """Delete a prompt"""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM llm_prompt WHERE id=%s', (prompt_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """Get a single prompt by ID"""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, prompt_text FROM llm_prompt WHERE id=%s', (prompt_id,))
            prompt = cur.fetchone()
    if not prompt:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': prompt['id'],
        'name': prompt['name'],
        'prompt_text': prompt['prompt_text']
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
                action_row = cur.fetchone()
        if not action_row:
            return jsonify({'status': 'error', 'error': 'Not found'}), 404
        action = dict(action_row)
        return jsonify({'status': 'success', 'action': action})
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    update_fields = ['field_name', 'prompt_template', 'prompt_template_id', 'llm_model', 'temperature', 'max_tokens', 'input_field', 'output_field', 'order']
                    set_fields = []
                    values = []
                    # If prompt_template_id is being updated, also update prompt_template
                    if 'prompt_template_id' in data:
                        cur.execute("SELECT prompt_text FROM llm_prompt WHERE id = %s", (data['prompt_template_id'],))
                        row = cur.fetchone()
                        if not row:
                            return jsonify({'status': 'error', 'error': 'Prompt template not found'}), 400
                        set_fields.append('prompt_template=%s')
                        values.append(row['prompt_text'])
                        set_fields.append('prompt_template_id=%s')
                        values.append(data['prompt_template_id'])
                    for f in update_fields:
                        if f in data and f not in ('prompt_template', 'prompt_template_id'):
                            set_fields.append(f"{f}=%s")
                            values.append(data[f])
                    if not set_fields:
                        return jsonify({'status': 'error', 'error': 'No fields to update'}), 400
                    values.append(action_id)
                    cur.execute(f"""
                        UPDATE llm_action SET {', '.join(set_fields)}, updated_at=NOW() WHERE id=%s
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
    print(f"[PRINT] /execute endpoint called for action_id={action_id}")
    """Execute an LLM action with robust debug logging."""
    data = request.get_json()
    current_app.logger.debug(f"[LLM EXECUTE] Action ID: {action_id}, Incoming data: {data}")

    if not data or 'input_text' not in data:
        current_app.logger.warning(f"[LLM EXECUTE] No input_text provided for action {action_id}.")
        return jsonify({'error': 'No input text provided'}), 400

    try:
        # Fetch the action via direct SQL
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, input_field, output_field, "order"
                    FROM llm_action WHERE id = %s
                """, (action_id,))
                action_row = cur.fetchone()
        if not action_row:
            return jsonify({'error': 'Action not found'}), 404
        action = dict(action_row)
        current_app.logger.debug(f"[LLM EXECUTE] Action object: {action}")

        post_id = data.get('post_id')
        fields = {'input': data['input_text']}
        # PATCH: Merge in section_fields if provided
        section_fields = data.get('section_fields')
        if section_fields and isinstance(section_fields, dict):
            fields.update(section_fields)
        current_app.logger.debug(f"[LLM EXECUTE] Final fields for action {action_id}: {fields}")
        # Call the LLMService as before (assume it can take a dict action)
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
        current_app.logger.error(f"[LLM EXECUTE] Exception executing action {action_id}: {str(e)}\n{traceback.format_exc()} | Data: {data} | Action: {action if 'action' in locals() else 'N/A'}")
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
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                for idx, prompt_id in enumerate(ids):
                    cur.execute('UPDATE llm_prompt SET "order"=%s WHERE id=%s', (idx, int(prompt_id)))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
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
                    SELECT id, name, type, content, tags, "order", created_at, updated_at
                    FROM llm_prompt_part
                    ORDER BY "order", id
                """)
                parts = cur.fetchall()
        return jsonify(parts)
    if request.method == 'POST':
        data = request.get_json()
        # --- Tag validation ---
        allowed_tags = {'role', 'operation', 'format', 'specimen'}
        tags = data.get('tags', [])
        if not isinstance(tags, list) or any(t not in allowed_tags for t in tags):
            return jsonify({'error': f"Tags must be a list containing only: {', '.join(allowed_tags)}"}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO llm_prompt_part (name, type, content, tags, "order", created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id
                """, (
                    data.get('name', ''),
                    data['type'],
                    data['content'],
                    tags,
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
                    SELECT id, name, type, content, tags, "order", created_at, updated_at
                    FROM llm_prompt_part WHERE id = %s
                """, (part_id,))
                part = cur.fetchone()
        if not part:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(part)
    if request.method == 'PUT':
        data = request.get_json()
        # --- Tag validation ---
        allowed_tags = {'role', 'operation', 'format', 'specimen'}
        tags = data.get('tags', [])
        if not isinstance(tags, list) or any(t not in allowed_tags for t in tags):
            return jsonify({'error': f"Tags must be a list containing only: {', '.join(allowed_tags)}"}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE llm_prompt_part SET name=%s, type=%s, content=%s, tags=%s, "order"=%s, updated_at=NOW()
                    WHERE id=%s
                """, (
                    data.get('name', ''),
                    data.get('type'),
                    data.get('content'),
                    tags,
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


# --- LLM Provider CRUD ---
@bp.route('/providers', methods=['GET', 'POST'])
def providers():
    if request.method == 'GET':
        # Return all providers from the database
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, name, description, api_url, auth_token, created_at, updated_at FROM llm_provider ORDER BY id')
                providers = cur.fetchall()
        return jsonify([
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description'],
                'api_url': p['api_url'],
                'auth_token': p['auth_token'],
                'created_at': p['created_at'],
                'updated_at': p['updated_at']
            } for p in providers
        ])
    # POST not implemented for now
    return jsonify({'error': 'Not implemented'}), 501

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
        # Return all models from the database
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, name, provider_id, description, strengths FROM llm_model ORDER BY id')
                models = cur.fetchall()
        return jsonify([
            {
                'id': m['id'],
                'name': m['name'],
                'provider_id': m['provider_id'],
                'description': m['description'],
                'strengths': m.get('strengths') if isinstance(m, dict) else m[4]
            } for m in models
        ])
    # POST not implemented for now
    return jsonify({'error': 'Not implemented'}), 501

@bp.route('/actions/<int:action_id>/test', methods=['POST'])
def test_action(action_id):
    """Test an LLM action using its prompt_template and return diagnostics."""
    from app.llm.services import LLMService
    from jinja2 import Template
    import logging
    logger = logging.getLogger("llm_test")
    action = None
    logger.info(f"[TEST] Called for action_id={action_id}")
    data = request.get_json() or {}
    logger.info(f"[TEST] Incoming POST data: {data}")
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Fetch action
            cur.execute("SELECT * FROM llm_action WHERE id = %s", (action_id,))
            row = cur.fetchone()
            if not row:
                logger.error("[TEST] Action not found")
                return jsonify({'error': 'Action not found'}), 404
            action = dict(row)
            # Fetch model
            cur.execute("SELECT * FROM llm_model WHERE name = %s", (action['llm_model'],))
            model_row = cur.fetchone()
            if not model_row:
                logger.error("[TEST] Model not found for this action")
                return jsonify({'error': 'Model not found for this action'}), 400
            model = dict(model_row)
            # Fetch provider
            cur.execute("SELECT * FROM llm_provider WHERE id = %s", (model['provider_id'],))
            provider_row = cur.fetchone()
            if not provider_row:
                logger.error("[TEST] Provider not found for this action")
                return jsonify({'error': 'Provider not found for this action'}), 400
            provider = dict(provider_row)
            # Fetch latest prompt template from llm_prompt
            cur.execute("SELECT prompt_text FROM llm_prompt WHERE id = %s", (action['prompt_template_id'],))
            prompt_row = cur.fetchone()
            if not prompt_row:
                logger.error("[TEST] Prompt template not found for this action")
                return jsonify({'error': 'Prompt template not found for this action'}), 400
            prompt_text = prompt_row['prompt_text']
            logger.info(f"[TEST] Using prompt_text from llm_prompt: {prompt_text}")
    provider_type = provider.get('type')
    if provider_type == 'local':
        provider_type = 'ollama'
    if not provider_type:
        logger.error("[TEST] Provider type missing for this action")
        return jsonify({'error': 'Provider type missing for this action'}), 400
    provider_config = provider
    test_input = data.get('input', {})
    logger.info(f"[TEST] Raw test_input: {test_input}")
    # Ensure test_input is a mapping for Jinja2
    if isinstance(test_input, str):
        test_input = {'input': test_input}
    elif not isinstance(test_input, dict):
        test_input = {}
    # Flatten if test_input = {'input': {...}}
    if isinstance(test_input, dict) and set(test_input.keys()) == {'input'} and isinstance(test_input['input'], dict):
        test_input = test_input['input']
    logger.info(f"[TEST] Normalized test_input: {test_input}")
    # Detect FIELDNAME in prompt
    match = re.search(r'\[data:([a-zA-Z0-9_]+)\]', prompt_text)
    fieldname = match.group(1) if match else None
    logger.info(f"[TEST] Detected FIELDNAME: {fieldname}")
    # Replace [data:variable] with {{ variable }} for Jinja2
    prompt_text_jinja = re.sub(r'\[data:([a-zA-Z0-9_]+)\]', r'{{ \1 }}', prompt_text)
    logger.info(f"[TEST] Prompt template after substitution: {prompt_text_jinja}")
    try:
        template = Template(prompt_text_jinja)
        rendered_prompt = template.render(**test_input)
        logger.info(f"[TEST] Rendered prompt: {rendered_prompt}")
    except Exception as e:
        logger.error(f"[TEST] Prompt rendering error: {str(e)}")
        return jsonify({'error': f'Prompt rendering error: {str(e)}'}), 400
    # Call the LLM service
    try:
        service = LLMService()
        service.config = provider_type
        service.api_url = provider.get('api_url')
        result = service.generate(
            rendered_prompt,
            model_name=action['llm_model'],
            temperature=action.get('temperature', 0.7),
            max_tokens=action.get('max_tokens', 1000)
        )
        return jsonify({'result': result, 'rendered_prompt': rendered_prompt})
    except Exception as e:
        logger.error(f"[TEST] LLM service error: {str(e)}")
        return jsonify({'error': f'LLM service error: {str(e)}'}), 500

# --- Post Substage Action Endpoints ---
@bp.route('/post_substage_actions', methods=['GET', 'POST'])
def post_substage_actions():
    if request.method == 'GET':
        post_id = request.args.get('post_id', type=int)
        substage = request.args.get('substage', type=str)
        if not post_id or not substage:
            return jsonify({'error': 'post_id and substage required'}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, post_id, substage, action_id, button_label, button_order
                    FROM post_substage_action
                    WHERE post_id = %s AND substage = %s
                    ORDER BY button_order, id
                """, (post_id, substage))
                rows = cur.fetchall()
                actions = []
                for row in rows:
                    # Try both dict and tuple access for robustness
                    if isinstance(row, dict):
                        actions.append({
                            'id': row['id'],
                            'post_id': row['post_id'],
                            'substage': row['substage'],
                            'action_id': row['action_id'],
                            'button_label': row['button_label'],
                            'button_order': row['button_order'],
                        })
                    else:
                        actions.append({
                            'id': row[0],
                            'post_id': row[1],
                            'substage': row[2],
                            'action_id': row[3],
                            'button_label': row[4],
                            'button_order': row[5],
                        })
        return jsonify(actions)
    if request.method == 'POST':
        data = request.get_json() or {}
        post_id = data.get('post_id')
        substage = data.get('substage')
        action_id = data.get('action_id')
        button_label = data.get('button_label')
        button_order = data.get('button_order', 0)
        if not post_id or not substage or not action_id:
            return jsonify({'error': 'post_id, substage, and action_id required'}), 400
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Upsert: if exists, update; else insert
                    cur.execute("""
                        SELECT id FROM post_substage_action WHERE post_id=%s AND substage=%s
                    """, (post_id, substage))
                    row = cur.fetchone()
                    if row:
                        cur.execute("""
                            UPDATE post_substage_action
                            SET action_id=%s, button_label=%s, button_order=%s
                            WHERE id=%s
                        """, (action_id, button_label, button_order, row['id'] if isinstance(row, dict) else row[0]))
                        new_id = row['id'] if isinstance(row, dict) else row[0]
                    else:
                        cur.execute("""
                            INSERT INTO post_substage_action (post_id, substage, action_id, button_label, button_order)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (post_id, substage, action_id, button_label, button_order))
                        new_id = cur.fetchone()[0]
                    conn.commit()
            return jsonify({'id': new_id, 'status': 'success'})
        except Exception as e:
            import traceback
            print('DEBUG: Exception in post_substage_actions:', type(e), e)
            traceback.print_exc()
            return jsonify({'status': 'error', 'error': f'{type(e).__name__}: {e}'}), 400

@bp.route('/post_substage_actions/<int:psa_id>', methods=['PUT', 'DELETE'])
def post_substage_action_detail(psa_id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        button_label = data.get('button_label')
        button_order = data.get('button_order')
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE post_substage_action
                    SET button_label = %s, button_order = %s
                    WHERE id = %s
                """, (button_label, button_order, psa_id))
                conn.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM post_substage_action WHERE id = %s", (psa_id,))
                conn.commit()
        return jsonify({'status': 'success'})

# --- Substage Action Default Endpoints ---
@bp.route('/substage_action_default', methods=['GET', 'POST'])
def substage_action_default():
    if request.method == 'GET':
        substage = request.args.get('substage', type=str)
        if not substage:
            return jsonify({'error': 'substage required'}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT substage, action_id FROM substage_action_default WHERE substage = %s
                """, (substage,))
                row = cur.fetchone()
                if not row:
                    return jsonify({'substage': substage, 'action_id': None})
                # Support both tuple and dict
                action_id = row['action_id'] if isinstance(row, dict) else row[1]
                return jsonify({'substage': substage, 'action_id': action_id})
    if request.method == 'POST':
        data = request.get_json() or {}
        substage = data.get('substage')
        action_id = data.get('action_id')
        if not substage or not action_id:
            return jsonify({'error': 'substage and action_id required'}), 400
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Upsert logic
                    cur.execute("""
                        INSERT INTO substage_action_default (substage, action_id)
                        VALUES (%s, %s)
                        ON CONFLICT (substage) DO UPDATE SET action_id = EXCLUDED.action_id
                        RETURNING id
                    """, (substage, action_id))
                    fetch = cur.fetchone()
                    new_id = fetch['id'] if isinstance(fetch, dict) else fetch[0] if fetch else None
                    conn.commit()
            return jsonify({'id': new_id, 'status': 'success'})
        except Exception as e:
            import traceback
            print('DEBUG: Exception in substage_action_default:', type(e), e)
            traceback.print_exc()
            return jsonify({'status': 'error', 'error': f'{type(e).__name__}: {e}'}), 400

@bp.route('/ollama/start', methods=['POST'])
def start_ollama():
    """Start the Ollama server if not already running."""
    # Check if Ollama is already running on localhost:11434
    def is_ollama_running():
        try:
            with socket.create_connection(("localhost", 11434), timeout=2):
                return True
        except Exception:
            return False
    if is_ollama_running():
        return jsonify({"success": True, "message": "Ollama already running."})
    try:
        # Start Ollama in the background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait briefly and check again
        time.sleep(2)
        if is_ollama_running():
            return jsonify({"success": True, "message": "Ollama started."})
        else:
            return jsonify({"success": False, "error": "Ollama did not start."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@bp.route('/providers/<int:provider_id>/models/available', methods=['GET'])
def available_models(provider_id):
    # Fetch provider info
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM llm_provider WHERE id = %s', (provider_id,))
            provider = cur.fetchone()
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    provider_type = (provider['type'] or '').lower()
    provider_name = (provider['name'] or '').lower()
    # Ollama: query local API
    if 'ollama' in provider_type or 'ollama' in provider_name:
        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=3)
            r.raise_for_status()
            data = r.json()
            installed = [m.get('name') for m in data.get('models', [])]
            return jsonify({'installed': installed})
        except Exception as e:
            return jsonify({'installed': [], 'error': str(e)}), 200
    # Other providers: dummy response
    return jsonify({'installed': []})
