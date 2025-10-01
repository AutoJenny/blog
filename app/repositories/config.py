"""
Config Repository module
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from config.database import db_manager
import logging
from datetime import datetime, date
import json
import requests

logger = logging.getLogger(__name__)

# Create config_bp blueprint
config_bp = Blueprint('config_bp', __name__, url_prefix='/api/config')

"""

# Auto-generated from blueprints/planning.py
# Module: repositories/config.py

@config_bp.route('/get-step-config')
def get_step_config(stage, substage, step):
    """Get step configuration for LLM actions."""
    try:
        with db_manager.get_cursor() as cursor:
            # Convert step name from URL format to database format
            db_step_name = step.replace('_', ' ').title()
            
            cursor.execute("""
                SELECT ws.id, ws.name, ws.description, ws.config
                FROM workflow_stage_entity s
                JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
                WHERE s.name ILIKE %s
                AND ss.name ILIKE %s
                AND ws.name ILIKE %s
            """, (stage, substage, db_step_name))
            result = cursor.fetchone()
            
            if result:
                # Handle config - it might already be a dict or a JSON string
                if isinstance(result['config'], dict):
                    config = result['config']
                elif isinstance(result['config'], str):
                    try:
                        config = json.loads(result['config'])
                    except json.JSONDecodeError:
                        config = {}
                else:
                    config = {}
                
                return jsonify({
                    'step_id': result['id'],
                    'step_name': result['name'],
                    'description': result['description'],
                    'config': config
                })
            else:
                return jsonify({'error': 'Step not found'}), 404
    
    except Exception as e:
        logger.error(f"Error getting step config: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/get-system-prompts')
def get_system_prompts():
    """Get all system prompts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT lp.id, lp.name, lp.description, 
                       COALESCE(lp.system_prompt, '') as system_prompt,
                       COALESCE(lp.prompt_text, '') as prompt_text
                FROM llm_prompt lp
                WHERE lp.system_prompt IS NOT NULL AND lp.system_prompt != ''
                ORDER BY lp.name
            """)
            system_prompts = cursor.fetchall()

            return jsonify({
                'system_prompts': [dict(prompt) for prompt in system_prompts]
            })
    except Exception as e:
        logger.error(f"Error getting system prompts: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/get-providers')
def get_providers():
    """Get available LLM providers."""
    try:
        providers = []
        for key, provider in llm_service.providers.items():
            providers.append({
                'id': key,
                'name': provider['name'],
                'base_url': provider['base_url'],
                'models': llm_service.get_available_models(key)
            })
        return jsonify(providers)
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/get-actions')
def get_actions():
    """Get all LLM actions/prompts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT lp.id, lp.name, lp.description, 
                       COALESCE(lp.system_prompt, '') as system_prompt,
                       COALESCE(lp.prompt_text, '') as prompt_text
                FROM llm_prompt lp
                WHERE lp.system_prompt IS NULL OR lp.system_prompt = ''
                ORDER BY lp.name
            """)
            task_prompts = cursor.fetchall()

            return jsonify({
                'task_prompts': [dict(prompt) for prompt in task_prompts]
            })
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/get-section-keywords')
def get_section_keywords(theme, description):
    """Extract relevant keywords for a section to help with topic matching"""
    # Convert to lowercase for matching
    text = f"{theme} {description}".lower()
    
    # Define keyword patterns for different types of content
    keywords = []
    
    # Historical/Ancient themes
    if any(word in text for word in ['celtic', 'ancient', 'origins', 'roots', 'historical', 'evolution', 'reformation']):
        keywords.extend(['ancient', 'historical', 'origins', 'celtic', 'roots'])
    
    # Harvest/Festival themes  
    if any(word in text for word in ['harvest', 'festival', 'celebration', 'rural', 'agricultural', 'crops']):
        keywords.extend(['harvest', 'festival', 'rural', 'agricultural', 'celebration'])
    
    # Ceres-specific themes
    if any(word in text for word in ['ceres', 'symbolism', 'ancient festival']):
        keywords.extend(['ceres', 'symbolism', 'ancient'])
    
    # Christianity themes
    if any(word in text for word in ['christianity', 'christian', 'intersection', 'influence', 'religion']):
        keywords.extend(['christianity', 'religion', 'intersection'])
    
    # Mythology themes
    if any(word in text for word in ['mythology', 'myth', 'symbolism', 'folklore', 'creatures', 'music', 'dance']):
        keywords.extend(['mythology', 'folklore', 'symbolism', 'music', 'dance', 'creatures'])
    
    # Rural community themes
    if any(word in text for word in ['rural', 'community', 'communities', 'traditions', 'practical']):
        keywords.extend(['rural', 'community', 'traditions', 'practical'])
    
    # Modern/Urban themes
    if any(word in text for word in ['modern', 'urban', 'revival', 'contemporary', 'today']):
        keywords.extend(['modern', 'urban', 'revival', 'contemporary'])
    
    return list(set(keywords))  # Remove duplicates


