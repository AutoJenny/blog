# blueprints/launchpad/__init__.py
"""Modular launchpad blueprint structure."""

from flask import Blueprint
from blueprints.launchpad_utils import strip_html_doc

# Import the old blueprint that contains most routes
from blueprints.launchpad_old import bp as old_bp

# Import extracted modular blueprints
from blueprints.launchpad import core, one_click_blog, cross_promotion, publishing

# Create main blueprint
bp = Blueprint('launchpad', __name__)

# Register template filters
bp.add_app_template_filter(strip_html_doc, 'strip_html_doc')

# Register extracted sub-blueprints
bp.register_blueprint(core.bp)
bp.register_blueprint(one_click_blog.bp)
bp.register_blueprint(cross_promotion.bp)
bp.register_blueprint(publishing.bp)

# IMPORTANT: All remaining routes still come from old_bp
# This is a temporary measure until we finish extracting syndication routes

# For now, we still need to import old_bp to get the syndication routes
# The modular blueprints above handle specific routes, while old_bp handles the rest
