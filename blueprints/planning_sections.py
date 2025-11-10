"""
Planning Sections Module

Contains section-related API functions extracted from planning_original_backup.py
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Import titling functions from extracted module
from blueprints.planning_titling import api_sections_title, api_save_sections

def api_design_section_structure():
    """Step 1: Design 7-section blog structure"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        # Fetch topics and expanded_idea from database if not provided
        if not topics or not expanded_idea:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT idea_scope, expanded_idea 
                    FROM post_development 
                    WHERE post_id = %s AND (idea_scope IS NOT NULL OR expanded_idea IS NOT NULL)
                """, (post_id,))
                result = cursor.fetchone()
                if result:
                    if not topics and result['idea_scope']:
                        idea_scope_data = json.loads(result['idea_scope'])
                        topics = idea_scope_data.get('generated_topics', [])
                    if not expanded_idea and result['expanded_idea']:
                        expanded_idea = result['expanded_idea']
        
        if not topics:
            return jsonify({
                'success': False,
                'error': 'No topics found in database'
            }), 400
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        # Load Section Structure Design prompt from database using explicit selection
        logger.info("Loading Section Structure Design prompt from database")
        prompt_name = None
        try:
            with db_manager.get_cursor() as cursor:
                # Get selected prompt name from post settings if post_id provided
                if post_id:
                    cursor.execute("""
                        SELECT extra_settings FROM post WHERE id = %s
                    """, (post_id,))
                    post_result = cursor.fetchone()
                    
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                        prompt_name = settings.get('section_structure_prompt_name')
                
                # LEGACY: If no selection exists, use default
                if not prompt_name:
                    prompt_name = 'Section Structure Design'
                
                # Get the selected prompt - NO FALLBACKS
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
                    logger.error(f'Selected prompt "{prompt_name}" not found for post {post_id}')
                    return jsonify({
                        'success': False,
                        'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                    }), 404
                
                if prompt_data and prompt_data['system_prompt']:
                    system_prompt = prompt_data['system_prompt']
                    logger.info("Loaded system prompt from database")
                else:
                    logger.warning("Section Structure Design system prompt not found in database, using fallback")
                    system_prompt = """You are a blog structure specialist. Design a 7-section blog post structure based on the provided topics and expanded idea.

CONSTRAINTS:
- Create exactly 7 sections
- Each section should have a clear purpose and flow
- Sections should build logically from introduction to conclusion
- Use the provided topics to inform section content
- Avoid hardcoded content - use the actual topics provided

OUTPUT:
- Strict JSON only, no prose
- Exactly 7 sections with clear purposes

FORMAT:
{
  "sections": [
    { "id": 1, "title": "Section Title", "purpose": "Clear purpose description", "topics": ["topic1", "topic2"] },
    ...
  ]
}"""
                
                if prompt_data and prompt_data['prompt_text']:
                    prompt_text = prompt_data['prompt_text']
                else:
                    prompt_text = """Design a 7-section blog structure for this post. Use the provided topics and expanded idea to create logical sections.

INPUT:
EXPANDED_IDEA:
[PLACEHOLDER]

TOPICS:
[PLACEHOLDER]

VALIDATION RULES:
- Create exactly 7 sections
- Each section needs id, title, purpose, and topics
- Output valid JSON only
- No explanatory text outside JSON"""

        except Exception as e:
            logger.error(f"Error loading Section Structure Design prompt: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to load Section Structure Design prompt'
            }), 500
        
        # Format the prompt with actual data
        formatted_topics = "\n".join([f"- {t['title']}: {t['description']}" for t in topics])
        
        # Extract a concise topic from expanded_idea for better prompt clarity
        topic_for_prompt = expanded_idea
        if expanded_idea:
            # Try to extract the main topic from the expanded idea
            lines = expanded_idea.split('\n')
            for line in lines:
                if 'blog post' in line.lower() and '"' in line:
                    # Extract text between quotes
                    start = line.find('"')
                    end = line.find('"', start + 1)
                    if start != -1 and end != -1:
                        topic_for_prompt = line[start+1:end]
                        break
                elif 'Welsh' in line and ('mythology' in line.lower() or 'myths' in line.lower()):
                    # Extract Welsh mythology topic
                    topic_for_prompt = "Welsh mythology and folklore"
                    break
        
        # Replace placeholders with actual data
        formatted_prompt = prompt_text.replace('[USER_TOPIC]', topic_for_prompt)
        formatted_prompt = formatted_prompt.replace('[TOPICS_DATA]', formatted_topics)
        formatted_prompt = formatted_prompt.replace('[USER_CULTURE]', 'Celtic')  # Default to Celtic for now
        
        # Call LLM service
        try:
            # LLMService already imported at module level
            llm_service = LLMService()
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': formatted_prompt}
            ]
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=3000)
            
            if response and 'content' in response:
                # Parse the JSON response
                try:
                    result = json.loads(response['content'])
                    
                    # Handle both old format (with 'sections' key) and new format (direct array)
                    if isinstance(result, list):
                        sections = result
                    elif 'sections' in result:
                        sections = result['sections']
                    else:
                        raise ValueError("Response must be a JSON array or contain 'sections' key")
                    
                    if not isinstance(sections, list):
                        raise ValueError("'sections' must be a list")
                    
                    if len(sections) != 7:
                        raise ValueError(f"Expected exactly 7 sections, got {len(sections)}")
                    
                    # Validate each section
                    for i, section in enumerate(sections):
                        if not isinstance(section, dict):
                            raise ValueError(f"Section {i} must be a dictionary")
                        # Check for either old format (id, title, purpose, topics) or new format (section_code, title, description)
                        if 'section_code' in section and 'title' in section and 'description' in section:
                            # New format - convert to old format for compatibility
                            section['id'] = section['section_code']
                            section['purpose'] = section['description']
                            section['topics'] = []  # Topics will be allocated later
                        elif 'id' in section and 'title' in section and 'purpose' in section:
                            # Old format - already correct
                            pass
                        else:
                            raise ValueError(f"Section {i} missing required keys: must have either (section_code, title, description) or (id, title, purpose)")
                    
                    # Save the generated structure to database
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            UPDATE post_development 
                            SET section_structure = %s, structure_design_at = %s, updated_at = %s
                            WHERE post_id = %s
                        """, (json.dumps({'sections': sections}), datetime.now(), datetime.now(), post_id))
                        
                        if cursor.rowcount == 0:
                            # Insert if no existing record
                            cursor.execute("""
                                INSERT INTO post_development (post_id, section_structure, structure_design_at, updated_at)
                                VALUES (%s, %s, %s, %s)
                            """, (post_id, json.dumps({'sections': sections}), datetime.now(), datetime.now()))
                    
                    logger.info(f"Section structure saved to database for post {post_id}")
                    
                    return jsonify({
                        'success': True,
                        'section_structure': {'sections': sections},
                        'raw_response': response['content']
                    })
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.error(f"Response content: {response['content']}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid JSON response from LLM'
                    }), 500
                    
                except ValueError as e:
                    logger.error(f"Invalid response structure: {e}")
                    logger.error(f"Response content: {response['content']}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid response structure: {str(e)}'
                    }), 500
            else:
                logger.error("No content in LLM response")
                return jsonify({
                    'success': False,
                    'error': 'No content in LLM response'
                }), 500
                
        except Exception as e:
            logger.error(f"Error calling LLM service: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate section structure'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in api_design_section_structure: {e}")
        return jsonify({'error': str(e)}), 500


def sanitize_sections_text(sections_data):
    """Sanitize sections text data"""
    # This function should be implemented if it exists elsewhere
    # For now, return the data as-is
    return sections_data
