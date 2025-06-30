"""
Workflow module for managing the blog post creation workflow.
"""

from flask import Blueprint

# Create the workflow blueprints
bp = Blueprint('workflow', __name__, url_prefix='/workflow')
api_workflow_bp = Blueprint('api_workflow', __name__, url_prefix='/api/workflow')

# Import routes after blueprint creation
from . import routes

# Import API workflow routes
from app.api.workflow import formats
from app.api.workflow import stage_formats
from app.api.workflow import post_formats
from app.api.workflow import step_formats
from app.api.workflow import format_routes
from app.api.workflow import steps

# DISABLED - DO NOT USE TOXIC DUPLICATE
# from . import routes
# from app.workflow.navigation import init_app

# Use proper nav module
from modules.nav import bp as nav_bp

def init_workflow(app):
    """Initialize the workflow module."""
    # Register the workflow blueprints
    app.register_blueprint(bp)
    app.register_blueprint(api_workflow_bp)
    
    # Register the API workflow blueprint (contains step_formats routes)
    from app.api.workflow import bp as api_workflow_bp_main
    app.register_blueprint(api_workflow_bp_main, name='api_workflow_main')
    
    # Register the formats blueprints
    app.register_blueprint(formats.formats_bp)
    app.register_blueprint(stage_formats.stage_formats_bp)
    app.register_blueprint(post_formats.post_formats_bp)

__all__ = ['bp', 'api_workflow_bp'] 