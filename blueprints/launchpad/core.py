# blueprints/launchpad/core.py
"""Core launchpad routes."""

from flask import Blueprint, render_template, jsonify

# Create a separate blueprint for core routes
bp = Blueprint('core', __name__)

@bp.route('/')
def index():
    """Main launchpad page."""
    return render_template('launchpad/index.html')

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "launchpad"})
