from flask import Blueprint
import os

llm_panel_bp = Blueprint('llm_panel', __name__,
                        template_folder=os.path.join('app', 'templates', 'modules', 'llm_panel', 'templates'),
                        static_folder=os.path.join('app', 'static', 'modules', 'llm_panel'),
                        static_url_path='/llm/panel/static') 