from flask import Blueprint, render_template, request
from modules.nav.services import get_workflow_stages, get_workflow_context, get_all_posts

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
@workflow_bp.route('/posts/<int:post_id>')
@workflow_bp.route('/posts/<int:post_id>/<stage>')
@workflow_bp.route('/posts/<int:post_id>/<stage>/<substage>')
@workflow_bp.route('/posts/<int:post_id>/<stage>/<substage>/<step>')
def workflow_index(post_id=None, stage='planning', substage='idea', step='basic_idea'):
    """Main workflow route that handles all workflow navigation."""
    # Get all posts for the selector
    all_posts = get_all_posts()
    
    # If no post_id provided or the provided post_id doesn't exist, use the first post
    if not all_posts:
        return "No posts found", 404
        
    if post_id is None or not any(p['id'] == post_id for p in all_posts):
        post_id = all_posts[0]['id']
    
    # Get the workflow context first
    workflow_ctx = get_workflow_context()
    
    # Build context with current navigation state
    context = {
        'post_id': post_id,
        'current_post_id': post_id,
        'all_posts': all_posts,
        'workflow_ready': True,
        'llm_actions_data': None,  # Placeholder for future context
        'substage': substage,  # Required by llm_actions/panels.html
        'post': {'id': post_id}  # Required by llm_actions/panels.html
    }
    
    # Update with workflow context
    context.update(workflow_ctx)
    
    # Override with current navigation state
    context.update({
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step
    })
    
    return render_template('workflow/index.html', **context) 