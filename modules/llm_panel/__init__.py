from flask import Blueprint
import os

llm_panel_bp = Blueprint('llm_panel', __name__,
                        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                        static_folder='static',
                        static_url_path='/llm/panel/static') 