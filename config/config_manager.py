# config/config_manager.py
"""
Configuration Management Utility
Provides utilities for managing configuration across the unified application
"""

import os
import json
from typing import Dict, Any, Optional
from config.unified_config import get_config, get_database_url, get_redis_url

class ConfigManager:
    """Configuration management utility"""
    
    def __init__(self, config_name=None):
        self.config = get_config(config_name)
        self.config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': get_database_url(),
            'host': self.config.DB_HOST,
            'port': self.config.DB_PORT,
            'name': self.config.DB_NAME,
            'user': self.config.DB_USER,
            'password': self.config.DB_PASSWORD
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            'url': get_redis_url(),
            'host': self.config.REDIS_HOST,
            'port': self.config.REDIS_PORT,
            'db': self.config.REDIS_DB
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI/LLM configuration"""
        return {
            'openai_api_key': self.config.OPENAI_API_KEY,
            'ollama_host': self.config.OLLAMA_HOST,
            'anthropic_api_key': self.config.ANTHROPIC_API_KEY
        }
    
    def get_social_media_config(self) -> Dict[str, Any]:
        """Get social media configuration"""
        return {
            'facebook': {
                'app_id': self.config.FACEBOOK_APP_ID,
                'app_secret': self.config.FACEBOOK_APP_SECRET
            },
            'twitter': {
                'api_key': self.config.TWITTER_API_KEY,
                'api_secret': self.config.TWITTER_API_SECRET
            },
            'linkedin': {
                'client_id': self.config.LINKEDIN_CLIENT_ID,
                'client_secret': self.config.LINKEDIN_CLIENT_SECRET
            }
        }
    
    def get_clan_api_config(self) -> Dict[str, Any]:
        """Get Clan API configuration"""
        return {
            'base_url': self.config.CLAN_API_BASE_URL,
            'api_key': self.config.CLAN_API_KEY
        }
    
    def get_image_processing_config(self) -> Dict[str, Any]:
        """Get image processing configuration"""
        return {
            'enabled': self.config.IMAGE_PROCESSING_ENABLED,
            'max_width': self.config.IMAGE_MAX_WIDTH,
            'max_height': self.config.IMAGE_MAX_HEIGHT,
            'quality': self.config.IMAGE_QUALITY,
            'upload_folder': self.config.UPLOAD_FOLDER,
            'allowed_extensions': list(self.config.ALLOWED_EXTENSIONS)
        }
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration"""
        return {
            'server': self.config.MAIL_SERVER,
            'port': self.config.MAIL_PORT,
            'use_tls': self.config.MAIL_USE_TLS,
            'username': self.config.MAIL_USERNAME,
            'password': self.config.MAIL_PASSWORD,
            'default_sender': self.config.MAIL_DEFAULT_SENDER
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'secret_key': self.config.SECRET_KEY,
            'csrf_enabled': self.config.WTF_CSRF_ENABLED,
            'csrf_time_limit': self.config.WTF_CSRF_TIME_LIMIT,
            'session_cookie_secure': self.config.SESSION_COOKIE_SECURE,
            'session_cookie_httponly': self.config.SESSION_COOKIE_HTTPONLY,
            'session_cookie_samesite': self.config.SESSION_COOKIE_SAMESITE
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': self.config.LOG_LEVEL,
            'file': self.config.LOG_FILE,
            'format': self.config.LOG_FORMAT
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            'origins': self.config.CORS_ORIGINS,
            'supports_credentials': self.config.CORS_SUPPORTS_CREDENTIALS
        }
    
    def get_blueprint_config(self) -> Dict[str, str]:
        """Get blueprint configuration"""
        return self.config.BLUEPRINT_PREFIXES
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            'environment': self.config_name,
            'debug': self.config.DEBUG,
            'testing': self.config.TESTING,
            'database': self.get_database_config(),
            'redis': self.get_redis_config(),
            'ai': self.get_ai_config(),
            'social_media': self.get_social_media_config(),
            'clan_api': self.get_clan_api_config(),
            'image_processing': self.get_image_processing_config(),
            'email': self.get_email_config(),
            'security': self.get_security_config(),
            'logging': self.get_logging_config(),
            'cors': self.get_cors_config(),
            'blueprints': self.get_blueprint_config()
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required settings
        if not self.config.SECRET_KEY or self.config.SECRET_KEY == 'dev-secret-key-change-in-production':
            if self.config_name == 'production':
                validation_results['errors'].append('SECRET_KEY must be set in production')
                validation_results['valid'] = False
            else:
                validation_results['warnings'].append('SECRET_KEY is using default value')
        
        if not self.config.DATABASE_URL:
            validation_results['errors'].append('DATABASE_URL must be set')
            validation_results['valid'] = False
        
        # Check AI configuration
        if not self.config.OPENAI_API_KEY and not self.config.OLLAMA_HOST:
            validation_results['warnings'].append('No AI/LLM configuration found')
        
        # Check social media configuration
        social_config = self.get_social_media_config()
        if not any(social_config[platform].get('app_id') or social_config[platform].get('api_key') or social_config[platform].get('client_id') 
                  for platform in social_config):
            validation_results['warnings'].append('No social media configuration found')
        
        return validation_results
    
    def export_config(self, filename: str = None) -> str:
        """Export configuration to JSON file"""
        if not filename:
            filename = f"config_export_{self.config_name}.json"
        
        config_data = self.get_all_config()
        
        # Remove sensitive data
        if 'secret_key' in config_data.get('security', {}):
            config_data['security']['secret_key'] = '***REDACTED***'
        
        if 'password' in config_data.get('database', {}):
            config_data['database']['password'] = '***REDACTED***'
        
        if 'password' in config_data.get('email', {}):
            config_data['email']['password'] = '***REDACTED***'
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return filename
    
    def get_config_summary(self) -> str:
        """Get a summary of the current configuration"""
        validation = self.validate_config()
        
        summary = f"""
Configuration Summary for {self.config_name.upper()}:
===============================================

Environment: {self.config_name}
Debug Mode: {self.config.DEBUG}
Database: {self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}
Redis: {self.config.REDIS_HOST}:{self.config.REDIS_PORT}
Log Level: {self.config.LOG_LEVEL}

Validation Status: {'✅ VALID' if validation['valid'] else '❌ INVALID'}

Errors: {len(validation['errors'])}
Warnings: {len(validation['warnings'])}

Blueprints: {len(self.config.BLUEPRINT_PREFIXES)} registered
CORS Origins: {len(self.config.CORS_ORIGINS)} configured
        """
        
        if validation['errors']:
            summary += "\nErrors:\n" + "\n".join(f"  - {error}" for error in validation['errors'])
        
        if validation['warnings']:
            summary += "\nWarnings:\n" + "\n".join(f"  - {warning}" for warning in validation['warnings'])
        
        return summary

# Global instance
config_manager = ConfigManager()
