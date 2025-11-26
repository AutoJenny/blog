"""
Planning Sections Module

Contains section-related API functions extracted from planning_original_backup.py
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Import titling functions from extracted module
from blueprints.planning_titling import api_sections_title, api_save_sections

def api_design_section_structure():
    """Step 1: Design section structure (7-section for themed posts, 11-section for profile posts)"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        expanded_idea = data.get('expanded_idea', '')
        post_id = data.get('post_id')
        product_data = data.get('product_data')
        post_type = data.get('post_type')
        
        # For profile posts, use product_data instead of topics
        if post_type == 'profile':
            if not product_data:
                logger.error(f"Profile post {post_id} missing product_data in request")
                return jsonify({
                    'success': False,
                    'error': 'Product data is required for profile posts'
                }), 400
            # Skip topic fetching for profile posts - product_data is provided
        else:
            # Fetch topics and expanded_idea from database if not provided (for themed posts)
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
                    # For profile posts, update the system prompt to specify 11 sections
                    if post_type == 'profile':
                        system_prompt = system_prompt.replace('7 sections', '11 sections')
                        system_prompt = system_prompt.replace('exactly 7', 'exactly 11')
                        system_prompt = system_prompt.replace('7-section', '11-section')
                else:
                    logger.warning("Section Structure Design system prompt not found in database, using fallback")
                    if post_type == 'profile':
                        system_prompt = """You are a blog structure specialist. Design an 11-section product profile blog post structure based on the provided product data.

CONSTRAINTS:
- Create exactly 11 sections
- Each section should have a clear purpose and flow
- Sections should build logically from introduction to conclusion
- Use the provided product data to inform section content
- Follow the standard product profile structure: Hero Block, The Object, Heritage & Origins (if available), The Maker (if available), Materials & Making, In Context, Features & Specifications, Care & Maintenance, Gallery (if images available), Explore Further, Credits & Sources

CRITICAL JSON FORMAT REQUIREMENTS - READ CAREFULLY:

YOUR RESPONSE MUST:
1. Start with the character { (opening brace)
2. End with the character } (closing brace)
3. Contain ONLY valid JSON - no other text whatsoever
4. Have NO markdown code blocks (no ```json or ```)
5. Have NO explanatory text before the {
6. Have NO explanatory text after the }
7. Have NO comments or prose anywhere
8. Use proper JSON syntax:
   - All strings in double quotes "
   - No trailing commas before closing brackets/braces
   - Proper comma separation between array elements
   - Proper closing of all brackets and braces

FORBIDDEN RESPONSES:
❌ "Here is the JSON structure:"
❌ "```json\n{...}\n```"
❌ Any text before {
❌ Any text after }
❌ Comments like // or /* */
❌ Trailing commas like ,] or ,}

REQUIRED FORMAT (copy this exactly):
{
  "sections": [
    { "section_code": "S01", "title": "Section Title", "description": "Clear purpose description", "section_type": "profile_hero", "data_sources": ["source1"], "conditional": null },
    { "section_code": "S02", "title": "Section Title", "description": "Clear purpose description", "section_type": "profile_object", "data_sources": ["source2"], "conditional": null }
  ]
}

VALIDATION CHECKLIST - Before submitting, verify:
□ Response starts with {
□ Response ends with }
□ No text before {
□ No text after }
□ No markdown code blocks
□ All strings use double quotes
□ No trailing commas
□ Valid JSON syntax throughout
□ Exactly 11 sections (S01 through S11)

IF YOUR RESPONSE DOES NOT START WITH { AND END WITH }, IT WILL FAIL.
IF YOUR RESPONSE CONTAINS ANY TEXT OTHER THAN JSON, IT WILL FAIL.
IF YOUR RESPONSE HAS INVALID JSON SYNTAX, IT WILL FAIL.

RETURN ONLY THE JSON OBJECT. NOTHING ELSE."""
                    else:
                        system_prompt = """You are a blog structure specialist. Design a 7-section blog post structure based on the provided topics and expanded idea.

CONSTRAINTS:
- Create exactly 7 sections
- Each section should have a clear purpose and flow
- Sections should build logically from introduction to conclusion
- Use the provided topics to inform section content
- Avoid hardcoded content - use the actual topics provided

CRITICAL JSON FORMAT REQUIREMENTS - READ CAREFULLY:

YOUR RESPONSE MUST:
1. Start with the character { (opening brace)
2. End with the character } (closing brace)
3. Contain ONLY valid JSON - no other text whatsoever
4. Have NO markdown code blocks (no ```json or ```)
5. Have NO explanatory text before the {
6. Have NO explanatory text after the }
7. Have NO comments or prose anywhere
8. Use proper JSON syntax:
   - All strings in double quotes "
   - No trailing commas before closing brackets/braces
   - Proper comma separation between array elements
   - Proper closing of all brackets and braces

FORBIDDEN RESPONSES:
❌ "Here is the JSON structure:"
❌ "```json\n{...}\n```"
❌ Any text before {
❌ Any text after }
❌ Comments like // or /* */
❌ Trailing commas like ,] or ,}

REQUIRED FORMAT (copy this exactly):
{
  "sections": [
    { "id": 1, "title": "Section Title", "purpose": "Clear purpose description", "topics": [] },
    { "id": 2, "title": "Section Title", "purpose": "Clear purpose description", "topics": [] }
  ]
}

VALIDATION CHECKLIST - Before submitting, verify:
□ Response starts with {
□ Response ends with }
□ No text before {
□ No text after }
□ No markdown code blocks
□ All strings use double quotes
□ No trailing commas
□ Valid JSON syntax throughout
□ Exactly 7 sections

IF YOUR RESPONSE DOES NOT START WITH { AND END WITH }, IT WILL FAIL.
IF YOUR RESPONSE CONTAINS ANY TEXT OTHER THAN JSON, IT WILL FAIL.
IF YOUR RESPONSE HAS INVALID JSON SYNTAX, IT WILL FAIL.

RETURN ONLY THE JSON OBJECT. NOTHING ELSE."""
                
                if prompt_data and prompt_data['prompt_text']:
                    prompt_text = prompt_data['prompt_text']
                    # For profile posts, update the prompt text to specify 11 sections
                    if post_type == 'profile':
                        prompt_text = prompt_text.replace('7 sections', '11 sections')
                        prompt_text = prompt_text.replace('exactly 7', 'exactly 11')
                        prompt_text = prompt_text.replace('7-section', '11-section')
                else:
                    if post_type == 'profile':
                        prompt_text = """Design an 11-section product profile blog structure for this post. Use the provided product data to create logical sections following the standard product profile structure.

PRODUCT DATA:
[PLACEHOLDER]

STANDARD PRODUCT PROFILE SECTIONS (11 total):
1. Hero Block (Required) - Visual introduction with headline and standfirst
2. The Object (Required) - Product concept, design, and distinctive qualities
3. Heritage & Origins (Conditional) - Historical context if heritage data exists
4. The Maker (Conditional) - Producer/workshop story if supplier data exists
5. Materials & Making (Required) - Materials, processes, craftsmanship
6. In Context (Required) - Usage, occasions, styling, cultural fit
7. Features & Specifications (Required) - Features, options, technical details
8. Care & Maintenance (Required) - Care instructions, cleaning, storage
9. Gallery (Conditional) - Visual showcase if images available
10. Explore Further (Required) - Commerce links
11. Credits & Sources (Required) - Attribution

CRITICAL JSON FORMAT REQUIREMENTS - READ CAREFULLY:

YOUR RESPONSE MUST:
1. Start with the character { (opening brace)
2. End with the character } (closing brace)
3. Contain ONLY valid JSON - no other text whatsoever
4. Have NO markdown code blocks (no ```json or ```)
5. Have NO explanatory text before the {
6. Have NO explanatory text after the }
7. Have NO comments or prose anywhere
8. Use proper JSON syntax:
   - All strings in double quotes "
   - No trailing commas before closing brackets/braces
   - Proper comma separation between array elements
   - Proper closing of all brackets and braces

FORBIDDEN RESPONSES:
❌ "Here is the JSON structure:"
❌ "```json\n{...}\n```"
❌ Any text before {
❌ Any text after }
❌ Comments like // or /* */
❌ Trailing commas like ,] or ,}

REQUIRED FORMAT (copy this exactly):
{
  "sections": [
    { "section_code": "S01", "title": "Section Title", "description": "Clear purpose description", "section_type": "profile_hero", "data_sources": ["source1"], "conditional": null },
    { "section_code": "S02", "title": "Section Title", "description": "Clear purpose description", "section_type": "profile_object", "data_sources": ["source2"], "conditional": null }
  ]
}

VALIDATION CHECKLIST - Before submitting, verify:
□ Response starts with {
□ Response ends with }
□ No text before {
□ No text after }
□ No markdown code blocks
□ All strings use double quotes
□ No trailing commas
□ Valid JSON syntax throughout
□ Exactly 11 sections (S01 through S11)

IF YOUR RESPONSE DOES NOT START WITH { AND END WITH }, IT WILL FAIL.
IF YOUR RESPONSE CONTAINS ANY TEXT OTHER THAN JSON, IT WILL FAIL.
IF YOUR RESPONSE HAS INVALID JSON SYNTAX, IT WILL FAIL.

RETURN ONLY THE JSON OBJECT. NOTHING ELSE."""
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

CRITICAL JSON FORMAT REQUIREMENTS:
- Your response MUST start with [ and end with ]
- NO markdown code blocks (no ```json or ```)
- NO explanatory text before [ or after ]
- NO comments or prose anywhere
- Valid JSON syntax only (proper quotes, no trailing commas, proper brackets)
- Return ONLY the JSON array, nothing else

REQUIRED FORMAT:
[
  { "id": 1, "title": "Section Title", "purpose": "Purpose description", "topics": [] },
  { "id": 2, "title": "Section Title", "purpose": "Purpose description", "topics": [] }
]

IF YOUR RESPONSE DOES NOT START WITH [ AND END WITH ], IT WILL FAIL."""

        except Exception as e:
            logger.error(f"Error loading Section Structure Design prompt: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to load Section Structure Design prompt'
            }), 500
        
        # Format the prompt with actual data
        if post_type == 'profile':
            if not product_data:
                logger.error(f"Profile post {post_id} missing product_data")
                return jsonify({
                    'success': False,
                    'error': 'Product data is required for profile posts. Please ensure the product is linked to this post.'
                }), 400
            # For profile posts, format product data
            try:
                product_type_data = product_data.get('product_type_data', {}) or {}
                materials = product_type_data.get('materials', []) or []
                decorations = product_type_data.get('decorations', []) or []
                occasions = product_type_data.get('occasions', []) or []
                categories = product_data.get('categories', []) or []
                
                product_summary = f"""
PRODUCT NAME: {product_data.get('name', 'Unknown')}
PRODUCT TYPE: {product_type_data.get('core_type', 'Unknown')}
MATERIALS: {', '.join(materials) if materials else 'Not specified'}
DECORATIONS: {', '.join(decorations) if decorations else 'None'}
OCCASIONS: {', '.join(occasions) if occasions else 'Not specified'}
SUPPLIER: {product_data.get('supplier_name', 'Unknown')}
HERITAGE DATA: {'Available' if product_data.get('has_heritage_data') else 'Not available'}
CATEGORIES: {', '.join([c.get('name', '') for c in categories if c and isinstance(c, dict)]) if categories else 'Not specified'}
"""
                formatted_prompt = prompt_text.replace('[PLACEHOLDER]', product_summary)
                formatted_prompt = formatted_prompt.replace('[EXPANDED_IDEA]', product_summary)
                formatted_prompt = formatted_prompt.replace('[TOPICS]', product_summary)
            except Exception as e:
                logger.error(f"Error formatting product data for prompt: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'Error formatting product data: {str(e)}'
                }), 500
        else:
            # For themed posts, format topics
            try:
                formatted_topics = "\n".join([f"- {t.get('title', 'Untitled')}: {t.get('description', 'No description')}" for t in topics if t])
            except Exception as e:
                logger.error(f"Error formatting topics: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'Error formatting topics: {str(e)}'
                }), 500
            
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
            formatted_prompt = formatted_prompt.replace('[PLACEHOLDER]', formatted_topics)
            formatted_prompt = formatted_prompt.replace('[EXPANDED_IDEA]', expanded_idea or '')
            formatted_prompt = formatted_prompt.replace('[TOPICS]', formatted_topics)
        
        # Call LLM service
        try:
            # LLMService already imported at module level
            llm_service = LLMService()
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': formatted_prompt}
            ]
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=3000)
            
            # Check for errors in response
            if 'error' in response:
                logger.error(f"LLM service returned error: {response['error']}")
                return jsonify({
                    'success': False,
                    'error': f"LLM service error: {response['error']}"
                }), 500
            
            if not response:
                logger.error("LLM service returned empty response")
                return jsonify({
                    'success': False,
                    'error': 'LLM service returned empty response'
                }), 500
            
            if 'content' not in response:
                logger.error(f"LLM response missing 'content' key. Response keys: {response.keys() if response else 'None'}")
                return jsonify({
                    'success': False,
                    'error': 'LLM response missing content'
                }), 500
            
            if response and 'content' in response:
                # Parse the JSON response - use robust parsing that handles extra content
                try:
                    content = response['content'].strip()
                    import re
                    
                    # Step 1: Try to extract JSON from markdown code blocks (most reliable)
                    json_text = None
                    json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', content, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1).strip()
                        logger.info("Extracted JSON array from code block")
                    else:
                        # Try JSON object in code blocks
                        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content, re.DOTALL)
                        if json_match:
                            json_text = json_match.group(1).strip()
                            logger.info("Extracted JSON object from code block")
                    
                    # Step 2: Parse JSON - use raw_decode to handle any extra content robustly
                    result = None
                    if json_text:
                        # Even if extracted from code block, use raw_decode to be safe
                        try:
                            decoder = json.JSONDecoder()
                            result, idx = decoder.raw_decode(json_text)
                            if idx < len(json_text.strip()):
                                logger.info(f"Code block had extra content (ignored {len(json_text) - idx} chars)")
                        except json.JSONDecodeError as parse_error:
                            # Fallback: try aggressive cleaning of common JSON issues
                            logger.warn(f"Initial parse failed: {parse_error}. Attempting aggressive cleanup...")
                            cleaned = json_text
                            
                            # Fix trailing commas before closing brackets/braces (most common issue)
                            cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                            # Fix trailing commas at end of lines before closing brackets/braces
                            cleaned = re.sub(r',(\s*\n\s*[}\]])', r'\1', cleaned)
                            # Fix missing commas between objects in arrays
                            cleaned = re.sub(r'}\s*{', r'}, {', cleaned)
                            # Fix missing commas between array elements
                            cleaned = re.sub(r']\s*\[', r'], [', cleaned)
                            # Remove any comments (// or /* */)
                            cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
                            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
                            
                            try:
                                decoder = json.JSONDecoder()
                                result, idx = decoder.raw_decode(cleaned)
                                logger.info("Successfully parsed after aggressive cleanup")
                            except json.JSONDecodeError as e2:
                                logger.warn(f"Cleanup parse also failed: {e2}. Trying one more pass...")
                                # One more aggressive pass - fix common issues
                                cleaned2 = cleaned
                                # Try to fix unclosed strings or brackets
                                # Count brackets to see if they're balanced
                                open_braces = cleaned2.count('{')
                                close_braces = cleaned2.count('}')
                                open_brackets = cleaned2.count('[')
                                close_brackets = cleaned2.count(']')
                                
                                # If unbalanced, try to fix
                                if open_braces > close_braces:
                                    cleaned2 += '}' * (open_braces - close_braces)
                                if open_brackets > close_brackets:
                                    cleaned2 += ']' * (open_brackets - close_brackets)
                                
                                try:
                                    decoder = json.JSONDecoder()
                                    result, idx = decoder.raw_decode(cleaned2)
                                    logger.info("Successfully parsed after bracket balancing")
                                except json.JSONDecodeError:
                                    # Last resort: try normal parse on cleaned version
                                    result = json.loads(cleaned2)
                    else:
                        # No code blocks - find JSON in content and use raw_decode
                        first_bracket = content.find('[')
                        first_brace = content.find('{')
                        
                        start_pos = -1
                        if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
                            start_pos = first_bracket
                        elif first_brace != -1:
                            start_pos = first_brace
                        
                        if start_pos != -1:
                            json_content = content[start_pos:]
                            
                            # Try to parse, with cleanup if needed
                            try:
                                decoder = json.JSONDecoder()
                                result, idx = decoder.raw_decode(json_content)
                                logger.info(f"Parsed JSON using raw_decode (start: {start_pos}, end: {start_pos + idx})")
                                
                                remaining = json_content[idx:].strip()
                                if remaining:
                                    logger.info(f"Ignored {len(remaining)} chars after JSON: {remaining[:100]}...")
                            except json.JSONDecodeError as parse_error:
                                # Try aggressive cleanup
                                logger.warn(f"Parse failed: {parse_error}. Attempting cleanup...")
                                cleaned = json_content
                                
                                # Fix trailing commas
                                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                                cleaned = re.sub(r',(\s*\n\s*[}\]])', r'\1', cleaned)
                                # Fix missing commas
                                cleaned = re.sub(r'}\s*{', r'}, {', cleaned)
                                # Remove comments
                                cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
                                cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
                                
                                try:
                                    decoder = json.JSONDecoder()
                                    result, idx = decoder.raw_decode(cleaned)
                                    logger.info("Successfully parsed after cleanup")
                                except json.JSONDecodeError as e2:
                                    # Try bracket balancing
                                    open_braces = cleaned.count('{')
                                    close_braces = cleaned.count('}')
                                    open_brackets = cleaned.count('[')
                                    close_brackets = cleaned.count(']')
                                    
                                    if open_braces > close_braces:
                                        cleaned += '}' * (open_braces - close_braces)
                                    if open_brackets > close_brackets:
                                        cleaned += ']' * (open_brackets - close_brackets)
                                    
                                    decoder = json.JSONDecoder()
                                    result, idx = decoder.raw_decode(cleaned)
                                    logger.info("Successfully parsed after bracket balancing")
                        else:
                            raise ValueError("No JSON array or object found in response")
                    
                    # Step 3: Process the parsed result (common path for both code block and raw_decode)
                    if result is None:
                        raise ValueError("Failed to parse JSON from response")
                    
                    # Handle both old format (with 'sections' key) and new format (direct array)
                    if isinstance(result, list):
                        sections = result
                    elif 'sections' in result:
                        sections = result['sections']
                    else:
                        raise ValueError("Response must be a JSON array or contain 'sections' key")
                    
                    if not isinstance(sections, list):
                        raise ValueError("'sections' must be a list")
                    
                    # Profile posts should have 11 sections, themed posts should have 7
                    expected_sections = 11 if post_type == 'profile' else 7
                    if len(sections) != expected_sections:
                        raise ValueError(f"Expected exactly {expected_sections} sections, got {len(sections)}")
                    
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
                    logger.error(f"Response content (first 500 chars): {response['content'][:500]}")
                    logger.error(f"Full response content length: {len(response['content'])}")
                    # Try to show where the JSON might be
                    if '```' in response['content']:
                        logger.error("Response contains code blocks - extraction may have failed")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid JSON response from LLM: {str(e)}. Response preview: {response["content"][:200]}...'
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
            logger.error(f"Error calling LLM service: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Failed to generate section structure: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in api_design_section_structure: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def sanitize_sections_text(sections_data):
    """Sanitize sections text data"""
    # This function should be implemented if it exists elsewhere
    # For now, return the data as-is
    return sections_data
