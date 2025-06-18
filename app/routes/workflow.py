from flask import Blueprint, render_template

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/')
def workflow_index():
    return render_template('workflow/index.html') 