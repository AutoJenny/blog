from flask import Blueprint

bp = Blueprint('llm_panel', __name__)

# Import routes at the bottom to avoid circular imports
from . import routes  # noqa 