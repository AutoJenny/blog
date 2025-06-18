from flask import Blueprint

bp = Blueprint('workflow_nav', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/workflow')

@bp.route('/')
def index():
    return 'Workflow Navigation Index'

@bp.route('/<int:post_id>/<stage_name>')
def stage(post_id, stage_name):
    return f'Stage: {stage_name} for post {post_id}'

@bp.route('/<int:post_id>/<stage_name>/<substage_name>/<step_name>')
def step(post_id, stage_name, substage_name, step_name):
    return f'Step: {step_name} in {substage_name} of {stage_name} for post {post_id}'

from . import routes  # noqa 