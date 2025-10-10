"""
Planning Brainstorm API Module

Micro-file for brainstorm-specific API endpoints
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService, parse_brainstorm_topics
import logging
import json

logger = logging.getLogger(__name__)

def api_generate_brainstorm_topics():
    """Generate brainstorming topics using LLM"""
    try:
        data = request.get_json()
        expanded_idea = data.get('expanded_idea', '')
        brainstorm_type = data.get('brainstorm_type', 'general')
        
        if not expanded_idea:
            return jsonify({'error': 'Expanded idea is required'}), 400
        
        # Load prompt from database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT system_prompt, prompt_text
                FROM llm_prompt 
                WHERE name = 'brainstorm_topics'
                ORDER BY id DESC
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({
                    'error': 'No brainstorm_topics prompt found in database. Please add a proper prompt with JSON format specification.'
                }), 500
            
            system_prompt = prompt_data['system_prompt']
            prompt_text = prompt_data['prompt_text']
        
        # Generate topics using LLM
        llm_service = LLMService()
        
        user_content = prompt_text.format(
            brainstorm_type=brainstorm_type,
            expanded_idea=expanded_idea
        )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ]
        
        response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
        
        if response and 'content' in response:
            topics = parse_brainstorm_topics(response['content'])
            
            return jsonify({
                'success': True,
                'topics': topics,
                'raw_content': response['content']
            })
        else:
            return jsonify({'error': 'Failed to generate topics'}), 500
            
    except Exception as e:
        logger.error(f"Error generating brainstorm topics: {e}")
        return jsonify({'error': str(e)}), 500
