"""
Planning Taxonomy API Module

Provides endpoints for taxonomy assignment to posts in the planning stage,
including LLM-generated taxonomy selection
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
import re

logger = logging.getLogger(__name__)

bp = Blueprint('planning_taxonomy_api', __name__, url_prefix='/planning/api')

@bp.route('/posts/<int:post_id>/taxonomy', methods=['GET'])
def get_post_taxonomy(post_id):
    """Get taxonomy assignment for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.theme_id, p.content_type_id, p.format_id,
                    theme.slug as theme_slug, theme.display_name as theme_name,
                    content_type.slug as content_type_slug, content_type.display_name as content_type_name,
                    content_type.common_assets as content_type_assets,
                    format.slug as format_slug, format.display_name as format_name
                FROM post p
                LEFT JOIN taxonomy_item theme ON p.theme_id = theme.id
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                LEFT JOIN taxonomy_item format ON p.format_id = format.id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            taxonomy = {
                'theme_id': result['theme_id'],
                'theme_slug': result['theme_slug'],
                'theme_name': result['theme_name'],
                'content_type_id': result['content_type_id'],
                'content_type_slug': result['content_type_slug'],
                'content_type_name': result['content_type_name'],
                'content_type_assets': result['content_type_assets'] or [],
                'format_id': result['format_id'],
                'format_slug': result['format_slug'],
                'format_name': result['format_name']
            }
            
            return jsonify({
                'success': True,
                'taxonomy': taxonomy
            })
    except Exception as e:
        logger.error(f"Error fetching post taxonomy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/taxonomy', methods=['POST', 'PUT'])
def assign_post_taxonomy(post_id):
    """Assign or update taxonomy for a post"""
    try:
        data = request.get_json()
        theme_id = data.get('theme_id')
        content_type_id = data.get('content_type_id')
        format_id = data.get('format_id')
        
        # Validate all three are provided
        if not theme_id or not content_type_id or not format_id:
            return jsonify({
                'success': False,
                'error': 'All three taxonomy fields are required: theme_id, content_type_id, format_id'
            }), 400
        
        with db_manager.get_cursor() as cursor:
            # Validate the content_type belongs to the theme
            cursor.execute("""
                SELECT parent_id FROM taxonomy_item WHERE id = %s
            """, (content_type_id,))
            content_type = cursor.fetchone()
            
            if not content_type:
                return jsonify({'success': False, 'error': 'Invalid content_type_id'}), 400
            
            if content_type['parent_id'] != theme_id:
                return jsonify({
                    'success': False,
                    'error': f'Content type {content_type_id} does not belong to theme {theme_id}'
                }), 400
            
            # Update post taxonomy
            cursor.execute("""
                UPDATE post
                SET theme_id = %s, content_type_id = %s, format_id = %s, updated_at = NOW()
                WHERE id = %s
            """, (theme_id, content_type_id, format_id, post_id))
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'message': 'Taxonomy assigned successfully'
            })
    except Exception as e:
        logger.error(f"Error assigning post taxonomy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/taxonomy/generate', methods=['POST'])
def generate_taxonomy():
    """Generate taxonomy assignment using LLM based on expanded_idea"""
    try:
        data = request.get_json()
        expanded_idea = data.get('expanded_idea')
        post_id = data.get('post_id')
        # CRITICAL: Accept year/week parameters to find the correct post for assignment
        year = data.get('year')
        week_number = data.get('week_number')
        
        # Initialize week_theme_id to None - will be set if week has selected theme
        week_theme_id = None
        
        if not expanded_idea:
            return jsonify({'success': False, 'error': 'expanded_idea is required'}), 400
        
        # Get week theme_id if year/week provided (for LLM context, but don't change post_id)
        # Always use the requested post_id - don't redirect to a different post
        if year and week_number:
            with db_manager.get_cursor() as cursor:
                # Check if new tables exist
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_selection'
                    ) as has_selection,
                    EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_posts'
                    ) as has_posts
                """)
                table_check = cursor.fetchone()
                has_new_tables = table_check['has_selection'] and table_check['has_posts']
                
                if has_new_tables:
                    # Use new V2 architecture - get selected theme for this week
                    cursor.execute("""
                        SELECT selected_theme_id
                        FROM calendar_week_selection
                        WHERE year = %s AND week_number = %s
                    """, (year, week_number))
                    week_selection = cursor.fetchone()
                    
                    if week_selection:
                        week_theme_id = week_selection['selected_theme_id']
                        logger.info(f"Week {year}/{week_number} has selected theme_id {week_theme_id}")
                    else:
                        week_theme_id = None
                else:
                    # Fallback to old calendar_schedule table
                    cursor.execute("""
                        SELECT cs.theme_id
                        FROM calendar_schedule cs
                        WHERE cs.year = %s 
                          AND cs.week_number = %s
                          AND cs.theme_id IS NOT NULL
                        ORDER BY cs.created_at DESC
                        LIMIT 1
                    """, (year, week_number))
                    
                    week_theme = cursor.fetchone()
                    
                    if week_theme:
                        week_theme_id = week_theme['theme_id']
                        logger.info(f"Week {year}/{week_number} has theme_id {week_theme_id}")
                    else:
                        week_theme_id = None
        
        # Fetch all taxonomy items from database
        valid_content_type_ids = set()  # Initialize outside the with block so it's accessible later
        with db_manager.get_cursor() as cursor:
            # Get themes
            cursor.execute("""
                SELECT ti.id, ti.slug, ti.display_name, ti.description
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                WHERE tt.name = 'theme' AND ti.is_active = TRUE
                ORDER BY ti.display_order
            """)
            themes = cursor.fetchall()
            
            # Get content types - filter by week_theme_id if available
            # CRITICAL: Only include content types that have a valid parent_id (belong to a theme)
            content_types = []
            use_week_theme = False
            
            if week_theme_id:
                # First validate that the theme actually exists
                cursor.execute("""
                    SELECT ti.id, ti.slug, ti.display_name
                    FROM taxonomy_item ti
                    JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                    WHERE ti.id = %s AND tt.name = 'theme' AND ti.is_active = TRUE
                """, (week_theme_id,))
                theme_check = cursor.fetchone()
                
                if theme_check:
                    # Theme exists, try to get content types for it
                    cursor.execute("""
                        SELECT ti.id, ti.slug, ti.display_name, ti.description, ti.parent_id,
                               parent.display_name as theme_name
                        FROM taxonomy_item ti
                        JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                        LEFT JOIN taxonomy_item parent ON ti.parent_id = parent.id
                        WHERE tt.name = 'content_type' 
                          AND ti.is_active = TRUE
                          AND ti.parent_id IS NOT NULL
                          AND ti.parent_id = %s
                        ORDER BY ti.display_order
                    """, (week_theme_id,))
                    content_types = cursor.fetchall()
                    logger.info(f"[Taxonomy Generation] Filtering content types to theme_id {week_theme_id}. Found {len(content_types)} content types.")
                    
                    if len(content_types) > 0:
                        use_week_theme = True
                    else:
                        logger.warn(f"[Taxonomy Generation] Theme {week_theme_id} has no content types. Falling back to all content types.")
                else:
                    logger.warn(f"[Taxonomy Generation] week_theme_id {week_theme_id} does not exist or is not a valid theme. Falling back to all content types.")
            
            # If we don't have content types yet (no week_theme, invalid theme, or theme has no content types), get all
            if not use_week_theme:
                logger.info(f"[Taxonomy Generation] Showing all content types (excluding those without parent)")
                cursor.execute("""
                    SELECT ti.id, ti.slug, ti.display_name, ti.description, ti.parent_id,
                           parent.display_name as theme_name
                    FROM taxonomy_item ti
                    JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                    LEFT JOIN taxonomy_item parent ON ti.parent_id = parent.id
                    WHERE tt.name = 'content_type' 
                      AND ti.is_active = TRUE
                      AND ti.parent_id IS NOT NULL
                    ORDER BY ti.display_order
                """)
                content_types = cursor.fetchall()
                # Reset week_theme_id since we're showing all content types
                week_theme_id = None
            
            logger.info(f"[Taxonomy Generation] Total content types available: {len(content_types)}")
            
            # Create a set of valid content_type_ids for validation (must be inside the with block)
            valid_content_type_ids = {ct['id'] for ct in content_types}
            logger.info(f"[Taxonomy Generation] Valid content_type_ids: {sorted(valid_content_type_ids)}")
            
            # Get formats
            cursor.execute("""
                SELECT ti.id, ti.slug, ti.display_name, ti.description
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                WHERE tt.name = 'format' AND ti.is_active = TRUE
                ORDER BY ti.display_order
            """)
            formats = cursor.fetchall()
        
        # Load taxonomy assignment prompt from database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT system_prompt, prompt_text
                FROM llm_prompt
                WHERE name = 'Taxonomy Assignment'
                ORDER BY id DESC
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            # Use enhanced system prompt that explicitly warns about field confusion
            system_prompt = """You are a content classification expert specializing in Scottish heritage and culture. 

CRITICAL: You must select taxonomy IDs with EXTREME precision:
- theme_id: Must be from THEMES list only
- content_type_id: Must be from CONTENT TYPES list only - NEVER use a format ID here
- format_id: Must be from FORMATS list only - NEVER use a content_type ID here

Each field has its own dedicated list. Mixing them up is a critical error."""
            
            # We'll build the user prompt completely from scratch for maximum clarity
            prompt_text = None  # Signal that we're building custom prompt
        
        # CRITICAL: Extract format IDs before formatting (needed for validation and prompt)
        format_ids = [f['id'] for f in formats]
        logger.info(f"[Taxonomy Generation] Format IDs available: {sorted(format_ids)}")
        
        # Format content types list - ONLY include the filtered content types
        # CRITICAL: Only show content types that are in valid_content_type_ids
        filtered_content_types = [ct for ct in content_types if ct['id'] in valid_content_type_ids]
        logger.info(f"[Taxonomy Generation] Showing {len(filtered_content_types)} content types in prompt (filtered from {len(content_types)} total)")
        
        # CRITICAL: Check if we have any content types available at all (system-wide check)
        if not filtered_content_types or len(valid_content_type_ids) == 0:
            logger.error(f"[Taxonomy Generation] No content types available in entire system! valid_content_type_ids={valid_content_type_ids}")
            return jsonify({
                'success': False,
                'error': 'No content types are available in the system. Please ensure content types exist in the taxonomy.'
            }), 400
        
        # COMPLETELY REWRITE PROMPT STRUCTURE - Make it impossible to confuse fields
        # Build a much clearer, more structured prompt that separates each section explicitly
        
        # Build themes section with explicit IDs
        themes_section = "=== THEMES (for theme_id field) ===\n"
        themes_section += "You MUST select ONE theme_id from this list:\n"
        for t in themes:
            themes_section += f"  theme_id {t['id']}: {t['display_name']} - {t['description']}\n"
        themes_section += f"\nValid theme_ids: {sorted([t['id'] for t in themes])}\n"
        
        # Build content types section - VERY EXPLICIT that these are for content_type_id ONLY
        content_types_section = "\n=== CONTENT TYPES (for content_type_id field ONLY) ===\n"
        content_types_section += "WARNING: These are CONTENT TYPES, NOT formats. Use these IDs ONLY for content_type_id field.\n"
        content_types_section += f"You MUST select ONE content_type_id from this list (there are {len(filtered_content_types)} options available):\n"
        for ct in filtered_content_types:
            content_types_section += f"  content_type_id {ct['id']}: {ct['display_name']} (belongs to theme: {ct['theme_name']}) - {ct['description']}\n"
        content_types_section += f"\nValid content_type_ids: {sorted(valid_content_type_ids)}\n"
        content_types_section += f"CRITICAL: You MUST select one of these IDs. Do NOT use an empty array []. Do NOT use these IDs for format_id. These are CONTENT TYPES only.\n"
        
        # Build formats section - VERY EXPLICIT that these are for format_id ONLY
        formats_section = "\n=== FORMATS (for format_id field ONLY) ===\n"
        formats_section += "WARNING: These are FORMATS, NOT content types. Use these IDs ONLY for format_id field.\n"
        formats_section += "You MUST select ONE format_id from this list:\n"
        for f in formats:
            formats_section += f"  format_id {f['id']}: {f['display_name']} - {f['description']}\n"
        formats_section += f"\nValid format_ids: {sorted(format_ids)}\n"
        formats_section += f"CRITICAL: Do NOT use these IDs for content_type_id. These are FORMATS only.\n"
        
        # Build the complete prompt with explicit field mapping
        formatted_prompt = f"""Based on the expanded idea provided, select the most appropriate taxonomy classification.

EXPANDED IDEA:
{expanded_idea}

{themes_section}
{content_types_section}
{formats_section}

=== JSON RESPONSE FORMAT ===
You MUST return ONLY valid JSON in this EXACT format (no markdown, no code blocks, just the JSON):

{{
  "theme_id": <integer from THEMES list above>,
  "content_type_id": <integer from CONTENT TYPES list above - NOT from FORMATS, NOT an array []>,
  "format_id": <integer from FORMATS list above - NOT from CONTENT TYPES, NOT an array []>,
  "reasoning": "<ONE brief sentence>"
}}

CRITICAL: All three ID fields (theme_id, content_type_id, format_id) MUST be integers, NOT arrays. Do NOT use [] for any field.

=== CRITICAL FIELD MAPPING RULES ===
1. theme_id → MUST be from THEMES list (IDs: {sorted([t['id'] for t in themes])})
2. content_type_id → MUST be from CONTENT TYPES list (IDs: {sorted(valid_content_type_ids)}) - NEVER use format IDs here
3. format_id → MUST be from FORMATS list (IDs: {sorted(format_ids)}) - NEVER use content_type IDs here

=== ABSOLUTE PROHIBITIONS ===
- NEVER use a format_id (like {sorted(format_ids)}) for content_type_id
- NEVER use a content_type_id (like {sorted(valid_content_type_ids)}) for format_id
- NEVER use the same ID for both content_type_id and format_id
- Each field MUST use IDs from its designated list only

Return ONLY the JSON object, no other text, no markdown code blocks, no explanations outside the JSON."""
        
        # CRITICAL: If week_theme_id is set, add instruction to use that theme
        if week_theme_id:
            theme_constraint = f"\n\n=== THEME CONSTRAINT ===\nYou MUST use theme_id {week_theme_id} (already selected for this week). Only content types belonging to this theme are shown in the CONTENT TYPES list above."
            formatted_prompt += theme_constraint
            logger.info(f"Adding theme constraint to prompt: theme_id {week_theme_id}")
        
        logger.info(f"[Taxonomy Generation] Generated structured prompt. Valid content_type_ids: {sorted(valid_content_type_ids)}, Valid format_ids: {sorted(format_ids)}")
        
        # Call LLM
        llm_service = LLMService()
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': formatted_prompt}
        ]
        
        response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=4000)
        
        if not response or 'content' not in response:
            return jsonify({'success': False, 'error': 'LLM response was empty'}), 500
        
        # Parse JSON from response
        content = response['content'].strip()
        logger.info(f"LLM raw response (first 2000 chars): {content[:2000]}")
        
        # Remove markdown code blocks if present
        if '```' in content:
            # Extract content between ```json and ``` or ``` and ```
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
                logger.info(f"Extracted from code block: {content[:500]}")
        
        # Extract JSON object (find first { to last })
        json_start = content.find('{')
        json_end = content.rfind('}')
        
        # If no closing brace found, try to find it by counting braces
        if json_end == -1 and json_start != -1:
            # Count opening and closing braces to find where it should end
            brace_count = 0
            json_end = len(content)
            for i in range(json_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
        
        if json_start == -1:
            # No opening brace - try extracting IDs directly
            logger.warn(f"No opening brace found. Trying direct ID extraction.")
            theme_match = re.search(r'"theme_id":\s*(\d+)', content)
            content_type_match = re.search(r'"content_type_id":\s*(\d+)', content)
            format_match = re.search(r'"format_id":\s*(\d+)', content)
            
            if theme_match and content_type_match and format_match:
                # Extract IDs directly and skip JSON parsing
                reasoning_match = re.search(r'"reasoning":\s*"([^"]*)', content)
                reasoning_text = reasoning_match.group(1) if reasoning_match else 'Auto-extracted (no JSON structure)'
                
                result = {
                    'theme_id': int(theme_match.group(1)),
                    'content_type_id': int(content_type_match.group(1)),
                    'format_id': int(format_match.group(1)),
                    'reasoning': reasoning_text
                }
                logger.info(f"Successfully extracted IDs without JSON structure: {result}")
                # Skip to validation
                json_content = None  # Signal that we already have result
            else:
                logger.error(f"Could not find JSON in response. Full content: {content}")
                return jsonify({
                    'success': False, 
                    'error': 'Could not parse JSON from LLM response',
                    'debug_info': {
                        'response_preview': content[:500],
                        'has_opening_brace': '{' in content,
                        'has_closing_brace': '}' in content
                    }
                }), 500
        elif json_end <= json_start:
            logger.error(f"Invalid JSON structure. json_start={json_start}, json_end={json_end}. Full content: {content}")
            return jsonify({
                'success': False, 
                'error': 'Could not parse JSON from LLM response',
                'debug_info': {
                    'response_preview': content[:500],
                    'has_opening_brace': '{' in content,
                    'has_closing_brace': '}' in content
                }
            }), 500
        else:
            json_content = content[json_start:json_end]
            logger.info(f"Extracted JSON content: {json_content}")
        
        # Only try to parse if we haven't already extracted result directly
        if json_content is not None:
            # Try to clean up common JSON issues
            # Remove trailing commas before closing braces/brackets
            json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
            
            # Remove any trailing newlines or whitespace
            json_content = json_content.strip()
            
            # If JSON appears truncated (doesn't end with }), try to fix it OR extract IDs
            if not json_content.endswith('}'):
                # First try to extract IDs directly (more reliable than trying to fix truncated JSON)
                theme_match = re.search(r'"theme_id":\s*(\d+)', json_content)
                content_type_match = re.search(r'"content_type_id":\s*(\d+)', json_content)
                format_match = re.search(r'"format_id":\s*(\d+)', json_content)
                
                if theme_match and content_type_match and format_match:
                    # Extract IDs and reasoning directly - skip JSON parsing
                    reasoning_match = re.search(r'"reasoning":\s*"([^"]*)', json_content)
                    reasoning_text = reasoning_match.group(1) if reasoning_match else 'Auto-extracted from truncated response'
                    
                    result = {
                        'theme_id': int(theme_match.group(1)),
                        'content_type_id': int(content_type_match.group(1)),
                        'format_id': int(format_match.group(1)),
                        'reasoning': reasoning_text
                    }
                    logger.info(f"Successfully extracted IDs from truncated JSON: {result}")
                    json_content = None  # Skip JSON parsing
                else:
                    # Try to fix incomplete reasoning string
                    if '"reasoning":' in json_content:
                        # Find the start of the reasoning value string
                        reasoning_match = re.search(r'"reasoning":\s*"([^"]*)$', json_content)
                        if reasoning_match:
                            # The reasoning string is incomplete - try to close it properly
                            # Find where the reasoning value starts
                            reasoning_start_idx = json_content.rfind('"reasoning":')
                            if reasoning_start_idx >= 0:
                                # Find the opening quote after "reasoning":
                                quote_start = json_content.find('"', reasoning_start_idx + len('"reasoning":'))
                                if quote_start >= 0:
                                    # Extract what we have, remove incomplete trailing quote/content, close properly
                                    json_content = json_content[:quote_start + 1] + json_content[quote_start + 1:].rstrip().rstrip('"').rstrip()
                                    json_content = json_content.rstrip().rstrip(',') + '"}'
                                    logger.info(f"Attempted to fix incomplete reasoning: {json_content[-150:]}")
            
            # Try parsing the cleaned JSON (if we haven't already extracted result)
            if json_content is not None:
                try:
                    result = json.loads(json_content)
                    logger.info(f"Successfully parsed JSON: {result}")
                    
                    # CRITICAL: Validate that all ID fields are integers, not arrays or other types
                    if not isinstance(result.get('theme_id'), int):
                        logger.error(f"[JSON Validation] theme_id is not an integer: {result.get('theme_id')} (type: {type(result.get('theme_id'))})")
                        return jsonify({
                            'success': False,
                            'error': f'theme_id must be an integer, but LLM returned: {result.get("theme_id")}',
                            'debug_info': {
                                'json_content': json_content,
                                'parsed_result': result
                            }
                        }), 400
                    
                    if not isinstance(result.get('content_type_id'), int):
                        logger.error(f"[JSON Validation] content_type_id is not an integer: {result.get('content_type_id')} (type: {type(result.get('content_type_id'))})")
                        # Try to extract from array if it's an array
                        if isinstance(result.get('content_type_id'), list):
                            if len(result.get('content_type_id')) > 0:
                                logger.warn(f"[JSON Validation] content_type_id is an array with values: {result.get('content_type_id')}. Using first value.")
                                result['content_type_id'] = result.get('content_type_id')[0]
                            else:
                                return jsonify({
                                    'success': False,
                                    'error': 'content_type_id is an empty array. The LLM did not select a content type. Please check if content types are available for the selected theme.',
                                    'debug_info': {
                                        'json_content': json_content,
                                        'parsed_result': result
                                    }
                                }), 400
                        else:
                            return jsonify({
                                'success': False,
                                'error': f'content_type_id must be an integer, but LLM returned: {result.get("content_type_id")}',
                                'debug_info': {
                                    'json_content': json_content,
                                    'parsed_result': result
                                }
                            }), 400
                    
                    if not isinstance(result.get('format_id'), int):
                        logger.error(f"[JSON Validation] format_id is not an integer: {result.get('format_id')} (type: {type(result.get('format_id'))})")
                        # Try to extract from array if it's an array
                        if isinstance(result.get('format_id'), list):
                            if len(result.get('format_id')) > 0:
                                logger.warn(f"[JSON Validation] format_id is an array with values: {result.get('format_id')}. Using first value.")
                                result['format_id'] = result.get('format_id')[0]
                            else:
                                return jsonify({
                                    'success': False,
                                    'error': 'format_id is an empty array. The LLM did not select a format.',
                                    'debug_info': {
                                        'json_content': json_content,
                                        'parsed_result': result
                                    }
                                }), 400
                        else:
                            return jsonify({
                                'success': False,
                                'error': f'format_id must be an integer, but LLM returned: {result.get("format_id")}',
                                'debug_info': {
                                    'json_content': json_content,
                                    'parsed_result': result
                                }
                            }), 400
                    
                except json.JSONDecodeError as e:
                    logger.warn(f"JSON parse error: {e}")
                    logger.warn(f"Attempted to parse: {json_content}")
                    
                    # CRITICAL: If parsing fails, try extracting IDs directly (most important data)
                    # This handles truncated responses where reasoning string is incomplete
                    theme_match = re.search(r'"theme_id":\s*(\d+)', json_content)
                    content_type_match = re.search(r'"content_type_id":\s*(\d+)', json_content)
                    format_match = re.search(r'"format_id":\s*(\d+)', json_content)
                    
                    if theme_match and content_type_match and format_match:
                        # Extract reasoning if possible (even if incomplete)
                        reasoning_match = re.search(r'"reasoning":\s*"([^"]*)', json_content)
                        reasoning_text = reasoning_match.group(1) if reasoning_match else 'Auto-extracted from truncated response'
                        
                        result = {
                            'theme_id': int(theme_match.group(1)),
                            'content_type_id': int(content_type_match.group(1)),
                            'format_id': int(format_match.group(1)),
                            'reasoning': reasoning_text
                        }
                        logger.info(f"Successfully extracted IDs from truncated/invalid JSON: {result}")
                    else:
                        # Check for array syntax in content_type_id
                        array_match = re.search(r'"content_type_id":\s*\[([^\]]*)\]', json_content)
                        if array_match:
                            logger.error(f"[JSON Parse] content_type_id is an array: {array_match.group(0)}")
                            return jsonify({
                                'success': False,
                                'error': 'LLM returned content_type_id as an array instead of an integer. This usually means no content types are available for the selected theme, or the LLM could not find a match.',
                                'debug_info': {
                                    'json_content': json_content,
                                    'parse_error': str(e),
                                    'full_response_preview': content[:1000],
                                    'content_type_array': array_match.group(0)
                                }
                            }), 400
                        
                        logger.error(f"Could not extract required IDs. Full LLM response: {content}")
                        return jsonify({
                            'success': False, 
                            'error': f'Invalid JSON from LLM: {str(e)}',
                            'debug_info': {
                                'json_content': json_content,
                                'parse_error': str(e),
                                'full_response_preview': content[:1000],
                                'has_theme_id': bool(theme_match),
                                'has_content_type_id': bool(content_type_match),
                                'has_format_id': bool(format_match)
                            }
                        }), 500
        
        # Validate the result
        theme_id = result.get('theme_id')
        content_type_id = result.get('content_type_id')
        format_id = result.get('format_id')
        reasoning = result.get('reasoning', '')
        
        if not theme_id or not content_type_id or not format_id:
            return jsonify({
                'success': False,
                'error': 'LLM response missing required fields: theme_id, content_type_id, format_id'
            }), 500
        
        # CRITICAL: Validate that IDs are actually the right type (prevent format_id being used as content_type_id)
        # This MUST happen FIRST before any other validation
        with db_manager.get_cursor() as cursor:
            # Check content_type_id is actually a content_type (not a format or theme)
            cursor.execute("""
                SELECT ti.id, tt.name as tier_name, ti.slug, ti.display_name
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                WHERE ti.id = %s
            """, (content_type_id,))
            ct_check = cursor.fetchone()
            if not ct_check:
                logger.error(f"[Taxonomy Validation] content_type_id {content_type_id} does not exist in database")
                return jsonify({
                    'success': False,
                    'error': f'Invalid content_type_id: {content_type_id} does not exist'
                }), 400
            if ct_check['tier_name'] != 'content_type':
                logger.error(f"[Taxonomy Validation] content_type_id {content_type_id} is actually a {ct_check['tier_name']} (slug: {ct_check['slug']}, name: {ct_check['display_name']}), not a content_type. LLM selected wrong type.")
                return jsonify({
                    'success': False,
                    'error': f'ID {content_type_id} ("{ct_check["display_name"]}") is a {ct_check["tier_name"]}, not a content_type. The LLM incorrectly selected a format/theme ID for content_type_id. Please try generating again.'
                }), 400
            
            # Check format_id is actually a format (not a content_type or theme)
            cursor.execute("""
                SELECT ti.id, tt.name as tier_name, ti.slug, ti.display_name
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                WHERE ti.id = %s
            """, (format_id,))
            fmt_check = cursor.fetchone()
            if not fmt_check:
                logger.error(f"[Taxonomy Validation] format_id {format_id} does not exist in database")
                return jsonify({
                    'success': False,
                    'error': f'Invalid format_id: {format_id} does not exist'
                }), 400
            if fmt_check['tier_name'] != 'format':
                logger.error(f"[Taxonomy Validation] format_id {format_id} is actually a {fmt_check['tier_name']} (slug: {fmt_check['slug']}, name: {fmt_check['display_name']}), not a format. LLM selected wrong type.")
                return jsonify({
                    'success': False,
                    'error': f'ID {format_id} ("{fmt_check["display_name"]}") is a {fmt_check["tier_name"]}, not a format. The LLM incorrectly selected a content_type/theme ID for format_id. Please try generating again.'
                }), 400
            
            # CRITICAL: Cross-check to ensure content_type_id is not the same as format_id
            if content_type_id == format_id:
                logger.error(f"[Taxonomy Validation] content_type_id and format_id are the same: {content_type_id}")
                return jsonify({
                    'success': False,
                    'error': f'content_type_id and format_id cannot be the same ID ({content_type_id}). The LLM selected the same ID for both fields.'
                }), 400
            
            # CRITICAL: Additional cross-check - ensure content_type_id is not in the formats list
            cursor.execute("""
                SELECT ti.id
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                WHERE tt.name = 'format' AND ti.id = %s
            """, (content_type_id,))
            if cursor.fetchone():
                logger.error(f"[Taxonomy Validation] content_type_id {content_type_id} is actually a format (cross-check confirmed)")
                return jsonify({
                    'success': False,
                    'error': f'ID {content_type_id} is a format, not a content_type. The LLM incorrectly used a format ID for content_type_id. Please try generating again.'
                }), 400
        
        # CRITICAL: If week_theme_id is set, override LLM's theme choice
        # This ensures we always use the week's selected theme
        if week_theme_id:
            if week_theme_id != theme_id:
                logger.warn(f"[Taxonomy Generation] LLM chose theme_id {theme_id} but week requires {week_theme_id}. Overriding to week theme.")
            theme_id = week_theme_id
            logger.info(f"[Taxonomy Generation] Using week_theme_id {week_theme_id} (overriding LLM choice)")
        else:
            logger.info(f"[Taxonomy Generation] No week_theme_id - using LLM's theme_id {theme_id}")
        
        # CRITICAL: Validate that the LLM selected a content_type from the filtered list
        # This MUST happen before any database queries to prevent orphaned content types
        if not valid_content_type_ids or content_type_id not in valid_content_type_ids:
            logger.error(f"[Taxonomy Generation] LLM selected content_type_id {content_type_id} which was NOT in the filtered list. Valid IDs: {sorted(valid_content_type_ids) if valid_content_type_ids else 'NONE'}")
            return jsonify({
                'success': False,
                'error': f'Content type {content_type_id} was not in the available options. This content type may be orphaned (no parent theme). Please try generating again.'
            }), 400
        
        # Validate IDs exist and content_type belongs to theme
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT parent_id FROM taxonomy_item WHERE id = %s
            """, (content_type_id,))
            content_type = cursor.fetchone()
            
            if not content_type:
                return jsonify({'success': False, 'error': f'Invalid content_type_id: {content_type_id}'}), 400
            
            # Check if content_type has a parent (should always have one)
            if content_type['parent_id'] is None:
                # This should never happen if validation above worked, but double-check
                logger.error(f"[Taxonomy Generation] Content type {content_type_id} has NULL parent_id despite passing validation!")
                return jsonify({
                    'success': False,
                    'error': f'Content type {content_type_id} has no parent theme. This content type was filtered out and should not have been selectable.'
                }), 400
            
            if content_type['parent_id'] != theme_id:
                return jsonify({
                    'success': False,
                    'error': f'Content type {content_type_id} does not belong to theme {theme_id}. Content type belongs to theme {content_type["parent_id"]}.'
                }), 400
        
        # NOTE: Always assign taxonomy to the requested post_id
        # The redirect logic was removed because users expect taxonomy to be assigned
        # to the post they're viewing, regardless of theme mismatches.
        # If there's a theme mismatch, the taxonomy assignment will update the post's theme_id
        # to match the generated taxonomy, which is the correct behavior.
        
        # If post_id provided, automatically assign the taxonomy
        assigned_post_id = post_id
        if post_id:
            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE post
                        SET theme_id = %s, content_type_id = %s, format_id = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (theme_id, content_type_id, format_id, post_id))
                    logger.info(f"Assigned taxonomy to post {post_id}: theme={theme_id}, content_type={content_type_id}, format={format_id}")
                    assigned_post_id = post_id
            except Exception as e:
                logger.error(f"Error auto-assigning taxonomy to post: {e}")
                # Don't fail the request, just log the error
        
        return jsonify({
            'success': True,
            'taxonomy': {
                'theme_id': theme_id,
                'content_type_id': content_type_id,
                'format_id': format_id,
                'reasoning': reasoning
            },
            'assigned_post_id': assigned_post_id  # CRITICAL: Return the post_id that was actually assigned to
        })
        
    except Exception as e:
        logger.error(f"Error generating taxonomy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

