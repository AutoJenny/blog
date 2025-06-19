from flask import Blueprint, render_template
from modules.nav.services import get_workflow_stages, get_workflow_context

workflow_bp = Blueprint('workflow', __name__)

@workflow_bp.route('/')
def workflow_index():
    # Get workflow context with default stage/substage for demo
    context = get_workflow_context('planning', 'idea', 'basic_idea')
    
    # Add real data for the template - this will be replaced with actual DB data
    context.update({
        'post_id': 1,
        'current_stage': 'planning',
        'current_substage': 'idea', 
        'current_step': 'basic_idea',
        'all_posts': [{'id': 1, 'title': 'Demo Post'}]  # This will be real DB data
    })
    
    return render_template('workflow/index.html', **context) 