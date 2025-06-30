from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
from flask_migrate import Migrate
from celery import Celery
from app.db import get_db_conn
import os

# Initialize extensions
migrate = Migrate()
cache = Cache()
celery = Celery()

# Import blueprints
from app.api import api_bp
from app.blog import bp as blog_bp
from app.main import bp as main_bp
from app.preview import bp as preview_bp
from app.workflow import bp as workflow_bp, api_workflow_bp
from modules.nav import bp as nav_bp
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
    migrate.init_app(app, get_db_conn)
    cache.init_app(app)
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Configure static files
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        response = send_from_directory(app.static_folder, filename)
        if filename.endswith('.js'):
            response.headers['Content-Type'] = 'application/javascript'
        return response
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(main_bp)
    app.register_blueprint(preview_bp, url_prefix='/preview')
    # Initialize workflow module (includes workflow_bp and api_workflow_bp)
    from app.workflow import init_workflow
    init_workflow(app)
    app.register_blueprint(nav_bp, url_prefix='/modules/nav')
    app.register_blueprint(db_bp)
    app.register_blueprint(settings_bp)
    
    # Register error handlers
    from app.errors import handlers
    app.register_error_handler(404, handlers.not_found_error)
    app.register_error_handler(500, handlers.internal_error)
    
    return app
