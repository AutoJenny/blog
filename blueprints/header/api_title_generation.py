"""Title and subtitle generation API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .helpers import resolve_target_post_id
from .llm_service import LLMService
import logging
import json
import re

logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMService()


def register_routes(bp):
    """Register title generation API routes"""
    
    @bp.route('/api/posts/<int:post_id>/generate-titles', methods=['POST'])
    def api_generate_titles(post_id):
        """Generate three title options based on Development tab content using LLM"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
        if error:
            return jsonify({'error': error}), 400 if 'required' in error else 404
        
        # Replace post_id with target_post_id for all operations
        post_id = target_post_id
        
        try:
            # Check if this is a recipe post
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            # For recipe posts, use recipe title directly and generate subtitle only
            if post_type == 'recipe':
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT cr.recipe_title, cr.recipe_description
                        FROM post p
                        LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                        WHERE p.id = %s
                    """, (post_id,))
                    recipe_data = cursor.fetchone()
                    
                    if recipe_data and recipe_data.get('recipe_title'):
                        recipe_title = recipe_data['recipe_title']
                        recipe_description = recipe_data.get('recipe_description', '')
                        
                        # For recipes, title is just the recipe name - simple and clean
                        title_options = [recipe_title, recipe_title, recipe_title]  # All same, user can edit if needed
                        
                        # Generate subtitle using recipe description
                        # Get subtitle generation prompt (step 61)
                        cursor.execute("""
                            SELECT 
                                sp.system_prompt,
                                tp.prompt_text as task_prompt
                            FROM workflow_step_prompt wsp
                            LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                            LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                            WHERE wsp.step_id = 61
                        """)
                        subtitle_result = cursor.fetchone()
                        
                        if subtitle_result:
                            subtitle_system = subtitle_result.get('system_prompt', '')
                            subtitle_task = subtitle_result.get('task_prompt', '')
                            
                            # Modify subtitle prompt for recipes - evocative phrase without repeating recipe name
                            subtitle_task = f"""Generate a short, evocative subtitle (8-12 words) for this Scottish recipe blog post.

Recipe Name: {recipe_title}
Recipe Description: {recipe_description}

CRITICAL REQUIREMENTS:
- Do NOT repeat the recipe name "{recipe_title}" in the subtitle
- Create a warm, inviting phrase that captures the essence, tradition, or appeal of this dish
- Focus on what makes it special: its heritage, when it's enjoyed, its comforting nature, or its regional significance
- Keep it poetic and evocative, not descriptive or instructional
- Examples of good subtitles: "A warming bowl of coastal comfort" or "Traditional fare for cold winter evenings" or "A taste of Highland heritage"

Return ONLY a single subtitle string, not an array. Do not use quotes or brackets."""
                            
                            messages = [
                                {'role': 'system', 'content': subtitle_system},
                                {'role': 'user', 'content': subtitle_task}
                            ]
                            
                            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                            
                            if 'error' not in llm_response and llm_response.get('content'):
                                generated_subtitle = llm_response['content'].strip()
                                # Remove quotes and brackets
                                generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                                
                                # Clean up any JSON array if LLM returned one
                                json_match = re.search(r'\[.*?\]', generated_subtitle, re.DOTALL)
                                if json_match:
                                    try:
                                        subtitle_array = json.loads(json_match.group(0))
                                        if isinstance(subtitle_array, list) and len(subtitle_array) > 0:
                                            generated_subtitle = subtitle_array[0].strip().strip('"').strip("'")
                                    except:
                                        pass
                                
                                # Remove any remaining quotes or brackets
                                generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                                
                                # If subtitle still contains the recipe name, try to extract just the evocative part
                                if recipe_title.lower() in generated_subtitle.lower():
                                    # Try to find a phrase that doesn't include the recipe name
                                    # Split by common separators and take the most evocative part
                                    parts = re.split(r'[:\-–—]', generated_subtitle)
                                    for part in parts:
                                        part = part.strip()
                                        if part and recipe_title.lower() not in part.lower() and len(part) > 10:
                                            generated_subtitle = part
                                            break
                                
                                # Final validation: if it still contains the recipe name, generate a simple fallback
                                if recipe_title.lower() in generated_subtitle.lower() or len(generated_subtitle) < 5:
                                    # Generate a simple evocative phrase manually
                                    if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                        generated_subtitle = "A warming bowl of coastal comfort"
                                    elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                        generated_subtitle = "Traditional fare for cold winter evenings"
                                    else:
                                        generated_subtitle = "A taste of Highland heritage"
                            else:
                                # If LLM fails, use a simple evocative phrase instead of recipe description
                                if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                    generated_subtitle = "A warming bowl of coastal comfort"
                                elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                    generated_subtitle = "Traditional fare for cold winter evenings"
                                else:
                                    generated_subtitle = "A taste of Highland heritage"
                        else:
                            # If no subtitle prompt found, use a simple evocative phrase
                            if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                generated_subtitle = "A warming bowl of coastal comfort"
                            elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                generated_subtitle = "Traditional fare for cold winter evenings"
                            else:
                                generated_subtitle = "A taste of Highland heritage"
                        
                        return jsonify({
                            'success': True,
                            'title_options': title_options,
                            'selected_index': 0,
                            'subtitle': generated_subtitle
                        })
            
            # For non-recipe posts, use normal title generation
            data = request.get_json()
            idea_seed = data.get('idea_seed', '')
            expanded_idea = data.get('expanded_idea', '')
            section_content = data.get('section_content', '')
            
            logger.info(f"Generating titles for post {post_id} with content: idea_seed={idea_seed[:50]}...")
            
            # Get prompts from database for step 60 (Title Generation)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                    LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                    WHERE wsp.step_id = 60
                """)
                
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'No prompts found for title generation'}), 404
                
                system_prompt = result.get('system_prompt', '')
                task_prompt = result.get('task_prompt', '')
            
            # Replace placeholders in task prompt with actual data
            prompt_vars = {
                'idea_seed': idea_seed,
                'expanded_idea': expanded_idea,
                'section_content': section_content
            }
            
            # Replace [data:field] placeholders
            for key, value in prompt_vars.items():
                task_prompt = task_prompt.replace(f'[data:{key}]', str(value))
            
            # Prepare messages for LLM
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': task_prompt}
            ]
            
            # Execute LLM request
            logger.info(f"Calling LLM for title generation with system prompt: {system_prompt[:100]}...")
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
            
            generated_content = llm_response['content'].strip()
            logger.info(f"LLM response: {generated_content[:200]}...")
            
            # Parse JSON response
            try:
                # Extract JSON array from response
                json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    title_options = json.loads(json_str)
                    
                    if not isinstance(title_options, list) or len(title_options) != 3:
                        raise ValueError("Response must be an array of exactly 3 titles")
                    
                    # Clean up titles
                    title_options = [title.strip().strip('"').strip("'") for title in title_options]
                    
                    return jsonify({
                        'success': True,
                        'title_options': title_options,
                        'selected_index': 0
                    })
                else:
                    raise ValueError("No JSON array found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {generated_content}")
                return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
            
        except Exception as e:
            logger.error(f"Error generating titles for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-subtitle', methods=['POST'])
    def api_generate_subtitle(post_id):
        """Generate multiple subtitle options based on Development tab content and selected title using LLM"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
        if error:
            return jsonify({'error': error}), 400 if 'required' in error else 404
        
        # Replace post_id with target_post_id for all operations
        post_id = target_post_id
        
        try:
            # Check if this is a recipe post
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            # For recipe posts, use the same logic as title generation
            if post_type == 'recipe':
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT cr.recipe_title, cr.recipe_description
                        FROM post p
                        LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                        WHERE p.id = %s
                    """, (post_id,))
                    recipe_data = cursor.fetchone()
                    
                    if recipe_data and recipe_data.get('recipe_title'):
                        recipe_title = recipe_data['recipe_title']
                        recipe_description = recipe_data.get('recipe_description', '')
                        
                        # Generate subtitle (same logic as api_generate_titles)
                        cursor.execute("""
                            SELECT 
                                sp.system_prompt,
                                tp.prompt_text as task_prompt
                            FROM workflow_step_prompt wsp
                            LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                            LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                            WHERE wsp.step_id = 61
                        """)
                        subtitle_result = cursor.fetchone()
                        
                        generated_subtitle = ''
                        if subtitle_result:
                            subtitle_system = subtitle_result.get('system_prompt', '')
                            subtitle_task = subtitle_result.get('task_prompt', '')
                            
                            # Modify subtitle prompt for recipes - evocative phrase without repeating recipe name
                            subtitle_task = f"""Generate a short, evocative subtitle (8-12 words) for this Scottish recipe blog post.

Recipe Name: {recipe_title}
Recipe Description: {recipe_description}

CRITICAL REQUIREMENTS:
- Do NOT repeat the recipe name "{recipe_title}" in the subtitle
- Create a warm, inviting phrase that captures the essence, tradition, or appeal of this dish
- Focus on what makes it special: its heritage, when it's enjoyed, its comforting nature, or its regional significance
- Keep it poetic and evocative, not descriptive or instructional
- Examples of good subtitles: "A warming bowl of coastal comfort" or "Traditional fare for cold winter evenings" or "A taste of Highland heritage"

Return ONLY a single subtitle string, not an array. Do not use quotes or brackets."""
                            
                            messages = [
                                {'role': 'system', 'content': subtitle_system},
                                {'role': 'user', 'content': subtitle_task}
                            ]
                            
                            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                            
                            if 'error' not in llm_response and llm_response.get('content'):
                                generated_subtitle = llm_response['content'].strip()
                                # Remove quotes and brackets
                                generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                                
                                # Clean up any JSON array if LLM returned one
                                json_match = re.search(r'\[.*?\]', generated_subtitle, re.DOTALL)
                                if json_match:
                                    try:
                                        subtitle_array = json.loads(json_match.group(0))
                                        if isinstance(subtitle_array, list) and len(subtitle_array) > 0:
                                            generated_subtitle = subtitle_array[0].strip().strip('"').strip("'")
                                    except:
                                        pass
                                
                                # Remove any remaining quotes or brackets
                                generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                                
                                # If subtitle still contains the recipe name, try to extract just the evocative part
                                if recipe_title.lower() in generated_subtitle.lower():
                                    # Try to find a phrase that doesn't include the recipe name
                                    # Split by common separators and take the most evocative part
                                    parts = re.split(r'[:\-–—]', generated_subtitle)
                                    for part in parts:
                                        part = part.strip()
                                        if part and recipe_title.lower() not in part.lower() and len(part) > 10:
                                            generated_subtitle = part
                                            break
                                
                                # Final validation: if it still contains the recipe name, generate a simple fallback
                                if recipe_title.lower() in generated_subtitle.lower() or len(generated_subtitle) < 5:
                                    # Generate a simple evocative phrase manually
                                    if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                        generated_subtitle = "A warming bowl of coastal comfort"
                                    elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                        generated_subtitle = "Traditional fare for cold winter evenings"
                                    else:
                                        generated_subtitle = "A taste of Highland heritage"
                            else:
                                # If LLM fails, use a simple evocative phrase instead of recipe description
                                if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                    generated_subtitle = "A warming bowl of coastal comfort"
                                elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                    generated_subtitle = "Traditional fare for cold winter evenings"
                                else:
                                    generated_subtitle = "A taste of Highland heritage"
                        else:
                            # If no subtitle prompt found, use a simple evocative phrase
                            if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                generated_subtitle = "A warming bowl of coastal comfort"
                            elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                generated_subtitle = "Traditional fare for cold winter evenings"
                            else:
                                generated_subtitle = "A taste of Highland heritage"
                        
                        # Return as a single-item array for consistency with the API
                        return jsonify({
                            'success': True,
                            'subtitle_options': [generated_subtitle],
                            'selected_index': 0
                        })
            
            # For non-recipe posts, use normal subtitle generation
            data = request.get_json()
            idea_seed = data.get('idea_seed', '')
            expanded_idea = data.get('expanded_idea', '')
            selected_title = data.get('selected_title', '')
            section_content = data.get('section_content', '')
            
            logger.info(f"Generating subtitles for post {post_id} with title: {selected_title[:50]}...")
            
            # Get prompts from database for step 61 (Subtitle Generation)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                    LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                    WHERE wsp.step_id = 61
                """)
                
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'No prompts found for subtitle generation'}), 404
                
                system_prompt = result.get('system_prompt', '')
                task_prompt = result.get('task_prompt', '')
            
            # Modify the task prompt to request multiple subtitle options
            task_prompt = task_prompt.replace(
                'CRITICAL: Return ONLY the subtitle text.',
                'CRITICAL: Return ONLY a JSON array of exactly 3 subtitle options. Format: ["subtitle1", "subtitle2", "subtitle3"]'
            )
            
            # Replace placeholders in task prompt with actual data
            prompt_vars = {
                'idea_seed': idea_seed,
                'expanded_idea': expanded_idea,
                'selected_title': selected_title,
                'section_content': section_content
            }
            
            # Replace [data:field] placeholders
            for key, value in prompt_vars.items():
                task_prompt = task_prompt.replace(f'[data:{key}]', str(value))
            
            # Prepare messages for LLM
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': task_prompt}
            ]
            
            # Execute LLM request
            logger.info(f"Calling LLM for subtitle generation with system prompt: {system_prompt[:100]}...")
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
            
            generated_content = llm_response['content'].strip()
            logger.info(f"LLM response: {generated_content}")
            
            # Parse JSON response for subtitles
            try:
                json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    subtitle_options = json.loads(json_str)
                    
                    if not isinstance(subtitle_options, list) or len(subtitle_options) != 3:
                        raise ValueError("Response must be an array of exactly 3 subtitles")
                    
                    # Clean up subtitles
                    subtitle_options = [subtitle.strip().strip('"').strip("'") for subtitle in subtitle_options]
                    selected_subtitle = subtitle_options[0]
                else:
                    raise ValueError("No JSON array found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
            
            return jsonify({
                'success': True,
                'subtitle_options': subtitle_options,
                'selected_index': 0
            })
            
        except Exception as e:
            logger.error(f"Error generating subtitles for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

