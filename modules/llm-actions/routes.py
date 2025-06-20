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