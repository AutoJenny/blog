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
    
    # Provide context variables as required by nav.html
    context = {
        'post_id': all_posts[0]['id'] if all_posts else 1,  # Use first post as default
        'current_stage': 'planning',
        'current_substage': 'idea',
        'current_step': 'basic_idea',
        'all_posts': all_posts
    }
    return render_template('nav.html', **context) 