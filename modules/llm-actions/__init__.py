from flask import Blueprint

bp = Blueprint('llm_actions', __name__, 
               url_prefix='/llm-actions',
               template_folder='templates') 