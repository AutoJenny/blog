"""
Prompt Manager

Handles retrieval and formatting of content generation prompts.
"""

import logging
from typing import Dict, Optional
from config.database import db_manager

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt templates for content generation."""
    
    PROMPT_NAMES = {
        'product_deep_dive': 'product_content_generation',
        'category_feature': 'category_content_generation',
        'product_comparison': 'product_comparison_generation'
    }
    
    def __init__(self):
        self._prompt_cache = {}
    
    def get_prompt(self, prompt_type: str) -> Optional[Dict]:
        """
        Get prompt template by type.
        
        Args:
            prompt_type: 'product_deep_dive', 'category_feature', or 'product_comparison'
            
        Returns:
            Dictionary with 'name', 'system_prompt', 'prompt_text', 'parameters'
        """
        prompt_name = self.PROMPT_NAMES.get(prompt_type)
        if not prompt_name:
            logger.error(f"Unknown prompt type: {prompt_type}")
            return None
        
        # Check cache
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        # Fetch from database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt
                WHERE name = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """, (prompt_name,))
            
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Prompt not found: {prompt_name}")
                return None
            
            prompt_data = {
                'name': result['name'],
                'system_prompt': result['system_prompt'] or '',
                'prompt_text': result['prompt_text'] or '',
                'parameters': result['parameters'] or {}
            }
            
            # Cache it
            self._prompt_cache[prompt_name] = prompt_data
            
            return prompt_data
    
    def format_prompt(self, prompt_text: str, variables: Dict[str, str]) -> str:
        """
        Format prompt template with variables.
        
        Args:
            prompt_text: Prompt template with {variable} placeholders
            variables: Dictionary of variable values
            
        Returns:
            Formatted prompt text
        """
        formatted = prompt_text
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            formatted = formatted.replace(placeholder, str(value))
        
        return formatted
    
    def get_model_config(self, prompt_type: str) -> Dict:
        """
        Get model configuration for prompt type.
        
        Args:
            prompt_type: Prompt type identifier
            
        Returns:
            Dictionary with 'model', 'temperature', 'max_tokens'
        """
        prompt = self.get_prompt(prompt_type)
        if not prompt:
            # Default config
            return {
                'model': 'llama3.2:latest',
                'temperature': 0.7,
                'max_tokens': 4000
            }
        
        params = prompt.get('parameters', {})
        return {
            'model': params.get('model', 'llama3.2:latest'),
            'temperature': params.get('temperature', 0.7),
            'max_tokens': params.get('max_tokens', 4000)
        }

