# config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'blog')
    DB_USER = os.getenv('DB_USER', 'autojenny')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Service settings
    CORE_PORT = os.getenv('CORE_PORT', '5000')
    LAUNCHPAD_PORT = os.getenv('LAUNCHPAD_PORT', '5001')
    LLM_ACTIONS_PORT = os.getenv('LLM_ACTIONS_PORT', '5002')
    POST_SECTIONS_PORT = os.getenv('POST_SECTIONS_PORT', '5003')
    POST_INFO_PORT = os.getenv('POST_INFO_PORT', '5004')
    IMAGES_PORT = os.getenv('IMAGES_PORT', '5005')
    CLAN_API_PORT = os.getenv('CLAN_API_PORT', '5006')
    
    # Unified app settings
    UNIFIED_PORT = os.getenv('UNIFIED_PORT', '5000')
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'unified_app.log')
    
    # Redis settings (if needed)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # External API settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    @classmethod
    def get_database_config(cls):
        """Get database configuration as dict."""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'dbname': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD
        }

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog_test')

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
