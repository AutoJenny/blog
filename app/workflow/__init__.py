"""
Workflow module for managing the blog post creation workflow.
"""

from flask import Blueprint

# Create the workflow blueprint
bp = Blueprint('workflow', __name__, url_prefix='/workflow')

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
    
    # Register the workflow blueprint
    app.register_blueprint(bp)
    
    # Import routes after nav module is registered to ensure proper template resolution
    from . import routes

__all__ = ['bp'] 