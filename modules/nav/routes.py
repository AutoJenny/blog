from flask import render_template, jsonify
from . import bp
from .services import get_workflow_stages, get_workflow_context, get_all_posts

@bp.route('/api/workflow/stages')
def get_stages():
    """Get all workflow stages and their substages."""
    return jsonify(get_workflow_stages())

@bp.context_processor
def inject_workflow_context():
    """Inject workflow navigation context into templates."""
    def workflow_context(stage=None, substage=None, step=None):
        return get_workflow_context(stage, substage, step)
    return dict(workflow_context=workflow_context)

@bp.route('/')
def nav_index():
    """Default route for the navigation module - redirects to dev preview."""
    return nav_dev()

@bp.route('/dev')
def nav_dev():
    """Standalone preview of the navigation module with mock context."""
    # Get real post data from database
    all_posts = get_all_posts()
    
    # Default to first post or 1 if no posts exist
    default_post_id = all_posts[0]['id'] if all_posts else 1
    
    # Provide context variables as required by nav.html
    context = {
        'post_id': default_post_id,
        'current_stage': 'planning',
        'current_substage': 'idea',
        'current_step': 'basic_idea',
        'all_posts': all_posts,
        'workflow_ready': True  # Add this to ensure navigation is shown
    }
    return render_template('nav.html', **context)

@bp.route('/dev/posts/<int:post_id>')
@bp.route('/dev/posts/<int:post_id>/<stage>')
@bp.route('/dev/posts/<int:post_id>/<stage>/<substage>')
@bp.route('/dev/posts/<int:post_id>/<stage>/<substage>/<step>')
def nav_dev_with_context(post_id, stage='planning', substage='idea', step='basic_idea'):
    """Preview with specific context."""
    all_posts = get_all_posts()
    
    context = {
        'post_id': post_id,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step,
        'all_posts': all_posts,
        'workflow_ready': True
    }
    return render_template('nav.html', **context) 