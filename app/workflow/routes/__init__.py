# This file intentionally left empty to mark the routes directory as a Python package
from .workflow_routes import workflow_bp
from .stage_routes import stage_bp
from .substage_routes import substage_bp
from .action_routes import action_bp

__all__ = ['workflow_bp', 'stage_bp', 'substage_bp', 'action_bp'] 