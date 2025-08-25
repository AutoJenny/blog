from flask import Flask, send_from_directory
from flask_cors import CORS
import os

# Import blueprints (blog and llm temporarily disabled due to import issues)
# from app.blog import bp as blog_bp
from app.main import bp as main_bp
# from app.llm import bp as llm_bp
from app.database.routes import bp as db_bp
from app.routes.settings import bp as settings_bp

def create_app(config=None):
    app = Flask(__name__)
    
    # Load config
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object('config.Config')
    
    # Initialize extensions
    CORS(app)
    
    # Configure static files
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        response = send_from_directory(app.static_folder, filename)
        if filename.endswith('.js'):
            response.headers['Content-Type'] = 'application/javascript'
        return response
    
    # Register blueprints
    # app.register_blueprint(blog_bp, url_prefix='/blog')  # Temporarily disabled
    app.register_blueprint(main_bp)
    # app.register_blueprint(llm_bp, url_prefix='/llm')  # Temporarily disabled
    app.register_blueprint(db_bp)
    app.register_blueprint(settings_bp)
    
    # Register error handlers
    from app.errors import handlers
    app.register_error_handler(404, handlers.not_found_error)
    app.register_error_handler(500, handlers.internal_error)
    
    return app
