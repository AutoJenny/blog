"""
Planning LLM Prompts API Module

Micro-file for LLM prompt-specific API endpoints
"""

from flask import request, jsonify
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

def api_get_prompt(prompt_type):
    """Get LLM prompt by type"""
    try:
        with db_manager.get_cursor() as cursor:
            # Try multiple search patterns for better matching
            search_patterns = [
                f'%{prompt_type}%',  # Contains the search term
                f'%{prompt_type.replace("-", " ")}%',  # Replace hyphens with spaces
                f'%{prompt_type.replace("-", "").replace("_", "")}%',  # Remove hyphens and underscores
            ]
            
            prompt_data = None
            for pattern in search_patterns:
                cursor.execute("""
                    SELECT name, system_prompt, prompt_text, parameters
                    FROM llm_prompt 
                    WHERE name ILIKE %s
                    ORDER BY id DESC
                    LIMIT 1
                """, (pattern,))
                
                prompt_data = cursor.fetchone()
                if prompt_data:
                    break
            
            if prompt_data:
                # Extract parameters from JSONB if they exist
                parameters = prompt_data['parameters'] or {}
                model = parameters.get('model', 'llama3.2:latest')
                temperature = parameters.get('temperature', 0.7)
                max_tokens = parameters.get('max_tokens', 2000)
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'system_prompt': prompt_data['system_prompt'],
                        'prompt_text': prompt_data['prompt_text'],
                        'model': model,
                        'temperature': temperature,
                        'max_tokens': max_tokens
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No prompt found for type: {prompt_type}'
                }), 404
                
    except Exception as e:
        logger.error(f"Error fetching prompt: {e}")
        return jsonify({'error': str(e)}), 500
