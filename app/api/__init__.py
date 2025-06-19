from flask import Blueprint

bp = Blueprint('api', __name__)

@bp.route('/v1/health')
def health_check():
    return "API health check - stub"

@bp.route('/v1/posts')
def list_posts():
    return "List posts - stub"

@bp.route('/v1/posts', methods=['POST'])
def create_post():
    return "Create post - stub" 