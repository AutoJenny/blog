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
        
        # Get year/week from request for theme lookup
        url_year = request.args.get('year', type=int) or data.get('year')
        url_week = request.args.get('week', type=int) or data.get('week')
        
        # Load prompt from database using explicit selection
        post_id = data.get('post_id')
        prompt_name = None
        theme_data = None
        
        with db_manager.get_cursor() as cursor:
            # Get selected prompt name from post settings if post_id provided
            if post_id:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('brainstorm_prompt_name')
            
            # If no selection exists, use default prompt names (old/new)
            if not prompt_name:
                prompt_name = 'brainstorm_topics'  # Try old name first
                cursor.execute("""
                    SELECT id FROM llm_prompt WHERE name = %s
                """, (prompt_name,))
                if not cursor.fetchone():
                    prompt_name = 'Topic Brainstorming'  # Try new name
            
            # Get the selected prompt - NO SILENT FALLBACKS
            cursor.execute("""
                SELECT system_prompt, prompt_text
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            system_prompt = prompt_data['system_prompt']
            prompt_text = prompt_data['prompt_text']
            
            # Get theme name and description from week context (if year/week provided)
            if url_year and url_week:
                # Use week persistence V2 selection view/table only; do not touch calendar_schedule
                cursor.execute("""
                    SELECT 
                        EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                              AND table_name = 'calendar_week_selection'
                        ) AS has_selection_table,
                        EXISTS (
                            SELECT FROM information_schema.views 
                            WHERE table_schema = 'public' 
                              AND table_name = 'calendar_week_selection_v2'
                        ) AS has_selection_view
                """)
                selection_check = cursor.fetchone()
                has_selection = selection_check['has_selection_table'] or selection_check['has_selection_view']
                
                if has_selection:
                    selection_source = 'calendar_week_selection' if selection_check['has_selection_table'] else 'calendar_week_selection_v2'
                    cursor.execute(f"""
                        SELECT selected_theme_id
                        FROM {selection_source}
                        WHERE year = %s AND week_number = %s
                    """, (url_year, url_week))
                    week_selection = cursor.fetchone()
                    
                    if week_selection and week_selection.get('selected_theme_id'):
                        theme_id = week_selection['selected_theme_id']
                        cursor.execute("""
                            SELECT ct.theme_title, ct.theme_description
                            FROM calendar_themes ct
                            WHERE ct.id = %s
                        """, (theme_id,))
                        theme_result = cursor.fetchone()
                        if theme_result:
                            theme_data = {
                                'title': theme_result.get('theme_title') or '',
                                'description': theme_result.get('theme_description') or ''
                            }
        
        # Generate topics using LLM
        llm_service = LLMService()
        
        # Determine topic count based on brainstorm type
        if brainstorm_type == 'comprehensive':
            # Use 30 topics instead of 50 to reduce LLM load and timeout risk
            topic_count = 30
        elif brainstorm_type == 'focused':
            topic_count = 25
        elif brainstorm_type == 'creative' or brainstorm_type == 'practical':
            topic_count = 30
        else:
            topic_count = 25  # Default
        
        # Build theme content string (similar to expanded idea prompt)
        theme_content = ''
        if theme_data and (theme_data.get('title') or theme_data.get('description')):
            if theme_data.get('title'):
                theme_content = f"Title: {theme_data['title']}\n\n"
            if theme_data.get('description'):
                theme_content += f"Description: {theme_data['description']}\n\n"
        
        # Replace topic count in prompt if specified, otherwise use format as-is
        # Handle both {brainstorm_type} and explicit count requirements
        if '{topic_count}' in prompt_text:
            user_content = prompt_text.format(
                brainstorm_type=brainstorm_type,
                theme_data=theme_content,
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
                theme_data=theme_content,
                expanded_idea=expanded_idea
            )
        else:
            user_content = prompt_text.format(
                brainstorm_type=brainstorm_type,
                theme_data=theme_content,
                expanded_idea=expanded_idea
            )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ]
        
        # Adjust max_tokens based on brainstorm type
        # Comprehensive now targets ~30 topics to reduce token usage and timeouts
        if brainstorm_type == 'comprehensive':
            max_tokens = 6000   # 30 topics with descriptions + overhead
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
            # Surface the actual LLM error if available
            error_msg = response.get('error') if isinstance(response, dict) else None
            if error_msg:
                return jsonify({'error': f'LLM error: {error_msg}'}), 500
            return jsonify({'error': 'Failed to generate topics (no content returned from LLM).'}), 500
            
    except Exception as e:
        logger.error(f"Error generating brainstorm topics: {e}")
        return jsonify({'error': str(e)}), 500
