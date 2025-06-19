from flask import Blueprint, render_template
from modules.nav.services import get_workflow_stages, get_workflow_context

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
def workflow_index():
    # Get workflow context from the navigation module
    workflow_context = get_workflow_context()
    
    # For now, provide minimal context with default values
    # In the future, this will be enhanced to fetch real data
    context = {
        'all_posts': [],  # Will be populated with actual posts
        'post_id': 1,     # Default post ID to prevent error message
        'current_stage': 'planning',  # Default to planning stage
        'current_substage': 'idea',   # Default to idea substage
        'current_step': 'basic_idea', # Default to basic idea step
        'llm_actions_data': None,     # Placeholder for future context
        'workflow_stages': workflow_context.get('stages', {})
    }
    
    return render_template('workflow/index.html', **context) 