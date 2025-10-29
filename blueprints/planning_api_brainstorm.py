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
        
        # Determine topic count based on brainstorm type
        if brainstorm_type == 'comprehensive':
            topic_count = 50
        elif brainstorm_type == 'focused':
            topic_count = 25
        elif brainstorm_type == 'creative' or brainstorm_type == 'practical':
            topic_count = 30
        else:
            topic_count = 25  # Default
        
        # Replace topic count in prompt if specified, otherwise use format as-is
        # Handle both {brainstorm_type} and explicit count requirements
        if '{topic_count}' in prompt_text:
            user_content = prompt_text.format(
                brainstorm_type=brainstorm_type,
                expanded_idea=expanded_idea,
                topic_count=topic_count
            )
        elif 'exactly 25' in prompt_text.lower() or 'exactly 50' in prompt_text.lower() or 'exactly' in prompt_text.lower():
            # Replace explicit counts in prompt text to match topic_count
            import re
            # Replace all instances of "exactly N" with the correct count
            user_content = re.sub(r'exactly\s+\d+', f'exactly {topic_count}', prompt_text, flags=re.IGNORECASE)
            # Also replace patterns like "25 topics" or "50 topics" but only specific known counts
            user_content = re.sub(r'\b(25|50)\s+topics?\b', f'{topic_count} topics', user_content, flags=re.IGNORECASE)
            user_content = user_content.format(
                brainstorm_type=brainstorm_type,
                expanded_idea=expanded_idea
            )
        else:
            user_content = prompt_text.format(
                brainstorm_type=brainstorm_type,
                expanded_idea=expanded_idea
            )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ]
        
        # Adjust max_tokens based on brainstorm type
        # Comprehensive needs 50 topics with descriptions (~150 tokens each) = ~8000 tokens minimum
        # Add overhead for JSON structure and model variance
        if brainstorm_type == 'comprehensive':
            max_tokens = 12000  # 50 topics × ~150 tokens + overhead
        elif brainstorm_type == 'focused':
            max_tokens = 5000   # 20-30 topics
        elif brainstorm_type == 'creative' or brainstorm_type == 'practical':
            max_tokens = 6000   # Similar to focused
        else:
            max_tokens = 6000   # Default
        
        response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=max_tokens)
        
        if response and 'content' in response:
            raw_content = response['content']
            topics = parse_brainstorm_topics(raw_content)
            
            # Log topic count for debugging
            logger.info(f"Generated {len(topics)} topics for brainstorm_type={brainstorm_type} (requested: 50 for comprehensive)")
            
            # Warn if comprehensive type got fewer than expected
            if brainstorm_type == 'comprehensive' and len(topics) < 45:
                logger.warning(f"Comprehensive brainstorm got only {len(topics)} topics (expected 50). Response may be truncated. Raw content length: {len(raw_content)} chars")
            
            return jsonify({
                'success': True,
                'topics': topics,
                'raw_content': raw_content,
                'topic_count': len(topics)
            })
        else:
            return jsonify({'error': 'Failed to generate topics'}), 500
            
    except Exception as e:
        logger.error(f"Error generating brainstorm topics: {e}")
        return jsonify({'error': str(e)}), 500
