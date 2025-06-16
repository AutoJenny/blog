from flask import Blueprint

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')
stage_bp = Blueprint('stage', __name__, url_prefix='/workflow/stage')
substage_bp = Blueprint('substage', __name__, url_prefix='/workflow/substage')
action_bp = Blueprint('action', __name__, url_prefix='/workflow/action')

from . import routes
from . import models
from . import schemas
from . import utils

def init_app(app):
    app.register_blueprint(workflow_bp)
    app.register_blueprint(stage_bp)
    app.register_blueprint(substage_bp)
    app.register_blueprint(action_bp)

def init_workflow(app):
    """Initialize the workflow module."""
    init_app(app) 