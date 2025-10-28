# blueprints/launchpad/syndication.py
"""Syndication-related routes and functionality."""

from flask import Blueprint, redirect
import logging

logger = logging.getLogger(__name__)

# Create blueprint for syndication routes
bp = Blueprint('launchpad_syndication', __name__)

@bp.route('/syndication/dashboard')
def syndication_dashboard():
    """Redirect to main syndication page."""
    return redirect('/launchpad/syndication')

