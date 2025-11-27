"""Newsletter Blueprint - Main router that imports and registers all sub-blueprints.

This file stays small (<100 LOC) and delegates to specialized modules.
"""

from flask import Blueprint
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Create main blueprint
bp = Blueprint('newsletter', __name__)

# Import and register all sub-blueprints
from .newsletter_issues import bp as issues_bp
from .newsletter_blocks import bp as blocks_bp
from .newsletter_generation_intro import bp as gen_intro_bp
from .newsletter_generation_snapshot import bp as gen_snapshot_bp
from .newsletter_generation_other import bp as gen_other_bp
from .newsletter_preview import bp as preview_bp
from .newsletter_approval import bp as approval_bp
from .newsletter_sources import bp as sources_bp
from .newsletter_content import bp as content_bp
from .newsletter_events import bp as events_bp
from .newsletter_round_scotland import bp as round_scotland_bp

# Register all sub-blueprints
bp.register_blueprint(issues_bp)
bp.register_blueprint(blocks_bp)
bp.register_blueprint(gen_intro_bp)
bp.register_blueprint(gen_snapshot_bp)
bp.register_blueprint(gen_other_bp)
bp.register_blueprint(preview_bp)
bp.register_blueprint(approval_bp)
bp.register_blueprint(sources_bp)
bp.register_blueprint(content_bp)
bp.register_blueprint(events_bp)
bp.register_blueprint(round_scotland_bp)
