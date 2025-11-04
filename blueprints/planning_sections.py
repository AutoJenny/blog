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
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({
                'success': False,
                'error': 'No data provided in request'
            }), 400
        
        topic_allocation = data.get('topic_allocation', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        
        logger.info(f"Titling request: post_id={post_id}, sections={len(topic_allocation) if isinstance(topic_allocation, list) else 'not a list'}, expanded_idea_length={len(expanded_idea) if expanded_idea else 0}")
        
        if not topic_allocation:
            logger.error("No topic_allocation provided in request")
            return jsonify({
                'success': False,
                'error': 'No topic allocation provided'
            }), 400
        
        if not isinstance(topic_allocation, list):
            logger.error(f"topic_allocation is not a list: {type(topic_allocation)}")
            return jsonify({
                'success': False,
                'error': f'topic_allocation must be a list, got {type(topic_allocation).__name__}'
            }), 400
        
        if len(topic_allocation) == 0:
            logger.error("topic_allocation is an empty list")
            return jsonify({
                'success': False,
                'error': 'topic_allocation list is empty'
            }), 400
        
        # Load Section Titling prompt from database using explicit selection
        logger.info("Loading Section Titling prompt from database")
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
                        prompt_name = settings.get('section_titling_prompt_name')
                
                # LEGACY: If no selection exists, use default
                if not prompt_name:
                    prompt_name = 'Section Titling'
                
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
                    logger.warning("Section Titling system prompt not found in database, using fallback")
                    system_prompt = """You are a titling specialist. Your job is to craft short, poetic, evocative section titles that fit the supplied sections and their bullet topics.

CRITICAL: You MUST return ONLY valid JSON. Do NOT add any explanatory text, prose, or comments before or after the JSON. Your response must start with { and end with }. Do NOT say "Here's the JSON" or any similar phrases. 

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
        # Include comprehensive section information to help LLM generate all titles
        sections_text = ""
        for i, allocation in enumerate(topic_allocation):
            section_theme = allocation.get('section_theme', f'Section {i+1}')
            topics = allocation.get('topics', [])
            topics_text = ", ".join(topics[:5])  # Limit to first 5 topics to avoid prompt bloat
            if len(topics) > 5:
                topics_text += f" (and {len(topics) - 5} more)"
            sections_text += f"Section {i+1}:\n"
            sections_text += f"  Theme: {section_theme}\n"
            if topics_text:
                sections_text += f"  Topics: {topics_text}\n"
            sections_text += "\n"
        
        # Create explicit section list for the JSON template
        section_templates = []
        for i, allocation in enumerate(topic_allocation):
            section_theme = allocation.get('section_theme', f'Section {i+1}')
            section_templates.append(f'{{ "index": {i+1}, "original": "{section_theme}", "title": "Your Creative Title Here" }}')
        
        formatted_prompt = f"""Generate creative section titles for ALL {len(topic_allocation)} sections. Return ONLY valid JSON, no other text.

BLOG POST TOPIC: {expanded_idea}

SECTIONS TO TITLE (YOU MUST TITLE ALL {len(topic_allocation)} OF THESE):
{sections_text.strip()}

REQUIREMENTS:
- Generate EXACTLY {len(topic_allocation)} titles (one per section)
- Each title: 2-4 words, poetic and evocative
- Return ONLY JSON, no explanations, no prose, no text before or after
- Number sections 1 to {len(topic_allocation)}

OUTPUT FORMAT (JSON ONLY - NO OTHER TEXT):
{{
  "post_title": "{expanded_idea[:100] if expanded_idea else 'Blog Post'}",
  "sections": [
    {", ".join(section_templates)}
  ]
}}

CRITICAL: Your response must start with {{ and end with }}. Do NOT add any text before or after the JSON. Do NOT say "Here's the JSON" or any other explanatory text. Return ONLY the JSON object."""
        
        # Call LLM service
        try:
            # LLMService already imported at module level
            llm_service = LLMService()
            
            # Debug: Log the prompt length and content
            logger.info(f"Prompt length: {len(formatted_prompt)} characters")
            logger.info(f"Number of sections in prompt: {len(topic_allocation)}")
            logger.info(f"Prompt preview: {formatted_prompt[:500]}...")
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': formatted_prompt}
            ]
            
            # Increase max_tokens significantly for multiple sections
            # Each section needs ~150-200 tokens, plus JSON structure overhead
            # For 7 sections: 7 × 200 + 500 = 1900 minimum, but we give much more headroom
            max_tokens = max(6000, len(topic_allocation) * 500 + 2000)
            logger.info(f"Using max_tokens={max_tokens} for {len(topic_allocation)} sections")
            
            # Add temperature and other parameters for more consistent output
            response = llm_service.execute_llm_request(
                'ollama', 
                'llama3.2:latest', 
                messages, 
                max_tokens=max_tokens,
                temperature=0.7  # Lower temperature for more consistent output
            )
            
            if response and 'content' in response:
                # Debug: Log the raw response
                logger.info(f"Raw LLM response length: {len(response['content'])} characters")
                logger.info(f"Raw LLM response preview: {response['content'][:200]}...")
                
                # Parse the JSON response with better error handling
                try:
                    content = response['content'].strip()
                    
                    # Remove any explanatory text before the JSON
                    # Look for the first { character which should be the start of JSON
                    json_start = content.find('{')
                    if json_start == -1:
                        # No JSON found, try markdown code blocks
                        if '```json' in content:
                            json_start = content.find('```json') + 7
                        elif '```' in content:
                            json_start = content.find('```') + 3
                        else:
                            logger.error(f"No JSON found in response. Content preview: {content[:500]}")
                            raise ValueError("No JSON object found in LLM response")
                    else:
                        # Remove any text before the first {
                        content = content[json_start:]
                    
                    # Find the matching closing brace by counting braces
                    json_end = 0
                    brace_count = 0
                    for i, char in enumerate(content):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end == 0 or brace_count != 0:
                        logger.error(f"Could not find matching closing brace. Brace count: {brace_count}, Content preview: {content[:500]}")
                        # Try to use the rest of the content anyway
                        json_end = len(content)
                    
                    json_content = content[:json_end].strip()
                    
                    # Log the extracted JSON for debugging
                    logger.info(f"Extracted JSON (length {len(json_content)}): {json_content[:300]}...")
                    
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
                    
                    # CRITICAL VALIDATION: Ensure we have titles for ALL sections
                    if len(sections) < len(topic_allocation):
                        logger.error(f"LLM only generated {len(sections)} titles but {len(topic_allocation)} sections were requested!")
                        logger.error(f"Generated sections: {[s.get('index') for s in sections]}")
                        return jsonify({
                            'success': False,
                            'error': f'LLM only generated {len(sections)} titles but {len(topic_allocation)} sections were requested. Please try again.',
                            'expected_count': len(topic_allocation),
                            'actual_count': len(sections),
                            'raw_response': response['content']
                        }), 500
                    
                    # Merge topics from topic allocation with generated titles
                    # Match sections by index, ensuring we have one title per allocation
                    enhanced_sections = []
                    for i, allocation in enumerate(topic_allocation):
                        # Find the section with matching index
                        matching_section = None
                        for section in sections:
                            section_index = section.get('index')
                            # Handle both numeric and string indices
                            if section_index == i + 1 or str(section_index) == str(i + 1):
                                matching_section = section
                                break
                        
                        if not matching_section:
                            logger.error(f"Could not find generated title for section {i+1} (allocation: {allocation.get('section_theme')})")
                            logger.error(f"Available section indices: {[s.get('index') for s in sections]}")
                            raise ValueError(f"Missing title for section {i+1}: {allocation.get('section_theme')}")
                        
                        # Create enhanced section with topics
                        enhanced_section = {
                            'id': i + 1,
                            'index': matching_section.get('index', i + 1),
                            'title': matching_section.get('title', f'Section {i+1}'),
                            'subtitle': matching_section.get('original', allocation.get('section_theme', '')),
                            'order': matching_section.get('index', i + 1),
                            'topics': allocation.get('topics', [])
                        }
                        enhanced_sections.append(enhanced_section)
                    
                    logger.info(f"Enhanced {len(enhanced_sections)} sections with topics (expected {len(topic_allocation)})")
                    
                    # Final validation: ensure we have exactly the right number
                    if len(enhanced_sections) != len(topic_allocation):
                        logger.error(f"Mismatch: enhanced {len(enhanced_sections)} sections but {len(topic_allocation)} allocations")
                        raise ValueError(f"Section count mismatch: expected {len(topic_allocation)}, got {len(enhanced_sections)}")
                    
                    logger.info(f"Successfully processed all {len(enhanced_sections)} sections")
                    return jsonify({
                        'success': True,
                        'sections': enhanced_sections,
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
        sections_data = data.get('sections', [])
        
        logger.info(f"Saving sections for post {post_id}: received {len(sections_data) if isinstance(sections_data, list) else 'non-list'} sections")
        
        # Handle different data formats
        if isinstance(sections_data, list):
            # Direct array format from titling page
            sections = sections_data
            section_headings = []
            metadata = {}
        elif isinstance(sections_data, dict) and 'sections' in sections_data:
            # Nested format from other pages
            sections = sections_data['sections']
            section_headings = sections_data.get('section_headings', [])
            metadata = sections_data.get('metadata', {})
        else:
            return jsonify({
                'success': False,
                'error': 'No sections data provided'
            }), 400
        
        if not sections:
            return jsonify({
                'success': False,
                'error': 'No sections data provided'
            }), 400
        
        logger.info(f"Processing {len(sections)} sections for saving")
        
        # Sanitize before saving - ensure we always save as {'sections': [...]} format
        try:
            if isinstance(sections_data, list):
                # For titling page format, create a proper structure for sanitization
                sanitized_data = {'sections': sections_data}
                sanitized_data = sanitize_sections_text(sanitized_data)
                # Ensure we still have the sections array
                if isinstance(sanitized_data, dict) and 'sections' in sanitized_data:
                    sections_data = sanitized_data
                else:
                    # If sanitization changed format, restore it
                    sections_data = {'sections': sections}
            else:
                sections_data = sanitize_sections_text(sections_data)
        except Exception as _e:
            logger.warning(f"Sanitization failed, proceeding without changes: {_e}")
            # Ensure proper format even if sanitization fails
            if isinstance(sections_data, list):
                sections_data = {'sections': sections_data}

        logger.info(f"Final sections_data structure: type={type(sections_data)}, sections_count={len(sections_data.get('sections', [])) if isinstance(sections_data, dict) else len(sections_data) if isinstance(sections_data, list) else 0}")

        # Convert to JSON strings for database storage
        sections_json = json.dumps(sections_data)
        
        # Extract section headings for section_headings field (used by trigger to sync to post_section)
        if not section_headings:
            section_headings = [section.get('title', section.get('section_heading', f'Section {i+1}')) for i, section in enumerate(sections)]
        headings_json = json.dumps(section_headings)
        
        # Create section order array
        section_order = [section.get('id', section.get('order', i+1)) for i, section in enumerate(sections)]
        order_json = json.dumps(section_order)
        
        logger.info(f"Saving {len(sections)} sections: headings={len(section_headings)}, order={len(section_order)}")
        
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
            
            # Also write directly to post_section table to ensure all sections are saved
            logger.info(f"Writing {len(sections)} sections to post_section table")
            for i, section in enumerate(sections):
                section_order_val = section.get('order', section.get('index', i + 1))
                section_title = section.get('title', section.get('section_heading', f'Section {i+1}'))
                section_description = section.get('subtitle', section.get('section_description', section.get('original', '')))
                
                # Check if section already exists
                cursor.execute("""
                    SELECT id FROM post_section 
                    WHERE post_id = %s AND section_order = %s
                """, (post_id, section_order_val))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing section
                    cursor.execute("""
                        UPDATE post_section 
                        SET section_heading = %s, 
                            section_description = %s,
                            updated_at = %s
                        WHERE post_id = %s AND section_order = %s
                    """, (section_title, section_description, datetime.now(), post_id, section_order_val))
                    logger.info(f"Updated section {section_order_val}: {section_title}")
                else:
                    # Insert new section
                    cursor.execute("""
                        INSERT INTO post_section (post_id, section_order, section_heading, section_description, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, 'draft', %s, %s)
                    """, (post_id, section_order_val, section_title, section_description, datetime.now(), datetime.now()))
                    logger.info(f"Inserted section {section_order_val}: {section_title}")
            
            logger.info(f"Successfully saved {len(sections)} sections to post_section table")
        
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
