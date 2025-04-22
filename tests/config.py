"""Test configuration settings."""

import os
import secrets
from datetime import timedelta

class TestConfig:
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Generate a random secret key for tests if not provided
    SECRET_KEY = os.environ.get('TEST_SECRET_KEY') or secrets.token_hex(32)
    WTF_CSRF_ENABLED = False
    
    # Test user credentials - must be provided via environment variables in CI/CD
    TEST_USER_EMAIL = os.environ.get('TEST_USER_EMAIL', 'test-user@example.com')
    TEST_USER_PASSWORD = os.environ.get('TEST_USER_PASSWORD') or secrets.token_urlsafe(16)
    
    # API keys - must be provided via environment variables
    OPENAI_API_KEY = os.environ.get('TEST_OPENAI_API_KEY')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 60
    
    # Mail configuration for testing
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'noreply@test.local'
    
    # Celery configuration for testing
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'memory://'
    
    @classmethod
    def init_app(cls, app):
        """Initialize application for testing."""
        app.logger.setLevel('ERROR')  # Reduce logging noise during tests 