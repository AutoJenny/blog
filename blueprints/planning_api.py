"""
Planning API Module

Contains API endpoint functions extracted from planning.py
"""

from flask import request, jsonify
from config.database import db_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def api_calendar_categories():
    """Get all calendar categories"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, color, icon, is_active
                FROM calendar_categories
                WHERE is_active = TRUE
                ORDER BY name
            """)

            categories = cursor.fetchall()

            return jsonify({
                'success': True,
                'categories': categories
            })

    except Exception as e:
        logger.error(f"Error fetching calendar categories: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_prompt(prompt_type):
    """Get LLM prompt by type"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, model, temperature, max_tokens
                FROM llm_prompt 
                WHERE name ILIKE %s
                ORDER BY id DESC
                LIMIT 1
            """, (f'%{prompt_type}%',))
            
            prompt_data = cursor.fetchone()
            
            if prompt_data:
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'system_prompt': prompt_data['system_prompt'],
                        'prompt_text': prompt_data['prompt_text'],
                        'model': prompt_data['model'],
                        'temperature': prompt_data['temperature'],
                        'max_tokens': prompt_data['max_tokens']
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