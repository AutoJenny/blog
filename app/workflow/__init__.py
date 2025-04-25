from flask import Blueprint

bp = Blueprint("workflow", __name__, url_prefix="/posts")

from app.workflow import routes  # noqa
