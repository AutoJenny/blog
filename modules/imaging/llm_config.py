# modules/imaging/llm_config.py - Imaging-specific LLM Configuration Storage

import json
import logging
from typing import Dict, Any, Optional
from config.database import db_manager

logger = logging.getLogger(__name__)

class ImagingLLMConfig:
    """Imaging-specific LLM configuration storage and management"""
    
    def __init__(self):
        self.config_table = 'imaging_llm_config'
        self.ensure_table_exists()
    
    def ensure_table_exists(self):
        """Ensure the imaging LLM config table exists"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS imaging_llm_config (
                        id SERIAL PRIMARY KEY,
                        config_key VARCHAR(255) UNIQUE NOT NULL,
                        config_value JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                logger.info("Imaging LLM config table ensured")
        except Exception as e:
            logger.error(f"Error ensuring imaging LLM config table: {e}")
            raise
    
    def save_config(self, config_key: str, config_data: Dict[str, Any]) -> bool:
        """Save imaging-specific LLM configuration"""
        try:
            with db_manager.get_cursor() as cursor:
                # Check if config already exists
                cursor.execute("""
                    SELECT id FROM imaging_llm_config 
                    WHERE config_key = %s
                """, (config_key,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing config
                    cursor.execute("""
                        UPDATE imaging_llm_config 
                        SET config_value = %s, updated_at = NOW()
                        WHERE config_key = %s
                    """, (json.dumps(config_data), config_key))
                else:
                    # Insert new config
                    cursor.execute("""
                        INSERT INTO imaging_llm_config (config_key, config_value)
                        VALUES (%s, %s)
                    """, (config_key, json.dumps(config_data)))
                
                logger.info(f"Imaging LLM config saved: {config_key}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving imaging LLM config: {e}")
            return False
    
    def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """Get imaging-specific LLM configuration"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT config_value FROM imaging_llm_config 
                    WHERE config_key = %s
                """, (config_key,))
                
                result = cursor.fetchone()
                if result:
                    return json.loads(result['config_value'])
                return None
                
        except Exception as e:
            logger.error(f"Error getting imaging LLM config: {e}")
            return None
    
    def save_image_generation_config(self, 
                                   image_model: str,
                                   llm_provider: str = None,
                                   llm_model: str = None,
                                   temperature: float = None,
                                   max_tokens: int = None,
                                   parameters: Dict[str, Any] = None) -> bool:
        """Save image generation specific configuration"""
        config_data = {
            'image_model': image_model,
            'llm_provider': llm_provider,
            'llm_model': llm_model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'parameters': parameters or {}
        }
        
        return self.save_config('image_generation', config_data)
    
    def get_image_generation_config(self) -> Optional[Dict[str, Any]]:
        """Get image generation specific configuration"""
        return self.get_config('image_generation')
    
    def save_model_preferences(self, 
                             preferred_models: Dict[str, str],
                             default_parameters: Dict[str, Any] = None) -> bool:
        """Save model preferences for imaging workflow"""
        config_data = {
            'preferred_models': preferred_models,
            'default_parameters': default_parameters or {}
        }
        
        return self.save_config('model_preferences', config_data)
    
    def get_model_preferences(self) -> Optional[Dict[str, Any]]:
        """Get model preferences for imaging workflow"""
        return self.get_config('model_preferences')
    
    def save_workflow_settings(self, 
                             auto_save: bool = True,
                             default_image_size: str = "1024x1024",
                             default_quality: str = "standard",
                             default_style: str = "natural") -> bool:
        """Save imaging workflow settings"""
        config_data = {
            'auto_save': auto_save,
            'default_image_size': default_image_size,
            'default_quality': default_quality,
            'default_style': default_style
        }
        
        return self.save_config('workflow_settings', config_data)
    
    def get_workflow_settings(self) -> Optional[Dict[str, Any]]:
        """Get imaging workflow settings"""
        return self.get_config('workflow_settings')
    
    def delete_config(self, config_key: str) -> bool:
        """Delete imaging-specific configuration"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM imaging_llm_config 
                    WHERE config_key = %s
                """, (config_key,))
                
                logger.info(f"Imaging LLM config deleted: {config_key}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting imaging LLM config: {e}")
            return False
    
    def list_configs(self) -> list:
        """List all imaging configurations"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT config_key, created_at, updated_at 
                    FROM imaging_llm_config 
                    ORDER BY updated_at DESC
                """)
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"Error listing imaging LLM configs: {e}")
            return []
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default imaging configuration"""
        return {
            'image_model': 'dall-e-3',
            'llm_provider': 'openai',
            'llm_model': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 1000,
            'parameters': {
                'size': '1024x1024',
                'quality': 'standard',
                'style': 'natural'
            },
            'workflow_settings': {
                'auto_save': True,
                'default_image_size': '1024x1024',
                'default_quality': 'standard',
                'default_style': 'natural'
            }
        }
