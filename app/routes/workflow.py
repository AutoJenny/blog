from flask import Blueprint, render_template
from modules.nav.services import get_workflow_stages, get_workflow_context

workflow_bp = Blueprint('workflow', __name__)

@workflow_bp.route('/')
def workflow_index():
    # Get workflow context - self-contained function
    context = get_workflow_context()
    
    # Add additional data for the template
    context.update({
        'post_id': 1,
        'all_posts': [{'id': 1, 'title': 'Demo Post'}]  # This will be real DB data
    })
    
    return render_template('workflow/index.html', **context) 