from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from celery import Celery
from flasgger import Swagger
from config import get_config
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
celery = Celery()
swagger = Swagger()
login = LoginManager()
login.login_view = 'auth.login'

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(get_config(config_name))
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    swagger.init_app(app)
    login.init_app(app)
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Ensure required directories exist
    for directory in ['logs', 'static/uploads', 'static/cache']:
        os.makedirs(os.path.join(app.root_path, directory), exist_ok=True)
    
    # Configure logging
    if not app.debug and not app.testing:
        # Email error logs
        if app.config.get('MAIL_SERVER'):
            auth = None
            if app.config.get('MAIL_USERNAME') or app.config.get('MAIL_PASSWORD'):
                auth = (app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD'))
            secure = None
            if app.config.get('MAIL_USE_TLS'):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT', 25)),
                fromaddr=app.config.get('MAIL_DEFAULT_SENDER', 'no-reply@example.com'),
                toaddrs=[app.config.get('ADMIN_EMAIL')],
                subject='Blog Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        
        # File logging
        file_handler = RotatingFileHandler(
            os.path.join(app.root_path, 'logs', 'blog.log'),
            maxBytes=10000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Blog startup')
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.llm import bp as llm_bp
    app.register_blueprint(llm_bp, url_prefix='/llm')
    
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # Register shell context
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Post': Post,
            'Tag': Tag,
            'LLMPrompt': LLMPrompt,
            'LLMInteraction': LLMInteraction
        }
    
    return app

from app.models import User, Post, Tag, LLMPrompt, LLMInteraction

@login.user_loader
def load_user(id):
    return User.query.get(int(id)) 