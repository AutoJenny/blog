from flask import Blueprint
import os

llm_panel_bp = Blueprint('llm_panel', __name__,
                        template_folder='templates',
                        static_folder='static',
                        static_url_path='/llm/panel/static')

# Import routes at the bottom to avoid circular imports
from . import routes  # noqa 