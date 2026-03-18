from flask import render_template, jsonify, request, url_for, redirect, current_app
from . import bp
from .services import get_workflow_context
from app.services.shared import get_workflow_stages_from_db, get_all_posts_from_db

def is_workflow_enabled():
    """Check if the workflow blueprint is enabled."""
    return False  # For blog-core, workflow is not enabled yet

@bp.route('/api/workflow/stages')
def get_stages():
    """Get all workflow stages and their substages."""
    return jsonify(get_workflow_stages_from_db())

@bp.route('/nav/<int:post_id>')
def nav_index(post_id):
    """Main navigation view in standalone mode."""
    stage = request.args.get('stage', 'planning')
    substage = request.args.get('substage', 'idea')
    
    all_posts = get_all_posts_from_db()
    if not post_id and all_posts:
        post_id = all_posts[0]['id']
    
    context = {
        'current_stage': stage,
        'current_substage': substage,
        'current_step': 'basic_idea',
        'all_posts': all_posts,
        'current_post_id': post_id,
        'workflow_enabled': is_workflow_enabled()
    }
    return render_template('nav.html', **context)

@bp.route('/stage/<stage>/<substage>', methods=['GET'])
def stage(stage, substage):
    """Handle stage navigation."""
    post_id = request.args.get('post_id', type=int)
    if not post_id:
        all_posts = get_all_posts_from_db()
        post_id = all_posts[0]['id'] if all_posts else 1
    
    # For blog-core, always use standalone mode
    return redirect(url_for('workflow_nav.nav_index', post_id=post_id, stage=stage, substage=substage))

@bp.route('/post/<int:post_id>')
def select_post(post_id):
    """Handle post selection."""
    stage = request.args.get('stage', 'planning')
    substage = request.args.get('substage', 'idea')
    
    # For blog-core, always use standalone mode
    context = {
        'post_id': post_id,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': None,
        'all_posts': get_all_posts_from_db()
    }
    return render_template('nav.html', **context)

@bp.context_processor
def inject_workflow_context():
    """Inject workflow navigation context into templates."""
    def workflow_context(stage=None, substage=None, step=None):
        return get_workflow_context(stage, substage, step)
    return dict(workflow_context=workflow_context)

@bp.route('/dev')
def nav_dev():
    """Development preview of the navigation module."""
    all_posts = get_all_posts_from_db()
    context = {
        'current_stage': 'planning',
        'current_substage': 'idea',
        'current_step': 'basic_idea',
        'all_posts': all_posts,
        'workflow_enabled': is_workflow_enabled()
    }
    return render_template('nav.html', **context) 