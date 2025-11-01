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
        
        if not expanded_idea:
            return jsonify({'success': False, 'error': 'expanded_idea is required'}), 400
        
        # Fetch all taxonomy items from database
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
            
            # Get content types
            cursor.execute("""
                SELECT ti.id, ti.slug, ti.display_name, ti.description, ti.parent_id,
                       parent.display_name as theme_name
                FROM taxonomy_item ti
                JOIN taxonomy_tier tt ON ti.tier_id = tt.id
                LEFT JOIN taxonomy_item parent ON ti.parent_id = parent.id
                WHERE tt.name = 'content_type' AND ti.is_active = TRUE
                ORDER BY ti.display_order
            """)
            content_types = cursor.fetchall()
            
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
            
            if not prompt_data:
                # Fallback prompt
                system_prompt = """You are a content classification expert specializing in Scottish heritage and culture. Your task is to analyze blog post concepts and select the most appropriate taxonomy classification."""
                prompt_text = """Based on the expanded idea provided, select the most appropriate taxonomy classification.

EXPANDED IDEA:
{expanded_idea}

AVAILABLE THEMES:
{themes_list}

AVAILABLE CONTENT TYPES:
{content_types_list}

AVAILABLE FORMATS:
{formats_list}

CRITICAL REQUIREMENTS:
1. You MUST select exactly one Theme, one Content Type, and one Format
2. The Content Type MUST belong to the selected Theme (check parent_id)
3. Return ONLY valid JSON in this exact format:
{{
  "theme_id": <integer>,
  "content_type_id": <integer>,
  "format_id": <integer>,
  "reasoning": "<brief explanation of your selections>"
}}

Return only the JSON object, no other text."""
            else:
                system_prompt = prompt_data['system_prompt']
                prompt_text = prompt_data['prompt_text']
        
        # Format themes list
        themes_list = "\n".join([
            f"- ID {t['id']}: {t['display_name']} - {t['description']}"
            for t in themes
        ])
        
        # Format content types list
        content_types_list = "\n".join([
            f"- ID {ct['id']}: {ct['display_name']} (Theme: {ct['theme_name']}) - {ct['description']}"
            for ct in content_types
        ])
        
        # Format formats list
        formats_list = "\n".join([
            f"- ID {f['id']}: {f['display_name']} - {f['description']}"
            for f in formats
        ])
        
        # Format the prompt
        formatted_prompt = prompt_text.replace('{expanded_idea}', expanded_idea)
        formatted_prompt = formatted_prompt.replace('{themes_list}', themes_list)
        formatted_prompt = formatted_prompt.replace('{content_types_list}', content_types_list)
        formatted_prompt = formatted_prompt.replace('{formats_list}', formats_list)
        
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
        logger.info(f"LLM raw response: {content[:1000]}")
        
        # Remove markdown code blocks if present
        if '```' in content:
            # Extract content between ```json and ``` or ``` and ```
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()
                logger.info(f"Extracted from code block: {content[:500]}")
        
        # Extract JSON object (find first { to last })
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start == -1 or json_end <= json_start:
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
        
        json_content = content[json_start:json_end]
        
        # Try to clean up common JSON issues
        # Remove trailing commas before closing braces/brackets
        json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
        
        # If JSON appears truncated, try to fix common truncation issues
        # Check if the last field (reasoning) might be incomplete
        if not json_content.strip().endswith('}'):
            # Try to close incomplete reasoning string and object
            if '"reasoning":' in json_content and json_content.count('"') % 2 != 0:
                # Reasoning string is incomplete, close it and the object
                # Find the start of the reasoning value
                reasoning_start = json_content.rfind('"reasoning":') + len('"reasoning":')
                reasoning_value_start = json_content.find('"', reasoning_start) + 1
                if reasoning_value_start > 0:
                    # Close the string and object
                    json_content = json_content[:reasoning_value_start] + json_content[reasoning_value_start:].rstrip().rstrip('"')
                    json_content = json_content.rstrip().rstrip(',') + '"}'
                    logger.info(f"Attempted to fix truncated JSON: {json_content[-100:]}")
        
        try:
            result = json.loads(json_content)
            logger.info(f"Successfully parsed JSON: {result}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Attempted to parse: {json_content}")
            logger.error(f"Full LLM response: {content}")
            
            # Try one more time with even more aggressive fixes
            # If reasoning is the problem, try extracting just the required fields
            try:
                # Try to extract just the IDs if present
                theme_match = re.search(r'"theme_id":\s*(\d+)', json_content)
                content_type_match = re.search(r'"content_type_id":\s*(\d+)', json_content)
                format_match = re.search(r'"format_id":\s*(\d+)', json_content)
                
                if theme_match and content_type_match and format_match:
                    result = {
                        'theme_id': int(theme_match.group(1)),
                        'content_type_id': int(content_type_match.group(1)),
                        'format_id': int(format_match.group(1)),
                        'reasoning': 'Auto-extracted from truncated response'
                    }
                    logger.info(f"Successfully extracted IDs from truncated JSON: {result}")
                else:
                    raise ValueError("Could not extract required IDs")
            except Exception as extract_error:
                return jsonify({
                    'success': False, 
                    'error': f'Invalid JSON from LLM: {str(e)}',
                    'debug_info': {
                        'json_content': json_content,
                        'parse_error': str(e),
                        'full_response_preview': content[:1000]
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
        
        # Validate IDs exist and content_type belongs to theme
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT parent_id FROM taxonomy_item WHERE id = %s
            """, (content_type_id,))
            content_type = cursor.fetchone()
            
            if not content_type:
                return jsonify({'success': False, 'error': f'Invalid content_type_id: {content_type_id}'}), 400
            
            if content_type['parent_id'] != theme_id:
                return jsonify({
                    'success': False,
                    'error': f'Content type {content_type_id} does not belong to theme {theme_id}'
                }), 400
        
        # If post_id provided, automatically assign the taxonomy
        if post_id:
            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE post
                        SET theme_id = %s, content_type_id = %s, format_id = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (theme_id, content_type_id, format_id, post_id))
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
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating taxonomy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

