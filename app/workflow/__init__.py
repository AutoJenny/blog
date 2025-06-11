from flask import Blueprint

workflow = Blueprint('workflow', __name__)

from . import routes
from app.workflow.navigation import init_app

def init_workflow(app):
    """Initialize the workflow module."""
    init_app(app) 