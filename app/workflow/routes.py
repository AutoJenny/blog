from flask import render_template, redirect, url_for, abort, request, jsonify
from app.workflow import workflow
from .navigation import navigator
from app.db import get_db_conn
import json
import os
import subprocess
import sys

# Mapping of substage names to Font Awesome icons
SUBSTAGE_ICONS = {
    'idea': 'lightbulb',
    'research': 'search',
    'structure': 'sitemap',
    'content': 'pen',
    'meta_info': 'tags',
    'images': 'image',
    'preflight': 'check-circle',
    'launch': 'rocket',
    'syndication': 'share-alt'
}

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
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    nav_context = navigator.get_navigation_context()
    return render_template('workflow/index.html', 
                         post=post, 
                         post_id=post_id, 
                         all_posts=all_posts, 
                         nav_context=nav_context,
                         substage_icons=SUBSTAGE_ICONS,
                         current_stage=None, 
                         current_substage=None, 
                         current_step=None)

@workflow.route('/<int:post_id>/<stage_name>/')
def stage(post_id, stage_name: str):
    navigator.load_navigation()
    stage = navigator.get_stage_by_name(stage_name)
    if not stage:
        abort(404, f"Stage '{stage_name}' not found.")
    substages = navigator.get_substages_for_stage(stage['id'])
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()
    nav_context = navigator.get_navigation_context(current_stage_id=stage['id'])
    return render_template('workflow/stage.html', 
                         stage=stage, 
                         substages=substages, 
                         post=post, 
                         post_id=post_id, 
                         all_posts=all_posts, 
                         nav_context=nav_context,
                         substage_icons=SUBSTAGE_ICONS,
                         current_stage=stage_name, 
                         current_substage=None, 
                         current_step=None)

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/')
def substage(post_id, stage_name: str, substage_name: str):
    navigator.load_navigation()
    substage = navigator.get_substage_by_name(stage_name, substage_name)
    if not substage:
        abort(404, f"Substage '{substage_name}' not found in stage '{stage_name}'.")
    steps = navigator.get_steps_for_substage(substage['id'])
    if not steps:
        abort(404, f"No steps found for substage '{substage_name}'.")
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    # Redirect to first step
    return redirect(url_for('workflow.step', 
                          post_id=post_id, 
                          stage_name=stage_name, 
                          substage_name=substage_name, 
                          step_name=steps[0]['name']))

@workflow.route('/<int:post_id>/<stage_name>/<substage_name>/<step_name>/')
def step(post_id, stage_name: str, substage_name: str, step_name: str):
    navigator.load_navigation()
    
    # Validate the path and get step
    step = navigator.validate_path(stage_name, substage_name, step_name)
    if not step:
        abort(404, f"Invalid path: {stage_name}/{substage_name}/{step_name}")
    
    # Get stage and substage
    stage = navigator.get_stage_by_name(stage_name)
    substage = navigator.get_substage_by_name(stage_name, substage_name)
    steps = navigator.get_steps_for_substage(substage['id'])
    
    # Get post data
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    all_posts = get_all_posts()

    # Get navigation context
    nav_context = navigator.get_navigation_context(
        current_stage_id=stage['id'],
        current_substage_id=substage['id'],
        current_step_id=step['id']
    )

    return render_template(
        f'workflow/steps/{step_name}.html',
        stage=stage,
        substage=substage,
        step=step,
        steps=steps,
        post=post,
        post_id=post_id,
        all_posts=all_posts,
        nav_context=nav_context,
        substage_icons=SUBSTAGE_ICONS,
        current_stage=stage_name,
        current_substage=substage_name,
        current_step=step_name
    )

# Redirect old URLs to new format with post_id
@workflow.route('/<stage_name>/<substage_name>/<step_name>/')
def legacy_step(stage_name, substage_name, step_name):
    latest = get_latest_post()
    if not latest:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.step', 
                          post_id=latest['id'], 
                          stage_name=stage_name, 
                          substage_name=substage_name, 
                          step_name=step_name))

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