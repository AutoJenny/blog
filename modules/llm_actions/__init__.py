from flask import Blueprint

bp = Blueprint('llm-actions', __name__, 
               url_prefix='/llm-actions',
               template_folder='templates') 