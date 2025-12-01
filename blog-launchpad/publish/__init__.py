"""
Publication Module
Clean, modular publication system for blog posts to clan.com
"""

from .publish_endpoint import bp as publish_bp

__all__ = ['publish_bp']

# Register blueprint function
def register_blueprint(app):
    """Register the publish blueprint with the Flask app."""
    app.register_blueprint(publish_bp)


