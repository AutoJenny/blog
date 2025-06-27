"""
API v1 blueprint.
"""
from flask import Blueprint

# Create the v1 API blueprint
bp = Blueprint('api_v1', __name__, url_prefix='/v1')

# Import routes after blueprint creation
from . import workflow  # v1 workflow routes

# Register workflow blueprint
from .workflow import bp as workflow_bp
bp.register_blueprint(workflow_bp, url_prefix='/workflow')

__all__ = ['bp'] 