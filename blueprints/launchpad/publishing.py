# blueprints/launchpad/publishing.py
"""Publishing-related routes and functionality."""

from flask import Blueprint, render_template, jsonify
import logging

logger = logging.getLogger(__name__)

# Create blueprint for publishing routes
bp = Blueprint('launchpad_publishing', __name__)

@bp.route('/publishing')
def publishing():
    """Publishing management page."""
    return render_template('launchpad/publishing.html')

