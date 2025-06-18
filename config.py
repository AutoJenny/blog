import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    """
    Base configuration class for the modular Flask project.
    Extend this class for module-specific configs as needed.
    All config values can be overridden by environment variables.
    """
    # Flask core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    TESTING = os.environ.get('FLASK_TESTING', '0') == '1'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/blog')
    
    # Caching
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', '')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '0') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')

    # Redis (optional)
    REDIS_URL = os.environ.get('REDIS_URL', '')

    # LLM/AI settings (example, extend as needed)
    OPENAI_API_BASE = os.environ.get('OPENAI_API_BASE', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL_NAME = os.environ.get('OPENAI_MODEL_NAME', '')
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', '')

    # Add module-specific config keys here as needed

# Example for a module-specific config (extend as needed)
# class WorkflowConfig(Config):
#     WORKFLOW_FEATURE_ENABLED = os.environ.get('WORKFLOW_FEATURE_ENABLED', '0') == '1' 