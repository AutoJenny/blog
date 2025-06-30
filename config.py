import os
from dotenv import load_dotenv
import re

basedir = os.path.abspath(os.path.dirname(__file__))

# Load .env for non-database settings (SECRET_KEY, etc.)
load_dotenv(os.path.join(basedir, ".env"))

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY") or "hard-to-guess-string"

    # TinyMCE
    TINYMCE_API_KEY = os.environ.get("TINYMCE_API_KEY")

    # Email
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

    # OpenAI
    OPENAI_AUTH_TOKEN = os.environ.get("OPENAI_AUTH_TOKEN")
    OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID")  # Optional
    OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_DEFAULT_MODEL = os.environ.get("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
    OPENAI_EMBEDDING_MODEL = os.environ.get(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )

    # Cache
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    # Celery
    CELERY_BROKER_URL = (
        os.environ.get("CELERY_BROKER_URL") or "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND = (
        os.environ.get("CELERY_RESULT_BACKEND") or "redis://localhost:6379/0"
    )

    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

    # LLM Service settings
    COMPLETION_SERVICE_TOKEN = os.environ.get("COMPLETION_SERVICE_TOKEN")
    OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
    DEFAULT_LLM_MODEL = os.environ.get("DEFAULT_LLM_MODEL", "llama3.1:70b")

    # Database
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")

    # Parse DATABASE_URL if present
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        match = re.match(r"postgres(?:ql)?://([^:]+)(?::([^@]+))?@([^:/]+)(?::(\d+))?/([^\s]+)", DATABASE_URL)
        if match:
            DB_USER = DB_USER or match.group(1)
            DB_PASSWORD = DB_PASSWORD or match.group(2)
            DB_HOST = DB_HOST or match.group(3)
            DB_PORT = DB_PORT or match.group(4)
            DB_NAME = DB_NAME or match.group(5)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    CACHE_TYPE = "redis"
    SSL_REDIRECT = True if os.environ.get("DYNO") else False

    @classmethod
    def init_app(cls, app):
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

def get_config(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    return config[config_name]

print('=== LLM API MODULE LOADED (AUDIT TEST) ===')