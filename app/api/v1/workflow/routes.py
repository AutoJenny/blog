"""
Routes for the v1 workflow API.
"""

from flask import request, jsonify
from app.llm.services import execute_request
from . import workflow_bp

@workflow_bp.route('/llm/run', methods=['POST'])
def run_llm():
    """
    Execute an LLM request with the provided parameters.
    
    Expected request body:
    {
        "post_id": int,
        "stage": str,
        "substage": str,
        "step": str
    }
    
    Returns:
    {
        "success": bool,
        "data": {
            "result": str
        },
        "error": null | {
            "message": str
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "data": None,
                "error": {"message": "No JSON data provided"}
            }), 400

        required_fields = ['post_id', 'stage', 'substage', 'step']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                "success": False,
                "data": None,
                "error": {"message": f"Missing required fields: {', '.join(missing_fields)}"}
            }), 400

        result = execute_request(
            post_id=data['post_id'],
            stage=data['stage'],
            substage=data['substage'],
            step=data['step']
        )

        return jsonify({
            "success": True,
            "data": {"result": result},
            "error": None
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "data": None,
            "error": {"message": str(e)}
        }), 500 