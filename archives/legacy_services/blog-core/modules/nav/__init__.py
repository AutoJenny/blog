from flask import Blueprint

bp = Blueprint('workflow_nav', __name__, 
               template_folder='templates',
               static_folder='static',
               static_url_path='/static/workflow_nav')

from . import routes  # noqa 