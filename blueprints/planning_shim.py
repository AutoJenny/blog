"""
Planning Blueprint - Compatibility Shim
Maintains backward compatibility while using refactored modules
"""

from flask import Blueprint

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

# Import all functions from refactored modules
from app.routes.calendar import *
from app.routes.update import *
from app.routes.save import *
from app.routes.misc import *
from app.planning.views import *
from app.services.allocation import *
from app.services.validation import *
from app.services.parsing import *
from app.services.prompting import *
from app.services.llm import *
from app.repositories.posts import *
from app.repositories.config import *

# Re-export the blueprint
__all__ = ['bp']
