from flask import Blueprint

hub_bp = Blueprint('hub', __name__)

from . import routes 