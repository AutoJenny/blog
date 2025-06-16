from flask import Blueprint, jsonify

core_bp = Blueprint('core', __name__)

@core_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200 