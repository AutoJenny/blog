"""
LLM Actions Module - API Endpoints

This module provides the following endpoints:

GET /api/v1/llm/actions
    Returns all available LLM actions

POST /api/v1/llm/actions/{action_id}/execute
    Executes an LLM action with the given parameters

GET /api/v1/llm/actions/{action_id}/runs/{run_id}
    Gets the status and result of a specific action run

GET /api/v1/llm/prompts
    Returns available prompt templates

GET /api/v1/llm/models
    Returns available LLM models

Note: This is a placeholder file. Implementation will be discussed.
"""

from flask import Blueprint

llm_actions = Blueprint('llm_actions', __name__, 
                       template_folder='templates',
                       static_folder='static',
                       static_url_path='/static/llm_actions')

from flask import render_template
from . import bp

@bp.route('/panels/<int:post_id>')
def panels(post_id):
    """Display the LLM action panels for a post."""
    return render_template(
        'llm-actions/index.html',
        post={'id': post_id},  # Minimal post object with just the ID
        substage='idea'  # Default substage
    ) 