from flask import Blueprint

bp = Blueprint('hub', __name__)

from . import main
from . import settings
from . import docs
from . import db
from . import errors 