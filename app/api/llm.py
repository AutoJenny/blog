print('=== LLM API MODULE LOADED (AUDIT TEST) ===')
# MIGRATION: This file is being refactored to use direct SQL (psycopg2) instead of ORM models.
from flask import Blueprint, jsonify, request, current_app
from app.llm.services import LLMService, execute_llm_request, log_llm_outgoing
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
from psycopg2.extras import Json
import os
from dotenv import dotenv_values
from app.llm.services import modular_prompt_to_canonical

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
                SELECT id, name, prompt_json
                FROM llm_prompt
                ORDER BY ("order" IS NULL), "order", id
            ''')
            prompts = cur.fetchall()
    return jsonify([
        {
            'id': p['id'],
            'name': p['name'],
            'prompt_json': p['prompt_json']
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


@bp.route('/prompts', methods=['POST'])
def create_prompt():
    data = request.get_json()
    current_app.logger.error(f"[CREATE PROMPT] Incoming data: {data}")
    name = data.get('name')
    prompt_json = data.get('prompt_json')
    # Robust: parse if string, else use as-is
    import json as _json
    current_app.logger.error(f"[CREATE PROMPT] prompt_json type before parse: {type(prompt_json)} value: {prompt_json}")
    if isinstance(prompt_json, str):
        try:
            prompt_json = _json.loads(prompt_json)
            current_app.logger.error(f"[CREATE PROMPT] prompt_json after json.loads: {type(prompt_json)} value: {prompt_json}")
        except Exception as e:
            return jsonify({'success': False, 'error': f'prompt_json is not valid JSON: {e}' }), 400
    current_app.logger.error(f"[CREATE PROMPT] prompt_json type before insert: {type(prompt_json)} value: {prompt_json}")
    if not name or not prompt_json:
        return jsonify({'success': False, 'error': 'Name and prompt_json required'}), 400
    # --- Generate canonical prompt_text from prompt_json ---
    prompt_text = ''
    try:
        prompt_text = modular_prompt_to_canonical(prompt_json, {}).get('prompt', '')
    except Exception as e:
        current_app.logger.error(f"[CREATE PROMPT] Error generating prompt_text: {e}")
        prompt_text = ''
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                from psycopg2.extras import Json
                current_app.logger.error(f"[CREATE PROMPT] Passing to Json(): {prompt_json}")
                cur.execute('''
                    INSERT INTO llm_prompt (name, prompt_json, prompt_text, created_at, updated_at, "order")
                    VALUES (%s, %s, %s, NOW(), NOW(), 0)
                    RETURNING id
                ''', (name, Json(prompt_json), prompt_text))
                new_id = cur.fetchone()['id']
                conn.commit()
        return jsonify({'success': True, 'prompt': {'id': new_id, 'name': name}})
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
    if not data or not data.get('name') or not data.get('prompt_json'):
        return jsonify({'success': False, 'error': 'Name and prompt_json required'}), 400
    prompt_json = data['prompt_json']
    # --- Generate canonical prompt_text from prompt_json ---
    prompt_text = ''
    try:
        prompt_text = modular_prompt_to_canonical(prompt_json, {}).get('prompt', '')
    except Exception as e:
        current_app.logger.error(f"[UPDATE PROMPT] Error generating prompt_text: {e}")
        prompt_text = ''
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                from psycopg2.extras import Json
                cur.execute('''
                    UPDATE llm_prompt SET name=%s, prompt_json=%s, prompt_text=%s, updated_at=NOW() WHERE id=%s
                ''', (data['name'], Json(prompt_json), prompt_text, prompt_id))
                conn.commit()
        return jsonify({'success': True, 'prompt': {
            'id': prompt_id,
            'name': data['name'],
            'prompt_json': prompt_json
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
            cur.execute('SELECT id, name, prompt_json FROM llm_prompt WHERE id=%s', (prompt_id,))
            prompt = cur.fetchone()
    if not prompt:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': prompt['id'],
        'name': prompt['name'],
        'prompt_json': prompt['prompt_json']
    })


@bp.route('/actions/<int:action_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_action(action_id):
    """Handle individual LLM action operations."""
    if request.method == 'GET':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, input_field, output_field, "order", timeout
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
                    update_fields = ['field_name', 'prompt_template', 'prompt_template_id', 'llm_model', 'temperature', 'max_tokens', 'input_field', 'order', 'timeout']
                    if 'output_field' in data:
                        update_fields.append('output_field')
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
    debug_mode = data.get('debug', False)
    current_app.logger.debug(f"[LLM EXECUTE] Action ID: {action_id}, Incoming data: {data}")

    # --- PATCH: Ensure Ollama is running before proceeding ---
    import socket, requests as _requests
    def is_ollama_running():
        try:
            with socket.create_connection(("localhost", 11434), timeout=2):
                return True
        except Exception:
            return False
    if not is_ollama_running():
        try:
            r = _requests.post("http://localhost:5000/api/v1/llm/ollama/start", timeout=10)
            if not r.ok or not r.json().get("success"):
                return jsonify({'error': 'Ollama is not running and could not be started automatically.'}), 503
            # Wait a moment for Ollama to be ready
            import time
            time.sleep(2)
            if not is_ollama_running():
                return jsonify({'error': 'Ollama did not start in time.'}), 503
        except Exception as e:
            return jsonify({'error': f'Failed to start Ollama: {e}'}), 503

    if not data or 'input_text' not in data or not data['input_text']:
        input_field = data.get('input_field', '(unknown)')
        current_app.logger.warning(f"[LLM EXECUTE] No input_text provided for action {action_id}. Input field: {input_field}")
        return jsonify({'error': f'No input text provided for field: {input_field}. Please enter a value for this field and try again.'}), 400

    try:
        # Fetch the action via direct SQL
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, input_field, output_field, "order", timeout
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
        # Fetch model and provider for this action
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM llm_model WHERE name = %s", (action['llm_model'],))
                model_row = cur.fetchone()
                if not model_row:
                    return jsonify({'error': 'Model not found for this action'}), 400
                model = dict(model_row)
                cur.execute("SELECT * FROM llm_provider WHERE id = %s", (model['provider_id'],))
                provider_row = cur.fetchone()
                if not provider_row:
                    return jsonify({'error': 'Provider not found for this action'}), 400
                provider = dict(provider_row)
        # Robust: Always use provider['type'] from DB, do not guess from model name
        provider_type = provider.get('type')
        if provider_type == 'local':
            provider_type = 'ollama'  # Legacy mapping
        if not provider_type:
            return jsonify({'error': 'Provider type missing for this action'}), 400
        llm = LLMService()
        llm.config = provider_type
        llm.api_url = provider.get('api_url')

        # --- RESTORE: Use normal prompt construction logic ---
        prompt_json = None
        raw_prompt_json = None
        raw_prompt_text = None
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT prompt_json, prompt_text FROM llm_prompt WHERE id=%s', (action['prompt_template_id'],))
                row = cur.fetchone()
                if row:
                    if isinstance(row, dict):
                        prompt_json = row.get('prompt_json')
                        raw_prompt_json = row.get('prompt_json')
                        raw_prompt_text = row.get('prompt_text')
                    elif len(row) > 1:
                        prompt_json = row[0]
                        raw_prompt_json = row[0]
                        raw_prompt_text = row[1]
        from app.llm.services import modular_prompt_to_canonical, parse_tagged_prompt_to_messages
        diagnostics = {
            'raw_prompt_json': raw_prompt_json,
            'raw_prompt_text': raw_prompt_text,
            'action_prompt_template': action.get('prompt_template'),
            'fields': fields
        }
        if prompt_json:
            parsed_prompt = modular_prompt_to_canonical(prompt_json, fields)
            canonical_prompt = parsed_prompt['prompt']
            diagnostics['parsed_prompt'] = canonical_prompt
            diagnostics['parsed_messages'] = parsed_prompt['messages']
            diagnostics['prompt_type'] = 'modular_prompt_json'
        else:
            parsed_prompt = parse_tagged_prompt_to_messages(action['prompt_template'], fields)
            canonical_prompt = parsed_prompt['prompt']
            diagnostics['parsed_prompt'] = canonical_prompt
            diagnostics['parsed_messages'] = parsed_prompt['messages']
            diagnostics['prompt_type'] = 'legacy_prompt_template'
        llm_request_json = {
            'model': action['llm_model'],
            'prompt': canonical_prompt,
            'temperature': float(action['temperature']),
            'max_tokens': int(action['max_tokens']),
            'stream': False
        }
        diagnostics['llm_request_json'] = llm_request_json
        current_app.logger.error(f"[LLM DIAGNOSTIC] Diagnostics: {json.dumps(diagnostics, ensure_ascii=False, indent=2)}")
        outgoing_prompt_string = log_llm_outgoing(llm_request_json)
        import requests
        r = requests.post("http://localhost:11434/api/generate", json=llm_request_json, timeout=action.get('timeout', 60) or 60)
        result = r.json()
        output = result.get('response', '')
        # --- Save output to selected DB field if specified ---
        save_status = None
        if action.get('output_field') and post_id:
            output_field = action['output_field']
            try:
                with get_db_conn() as conn:
                    with conn.cursor() as cur:
                        # Try post table first
                        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post'")
                        valid_fields = [row["column_name"] for row in cur.fetchall()]
                        if output_field in valid_fields:
                            cur.execute(f"UPDATE post SET {output_field} = %s, updated_at = NOW() WHERE id = %s", (output, post_id))
                            conn.commit()
                            save_status = f"Saved output to post.{output_field} for post_id={post_id}"
                        else:
                            # Try post_development table
                            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development'")
                            dev_fields = [row["column_name"] for row in cur.fetchall()]
                            if output_field in dev_fields:
                                cur.execute(f"UPDATE post_development SET {output_field} = %s WHERE post_id = %s", (output, post_id))
                                conn.commit()
                                save_status = f"Saved output to post_development.{output_field} for post_id={post_id}"
                            else:
                                save_status = f"Invalid output_field: {output_field}"
            except Exception as e:
                save_status = f"Error saving output: {e}"
        if debug_mode:
            return jsonify({'output': output, 'llm_request_json': llm_request_json, 'diagnostics': diagnostics, 'outgoing_prompt_string': outgoing_prompt_string, 'save_status': save_status})
        return jsonify({'output': output})
    except ValueError as e:
        current_app.logger.error(f"[LLM EXECUTE] ValueError executing action {action_id}: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import requests
        err_str = str(e)
        # Detect Ollama connection errors
        if (
            isinstance(e, requests.ConnectionError) or
            'Failed to establish a new connection' in err_str or
            'Connection refused' in err_str or
            'Max retries exceeded with url' in err_str or
            'HTTPConnectionPool' in err_str
        ):
            current_app.logger.error(f"[LLM EXECUTE] OllamaConnectionError executing action {action_id}: {err_str}\n{traceback.format_exc()} | Data: {data} | Action: {action if 'action' in locals() else 'N/A'}")
            return jsonify({'error': 'OllamaConnectionError', 'message': err_str}), 503
        current_app.logger.error(f"[LLM EXECUTE] Exception executing action {action_id}: {err_str}\n{traceback.format_exc()} | Data: {data} | Action: {action if 'action' in locals() else 'N/A'}")
        return jsonify({'error': err_str}), 500


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
        allowed_tags = {'role', 'operation', 'format', 'specimen', 'style'}
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
        allowed_tags = {'role', 'operation', 'format', 'specimen', 'style'}
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
            max_tokens=action.get('max_tokens', 1000),
            timeout=action.get('timeout', 60) or 60
        )
        return jsonify({'result': result, 'rendered_prompt': rendered_prompt})
    except Exception as e:
        logger.error(f"[TEST] LLM service error: {str(e)}")
        return jsonify({'error': f'LLM service error: {str(e)}'}), 500

# --- Post Workflow Step Action Endpoints ---
@bp.route('/post_workflow_step_actions', methods=['GET', 'POST'])
def post_workflow_step_actions():
    if request.method == 'GET':
        post_id = request.args.get('post_id', type=int)
        step_id = request.args.get('step_id', type=int)
        if not post_id or not step_id:
            return jsonify({'error': 'post_id and step_id required'}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, post_id, step_id, action_id, input_field, output_field, button_label, button_order
                    FROM post_workflow_step_action
                    WHERE post_id = %s AND step_id = %s
                    ORDER BY button_order, id
                """, (post_id, step_id))
                rows = cur.fetchall()
                actions = []
                for row in rows:
                    if isinstance(row, dict):
                        actions.append(row)
                    else:
                        actions.append({
                            'id': row[0],
                            'post_id': row[1],
                            'step_id': row[2],
                            'action_id': row[3],
                            'input_field': row[4],
                            'output_field': row[5],
                            'button_label': row[6],
                            'button_order': row[7],
                        })
        return jsonify({'actions': actions})

    if request.method == 'POST':
        data = request.get_json() or {}
        post_id = data.get('post_id')
        step_id = data.get('step_id')
        action_id = data.get('action_id')
        input_field = data.get('input_field')
        output_field = data.get('output_field') if 'output_field' in data else None
        button_label = data.get('button_label')
        button_order = data.get('button_order', 0)
        missing = []
        if not post_id:
            missing.append('post_id')
        if not step_id:
            missing.append('step_id')
        if not action_id:
            missing.append('action_id')
        if missing:
            return jsonify({'error': 'post_id, step_id, and action_id required', 'missing': missing, 'data': data}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO post_workflow_step_action (post_id, step_id, action_id, input_field, output_field, button_label, button_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (post_id, step_id, action_id, input_field, output_field, button_label, button_order))
                new_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'status': 'success', 'id': new_id})

@bp.route('/post_workflow_step_actions/<int:pws_id>', methods=['PUT', 'DELETE'])
def post_workflow_step_action_detail(pws_id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        button_label = data.get('button_label')
        button_order = data.get('button_order')
        input_field = data.get('input_field')
        output_field = data.get('output_field')
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE post_workflow_step_action
                    SET button_label = %s, button_order = %s, input_field = %s, output_field = %s
                    WHERE id = %s
                """, (button_label, button_order, input_field, output_field, pws_id))
                conn.commit()
        return jsonify({'status': 'success'})
    if request.method == 'DELETE':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM post_workflow_step_action WHERE id = %s", (pws_id,))
                conn.commit()
        return jsonify({'status': 'success'})

@bp.route('/post_workflow_step_actions/list', methods=['GET'])
def list_post_workflow_step_actions():
    """List all post_workflow_step_action entries, paginated and ordered by post.updated_at DESC."""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM post_workflow_step_action')
            total_count = cur.fetchone()[0]
            cur.execute('''
                SELECT pws.id, pws.post_id, pws.step_id, pws.action_id, pws.input_field, pws.output_field, pws.button_label, pws.button_order, p.updated_at
                FROM post_workflow_step_action pws
                JOIN post p ON pws.post_id = p.id
                ORDER BY p.updated_at DESC NULLS LAST, p.id DESC
                LIMIT %s OFFSET %s
            ''', (page_size, offset))
            rows = cur.fetchall()
            actions = []
            for row in rows:
                if isinstance(row, dict):
                    actions.append(row)
                else:
                    actions.append({
                        'id': row[0],
                        'post_id': row[1],
                        'step_id': row[2],
                        'action_id': row[3],
                        'input_field': row[4],
                        'output_field': row[5],
                        'button_label': row[6],
                        'button_order': row[7],
                        'updated_at': row[8],
                    })
    return jsonify({'actions': actions, 'total_count': total_count, 'page': page, 'page_size': page_size})

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

@bp.route('/actions', methods=['POST'])
def create_action():
    data = request.get_json()
    current_app.logger.error(f"[CREATE_ACTION] Incoming data: {data}")
    name = data.get('field_name')
    prompt_template_id = data.get('prompt_template_id')
    llm_model = data.get('llm_model')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 1000)
    provider_id = data.get('provider_id')
    order = data.get('order', 0)
    input_field = data.get('input_field')
    output_field = data.get('output_field') if 'output_field' in data else None
    timeout = data.get('timeout', 60)
    # Validate required fields
    if not name:
        current_app.logger.error("[CREATE_ACTION] Field name is missing")
        return jsonify({'status': 'error', 'error': 'Field name is required'}), 400
    if not provider_id:
        current_app.logger.error("[CREATE_ACTION] Provider is missing")
        return jsonify({'status': 'error', 'error': 'Provider is required'}), 400
    if not prompt_template_id:
        current_app.logger.error("[CREATE_ACTION] Prompt template ID is missing")
        return jsonify({'status': 'error', 'error': 'Prompt template is required'}), 400
    # output_field is not required
    try:
        provider_id = int(provider_id)
    except Exception:
        current_app.logger.error(f"[CREATE_ACTION] Provider ID not an integer: {provider_id}")
        return jsonify({'status': 'error', 'error': 'Provider ID must be an integer'}), 400
    try:
        prompt_template_id = int(prompt_template_id)
    except Exception:
        current_app.logger.error(f"[CREATE_ACTION] Prompt template ID not an integer: {prompt_template_id}")
        return jsonify({'status': 'error', 'error': 'Prompt template ID must be an integer'}), 400
    if provider_id < 1:
        current_app.logger.error(f"[CREATE_ACTION] Provider ID not positive: {provider_id}")
        return jsonify({'status': 'error', 'error': 'Provider ID must be a positive integer'}), 400
    if prompt_template_id < 1:
        current_app.logger.error(f"[CREATE_ACTION] Prompt template ID not positive: {prompt_template_id}")
        return jsonify({'status': 'error', 'error': 'Prompt template ID must be a positive integer'}), 400
    # Fetch the actual prompt_template text from llm_prompt
    prompt_template = None
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT prompt_text FROM llm_prompt WHERE id=%s', (prompt_template_id,))
            row = cur.fetchone()
            current_app.logger.error(f"[CREATE_ACTION] Fetched prompt_template row for id={prompt_template_id}: {row}")
            if not row:
                current_app.logger.error(f"[CREATE_ACTION] Prompt template not found for id={prompt_template_id}")
                return jsonify({'status': 'error', 'error': 'Prompt template not found'}), 400
            prompt_template = row['prompt_text'] if isinstance(row, dict) else row[0]
    if not prompt_template:
        current_app.logger.error(f"[CREATE_ACTION] Prompt template is empty or null for id={prompt_template_id}")
        return jsonify({'status': 'error', 'error': 'Prompt template is empty or null'}), 400
    insert_tuple = (
        name,
        prompt_template,
        prompt_template_id,
        llm_model,
        temperature,
        max_tokens,
        order,
        input_field,
        output_field,
        provider_id,
        timeout
    )
    current_app.logger.error(f"[CREATE_ACTION] FINAL Insert tuple: {insert_tuple}")
    current_app.logger.error(f"[CREATE_ACTION] FINAL Tuple types: {[str(type(x)) for x in insert_tuple]}")
    # Proceed to insert
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                current_app.logger.error("[CREATE_ACTION] About to execute INSERT into llm_action")
                cur.execute('''
                    INSERT INTO llm_action (field_name, prompt_template, prompt_template_id, llm_model, temperature, max_tokens, "order", input_field, output_field, provider_id, timeout)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', insert_tuple)
                new_id = cur.fetchone()['id']
                current_app.logger.error(f"[CREATE_ACTION] Inserted new llm_action with id: {new_id}")
                conn.commit()
        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        # Return the tuple and types for debugging
        tuple_types = [str(type(x)) for x in insert_tuple]
        current_app.logger.error(f"[CREATE_ACTION] Exception during insert: {e}")
        return jsonify({'status': 'error', 'error': str(e), 'insert_tuple': insert_tuple, 'tuple_types': tuple_types}), 400

@bp.route('/debug/db_url', methods=['GET'])
def debug_db_url():
    db_url = None
    try:
        # Try to get the DB URL the same way as get_db_conn
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env')
        config = dotenv_values(config_path)
        db_url = config.get('DATABASE_URL')
    except Exception as e:
        db_url = f"[ERROR] {e}"
    # Try to fetch a few rows from llm_action
    rows = []
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM llm_action ORDER BY id DESC LIMIT 3;')
                rows = cur.fetchall()
    except Exception as e:
        rows = [f"[ERROR] {e}"]
    return jsonify({'db_url': db_url, 'llm_action_rows': rows})

@bp.route('/actions', methods=['GET'])
def list_actions():
    """Return all LLM actions as JSON."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, field_name, prompt_template, prompt_template_id, llm_model, provider_id, temperature, max_tokens, input_field, output_field, "order", timeout
                FROM llm_action
                ORDER BY "order", id
            """)
            actions = cur.fetchall()
    # Convert to list of dicts if needed
    result = []
    for a in actions:
        result.append(dict(a) if isinstance(a, dict) else {
            "id": a[0],
            "field_name": a[1],
            "prompt_template": a[2],
            "prompt_template_id": a[3],
            "llm_model": a[4],
            "provider_id": a[5],
            "temperature": a[6],
            "max_tokens": a[7],
            "input_field": a[8],
            "output_field": a[9],
            "order": a[10],
            "timeout": a[11],
        })
    return jsonify(result)

@bp.route('/test-direct', methods=['GET'])
def test_direct():
    import requests
    payload = {
        "model": "llama3.1:70b",
        "prompt": 'Start every response with "TITLE: NONSENSE". Write entirely in French. Write a short poem. Data for this operation as follows: dog breakfasts',
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }
    r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    return jsonify(r.json())

@bp.route('/ollama/status', methods=['GET'])
def ollama_status():
    """Return Ollama running status."""
    import socket
    def is_ollama_running():
        try:
            with socket.create_connection(("localhost", 11434), timeout=2):
                return True
        except Exception:
            return False
    if is_ollama_running():
        return jsonify({"status": "running"})
    else:
        return jsonify({"status": "not running"})
