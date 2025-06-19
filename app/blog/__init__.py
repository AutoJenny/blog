from flask import Blueprint

bp = Blueprint('blog', __name__)

@bp.route('/new', methods=['POST'])
def new_post():
    return "New post - stub"

@bp.route('/<slug>')
def get_post(slug):
    return f"Get post: {slug} - stub"

@bp.route('/<slug>', methods=['PUT'])
def update_post(slug):
    return f"Update post: {slug} - stub"

@bp.route('/posts')
def posts_listing():
    return "Posts listing - stub"

@bp.route('/public/<int:post_id>/')
def post_public(post_id):
    return f"Public post: {post_id} - stub" 