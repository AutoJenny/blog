from flask import render_template, redirect, url_for, abort, request, jsonify
from app.workflow import workflow
from .navigation import navigator
from app.db import get_db_conn
import json
import os
import subprocess
import sys

# Helper to get the most recent, non-deleted post
def get_latest_post():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 1
            """)
            return cur.fetchone()

def get_post_and_idea_seed(post_id):
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT p.id, pd.idea_seed FROM post p LEFT JOIN post_development pd ON p.id = pd.post_id WHERE p.id = %s", (post_id,))
            return cur.fetchone()

def get_all_posts():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT p.id, COALESCE(pd.idea_seed, p.title, 'Untitled') AS title FROM post p LEFT JOIN post_development pd ON p.id = pd.post_id WHERE p.status != 'deleted' ORDER BY p.updated_at DESC, p.id DESC")
            return cur.fetchall()

def load_step_config(stage_name: str, substage_name: str, step_name: str):
    config_path = os.path.join(os.path.dirname(__file__), 'config', f'{stage_name}_steps.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get(stage_name, {}).get(substage_name, {}).get(step_name, {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

@workflow.route('/')
def index():
    latest = get_latest_post()
    if not latest:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.stages', post_id=latest['id']))

@workflow.route('/<int:post_id>/')
def stages(post_id):
    navigator.load_navigation()
    stages = navigator.stages
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    return render_template('workflow/index.html', stages=stages, post=post, post_id=post_id, all_posts=all_posts, current_stage=None, current_substage=None, current_step=None)

@workflow.route('/<int:post_id>/<stage_name>/')
def stage(post_id, stage_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    return render_template('workflow/stage.html', stage=stage, substages=substages, post=post, post_id=post_id, all_posts=all_posts, current_stage=stage_name, current_substage=None, current_step=None)

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/')
def substage(post_id, stage_name: str, substage_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    substage = next((s for s in substages if s['name'] == substage_name), None)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    if not steps:
        abort(404, f"No steps found for substage '{substage_name}'.")
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    # Redirect to first step
    return redirect(url_for('workflow.step', post_id=post_id, stage_name=stage_name, substage_name=substage_name, step_name=steps[0]['name']))

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/<step_name>/')
def step(post_id, stage_name: str, substage_name: str, step_name: str):
    navigator.load_navigation()
    stage = next((s for s in navigator.stages if s['name'] == stage_name), None)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    substage = next((s for s in substages if s['name'] == substage_name), None)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    step = next((s for s in steps if s['name'] == step_name), None)
    if not step:
        abort(404, f"Step '{step_name}' not found in substage '{substage_name}'.")
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()

    # Load step configuration
    step_config = load_step_config(stage_name, substage_name, step_name)
    
    # Load input and output values from database
    input_values = {}
    output_values = {}
    if step_config:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Load input values
                if 'inputs' in step_config:
                    for input_id, input_config in step_config['inputs'].items():
                        cur.execute(f"SELECT {input_config['db_field']} FROM {input_config['db_table']} WHERE post_id = %s", (post_id,))
                        result = cur.fetchone()
                        if result is not None and input_config['db_field'] in result and result[input_config['db_field']] is not None:
                            input_values[input_id] = result[input_config['db_field']]
                
                # Load output values
                if 'outputs' in step_config:
                    for output_id, output_config in step_config['outputs'].items():
                        cur.execute(f"SELECT {output_config['db_field']} FROM {output_config['db_table']} WHERE post_id = %s", (post_id,))
                        result = cur.fetchone()
                        if result is not None and output_config['db_field'] in result and result[output_config['db_field']] is not None:
                            output_values[output_id] = result[output_config['db_field']]

    # Debug print statements
    print(f"DEBUG: step_config for {stage_name}/{substage_name}/{step_name}: {step_config}")
    print(f"DEBUG: input_values for post_id={post_id}: {input_values}")
    print(f"DEBUG: output_values for post_id={post_id}: {output_values}")

    # Parse output as JSON array if possible (for outputs like provisional_title)
    output_titles = None
    if 'outputs' in step_config:
        for output_id in step_config['outputs']:
            val = output_values.get(output_id)
            if val and isinstance(val, str) and val.strip().startswith('[') and val.strip().endswith(']'):
                try:
                    output_titles = json.loads(val)
                except Exception:
                    output_titles = None

    return render_template(
        f'workflow/steps/{step_name}.html',
        stage=stage,
        substage=substage,
        step=step,
        post=post,
        post_id=post_id,
        all_posts=all_posts,
        current_stage=stage_name,
        current_substage=substage_name,
        current_step=step_name,
        step_config=step_config,
        input_values=input_values,
        output_values=output_values,
        output_titles=output_titles
    )

# Redirect old URLs to new format with post_id
def _redirect_to_new(post_id, *args):
    return redirect(url_for(request.endpoint, post_id=post_id, **request.view_args))

@workflow.route('/<stage_name>/<substage_name>/<step_name>/')
def legacy_step(stage_name, substage_name, step_name):
    latest = get_latest_post()
    if not latest:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.step', post_id=latest['id'], stage_name=stage_name, substage_name=substage_name, step_name=step_name))

@workflow.route('/api/run_llm/', methods=['POST'])
def api_run_llm():
    data = request.get_json()
    post_id = data.get('post_id')
    stage_name = data.get('stage_name')
    substage_name = data.get('substage_name')
    step_name = data.get('step_name')
    if not all([post_id, stage_name, substage_name, step_name]):
        return jsonify({'error': 'Missing required parameters'}), 400
    try:
        # Run the backend script
        result = subprocess.run(
            [
                sys.executable,
                'app/workflow/scripts/llm_processor.py',
                str(post_id),
                stage_name,
                substage_name,
                step_name
            ],
            capture_output=True,
            text=True,
            cwd='/Users/nickfiddes/Code/projects/blog'
        )
        if result.returncode == 0:
            return jsonify({'status': 'success', 'output': result.stdout})
        else:
            return jsonify({'status': 'error', 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500 