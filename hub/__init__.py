from flask import Blueprint

bp = Blueprint('hub', __name__)

from . import routes 