from flask import Flask
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
from app.workflow import bp as workflow_bp
from modules.nav import bp as nav_bp

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
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(main_bp)
    app.register_blueprint(preview_bp, url_prefix='/preview')
    app.register_blueprint(workflow_bp)
    app.register_blueprint(nav_bp, url_prefix='/modules/nav')
    
    # Register error handlers
    from app.errors import handlers
    app.register_error_handler(404, handlers.not_found_error)
    app.register_error_handler(500, handlers.internal_error)
    
    return app
