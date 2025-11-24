"""Summary and slug generation API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .helpers import resolve_target_post_id, resolve_target_post_id_with_auto_week_check
from .llm_service import LLMService
from slugify import slugify
import logging
import json
import re

logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMService()


def register_routes(bp):
    """Register summary generation API routes"""
    
    @bp.route('/api/posts/<int:post_id>/generate-title-summary', methods=['POST'])
    def api_generate_title_summary(post_id):
        """Generate all header elements (title, subtitle, summary, slug) in one call"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        target_post_id, error = resolve_target_post_id_with_auto_week_check(post_id, year, week)
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
                        title_options = [recipe_title, recipe_title, recipe_title]
                        
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
                        
                        # Generate summary and slug (simplified for recipes)
                        # For now, return what we have - summary and slug can be generated separately if needed
                        return jsonify({
                            'success': True,
                            'title_options': title_options,
                            'selected_index': 0,
                            'subtitle': generated_subtitle,
                            'summary': '',  # Can be generated separately
                            'slug': recipe_title.lower().replace(' ', '-').replace("'", '').replace(':', '')
                        })
            
            # For profile posts, generate title starting with product name
            if post_type == 'profile':
                with db_manager.get_cursor() as cursor:
                    # Get product name
                    cursor.execute("""
                        SELECT cp.name, cp.short_description, cp.description
                        FROM post p
                        LEFT JOIN clan_products cp ON cp.id = p.profile_product_id
                        WHERE p.id = %s
                    """, (post_id,))
                    product_data = cursor.fetchone()
                    
                    if product_data and product_data.get('name'):
                        product_name = product_data['name']
                        product_description = product_data.get('short_description', '') or product_data.get('description', '')
                        
                        # Get section content for benefit generation
                        cursor.execute("""
                            SELECT section_heading, draft
                            FROM post_section
                            WHERE post_id = %s
                            ORDER BY section_order
                        """, (post_id,))
                        sections = cursor.fetchall()
                        section_content = '\n'.join([f"{s.get('section_heading', '')}: {s.get('draft', '')}" for s in sections])
                        
                        # Generate benefit summary using LLM
                        # Get title generation prompt as base
                        cursor.execute("""
                            SELECT 
                                sp.system_prompt,
                                tp.prompt_text as task_prompt
                            FROM workflow_step_prompt wsp
                            LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                            LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                            WHERE wsp.step_id = 60
                        """)
                        prompt_result = cursor.fetchone()
                        
                        system_prompt = prompt_result.get('system_prompt', '') if prompt_result else ''
                        
                        # Create profile-specific title prompt
                        profile_title_prompt = f"""Generate 3 title options for a product profile blog post.

CRITICAL REQUIREMENTS:
- Each title MUST start with the full product name verbatim: "{product_name}"
- Followed by a colon and space: ": "
- Then add 3-6 words summarizing a key benefit or appeal of this product
- Do NOT repeat the product name after the initial mention
- Focus on benefits like: quality, heritage, craftsmanship, functionality, design, tradition, etc.
- Keep the benefit summary concise and compelling

Product Name: {product_name}
Product Description: {product_description[:500] if product_description else 'No description available'}

Section Content (for context):
{section_content[:1000] if section_content else 'No section content available'}

Examples of good titles:
- "Luxury Scottish Cashmere Sweater, V‑Neck: Timeless Elegance and Comfort"
- "Traditional Tartan Scarf: Heritage Woven in Every Thread"
- "Handcrafted Leather Sporran: Authentic Scottish Accessory"

Return ONLY a JSON array of exactly 3 title strings, like this:
["{product_name}: Benefit 1", "{product_name}: Benefit 2", "{product_name}: Benefit 3"]"""
                        
                        messages = [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': profile_title_prompt}
                        ]
                        
                        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                        
                        if 'error' not in llm_response and llm_response.get('content'):
                            generated_content = llm_response['content'].strip()
                            
                            # Parse JSON response
                            try:
                                json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
                                if json_match:
                                    json_str = json_match.group(0)
                                    title_options = json.loads(json_str)
                                    
                                    if not isinstance(title_options, list) or len(title_options) != 3:
                                        raise ValueError("Response must be an array of exactly 3 titles")
                                    
                                    # Clean up titles and ensure they start with product name
                                    cleaned_titles = []
                                    for title in title_options:
                                        title = title.strip().strip('"').strip("'")
                                        # Ensure it starts with product name
                                        if not title.lower().startswith(product_name.lower()):
                                            title = f"{product_name}: {title}"
                                        cleaned_titles.append(title)
                                    
                                    title_options = cleaned_titles
                                else:
                                    raise ValueError("No JSON array found in response")
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"Failed to parse LLM response for profile title: {e}, using fallback")
                                # Fallback: use product name with generic benefits
                                title_options = [
                                    f"{product_name}: Quality Craftsmanship and Heritage",
                                    f"{product_name}: Timeless Design and Functionality",
                                    f"{product_name}: Authentic Scottish Tradition"
                                ]
                        else:
                            # Fallback if LLM fails
                            title_options = [
                                f"{product_name}: Quality Craftsmanship and Heritage",
                                f"{product_name}: Timeless Design and Functionality",
                                f"{product_name}: Authentic Scottish Tradition"
                            ]
                        
                        # Set selected_title for use in subtitle/summary generation
                        selected_title = title_options[0] if title_options else product_name
                        
                        # Get section content for subtitle/summary generation
                        cursor.execute("""
                            SELECT section_heading, draft
                            FROM post_section
                            WHERE post_id = %s
                            ORDER BY section_order
                        """, (post_id,))
                        sections = cursor.fetchall()
                        section_content = '\n'.join([f"{s.get('section_heading', '')}: {s.get('draft', '')}" for s in sections])
                        
                        # Get development data for subtitle/summary
                        cursor.execute("""
                            SELECT 
                                pd.idea_seed,
                                pd.expanded_idea
                            FROM post_development pd
                            WHERE pd.post_id = %s
                        """, (post_id,))
                        dev_result = cursor.fetchone()
                        idea_seed = dev_result.get('idea_seed', '') if dev_result else ''
                        expanded_idea = dev_result.get('expanded_idea', '') if dev_result else ''
                        
                        # Skip normal title generation, continue to subtitle/summary below
                        skip_title_generation = True
                    else:
                        return jsonify({'error': 'Product not found for profile post'}), 404
            else:
                # Not a profile post
                skip_title_generation = False
            
            # For non-recipe, non-profile posts, use normal generation
            if not skip_title_generation:
                # Get content from Development tab
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            pd.idea_seed,
                            pd.expanded_idea,
                            p.title,
                            p.title_choices
                        FROM post_development pd
                        JOIN post p ON p.id = pd.post_id
                        WHERE pd.post_id = %s
                    """, (post_id,))
                    
                    result = cursor.fetchone()
                    
                    if not result:
                        return jsonify({'error': 'No post development data found'}), 404
                    
                    idea_seed = result.get('idea_seed', '')
                    expanded_idea = result.get('expanded_idea', '')
                    current_title = result.get('title', '')
                    title_choices = result.get('title_choices', '[]')
                    
                    # Get section content
                    cursor.execute("""
                        SELECT section_heading, draft
                        FROM post_section
                        WHERE post_id = %s
                        ORDER BY section_order
                    """, (post_id,))
                    
                    sections = cursor.fetchall()
                    section_content = '\n'.join([f"{s.get('section_heading', '')}: {s.get('draft', '')}" for s in sections])
            
            logger.info(f"Generating all header elements for post {post_id}")
            
            # Generate titles using the same logic as api_generate_titles (skip for profile posts)
            if not skip_title_generation:
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
                
                # Execute LLM request for titles
                logger.info(f"Calling LLM for title generation")
                llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                
                if 'error' in llm_response:
                    logger.error(f"LLM generation failed: {llm_response['error']}")
                    return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
                
                generated_content = llm_response['content'].strip()
                
                # Parse JSON response for titles
                try:
                    json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        title_options = json.loads(json_str)
                        
                        if not isinstance(title_options, list) or len(title_options) != 3:
                            raise ValueError("Response must be an array of exactly 3 titles")
                        
                        # Clean up titles
                        title_options = [title.strip().strip('"').strip("'") for title in title_options]
                        selected_title = title_options[0]
                    else:
                        raise ValueError("No JSON array found in response")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
            # For profile posts, titles already generated above (title_options and selected_title are set)
            
            # Generate subtitle using the same logic as api_generate_subtitle
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
            
            # Modify the task prompt to request multiple subtitle options
            task_prompt = task_prompt.replace(
                'CRITICAL: Return ONLY the subtitle text.',
                'CRITICAL: Return ONLY a JSON array of exactly 3 subtitle options. Format: ["subtitle1", "subtitle2", "subtitle3"]'
            )
            
            # Prepare messages for LLM
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': task_prompt}
            ]
            
            # Execute LLM request for subtitle
            logger.info(f"Calling LLM for subtitle generation")
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
            
            generated_content = llm_response['content'].strip()
            
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
            
            # Generate summary using the same logic as api_generate_summary
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                    LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                    WHERE wsp.step_id = 62
                """)
                
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'No prompts found for summary generation'}), 404
                
                system_prompt = result.get('system_prompt', '')
                task_prompt = result.get('task_prompt', '')
            
            # Prepare content for summary generation
            summary_content = f"Selected Idea: {idea_seed}\n\nExpanded Idea: {expanded_idea}\n\nSection Content:\n{section_content}"
            
            # Format the prompt with the content
            formatted_prompt = task_prompt.format(content=summary_content)
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_prompt}
            ]
            
            # Execute LLM request for summary
            logger.info(f"Calling LLM for summary generation")
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
            
            summary = llm_response.get('content', '').strip()
            
            if not summary:
                logger.error("Empty summary response from LLM")
                return jsonify({'error': 'Empty summary response from LLM'}), 500
            
            # Generate slug from the selected title
            slug = slugify(title_options[0] if title_options else "default-title")
            
            return jsonify({
                'success': True,
                'title_options': title_options,
                'subtitle_options': subtitle_options,
                'subtitle_selected_index': 0,
                'summary': summary,
                'slug': slug
            })
            
        except Exception as e:
            logger.error(f"Error generating all header elements for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-summary', methods=['POST'])
    def api_generate_summary(post_id):
        """Generate summary for a post using LLM"""
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        target_post_id, error = resolve_target_post_id_with_auto_week_check(post_id, year, week)
        if error:
            return jsonify({'error': error}), 400 if 'required' in error else 404
        
        # Replace post_id with target_post_id for all operations
        post_id = target_post_id
        
        try:
            data = request.get_json()
            content = data.get('content', '')
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # Get prompts from database for step 62 (Summary Generation)
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                    JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                    WHERE wsp.step_id = 62
                """)
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'Summary generation prompts not found'}), 404
                
                system_prompt = result.get('system_prompt', '')
                task_prompt = result.get('task_prompt', '')
            
            # Format the prompt with the content
            formatted_prompt = task_prompt.format(content=content)
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_prompt}
            ]
            
            # Generate summary using LLM
            try:
                llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                
                if 'error' in llm_response:
                    logger.error(f"LLM generation failed: {llm_response['error']}")
                    raise Exception("LLM failed")
                
                summary = llm_response.get('content', '').strip()
                
                if not summary:
                    raise Exception("Empty response")
                    
            except Exception as e:
                logger.error(f"LLM service error: {e}")
                # NO FALLBACK - fail cleanly instead of generating generic fluff
                return jsonify({'error': f'LLM generation failed: {str(e)}'}), 500
            
            return jsonify({
                'success': True,
                'summary': summary.strip()
            })
            
        except Exception as e:
            logger.error(f"Error generating summary for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/posts/<int:post_id>/generate-slug', methods=['POST'])
    def api_generate_slug(post_id):
        """Generate slug from selected title using Python slugify"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get the selected title from the post
                cursor.execute("""
                    SELECT title FROM post WHERE id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'Post not found'}), 404
                
                title = result.get('title', '')
                if not title:
                    return jsonify({'error': 'No title found to generate slug from'}), 400
                
                # Generate slug from title using Python slugify
                generated_slug = slugify(title)
                
                return jsonify({
                    'success': True,
                    'slug': generated_slug
                })
                
        except Exception as e:
            logger.error(f"Error generating slug for post {post_id}: {e}")
            return jsonify({'error': str(e)}), 500

