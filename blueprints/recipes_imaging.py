# blueprints/recipes_imaging.py
"""Recipe-specific image generation routes and API endpoints."""

from flask import Blueprint, render_template, jsonify, request
import logging
from config.database import db_manager
from utils.taxonomy_helpers import get_post_type
import json

bp = Blueprint('recipes_imaging', __name__)
logger = logging.getLogger(__name__)


def _sync_recipe_prompts_to_sections(post_id, style_prompt_data, cursor):
    """Sync recipe image prompts from style data to actual sections."""
    try:
        logger.info(f"Syncing recipe prompts to sections for post {post_id}")
        logger.info(f"Style prompt data keys: {list(style_prompt_data.keys()) if isinstance(style_prompt_data, dict) else 'Not a dict'}")
        
        # Map prompts to sections
        prompt_mapping = {
            'recipe_ingredients': style_prompt_data.get('ingredients_image_prompt'),
            'recipe_method': style_prompt_data.get('method_image_prompt')
        }
        
        logger.info(f"Prompt mapping: ingredients={bool(prompt_mapping['recipe_ingredients'])}, method={bool(prompt_mapping['recipe_method'])}")
        
        for section_type, prompt_text in prompt_mapping.items():
            if not prompt_text:
                logger.warning(f"No prompt text for {section_type}")
                continue
            
            # Extract prompt text from object if needed
            if isinstance(prompt_text, dict):
                # If it's a structured object, extract the description or combine subject + description
                if 'description' in prompt_text:
                    prompt_text = prompt_text['description']
                elif 'subject' in prompt_text:
                    prompt_text = prompt_text['subject']
                elif 'image_prompt' in prompt_text:
                    prompt_text = prompt_text['image_prompt']
                else:
                    # Fallback: convert to string
                    prompt_text = str(prompt_text)
            elif not isinstance(prompt_text, str):
                prompt_text = str(prompt_text)
            
            # For ingredients section, enhance prompt with actual ingredients from JSON
            if section_type == 'recipe_ingredients':
                # Get actual ingredients from post_section_elements
                cursor.execute("""
                    SELECT post_section_elements
                    FROM post_section
                    WHERE post_id = %s AND section_type = 'recipe_ingredients'
                    LIMIT 1
                """, (post_id,))
                ingredients_section = cursor.fetchone()
                
                if ingredients_section and ingredients_section.get('post_section_elements'):
                    try:
                        ingredients_data = json.loads(ingredients_section['post_section_elements']) if isinstance(ingredients_section['post_section_elements'], str) else ingredients_section['post_section_elements']
                        
                        if isinstance(ingredients_data, dict) and 'ingredients' in ingredients_data:
                            # Extract ingredient names
                            ingredient_names = []
                            for ing in ingredients_data['ingredients']:
                                if isinstance(ing, dict) and 'item' in ing:
                                    ingredient_names.append(ing['item'])
                            
                            if ingredient_names:
                                # Replace generic "including" with actual ingredients
                                # Remove any "including X, Y, Z" pattern and replace with actual list
                                import re
                                prompt_text = re.sub(r'including[^.]*\.?', '', prompt_text, flags=re.IGNORECASE)
                                prompt_text = prompt_text.strip()
                                
                                # Append actual ingredients list
                                ingredients_list = ', '.join(ingredient_names)
                                prompt_text = f"{prompt_text} The ingredients shown are: {ingredients_list}."
                                logger.info(f"Enhanced ingredients prompt with actual ingredients: {ingredients_list}")
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.warning(f"Could not extract ingredients from JSON: {e}")
            
            logger.info(f"Syncing {section_type} prompt (length: {len(prompt_text)})")
                
            # Find the section
            cursor.execute("""
                SELECT id FROM post_section
                WHERE post_id = %s AND section_type = %s
                LIMIT 1
            """, (post_id, section_type))
            section = cursor.fetchone()
            
            if not section:
                logger.warning(f"Section not found for {section_type} in post {post_id}")
                continue
            
            # Save prompt to section's image_prompts field
            image_prompts_json = json.dumps({
                'image_prompt': prompt_text,
                'base_concept': prompt_text
            })
            
            cursor.execute("""
                UPDATE post_section
                SET image_prompts = %s
                WHERE id = %s
            """, (image_prompts_json, section['id']))
            
            logger.info(f"Successfully synced {section_type} prompt to section {section['id']}")
        
        cursor.connection.commit()
        logger.info(f"Completed syncing prompts for post {post_id}")
    except Exception as e:
        logger.error(f"Error syncing recipe prompts to sections: {e}", exc_info=True)
        # Don't fail the whole request if sync fails


@bp.route('/posts/<int:post_id>/recipes/image-style-prompt')
def recipe_image_style_prompt(post_id):
    """Recipe image style and prompt generation page."""
    try:
        # Verify this is a recipe post
        post_type = get_post_type(post_id)
        if post_type != 'recipe':
            return "This page is only for recipe posts", 400
        
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, cr.recipe_title, cr.recipe_description, cr.seasonal_context
                FROM post p
                LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get existing style/prompts if any
            cursor.execute("""
                SELECT post_section_elements
                FROM post_section
                WHERE post_id = %s AND section_type = 'recipe_image_style'
                LIMIT 1
            """, (post_id,))
            style_section = cursor.fetchone()
            
            style_data = None
            if style_section and style_section.get('post_section_elements'):
                try:
                    style_data = json.loads(style_section['post_section_elements']) if isinstance(style_section['post_section_elements'], str) else style_section['post_section_elements']
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse style data for post {post_id}")
            
            # Get recipe data for prompt generation
            recipe_title = post.get('recipe_title') or post.get('title', '')
            recipe_description = post.get('recipe_description') or post.get('subtitle', '')
            seasonal_context = post.get('seasonal_context', '')
            
            return render_template(
                'recipes/image_style_prompt.html',
                post_id=post_id,
                post=post,
                recipe_title=recipe_title,
                recipe_description=recipe_description,
                seasonal_context=seasonal_context,
                style_data=style_data
            )
    except Exception as e:
        logger.error(f"Error in recipe_image_style_prompt: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


@bp.route('/api/posts/<int:post_id>/recipes/image-style-prompt/generate', methods=['POST'])
def api_generate_recipe_image_style_prompt(post_id):
    """Generate style guidelines and prompts for all three recipe images."""
    try:
        # Verify this is a recipe post
        post_type = get_post_type(post_id)
        if post_type != 'recipe':
            return jsonify({'error': 'This endpoint is only for recipe posts'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Get recipe data
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, cr.recipe_title, cr.recipe_description, cr.seasonal_context
                FROM post p
                LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get the prompt template
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt
                WHERE name = 'Recipe Image Style & Prompts (Scottish Recipes)'
                LIMIT 1
            """, ())
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Prompt template not found'}), 404
            
            # Replace placeholders
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            recipe_title = post.get('recipe_title') or post.get('title', '')
            recipe_description = post.get('recipe_description') or post.get('subtitle', '')
            seasonal_context = post.get('seasonal_context', '')
            
            prompt_text = prompt_text.replace('[data:title]', recipe_title)
            prompt_text = prompt_text.replace('[data:subtitle]', recipe_description)
            prompt_text = prompt_text.replace('[data:seasonal_context]', seasonal_context)
            
            # Call LLM
            from blueprints.header import LLMService
            llm_service = LLMService()
            
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            result = llm_service.execute_llm_request(
                'ollama',
                'llama3.2:latest',
                messages
            )
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            generated_content = result.get('content', '').strip()
            if not generated_content:
                return jsonify({'error': 'LLM returned empty content'}), 500
            
            # Parse JSON from response
            from utils.recipe_json_parser import extract_json_from_response
            style_prompt_data = extract_json_from_response(generated_content)
            
            if not style_prompt_data:
                return jsonify({
                    'error': 'Failed to parse JSON from LLM response',
                    'raw_response': generated_content[:500]
                }), 500
            
            # Save to post_section with special section_type
            cursor.execute("""
                SELECT id FROM post_section
                WHERE post_id = %s AND section_type = 'recipe_image_style'
                LIMIT 1
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE post_section
                    SET post_section_elements = %s, draft = %s
                    WHERE id = %s
                """, (json.dumps(style_prompt_data), generated_content, existing['id']))
            else:
                cursor.execute("""
                    INSERT INTO post_section (post_id, section_order, section_type, section_heading, post_section_elements, draft, status)
                    VALUES (%s, 0, 'recipe_image_style', 'Recipe Image Style & Prompts', %s, %s, 'draft')
                """, (post_id, json.dumps(style_prompt_data), generated_content))
            
            cursor.connection.commit()
            
            # Sync prompts to actual sections (use a new cursor for the sync)
            with db_manager.get_cursor() as sync_cursor:
                _sync_recipe_prompts_to_sections(post_id, style_prompt_data, sync_cursor)
            
            return jsonify({
                'success': True,
                'style_data': style_prompt_data,
                'raw_response': generated_content
            })
            
    except Exception as e:
        logger.error(f"Error in api_generate_recipe_image_style_prompt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/recipes/image-style-prompt', methods=['PUT'])
def api_update_recipe_image_style_prompt(post_id):
    """Update style guidelines and prompts (editable)."""
    try:
        data = request.get_json()
        style_data = data.get('style_data')
        
        if not style_data:
            return jsonify({'error': 'style_data is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM post_section
                WHERE post_id = %s AND section_type = 'recipe_image_style'
                LIMIT 1
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE post_section
                    SET post_section_elements = %s
                    WHERE id = %s
                """, (json.dumps(style_data), existing['id']))
            else:
                cursor.execute("""
                    INSERT INTO post_section (post_id, section_order, section_type, section_heading, post_section_elements, status)
                    VALUES (%s, 0, 'recipe_image_style', 'Recipe Image Style & Prompts', %s, 'draft')
                """, (post_id, json.dumps(style_data)))
            
            cursor.connection.commit()
            
            # Sync prompts to actual sections (use a new cursor for the sync)
            with db_manager.get_cursor() as sync_cursor:
                _sync_recipe_prompts_to_sections(post_id, style_data, sync_cursor)
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error in api_update_recipe_image_style_prompt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/recipes/sync-prompts', methods=['POST'])
def api_sync_recipe_prompts(post_id):
    """Manually sync recipe prompts from style data to sections."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get style data
            cursor.execute("""
                SELECT post_section_elements
                FROM post_section
                WHERE post_id = %s AND section_type = 'recipe_image_style'
                LIMIT 1
            """, (post_id,))
            style_section = cursor.fetchone()
            
            if not style_section or not style_section.get('post_section_elements'):
                return jsonify({'error': 'No style data found. Please generate prompts first.'}), 404
            
            style_data = json.loads(style_section['post_section_elements']) if isinstance(style_section['post_section_elements'], str) else style_section['post_section_elements']
            
            # Sync prompts
            _sync_recipe_prompts_to_sections(post_id, style_data, cursor)
            
            return jsonify({'success': True, 'message': 'Prompts synced successfully'})
            
    except Exception as e:
        logger.error(f"Error in api_sync_recipe_prompts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
