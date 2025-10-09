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

def api_sections_title():
    """Stage 2: Create titles and descriptions for sections with allocated topics"""
    try:
        data = request.get_json()
        topic_allocation = data.get('topic_allocation', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        if not topic_allocation:
            return jsonify({
                'success': False,
                'error': 'No topic allocation provided'
            }), 400
        
        # Load Section Titling prompt from database
        logger.info("Loading Section Titling prompt from database")
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name = 'Section Titling'
                    ORDER BY id DESC
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if prompt_data and prompt_data['system_prompt']:
                    system_prompt = prompt_data['system_prompt']
                    logger.info("Loaded system prompt from database")
                else:
                    logger.warning("Section Titling system prompt not found in database, using fallback")
                    system_prompt = """You are a titling specialist. Your job is to craft short, poetic, evocative section titles that fit the supplied sections and their bullet topics. 

CONSTRAINTS:
- 2–4 words per title.
- No colons, dashes, or sub-clauses.
- Avoid literal echoes of the original section titles unless used metaphorically and sparingly.
- Use evocative imagery, mood, and metaphor; keep it culturally appropriate without naming specific festivals unless present in bullets.
- Title Case or Small Caps casing acceptable; no emoji; ASCII only.

OUTPUT:
- Strict JSON only, no prose.
- Exactly one title per input section, preserving input order.

FORMAT:
{
  "post_title": "<copied from input>",
  "sections": [
    { "index": 1, "original": "<original section title>", "title": "<2-4 word creative title>" },
    ...
  ]
}"""
                
                if prompt_data and prompt_data['prompt_text']:
                    prompt_text = prompt_data['prompt_text']
                else:
                    prompt_text = """Generate creative section titles for this post. Follow all constraints and output format exactly.

INPUT:
POST_TITLE:
[PLACEHOLDER]

SECTIONS_AND_TOPICS:
[PLACEHOLDER]

VALIDATION RULES:
- Ensure every section gets exactly one title
- Preserve original section order
- Output valid JSON only
- No explanatory text outside JSON"""

        except Exception as e:
            logger.error(f"Error loading Section Titling prompt: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to load Section Titling prompt'
            }), 500
        
        # Format the prompt with actual data
        formatted_prompt = prompt_text.replace('[PLACEHOLDER]', f"""
POST_TITLE:
{expanded_idea}

SECTIONS_AND_TOPICS:
{json.dumps(topic_allocation, indent=2)}
""")
        
        # Call LLM service
        try:
            # LLMService already imported at module level
            llm_service = LLMService()
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': formatted_prompt}
            ]
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
            
            if response and 'content' in response:
                # Parse the JSON response
                try:
                    result = json.loads(response['content'])
                    
                    # Validate the response structure
                    if 'sections' not in result:
                        raise ValueError("Response missing 'sections' key")
                    
                    if not isinstance(result['sections'], list):
                        raise ValueError("'sections' must be a list")
                    
                    # Validate each section
                    for i, section in enumerate(result['sections']):
                        if not isinstance(section, dict):
                            raise ValueError(f"Section {i} must be a dictionary")
                        if 'index' not in section or 'original' not in section or 'title' not in section:
                            raise ValueError(f"Section {i} missing required keys: index, original, title")
                    
                    return jsonify({
                        'success': True,
                        'result': result
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
                'error': 'Failed to generate section titles'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in api_sections_title: {e}")
        return jsonify({'error': str(e)}), 500


def api_save_sections(post_id):
    """Save generated sections to post_development table"""
    try:
        data = request.get_json()
        sections_data = data.get('sections', {})
        
        if not sections_data or 'sections' not in sections_data:
            return jsonify({
                'success': False,
                'error': 'No sections data provided'
            }), 400
        
        sections = sections_data['sections']
        section_headings = sections_data.get('section_headings', [])
        metadata = sections_data.get('metadata', {})
        
        # Sanitize before saving
        try:
            sections_data = sanitize_sections_text(sections_data)
        except Exception as _e:
            logger.warning(f"Sanitization failed, proceeding without changes: {_e}")

        # Convert to JSON strings for database storage
        sections_json = json.dumps(sections_data)
        headings_json = json.dumps(section_headings)
        
        # Create section order array
        section_order = [section.get('id', f"section_{i+1}") for i, section in enumerate(sections)]
        order_json = json.dumps(section_order)
        
        # Save to database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET sections = %s, section_headings = %s, section_order = %s, updated_at = %s
                WHERE post_id = %s
            """, (sections_json, headings_json, order_json, datetime.now(), post_id))
            
            if cursor.rowcount == 0:
                # Insert if no existing record
                cursor.execute("""
                    INSERT INTO post_development (post_id, sections, section_headings, section_order, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (post_id, sections_json, headings_json, order_json, datetime.now()))
        
        return jsonify({
            'success': True,
            'message': 'Sections saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in api_save_sections: {e}")
        return jsonify({'error': str(e)}), 500


def api_design_section_structure():
    """Step 1: Design 7-section blog structure"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        # Fetch topics from database if not provided
        if not topics:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT idea_scope 
                    FROM post_development 
                    WHERE post_id = %s AND idea_scope IS NOT NULL
                """, (post_id,))
                result = cursor.fetchone()
                if result:
                    idea_scope_data = json.loads(result['idea_scope'])
                    topics = idea_scope_data.get('generated_topics', [])
        
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
        
        # Load Section Structure Design prompt from database
        logger.info("Loading Section Structure Design prompt from database")
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name = 'Section Structure Design'
                    ORDER BY id DESC
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
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
        
        # Replace placeholders with actual data
        formatted_prompt = prompt_text.replace('[USER_TOPIC]', expanded_idea)
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
