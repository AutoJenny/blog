from flask import Flask, jsonify
from flask_caching import Cache
from flask_mail import Mail
from celery import Celery
from flasgger import Swagger
from config import Config
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime
from flask_cors import CORS
from flask_migrate import Migrate
from app.database import get_db_conn

# DEPRECATED: SQLAlchemy ORM is being removed. Use direct SQL (psycopg2) for all DB access.

# Load environment variables
load_dotenv()

# Initialize extensions
cache = Cache()
mail = Mail()
celery = Celery(__name__)
swagger = Swagger()
migrate = Migrate()

print('=== FLASK APP __init__.py LOADED (AUDIT TEST) ===')

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    cache.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    migrate.init_app(app, get_db_conn)

    # Make config available to all templates
    @app.context_processor
    def inject_config():
        return dict(config=app.config)

    # Configure Celery
    celery.conf.update(app.config)
    celery.conf.beat_schedule = {
        "check-scheduled-posts": {
            "task": "app.tasks.check_scheduled_posts",
            "schedule": timedelta(minutes=1),
        },
        "cleanup-old-drafts": {
            "task": "app.tasks.cleanup_old_drafts",
            "schedule": timedelta(days=1),
            "kwargs": {"days": 30},
        },
    }

    # Ensure required directories exist
    for directory in ["logs", "static/uploads", "static/cache"]:
        os.makedirs(os.path.join(app.root_path, directory), exist_ok=True)

    # Configure logging
    if not app.debug and not app.testing:
        # Email error logs
        if app.config.get("MAIL_SERVER"):
            auth = None
            mail_username = app.config.get("MAIL_USERNAME")
            mail_password = app.config.get("MAIL_PASSWORD")
            if mail_username and mail_password:
                auth = (str(mail_username), str(mail_password))

            secure = None
            if app.config.get("MAIL_USE_TLS"):
                secure = ()

            mail_server = str(app.config.get("MAIL_SERVER"))
            mail_port = int(app.config.get("MAIL_PORT", 25))
            admin_email = app.config.get("ADMIN_EMAIL")

            if admin_email:
                mail_handler = SMTPHandler(
                    mailhost=(mail_server, mail_port),
                    fromaddr=str(
                        app.config.get("MAIL_DEFAULT_SENDER", "no-reply@example.com")
                    ),
                    toaddrs=[str(admin_email)],
                    subject="Blog Error",
                    credentials=auth,
                    secure=secure,
                )
                mail_handler.setLevel(logging.ERROR)
                app.logger.addHandler(mail_handler)

        # File logging
        file_handler = RotatingFileHandler(
            os.path.join(app.root_path, "logs", "blog.log"),
            maxBytes=10000,
            backupCount=10,
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info("Blog startup")

    # Register template context processors
    @app.context_processor
    def utility_processor():
        return {"year": datetime.utcnow().year}

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')

    # Temporarily disabled LLM blueprints
    # from app.llm import bp as llm_bp
    # app.register_blueprint(llm_bp, url_prefix='/llm')

    # from app.api.llm import bp as llm_api_bp
    # app.register_blueprint(llm_api_bp, url_prefix='/api/v1/llm')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Temporarily disabled workflow blueprint
    # from app.workflow.routes import workflow as workflow_bp
    # app.register_blueprint(workflow_bp, url_prefix='/workflow')

    from app.routes.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.database.routes import bp as db_bp
    app.register_blueprint(db_bp)

    # Add debug route listing
    @app.route('/debug/routes')
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'route': str(rule)
            })
        return jsonify(routes)

    print("\n=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}")
    print("=======================\n")

    return app

# from app import models
