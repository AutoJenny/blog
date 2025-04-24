"""Test configuration settings."""

import os
import secrets
from datetime import timedelta


class TestConfig:
    """Test configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Generate a random secret key for tests if not provided
    SECRET_KEY = os.environ.get("TEST_SECRET_KEY") or secrets.token_hex(32)
    WTF_CSRF_ENABLED = False

    # OpenAI settings
    OPENAI_AUTH_TOKEN = os.environ.get("TEST_OPENAI_AUTH_TOKEN")

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Cache configuration
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 60

    # Mail configuration for testing
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = "noreply@test.local"

    # Celery configuration for testing
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "memory://"

    # LLM Service settings
    COMPLETION_SERVICE_TOKEN = os.environ.get("TEST_COMPLETION_SERVICE_TOKEN")

    @classmethod
    def init_app(cls, app):
        """Initialize application for testing."""
        app.logger.setLevel("ERROR")  # Reduce logging noise during tests
