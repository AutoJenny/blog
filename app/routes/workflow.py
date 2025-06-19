from flask import Blueprint, render_template
from modules.nav.services import get_workflow_stages, get_workflow_context, get_all_posts

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
def workflow_index():
    # Get workflow context from nav module
    workflow_context = get_workflow_context()
    
    # Pass through all context variables directly
    context = {
        **workflow_context,  # Include all workflow context
        'llm_actions_data': None,  # Placeholder for future context
    }
    
    return render_template('workflow/index.html', **context) 