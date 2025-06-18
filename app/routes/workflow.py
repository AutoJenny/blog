from flask import Blueprint, render_template

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
def workflow_index():
    # Provide minimal context required by nav.html and llm_actions.html
    return render_template(
        'workflow/index.html',
        all_posts=[],
        post_id=None,
        current_stage=None,
        current_substage=None,
        current_step=None,
        llm_actions_data=None  # Placeholder for future context
    ) 