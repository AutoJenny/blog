from flask import render_template, redirect, url_for, abort, request
from app.workflow import workflow
from .navigation import navigator
from app.db import get_db_conn

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
    return render_template(f'workflow/steps/{step_name}.html', stage=stage, substage=substage, step=step, post=post, post_id=post_id, all_posts=all_posts, current_stage=stage_name, current_substage=substage_name, current_step=step_name)

# Redirect old URLs to new format with post_id
def _redirect_to_new(post_id, *args):
    return redirect(url_for(request.endpoint, post_id=post_id, **request.view_args))

@workflow.route('/<stage_name>/<substage_name>/<step_name>/')
def legacy_step(stage_name, substage_name, step_name):
    latest = get_latest_post()
    if not latest:
        abort(404, "No posts found.")
    return redirect(url_for('workflow.step', post_id=latest['id'], stage_name=stage_name, substage_name=substage_name, step_name=step_name)) 