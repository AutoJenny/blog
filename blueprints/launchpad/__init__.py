# blueprints/launchpad/__init__.py
"""Modular launchpad blueprint structure."""

from flask import Blueprint
from blueprints.launchpad_utils import strip_html_doc

# Create main blueprint
bp = Blueprint('launchpad', __name__, url_prefix='/launchpad')

# Register template filters
bp.add_app_template_filter(strip_html_doc, 'strip_html_doc')

# Import and register sub-blueprints
from blueprints.launchpad import (
    core,
    publishing,
    syndication,
    cross_promotion,
    one_click_blog
)

# Register all sub-blueprints
bp.register_blueprint(core.bp)
bp.register_blueprint(publishing.bp)
bp.register_blueprint(syndication.bp)
bp.register_blueprint(cross_promotion.bp)
bp.register_blueprint(one_click_blog.bp)

