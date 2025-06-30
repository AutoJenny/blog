from flask import Blueprint

bp = Blueprint('nav', __name__, 
               template_folder='templates',
               static_folder='static',
               static_url_path='/static/nav')

from . import routes  # noqa 