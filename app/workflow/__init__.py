"""
Workflow module for managing the blog post creation workflow.
"""

from flask import Blueprint

# Create the workflow blueprints
bp = Blueprint('workflow', __name__, url_prefix='/workflow')
api_workflow_bp = Blueprint('api_workflow', __name__, url_prefix='/api/workflow')

# Import routes after blueprint creation
from . import routes

# DISABLED - DO NOT USE TOXIC DUPLICATE
# from . import routes
# from app.workflow.navigation import init_app

# Use proper nav module
from modules.nav import bp as nav_bp

def init_workflow(app):
    """Initialize the workflow module."""
    # Register the proper nav module
    app.register_blueprint(nav_bp, url_prefix='/workflow_nav')
    
    # Register the workflow blueprints
    app.register_blueprint(bp)
    app.register_blueprint(api_workflow_bp)

__all__ = ['bp', 'api_workflow_bp'] 