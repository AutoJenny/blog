from flask import Blueprint
import os

bp = Blueprint('llm_panel', __name__,
    url_prefix='/llm/panel',
    static_folder='static',
    static_url_path='/static/llm_panel',
    template_folder='templates'
)

# Import routes at the bottom to avoid circular imports
from . import routes  # noqa 