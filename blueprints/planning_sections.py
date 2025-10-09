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

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON, no other text whatsoever.
- Do NOT echo back the input data.
- Do NOT include section_id, section_theme, or topics in your response.
- Generate NEW creative titles for each section.
- Exactly one title per input section, preserving input order.

REQUIRED JSON FORMAT:
{
  "post_title": "<copied from input>",
  "sections": [
    { "index": 1, "original": "<original section title>", "title": "<2-4 word creative title>" },
    { "index": 2, "original": "<original section title>", "title": "<2-4 word creative title>" }
  ]
}

CRITICAL: Your response must contain ONLY the JSON object above. No other text.

IMPORTANT: Do NOT return the input data structure. Do NOT include section_id, section_theme, or topics in your response. Generate NEW creative titles based on the input, but return them in the required format above.

DO NOT USE THESE KEYS IN YOUR RESPONSE:
- SECTIONS_AND_TOPICS
- section_id
- section_theme  
- topics

ONLY USE THESE KEYS IN YOUR RESPONSE:
- post_title
- sections (with index, original, title)"""
                
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
        # Use the simplest possible format to avoid LLM confusion
        sections_text = ""
        for i, allocation in enumerate(topic_allocation):
            section_theme = allocation.get('section_theme', f'Section {i+1}')
            sections_text += f"{i+1}. {section_theme}\n"
        
        formatted_prompt = f"""Generate creative section titles for this blog post.

BLOG POST TOPIC: {expanded_idea}

SECTIONS TO TITLE:
{sections_text.strip()}

REQUIREMENTS:
- Generate exactly {len(topic_allocation)} titles
- Each title should be 2-4 words
- Make titles poetic and evocative
- Do not include the blog post topic in your titles

OUTPUT FORMAT (JSON only):
{{
  "post_title": "{expanded_idea}",
  "sections": [
    {{ "index": 1, "original": "{topic_allocation[0].get('section_theme', 'Section 1')}", "title": "Your Creative Title Here" }}
  ]
}}"""
        
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
                # Parse the JSON response with better error handling
                try:
                    content = response['content'].strip()
                    
                    # Try to extract JSON from the response (handle prose + JSON format)
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_content = content[json_start:json_end]
                    else:
                        # Fallback: try markdown code blocks
                        if content.startswith('```json') and content.endswith('```'):
                            json_content = content[7:-3].strip()
                        elif content.startswith('```') and content.endswith('```'):
                            json_content = content[3:-3].strip()
                        else:
                            json_content = content
                    
                    # Handle case where LLM includes input data in response (invalid JSON)
                    # Look for the first complete JSON object
                    try:
                        result = json.loads(json_content)
                    except json.JSONDecodeError:
                        # Try to find the first valid JSON object
                        lines = json_content.split('\n')
                        for i, line in enumerate(lines):
                            if line.strip().startswith('{'):
                                # Try to find the matching closing brace
                                brace_count = 0
                                json_lines = []
                                for j in range(i, len(lines)):
                                    json_lines.append(lines[j])
                                    for char in lines[j]:
                                        if char == '{':
                                            brace_count += 1
                                        elif char == '}':
                                            brace_count -= 1
                                    if brace_count == 0:
                                        break
                                try:
                                    partial_json = '\n'.join(json_lines)
                                    result = json.loads(partial_json)
                                    break
                                except json.JSONDecodeError:
                                    continue
                        else:
                            raise json.JSONDecodeError("No valid JSON found", json_content, 0)
                    
                    # Validate the response structure
                    logger.info(f"Parsed LLM result: {result}")
                    
                    sections = []
                    
                    # Handle different response formats
                    if 'sections' in result:
                        # Expected format: {"sections": [...]}
                        sections = result['sections']
                    elif isinstance(result, dict) and 'index' in result and 'original' in result and 'title' in result:
                        # Single section format: {"index": 1, "original": "...", "title": "..."}
                        sections = [result]
                    elif isinstance(result, list):
                        # Direct array format: [{"index": 1, ...}, {"index": 2, ...}]
                        sections = result
                    elif isinstance(result, dict) and ('section_id' in result or 'section_theme' in result or 'topics' in result or 'SECTIONS_AND_TOPICS' in result):
                        # LLM returned input data instead of output - this is an error case
                        logger.error(f"LLM returned input data instead of output. Keys: {list(result.keys())}")
                        logger.error(f"Full response: {result}")
                        raise ValueError("LLM returned input data instead of generating titles. Please try again.")
                    else:
                        logger.error(f"Unexpected response format. Available keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        raise ValueError(f"Unexpected response format. Available keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    
                    if not isinstance(sections, list):
                        logger.error(f"'sections' is not a list, it's: {type(sections)}")
                        raise ValueError(f"'sections' must be a list, got {type(sections)}")
                    
                    # Validate each section
                    for i, section in enumerate(sections):
                        if not isinstance(section, dict):
                            logger.error(f"Section {i} is not a dictionary: {section}")
                            raise ValueError(f"Section {i} must be a dictionary")
                        if 'index' not in section or 'original' not in section or 'title' not in section:
                            logger.error(f"Section {i} missing required keys. Available keys: {list(section.keys())}")
                            raise ValueError(f"Section {i} missing required keys: index, original, title. Available: {list(section.keys())}")
                    
                    logger.info(f"Successfully validated {len(sections)} sections")
                    return jsonify({
                        'success': True,
                        'sections': sections,
                        'raw_response': response['content']
                    })
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.error(f"Response content: {response['content']}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid JSON response from LLM',
                        'raw_response': response['content']
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
                            SET section_structure = %s, updated_at = %s
                            WHERE post_id = %s
                        """, (json.dumps({'sections': sections}), datetime.now(), post_id))
                        
                        if cursor.rowcount == 0:
                            # Insert if no existing record
                            cursor.execute("""
                                INSERT INTO post_development (post_id, section_structure, updated_at)
                                VALUES (%s, %s, %s)
                            """, (post_id, json.dumps({'sections': sections}), datetime.now()))
                    
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
