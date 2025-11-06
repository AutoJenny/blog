# blueprints/recipes_research.py
"""Recipe research routes and API endpoints."""

from flask import Blueprint, render_template, jsonify, request
import logging
from config.database import db_manager
from utils.taxonomy_helpers import get_post_type
import json

bp = Blueprint('recipes_research', __name__)
logger = logging.getLogger(__name__)


@bp.route('/posts/<int:post_id>/recipes/research')
def recipe_research(post_id):
    """Recipe research page - gather authentic recipe information from authoritative sources."""
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
            
            # Get existing research data if any
            cursor.execute("""
                SELECT recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            research_data = None
            if dev_data and dev_data.get('recipe_research'):
                try:
                    research_data = json.loads(dev_data['recipe_research']) if isinstance(dev_data['recipe_research'], str) else dev_data['recipe_research']
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse recipe_research for post {post_id}")
            
            # Get Further Reading sources if available
            cursor.execute("""
                SELECT post_section_elements
                FROM post_section
                WHERE post_id = %s AND section_type = 'recipe_further_reading'
                LIMIT 1
            """, (post_id,))
            further_reading = cursor.fetchone()
            
            further_reading_sources = []
            if further_reading and further_reading.get('post_section_elements'):
                try:
                    sources_data = json.loads(further_reading['post_section_elements']) if isinstance(further_reading['post_section_elements'], str) else further_reading['post_section_elements']
                    if isinstance(sources_data, dict) and 'sources' in sources_data:
                        further_reading_sources = sources_data['sources']
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse further reading sources for post {post_id}")
            
            recipe_title = post.get('recipe_title') or post.get('title', '')
            recipe_description = post.get('recipe_description') or post.get('subtitle', '')
            seasonal_context = post.get('seasonal_context', '')
            
            return render_template(
                'recipes/research.html',
                post_id=post_id,
                post=post,
                recipe_title=recipe_title,
                recipe_description=recipe_description,
                seasonal_context=seasonal_context,
                research_data=research_data,
                further_reading_sources=further_reading_sources
            )
    except Exception as e:
        logger.error(f"Error in recipe_research: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500


@bp.route('/api/posts/<int:post_id>/recipes/research/generate', methods=['POST'])
def api_generate_recipe_research(post_id):
    """Generate recipe research using LLM with Further Reading sources and authoritative recipe sites."""
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
            
            # Get Further Reading sources
            cursor.execute("""
                SELECT post_section_elements
                FROM post_section
                WHERE post_id = %s AND section_type = 'recipe_further_reading'
                LIMIT 1
            """, (post_id,))
            further_reading = cursor.fetchone()
            
            further_reading_sources = []
            if further_reading and further_reading.get('post_section_elements'):
                try:
                    sources_data = json.loads(further_reading['post_section_elements']) if isinstance(further_reading['post_section_elements'], str) else further_reading['post_section_elements']
                    if isinstance(sources_data, dict) and 'sources' in sources_data:
                        further_reading_sources = sources_data['sources']
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Get the research prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt
                WHERE name = 'Recipe Research (Scottish Recipes)'
                LIMIT 1
            """, ())
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Research prompt template not found'}), 404
            
            # Replace placeholders
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            recipe_title = post.get('recipe_title') or post.get('title', '')
            recipe_description = post.get('recipe_description') or post.get('subtitle', '')
            seasonal_context = post.get('seasonal_context', '')
            
            prompt_text = prompt_text.replace('[data:title]', recipe_title)
            prompt_text = prompt_text.replace('[data:subtitle]', recipe_description)
            prompt_text = prompt_text.replace('[data:seasonal_context]', seasonal_context)
            
            # Add Further Reading sources to prompt
            if further_reading_sources:
                sources_text = "\n\nFURTHER READING SOURCES TO USE:\n"
                for i, source in enumerate(further_reading_sources, 1):
                    title = source.get('title', '')
                    url = source.get('url', '')
                    why_good = source.get('why_good', '')
                    sources_text += f"{i}. {title} ({url})\n"
                    if why_good:
                        sources_text += f"   Why it's good: {why_good}\n"
                prompt_text += sources_text
            
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
            research_data = extract_json_from_response(generated_content)
            
            if not research_data:
                # If no JSON, store as plain text
                research_data = {'research_text': generated_content}
            
            # Save to post_development
            cursor.execute("""
                SELECT id FROM post_development WHERE post_id = %s
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE post_development
                    SET recipe_research = %s
                    WHERE post_id = %s
                """, (json.dumps(research_data), post_id))
            else:
                cursor.execute("""
                    INSERT INTO post_development (post_id, recipe_research)
                    VALUES (%s, %s)
                """, (post_id, json.dumps(research_data)))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'research_data': research_data,
                'raw_response': generated_content
            })
            
    except Exception as e:
        logger.error(f"Error in api_generate_recipe_research: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/recipes/research', methods=['PUT'])
def api_update_recipe_research(post_id):
    """Update recipe research data (editable)."""
    try:
        data = request.get_json()
        research_data = data.get('research_data')
        
        if not research_data:
            return jsonify({'error': 'research_data is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM post_development WHERE post_id = %s
            """, (post_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE post_development
                    SET recipe_research = %s
                    WHERE post_id = %s
                """, (json.dumps(research_data), post_id))
            else:
                cursor.execute("""
                    INSERT INTO post_development (post_id, recipe_research)
                    VALUES (%s, %s)
                """, (post_id, json.dumps(research_data)))
            
            cursor.connection.commit()
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error in api_update_recipe_research: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

