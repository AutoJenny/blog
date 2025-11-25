# blueprints/launchpad/one_click_blog.py
"""One-click blog automation routes."""

from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('one_click_blog', __name__)

@bp.route('/one-click-blog')
def one_click_blog():
    """One-Click Blog automation page."""
    template_name = 'launchpad/one_click_blog.html'
    logger.info(f"[One-Click Blog] Rendering template: {template_name}")
    return render_template(template_name)

