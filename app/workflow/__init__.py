from flask import Blueprint

bp = Blueprint('workflow', __name__, url_prefix='/workflow')

from app.workflow import routes
from app.workflow.navigation import init_app

def init_workflow(app):
    """Initialize the workflow module."""
    init_app(app) 