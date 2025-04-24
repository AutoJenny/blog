from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail
from celery import Celery
from flasgger import Swagger
from config import Config
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
mail = Mail()
celery = Celery(__name__)
swagger = Swagger()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)

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

    # Register context processors
    from app.main.context_processors import inject_year

    app.context_processor(inject_year)

    # Register blueprints
    from app.main import bp as main_bp
    from app.blog import bp as blog_bp
    from app.api import bp as api_bp
    from app.workflow import bp as workflow_bp
    from app.llm import bp as llm_bp
    from app.db import bp as db_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp, url_prefix="/blog")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(workflow_bp, url_prefix="/workflow")
    app.register_blueprint(llm_bp, url_prefix="/llm")
    app.register_blueprint(db_bp)

    # Register shell context
    @app.shell_context_processor
    def make_shell_context():
        from app.models import Post, Tag, LLMPrompt, LLMInteraction

        return {
            "db": db,
            "Post": Post,
            "Tag": Tag,
            "LLMPrompt": LLMPrompt,
            "LLMInteraction": LLMInteraction,
        }

    return app


from app import models
