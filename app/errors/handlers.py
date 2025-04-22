from flask import render_template, request, jsonify
from app.errors import bp
from app import db

def wants_json_response():
    return request.accept_mimetypes.accept_json and \
        not request.accept_mimetypes.accept_html

@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@bp.app_errorhandler(429)
def too_many_requests(error):
    if wants_json_response():
        return jsonify({'error': 'Too many requests'}), 429
    return render_template('errors/429.html'), 429

@bp.app_errorhandler(403)
def forbidden(error):
    if wants_json_response():
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('errors/403.html'), 403 