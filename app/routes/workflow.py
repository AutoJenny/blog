from flask import Blueprint, render_template
from modules.nav.services import get_workflow_stages, get_workflow_context, get_all_posts

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
def workflow_index():
    # Get real data from nav module services
    all_posts = get_all_posts()
    workflow_context = get_workflow_context()
    
    # Use real data from the database via nav module services
    context = {
        'all_posts': all_posts,  # Real posts from database
        'post_id': all_posts[0]['id'] if all_posts else 1,  # Use first post as default
        'current_stage': workflow_context.get('current_stage', 'planning'),
        'current_substage': workflow_context.get('current_substage', 'idea'),
        'current_step': workflow_context.get('current_step', 'basic_idea'),
        'llm_actions_data': None,  # Placeholder for future context
        'workflow_stages': workflow_context.get('stages', {})
    }
    
    return render_template('workflow/index.html', **context) 