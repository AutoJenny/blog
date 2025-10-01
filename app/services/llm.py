"""
Llm Services module
Auto-generated from blueprints/planning.py
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from config.database import db_manager
import logging
from datetime import datetime, date
import json
import requests

logger = logging.getLogger(__name__)

# Create llm_bp blueprint
llm_bp = Blueprint('llm_bp', __name__, url_prefix='/api/llm')

"""

# Auto-generated from blueprints/planning.py
# Module: services/llm.py

# Function LLMService not found

@llm_bp.route('/run-llm')
def run_llm():
    """Execute LLM processing for planning steps."""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        stage = data.get('stage', 'planning')
        substage = data.get('substage', 'idea')
        step = data.get('step', 'initial_concept')
        task = data.get('task', '')
        output_field = data.get('output_field', 'basic_idea')
        
        if not post_id or not task:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get step configuration
        with db_manager.get_cursor() as cursor:
            # Get system and task prompts for this step
            cursor.execute("""
                SELECT lp.system_prompt, lp.prompt_text
                FROM llm_prompt lp
                JOIN workflow_step_entity ws ON ws.name = lp.name
                JOIN workflow_sub_stage_entity ss ON ss.id = ws.sub_stage_id
                JOIN workflow_stage_entity s ON s.id = ss.stage_id
                WHERE s.name ILIKE %s AND ss.name ILIKE %s AND ws.name ILIKE %s
                ORDER BY lp.id DESC
                LIMIT 1
            """, (stage, substage, step.replace('_', ' ').title()))
            
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'No prompts found for this step'}), 404
            
            # Build messages
            messages = []
            if prompt_data['system_prompt']:
                messages.append({'role': 'system', 'content': prompt_data['system_prompt']})
            
            # Use task prompt or user input
            user_content = prompt_data['prompt_text'] if prompt_data['prompt_text'] else task
            messages.append({'role': 'user', 'content': user_content})
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.1:8b', messages)
            
            if 'error' in result:
                return jsonify({'error': result['error']}), 500
            
            # Save result to database
            cursor.execute("""
                INSERT INTO post_development (post_id, {})
                VALUES (%s, %s)
                ON CONFLICT (post_id) 
                DO UPDATE SET {} = %s, updated_at = NOW()
            """.format(output_field, output_field), 
            (post_id, result['content'], result['content']))
            
            return jsonify({
                'success': True,
                'result': result['content'],
                'output_field': output_field
            })
    
    except Exception as e:
        logger.error(f"Error running LLM: {e}")
        return jsonify({'error': str(e)}), 500


