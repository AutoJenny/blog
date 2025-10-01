"""
Planning Blueprint - Modular Version
Uses the refactored app/ modules
"""

from flask import Blueprint

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

# Import all the modular blueprints
from app.routes.calendar import calendar_bp
from app.routes.misc import misc_bp
from app.planning.views import planning_bp
from app.services.llm import llm_bp
from app.services.allocation import allocation_bp
from app.services.validation import validation_bp
from app.services.parsing import parsing_bp
from app.services.prompting import prompting_bp
from app.repositories.posts import posts_bp
from app.repositories.config import config_bp

# Register all the sub-blueprints
bp.register_blueprint(calendar_bp)
bp.register_blueprint(misc_bp)
bp.register_blueprint(planning_bp)
bp.register_blueprint(llm_bp)
bp.register_blueprint(allocation_bp)
bp.register_blueprint(validation_bp)
bp.register_blueprint(parsing_bp)
bp.register_blueprint(prompting_bp)
bp.register_blueprint(posts_bp)
bp.register_blueprint(config_bp)

# Export the main blueprint
__all__ = ['bp']
