from flask import Blueprint

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(404)
def not_found_error(error):
    return "404 - stub", 404

@bp.app_errorhandler(500)
def internal_error(error):
    return "500 - stub", 500 