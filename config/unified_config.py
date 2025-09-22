# config/unified_config.py
"""
Unified Configuration System for BlogForge
Centralizes all configuration from individual microservices
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings"""
    
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'blog')
    DB_USER = os.environ.get('DB_USER', 'autojenny')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'unified_app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Session Configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/content/posts')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # AI/LLM Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    
    # Clan API Configuration
    CLAN_API_BASE_URL = os.environ.get('CLAN_API_BASE_URL', 'https://api.clan.com')
    CLAN_API_KEY = os.environ.get('CLAN_API_KEY', '')
    
    # Redis Configuration (for caching)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@blogforge.com')
    
    # Social Media Configuration
    FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
    FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
    LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID', '')
    LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET', '')
    
    # Image Processing Configuration
    IMAGE_PROCESSING_ENABLED = os.environ.get('IMAGE_PROCESSING_ENABLED', 'True').lower() == 'true'
    IMAGE_MAX_WIDTH = int(os.environ.get('IMAGE_MAX_WIDTH', 1920))
    IMAGE_MAX_HEIGHT = int(os.environ.get('IMAGE_MAX_HEIGHT', 1080))
    IMAGE_QUALITY = int(os.environ.get('IMAGE_QUALITY', 85))
    
    # Cache Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Security Configuration
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600))
    
    # Performance Configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = DEBUG
    
    # Blueprint Configuration
    BLUEPRINT_PREFIXES = {
        'core': '',
        'launchpad': '/launchpad',
        'llm_actions': '/llm-actions',
        'post_sections': '/post-sections',
        'post_info': '/post-info',
        'images': '/images',
        'clan_api': '/clan-api',
        'database': '/db',
        'settings': '/settings'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://localhost:5001',
        'http://127.0.0.1:5001',
        'http://localhost:5002',
        'http://127.0.0.1:5002'
    ]
    
    # Development-specific database settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    
    # Development AI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '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')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog_test')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    
    # Production-specific settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Production security
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    
    # Production database
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

class StagingConfig(Config):
    """Staging configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    DATABASE_URL = os.environ.get('STAGING_DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog_staging')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])

def get_database_url():
    """Get database URL from configuration"""
    config_class = get_config()
    return config_class.DATABASE_URL

def get_redis_url():
    """Get Redis URL from configuration"""
    config_class = get_config()
    return config_class.REDIS_URL

def get_openai_api_key():
    """Get OpenAI API key from configuration"""
    config_class = get_config()
    return config_class.OPENAI_API_KEY

def get_ollama_host():
    """Get Ollama host from configuration"""
    config_class = get_config()
    return config_class.OLLAMA_HOST

def get_clan_api_key():
    """Get Clan API key from configuration"""
    config_class = get_config()
    return config_class.CLAN_API_KEY

def get_social_media_config():
    """Get social media configuration"""
    config_class = get_config()
    return {
        'facebook': {
            'app_id': config_class.FACEBOOK_APP_ID,
            'app_secret': config_class.FACEBOOK_APP_SECRET
        },
        'twitter': {
            'api_key': config_class.TWITTER_API_KEY,
            'api_secret': config_class.TWITTER_API_SECRET
        },
        'linkedin': {
            'client_id': config_class.LINKEDIN_CLIENT_ID,
            'client_secret': config_class.LINKEDIN_CLIENT_SECRET
        }
    }

def get_image_processing_config():
    """Get image processing configuration"""
    config_class = get_config()
    return {
        'enabled': config_class.IMAGE_PROCESSING_ENABLED,
        'max_width': config_class.IMAGE_MAX_WIDTH,
        'max_height': config_class.IMAGE_MAX_HEIGHT,
        'quality': config_class.IMAGE_QUALITY
    }

def get_blueprint_prefixes():
    """Get blueprint URL prefixes"""
    config_class = get_config()
    return config_class.BLUEPRINT_PREFIXES
