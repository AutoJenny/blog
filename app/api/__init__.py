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

# Import and register deprecated LLM API blueprint (for /api/v1/llm endpoints)
from . import llm as deprecated_llm
api_bp.register_blueprint(deprecated_llm.bp)

__all__ = ['api_bp'] 