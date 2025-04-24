from flask import Blueprint

bp = Blueprint("workflow", __name__)

from app.workflow import routes  # noqa
