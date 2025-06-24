from flask import Blueprint

llm_panel_bp = Blueprint('llm_panel', __name__,
                        template_folder='templates',
                        static_folder='static',
                        static_url_path='/llm/panel/static') 