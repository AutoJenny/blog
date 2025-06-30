from flask import Blueprint
from . import base
from . import workflow

# Create the main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register workflow blueprint
api_bp.register_blueprint(workflow.bp)

# Import routes after blueprint creation
from . import base  # Basic API routes
from . import workflow  # Workflow routes

__all__ = ['api_bp'] 