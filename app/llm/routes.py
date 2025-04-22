from flask import jsonify, request
from app.llm import bp
from app.services.llm_service import LLMService

@bp.route('/generate-summary/<int:post_id>')
def generate_summary(post_id):
    llm_service = LLMService()
    try:
        summary = llm_service.generate_post_summary(post_id)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 