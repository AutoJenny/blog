from flask import Blueprint

bp = Blueprint('servers', __name__, url_prefix='/servers')

from . import routes