# blueprints/launchpad/one_click_blog.py
"""One-click blog automation routes."""

from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

# Create blueprint for one-click blog routes
bp = Blueprint('launchpad_one_click_blog', __name__)

@bp.route('/one-click-blog')
def one_click_blog():
    """One-Click Blog automation page."""
    return render_template('launchpad/one_click_blog.html')

