# blueprints/launchpad/cross_promotion.py
"""Cross-promotion management routes."""

from flask import Blueprint, render_template, jsonify
import logging

logger = logging.getLogger(__name__)

# Create blueprint for cross-promotion routes  
bp = Blueprint('launchpad_cross_promotion', __name__)

@bp.route('/cross-promotion')
def cross_promotion():
    """Cross-promotion management page."""
    return render_template('launchpad/cross_promotion.html')

