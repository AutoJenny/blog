from flask import render_template, jsonify, request, url_for, redirect
from . import bp
from .services import get_workflow_stages, get_workflow_context, get_all_posts

@bp.route('/api/workflow/stages')
def get_stages():
    """Get all workflow stages and their substages."""
    return jsonify(get_workflow_stages())

@bp.route('/stage/<stage>/<substage>', methods=['GET'])
def stage(stage, substage):
    """Handle stage navigation."""
    post_id = request.args.get('post_id', type=int)
    if not post_id:
        all_posts = get_all_posts()
        post_id = all_posts[0]['id'] if all_posts else 1
    
    # In integrated mode, redirect to main workflow route
    if request.blueprint != 'workflow_nav':
        return redirect(url_for('workflow.index', stage=stage, substage=substage, post_id=post_id))
        
    # In standalone mode, render nav template
    context = {
        'post_id': post_id,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': None,  # Will be set by the specific stage handler
        'all_posts': get_all_posts()
    }
    return render_template('nav.html', **context)

@bp.route('/post/<int:post_id>')
def select_post(post_id):
    """Handle post selection."""
    stage = request.args.get('stage', 'planning')
    substage = request.args.get('substage', 'idea')
    
    # In integrated mode, redirect to main workflow route
    if request.blueprint != 'workflow_nav':
        return redirect(url_for('workflow.index', stage=stage, substage=substage, post_id=post_id))
        
    # In standalone mode, render nav template
    context = {
        'post_id': post_id,
        'current_stage': stage,
        'current_substage': substage,
        'current_step': None,
        'all_posts': get_all_posts()
    }
    return render_template('nav.html', **context)

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