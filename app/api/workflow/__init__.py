"""Workflow API Blueprint

This module initializes the workflow API blueprint and registers all routes.
Routes are imported after blueprint creation to avoid circular imports.
"""

from flask import Blueprint

# Create the blueprint
bp = Blueprint('api_workflow', __name__, url_prefix='/api/workflow')

# Import routes after blueprint creation to avoid circular imports
from . import routes  # Basic workflow routes
from . import step_formats  # Format-related routes
from . import format_routes  # Format system routes
from . import steps  # Step management routes (GET, PUT, DELETE, reorder)

__all__ = ['bp'] 