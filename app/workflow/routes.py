from flask import render_template, redirect, url_for, abort, request, jsonify
from app.workflow import workflow
# DISABLED - DO NOT USE TOXIC DUPLICATE
# from .navigation import navigator

# Use proper nav module instead
from modules.nav.services import get_workflow_context
from app.services.shared import get_workflow_stages_from_db, get_all_posts_from_db
from app.database import get_db_conn
import subprocess
import sys
import json
import os

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
    """Workflow index page."""
    all_posts = get_all_posts_from_db()
    if not all_posts:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.stages', post_id=all_posts[0]['id']))

@workflow.route('/posts/<int:post_id>/<stage>/<substage>')
@workflow.route('/posts/<int:post_id>')
def workflow_index(post_id, stage=None, substage=None):
    """Main workflow page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    context = get_workflow_context(stage, substage)
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': None
    })
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/')
def stages(post_id):
    """Workflow stages index page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get workflow context from the nav module
    context = get_workflow_context()
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': None,
        'current_substage': None,
        'current_step': None
    })
    
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/<stage>/')
def stage(post_id, stage: str):
    """Stage view page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get workflow context from the nav module
    context = get_workflow_context(stage)
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': stage,
        'current_substage': None,
        'current_step': None
    })
    
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/<stage>/<substage>/')
def substage(post_id, stage: str, substage: str):
    """Substage view page."""
    post = get_post_and_idea_seed(post_id)
    if not post:
        abort(404, f"Post {post_id} not found.")
    
    # Get workflow context from the nav module
    context = get_workflow_context(stage, substage)
    if not context:
        abort(404, f"Invalid path: {stage}/{substage}")
    
    context.update({
        'post': post,
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': get_all_posts(),
        'substage_icons': SUBSTAGE_ICONS,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': None
    })
    
    return render_template('workflow/index.html', **context)

@workflow.route('/posts/<int:post_id>/<stage>/<substage>/<step>/')
def step(post_id, stage: str, substage: str, step: str):
    """Handle old URL format and redirect to new format."""
    # Get workflow context to validate the path
    context = get_workflow_context(stage, substage, step)
    if not context:
        abort(404, f"Invalid path: {stage}/{substage}/{step}")
    return redirect(url_for('workflow.workflow_index', post_id=post_id, stage=stage, substage=substage))

@workflow.route('/api/v1/workflow/llm/', methods=['POST'])
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

@workflow.route('/api/v1/workflow/title_order/', methods=['POST'])
def api_update_title_order():
    data = request.get_json()
    post_id = data.get('post_id')
    titles = data.get('titles')
    if not all([post_id, titles]):
        return jsonify({'error': 'Missing required parameters'}), 400
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE post_development SET title_order = %s WHERE post_id = %s", (json.dumps(titles), post_id))
                conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500 