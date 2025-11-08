# Authoring Content API Blueprint
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)
bp = Blueprint('authoring_content', __name__)

# Import micro-modules
from blueprints.authoring_api_sections import api_get_sections as sections_api_func, api_get_section as section_api_func

# Import LLM service
try:
    from modules.llm_service import llm_service
except ImportError:
    # Fallback for when llm_service is not available
    llm_service = None

@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get all sections for a post"""
    return sections_api_func(post_id)

@bp.route('/api/posts/<int:post_id>/sections/<section_id>')
def api_get_section_detail(post_id, section_id):
    """Get detailed information for a specific section"""
    return section_api_func(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>', methods=['PUT'])
def api_save_section_content(post_id, section_id):
    """Save section content (draft, polished, etc.)"""
    try:
        data = request.get_json()
        
        # Extract content fields
        draft = data.get('draft', '')
        polished = data.get('polished', '')
        ideas_to_include = data.get('ideas_to_include', '')
        facts_to_include = data.get('facts_to_include', '')
        highlighting = data.get('highlighting', '')
        status = data.get('status', 'draft')
        
        with db_manager.get_cursor() as cursor:
            # Update the section
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, polished = %s, ideas_to_include = %s, 
                    facts_to_include = %s, highlighting = %s, status = %s
                WHERE post_id = %s AND id = %s
            """, (draft, polished, ideas_to_include, facts_to_include, 
                  highlighting, status, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section content saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving section content: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate', methods=['POST'])
def api_generate_section_draft(post_id, section_id):
    """Generate section draft using LLM"""
    try:
        data = request.get_json()
        
        # Get section data (including section_type for recipe/profile sections)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT section_heading, section_description, ideas_to_include, 
                       facts_to_include, highlighting, section_order, section_type
                FROM post_section 
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            # If not found in post_section, check post_development.sections
            if not section:
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if result and result.get('sections'):
                    import json
                    try:
                        sections_data = json.loads(result['sections'])
                        if isinstance(sections_data, dict) and 'sections' in sections_data:
                            sections_list = sections_data['sections']
                        elif isinstance(sections_data, list):
                            sections_list = sections_data
                        else:
                            sections_list = []
                        
                        # Find the section matching the requested ID
                        section_data = next((s for s in sections_list if str(s.get('id', '')) == str(section_id)), None)
                        
                        if section_data:
                            # Convert JSON section to post_section-like format
                            section = {
                                'section_heading': section_data.get('title', f'Section {section_id}'),
                                'section_description': section_data.get('subtitle', ''),
                                'ideas_to_include': None,
                                'facts_to_include': None,
                                'highlighting': None,
                                'section_order': section_data.get('order', section_data.get('index', int(section_id)))
                            }
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")

            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get post context
            cursor.execute("""
                SELECT title, status FROM post WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get post_development data (may be minimal for recipe posts)
            cursor.execute("""
                SELECT idea_seed, sections, section_structure, recipe_research FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            # Check if this is a recipe post
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            is_recipe_post = (post_type == 'recipe')
            
            # Get Section Drafting prompt - prioritize section_type for recipe/profile sections
            prompt_name = None
            section_type = section.get('section_type') if section else None
            
            # For recipe/profile sections, try section-specific prompt first
            if section_type and section_type.startswith('recipe_'):
                # Map section_type to prompt name (e.g., 'recipe_background' -> 'Recipe Background')
                section_prompt_map = {
                    'recipe_background': 'Recipe Background',
                    'recipe_ingredients': 'Recipe Ingredients',
                    'recipe_method': 'Recipe Method',
                    'recipe_variants': 'Recipe Variants',
                    'recipe_serving': 'Recipe Serving Suggestions',
                    'recipe_further_reading': 'Recipe Further Reading'
                }
                base_section_name = section_prompt_map.get(section_type)
                if base_section_name:
                    # Try section-specific prompt first (e.g., "Recipe Background (Recipe)")
                    cursor.execute("""
                        SELECT name FROM llm_prompt 
                        WHERE name = %s OR name = %s
                        ORDER BY 
                            CASE WHEN name = %s THEN 1 ELSE 2 END,
                            updated_at DESC
                        LIMIT 1
                    """, (
                        f'{base_section_name} (Recipe)',
                        base_section_name,
                        f'{base_section_name} (Recipe)'
                    ))
                    section_prompt = cursor.fetchone()
                    if section_prompt:
                        prompt_name = section_prompt['name']
            
            # If no section-specific prompt found, check post-level settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('section_drafting_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                prompt_name = 'Section Drafting'
            
            # Get the selected prompt - NO FALLBACKS
            cursor.execute("""
                SELECT prompt_text, system_prompt
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
            
            import json
            import re
            
            # Build the prompt
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # For recipe posts, use simpler data extraction
            if is_recipe_post:
                # Get recipe data from calendar_recipes using recipe_id (unique recipe definition ID)
                cursor.execute("""
                    SELECT cr.recipe_title, cr.recipe_description, cr.seasonal_context
                    FROM post p
                    JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                recipe_data = cursor.fetchone()
                
                # Extract values for recipe posts
                if not recipe_data:
                    return jsonify({'error': 'Recipe data not found'}), 404
                
                selected_idea = dev_data.get('idea_seed') if dev_data else recipe_data.get('recipe_title', '')
                section_title = section.get('section_heading', '')
                section_description = section.get('section_description', '')
                topics_text = ''
                
                # Get recipe-specific context
                recipe_title = recipe_data.get('recipe_title') or post.get('title', '')
                recipe_description = recipe_data.get('recipe_description') or ''
                seasonal_context = recipe_data.get('seasonal_context') or ''
                
                # Get research data if available
                research_data = None
                if dev_data:
                    research_raw = dev_data.get('recipe_research')
                    if research_raw is not None:
                        try:
                            # Handle both string (JSON) and dict (JSONB) formats
                            if isinstance(research_raw, str):
                                research_data = json.loads(research_raw)
                            elif isinstance(research_raw, dict):
                                research_data = research_raw
                            else:
                                logger.warning(f"Unexpected recipe_research type: {type(research_raw)}")
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Failed to parse recipe_research for post {post_id}: {e}")
                
                # Get avoid headings (all other sections)
                cursor.execute("""
                    SELECT section_heading, section_description
                    FROM post_section
                    WHERE post_id = %s AND section_order != %s
                    ORDER BY section_order
                """, (post_id, section.get('section_order', 0)))
                other_sections = cursor.fetchall()
                avoid_headings = '\n'.join([
                    f"{s['section_heading']}: {s['section_description']}"
                    for s in other_sections
                    if s['section_heading'] or s['section_description']
                ])
                
                # Replace placeholders for recipe prompts
                # Ensure all substitution values are strings (not None)
                prompt_text = re.sub(r'\[data:title\]', recipe_title or '', prompt_text)
                prompt_text = re.sub(r'\[data:subtitle\]', recipe_description or '', prompt_text)
                prompt_text = re.sub(r'\[data:seasonal_context\]', seasonal_context or '', prompt_text)
                # Only substitute if selected_idea is not None
                if selected_idea:
                    prompt_text = re.sub(r'\[Selected Idea\]', selected_idea, prompt_text)
                else:
                    # Remove the placeholder if no idea is selected
                    prompt_text = re.sub(r'\[Selected Idea\]', '', prompt_text)
                # Ensure all substitution values are strings (not None)
                prompt_text = re.sub(r'\[Title\]', section_title or '', prompt_text)
                prompt_text = re.sub(r'\[Subtitle\]', section_description or '', prompt_text)
                prompt_text = re.sub(r'\[Description\]', section_description or '', prompt_text)
                prompt_text = re.sub(r'\[Topics\]', topics_text or '', prompt_text)
                prompt_text = re.sub(r'\[Avoid Headings\]', avoid_headings or '', prompt_text)
                
                # Add research data to prompt if available (critical for authentic recipes)
                if research_data:
                    research_text = "\n\n=== AUTHENTIC RECIPE RESEARCH DATA (USE THIS, NOT INVENTED INGREDIENTS/METHODS) ===\n"
                    
                    # Add authentic ingredients
                    if research_data.get('authentic_ingredients'):
                        research_text += "\nAUTHENTIC INGREDIENTS:\n"
                        for ing in research_data['authentic_ingredients']:
                            item = ing.get('item', '')
                            amount = ing.get('amount', '')
                            notes = ing.get('notes', '')
                            research_text += f"- {item}: {amount}"
                            if notes:
                                research_text += f" ({notes})"
                            sources = ing.get('sources', [])
                            if sources:
                                research_text += f" [Sources: {', '.join(sources)}]"
                            research_text += "\n"
                    
                    # Add authentic method
                    if research_data.get('authentic_method'):
                        method = research_data['authentic_method']
                        if method.get('summary'):
                            research_text += f"\nAUTHENTIC METHOD SUMMARY: {method['summary']}\n"
                        if method.get('key_steps'):
                            research_text += "\nKEY AUTHENTIC STEPS:\n"
                            for step in method['key_steps']:
                                research_text += f"- {step}\n"
                        if method.get('traditional_techniques'):
                            research_text += f"\nTRADITIONAL TECHNIQUES: {', '.join(method['traditional_techniques'])}\n"
                    
                    # Add authenticity notes
                    if research_data.get('authenticity_notes'):
                        research_text += f"\nAUTHENTICITY NOTES: {research_data['authenticity_notes']}\n"
                    
                    research_text += "\n=== END RESEARCH DATA ===\n"
                    prompt_text += research_text
            else:
                # For themed posts, use existing logic
                if not dev_data:
                    return jsonify({'error': 'Post development data not found'}), 404
                
                # Extract data from dev_data JSON fields
                sections_list = json.loads(dev_data['sections']) if isinstance(dev_data['sections'], str) else dev_data['sections']
                structure_data = json.loads(dev_data['section_structure']) if isinstance(dev_data['section_structure'], str) else dev_data['section_structure']
                
                # Find current section in sections list (by order or id)
                sections = sections_list.get('sections', []) if isinstance(sections_list, dict) else sections_list
                section_order = section.get('section_order', int(section_id))
                current_section_data = next((s for s in sections if str(s.get('id', '')) == str(section_id) or s.get('order') == section_order or s.get('index') == section_order), None)
                
                # Find current section in structure (by id)
                structure_sections = structure_data.get('sections', []) if isinstance(structure_data, dict) else []
                section_id_str = f"S{str(section['section_order']).zfill(2)}"
                current_structure_data = next((s for s in structure_sections if s.get('id') == section_id_str), None)
                
                # Extract values
                selected_idea = dev_data['idea_seed'] or ''
                section_title = current_section_data.get('title', '') if current_section_data else ''
                section_description = current_structure_data.get('description', '') if current_structure_data else ''
                topics = current_section_data.get('topics', []) if current_section_data else []
                topics_text = '\n- '.join(topics) if topics else ''
                
                # Get avoid headings (all other sections)
                cursor.execute("""
                    SELECT section_heading, section_description
                    FROM post_section
                    WHERE post_id = %s AND section_order != %s
                    ORDER BY section_order
                """, (post_id, section['section_order']))
                other_sections = cursor.fetchall()
                avoid_headings = '\n'.join([
                    f"{s['section_heading']}: {s['section_description']}"
                    for s in other_sections
                    if s['section_heading'] or s['section_description']
                ])
                
                # Replace placeholders
                # Only substitute if selected_idea is not None
                if selected_idea:
                    prompt_text = re.sub(r'\[Selected Idea\]', selected_idea, prompt_text)
                else:
                    # Remove the placeholder if no idea is selected
                    prompt_text = re.sub(r'\[Selected Idea\]', '', prompt_text)
                # Ensure all substitution values are strings (not None)
                prompt_text = re.sub(r'\[Title\]', section_title or '', prompt_text)
                prompt_text = re.sub(r'\[Subtitle\]', section_description or '', prompt_text)
                prompt_text = re.sub(r'\[Description\]', section_description or '', prompt_text)
                prompt_text = re.sub(r'\[Topics\]', topics_text or '', prompt_text)
                prompt_text = re.sub(r'\[Avoid Headings\]', avoid_headings or '', prompt_text)
                
                # Set variables for logging
                topics = current_section_data.get('topics', []) if current_section_data else []
            
            # Log generation info
            section_title_for_log = section.get('section_heading', '') if is_recipe_post else (section_title if 'section_title' in locals() else '')
            topics_count = len(topics) if 'topics' in locals() else 0
            section_description_for_log = section_description if 'section_description' in locals() else ''
            logger.info(f"Generated for: {section_title_for_log}, {topics_count} topics, description length: {len(section_description_for_log) if section_description_for_log else 0}")
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Prepare intercept context for LLM message tracking
            intercept_context = {
                'post_id': post_id,
                'section_id': section_id,
                'step_id': 62,  # Section drafting step
                'context_type': 'section_draft_generation'
            }
            
            # Execute LLM request
            result = llm_service.execute_llm_request(
                'ollama', 
                'llama3.2:latest', 
                messages,
                intercept_context=intercept_context
            )
            
            # Defensive check: ensure result is a dict
            if not isinstance(result, dict):
                logger.error(f"LLM service returned non-dict result: {type(result)}: {result}")
                return jsonify({'error': 'LLM service returned invalid response format'}), 500
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            generated_content = result.get('content', '').strip()
            if not generated_content:
                return jsonify({'error': 'LLM returned empty content'}), 500
            
            # Strip any H2 headings that LLM might have added (defensive measure)
            # H2 headings should only come from section_heading field, never from generated content
            import re
            original_content = generated_content
            generated_content = re.sub(r'<h2[^>]*>.*?</h2>', '', generated_content, flags=re.IGNORECASE | re.DOTALL)
            if original_content != generated_content:
                logger.info(f"Stripped H2 heading from generated content for section {section_id}")
            
            # For recipe sections that require structured JSON, parse and store separately
            structured_data = None
            if is_recipe_post and section_type:
                from utils.recipe_json_parser import (
                    extract_json_from_response,
                    validate_ingredients_json,
                    validate_method_json,
                    validate_variants_json,
                    validate_serving_json,
                    validate_further_reading_json,
                    sort_ingredients_by_weight
                )
                
                # Try to extract JSON from response
                json_data = extract_json_from_response(generated_content)
                
                if json_data:
                    # Validate based on section type
                    is_valid = False
                    if section_type == 'recipe_ingredients':
                        is_valid = validate_ingredients_json(json_data)
                        if is_valid and 'ingredients' in json_data:
                            # Sort ingredients by weight
                            json_data['ingredients'] = sort_ingredients_by_weight(json_data['ingredients'])
                    elif section_type == 'recipe_method':
                        is_valid = validate_method_json(json_data)
                    elif section_type == 'recipe_variants':
                        is_valid = validate_variants_json(json_data)
                    elif section_type == 'recipe_serving':
                        is_valid = validate_serving_json(json_data)
                    elif section_type == 'recipe_further_reading':
                        is_valid = validate_further_reading_json(json_data)
                    
                    if is_valid:
                        import json as json_module
                        structured_data = json_module.dumps(json_data)
                        logger.info(f"Extracted and validated structured JSON for {section_type}")
                    else:
                        logger.warning(f"JSON validation failed for {section_type}, storing as plain text")
            
            # For recipe sections with structured data, render to HTML and save to polished
            polished_html = None
            if structured_data and section_type and section_type.startswith('recipe_'):
                try:
                    from utils.recipe_section_renderer import render_recipe_section
                    # structured_data is a JSON string, need to parse it to dict
                    import json as json_module
                    section_elements = json_module.loads(structured_data)
                    polished_html = render_recipe_section(section_type, section_elements, generated_content)
                    logger.info(f"Rendered recipe section {section_id} ({section_type}) to HTML")
                except Exception as e:
                    logger.error(f"Error rendering recipe section {section_id} to HTML: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fall back to generated_content if rendering fails
                    polished_html = generated_content
            
            # Save the generated content - try UPDATE first, then INSERT if needed
            if structured_data:
                if polished_html:
                    # Save both JSON (for editing) and HTML (for preview/publish)
                    cursor.execute("""
                        UPDATE post_section 
                        SET draft = %s, post_section_elements = %s, polished = %s, status = 'draft'
                        WHERE post_id = %s AND id = %s
                    """, (generated_content, structured_data, polished_html, post_id, section_id))
                else:
                    cursor.execute("""
                        UPDATE post_section 
                        SET draft = %s, post_section_elements = %s, status = 'draft'
                        WHERE post_id = %s AND id = %s
                    """, (generated_content, structured_data, post_id, section_id))
            else:
                cursor.execute("""
                    UPDATE post_section 
                    SET draft = %s, status = 'draft'
                    WHERE post_id = %s AND id = %s
                """, (generated_content, post_id, section_id))
            
            # If no row was updated, create one (section might be from post_development.sections)
            if cursor.rowcount == 0:
                # For recipe sections, ensure polished HTML is set
                if structured_data and section_type and section_type.startswith('recipe_') and not polished_html:
                    try:
                        from utils.recipe_section_renderer import render_recipe_section
                        # Parse JSON if needed
                        if isinstance(structured_data, str):
                            import json
                            section_elements = json.loads(structured_data)
                        else:
                            section_elements = structured_data
                        polished_html = render_recipe_section(section_type, section_elements, generated_content)
                    except Exception as e:
                        logger.error(f"Error rendering recipe section {section_id} to HTML during insert: {e}")
                        polished_html = None
                
                # Get section_order from the section data we retrieved
                section_order = section.get('section_order', int(section_id))
                try:
                    if structured_data:
                        if polished_html:
                            cursor.execute("""
                                INSERT INTO post_section (post_id, id, section_order, section_heading, section_description, draft, post_section_elements, polished, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'draft')
                            """, (
                                post_id, 
                                int(section_id), 
                                section_order,
                                section.get('section_heading', f'Section {section_id}'),
                                section.get('section_description', ''),
                                generated_content,
                                structured_data,
                                polished_html
                            ))
                        else:
                            cursor.execute("""
                                INSERT INTO post_section (post_id, id, section_order, section_heading, section_description, draft, post_section_elements, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft')
                            """, (
                                post_id, 
                                int(section_id), 
                                section_order,
                                section.get('section_heading', f'Section {section_id}'),
                                section.get('section_description', ''),
                                generated_content,
                                structured_data
                            ))
                    else:
                        cursor.execute("""
                            INSERT INTO post_section (post_id, id, section_order, section_heading, section_description, draft, status)
                            VALUES (%s, %s, %s, %s, %s, %s, 'draft')
                        """, (
                            post_id, 
                            int(section_id), 
                            section_order,
                            section.get('section_heading', f'Section {section_id}'),
                            section.get('section_description', ''),
                            generated_content
                        ))
                except Exception as insert_error:
                    # If insert fails (e.g., duplicate key), try update instead
                    if 'duplicate' in str(insert_error).lower() or 'unique' in str(insert_error).lower():
                        cursor.execute("""
                            UPDATE post_section 
                            SET draft = %s, status = 'draft'
                            WHERE post_id = %s AND id = %s
                        """, (generated_content, post_id, int(section_id)))
                    else:
                        raise
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'draft': generated_content,
                'message': 'Section draft generated successfully'
            })
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        # Log full exception details for debugging
        import traceback
        logger.error(f"Error generating section draft: {error_type}: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Check if this is the decode error we're trying to fix
        if 'decoding to str' in error_msg or 'NoneType' in error_msg or 'bytes-like object' in error_msg:
            logger.error(f"LLM response decode error detected: {error_msg}")
            return jsonify({'error': 'LLM provider returned empty or invalid response. Please check Ollama is running and try again.'}), 500
        logger.error(f"Error generating section draft: {error_msg}")
        return jsonify({'error': error_msg}), 500

@bp.route('/api/llm/prompts/image-concepts', methods=['GET', 'PUT'])
def api_image_concepts_prompt():
    """Get or update the Image Concepts prompt
    
    Supports illustration_method query parameter:
    - 'Photo-harvesting' → 'Image Concepts Generation (Photo-harvesting)'
    - 'LLM-creation' or default → 'Image Concepts Generation'
    """
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                # Determine which prompt to update based on illustration_method
                illustration_method = request.args.get('illustration_method', 'LLM-creation')
                prompt_name = 'Image Concepts Generation (Photo-harvesting)' if illustration_method == 'Photo-harvesting' else 'Image Concepts Generation'
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = %s
                """, (system_prompt, prompt_text, prompt_name))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Prompt "{prompt_name}" updated successfully'
                })
            else:
                # Get the prompt - check illustration_method query parameter
                illustration_method = request.args.get('illustration_method', 'LLM-creation')
                prompt_name = 'Image Concepts Generation (Photo-harvesting)' if illustration_method == 'Photo-harvesting' else 'Image Concepts Generation'
                
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (prompt_name,))
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': f'Image Concepts prompt "{prompt_name}" not found'}), 404
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'prompt_text': prompt_data['prompt_text'],
                        'system_prompt': prompt_data['system_prompt'],
                        'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                    }
                })
                
    except Exception as e:
        logger.error(f"Error with image concepts prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/section-drafting-prompt-selection', methods=['GET'])
def api_get_section_drafting_prompt_selection(post_id):
    """Get available prompt options and current selection for section drafting"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get taxonomy for the post
            cursor.execute("""
                SELECT ti.display_name as content_type_name
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            taxonomy_result = cursor.fetchone()
            content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
            
            # Get available prompts
            available_prompts = []
            
            # Default prompt
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Section Drafting'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            default_prompt = cursor.fetchone()
            if default_prompt:
                available_prompts.append({
                    'name': default_prompt['name'],
                    'id': default_prompt['id'],
                    'is_default': True
                })
            
            # Category-specific prompt (if category exists)
            if content_type_name:
                cursor.execute("""
                    SELECT name, id FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (f'Section Drafting ({content_type_name})',))
                category_prompt = cursor.fetchone()
                if category_prompt:
                    available_prompts.append({
                        'name': category_prompt['name'],
                        'id': category_prompt['id'],
                        'is_default': False
                    })
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('section_drafting_prompt_name')
            
            # LEGACY POSTS: If no selection exists, explicitly set to default prompt
            if not current_selection and available_prompts:
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this explicit selection to the post for legacy posts
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['section_drafting_prompt_name'] = current_selection
                    
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection,
                'content_type_name': content_type_name
            })
    except Exception as e:
        logger.error(f"Error fetching section drafting prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/section-drafting-prompt-selection', methods=['POST'])
def api_set_section_drafting_prompt_selection(post_id):
    """Set the selected prompt for section drafting"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name') if data else None
        
        if not prompt_name:
            return jsonify({'error': 'prompt_name is required'}), 400
        
        # Verify prompt exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM llm_prompt WHERE name = %s
            """, (prompt_name,))
            if not cursor.fetchone():
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            # Save selection to post.extra_settings - PERSIST TO DATABASE
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['section_drafting_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting section drafting prompt selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/section-drafting-prompt', methods=['GET'])
def api_get_section_drafting_prompt(post_id):
    """Get the section drafting prompt for a post, optionally filtered by prompt_name query parameter"""
    try:
        # Get prompt_name from query parameter (passed from frontend)
        prompt_name = request.args.get('prompt_name')
        
        with db_manager.get_cursor() as cursor:
            # If prompt_name not provided, get from post.extra_settings
            if not prompt_name:
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('section_drafting_prompt_name')
                
                # LEGACY: If still no prompt_name, use default
                if not prompt_name:
                    prompt_name = 'Section Drafting'
            
            # Get the prompt by exact name - NO FALLBACKS
            cursor.execute("""
                SELECT name, system_prompt, prompt_text, parameters
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            # FAIL CLEARLY if prompt not found
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            # Extract parameters from JSONB if they exist
            parameters = prompt_data['parameters'] or {}
            model = parameters.get('model', 'llama3.2:latest')
            temperature = parameters.get('temperature', 0.7)
            max_tokens = parameters.get('max_tokens', 2000)
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': prompt_data['name'],
                    'system_prompt': prompt_data['system_prompt'],
                    'prompt_text': prompt_data['prompt_text'],
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            })
    except Exception as e:
        logger.error(f"Error fetching section drafting prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/section-drafting-prompt', methods=['PUT'])
def api_update_section_drafting_prompt(post_id):
    """Update the section drafting prompt for a post"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        prompt_text = data.get('prompt_text', '')
        
        if not system_prompt and not prompt_text:
            return jsonify({'error': 'system_prompt or prompt_text is required'}), 400
        
        # Get the prompt name from post settings
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            prompt_name = None
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                prompt_name = settings.get('section_drafting_prompt_name')
            
            # LEGACY: If no selection exists, use default
            if not prompt_name:
                prompt_name = 'Section Drafting'
            
            # Update the prompt in the database
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = COALESCE(%s, system_prompt),
                    prompt_text = COALESCE(%s, prompt_text),
                    updated_at = NOW()
                WHERE name = %s
                RETURNING name, system_prompt, prompt_text
            """, (system_prompt if system_prompt else None, 
                  prompt_text if prompt_text else None, 
                  prompt_name))
            
            updated_prompt = cursor.fetchone()
            cursor.connection.commit()
            
            if not updated_prompt:
                return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'name': updated_prompt['name'],
                    'system_prompt': updated_prompt['system_prompt'],
                    'prompt_text': updated_prompt['prompt_text']
                }
            })
    except Exception as e:
        logger.error(f"Error updating section drafting prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/section-drafting', methods=['GET', 'PUT'])
def api_section_drafting_prompt():
    """Legacy endpoint - redirects to post-specific endpoint"""
    # For backward compatibility, try to get post_id from query or use default
    post_id = request.args.get('post_id', type=int)
    if post_id:
        if request.method == 'PUT':
            return api_update_section_drafting_prompt(post_id)
        else:
            return api_get_section_drafting_prompt(post_id)
    else:
        # Fallback to old behavior for non-post-specific requests
        try:
            with db_manager.get_cursor() as cursor:
                if request.method == 'PUT':
                    # Update the prompt
                    data = request.get_json()
                    system_prompt = data.get('system_prompt', '')
                    prompt_text = data.get('prompt_text', '')
                    
                    cursor.execute("""
                        UPDATE llm_prompt 
                        SET system_prompt = %s, prompt_text = %s
                        WHERE name = 'Section Drafting'
                    """, (system_prompt, prompt_text))
                    
                    cursor.connection.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': 'Prompt updated successfully'
                    })
                else:
                    # Get the prompt
                    cursor.execute("""
                        SELECT name, prompt_text, system_prompt, updated_at
                        FROM llm_prompt 
                        WHERE name = 'Section Drafting'
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """)
                    prompt_data = cursor.fetchone()
                    
                    if not prompt_data:
                        return jsonify({'error': 'Section Drafting prompt not found'}), 404
                    
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'name': prompt_data['name'],
                            'prompt_text': prompt_data['prompt_text'],
                            'system_prompt': prompt_data['system_prompt'],
                            'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                        }
                    })
                    
        except Exception as e:
            logger.error(f"Error with section drafting prompt: {e}")
            return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-prompts', methods=['GET', 'PUT'])
def api_image_prompts_prompt():
    """
    Get or update Image Prompts prompt.
    
    Supports illustration_method query parameter:
    - 'Photo-harvesting' → 'Image Prompts Generation (Photo-harvesting)' (for image searching)
    - 'LLM-creation' or default → 'Image Prompts Generation' (for image generation)
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Determine which prompt to use based on illustration_method
            illustration_method = request.args.get('illustration_method', 'LLM-creation')
            prompt_name = 'Image Prompts Generation (Photo-harvesting)' if illustration_method == 'Photo-harvesting' else 'Image Prompts Generation'
            
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt_template = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                # Create complete system prompt by adding JSON format instruction
                system_prompt_complete = system_prompt_template
                if system_prompt_template and not system_prompt_template.endswith('JSON object'):
                    system_prompt_complete += '\n\nIMPORTANT: Respond ONLY with a JSON object in this exact format: {"image_prompt": "..."}. No commentary or meta text.'
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt_template = %s, system_prompt = %s, prompt_text = %s
                    WHERE name = %s
                """, (system_prompt_template, system_prompt_complete, prompt_text, prompt_name))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Prompt "{prompt_name}" updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, system_prompt_template, updated_at
                    FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (prompt_name,))
                prompt_data = cursor.fetchone()

                if not prompt_data:
                    return jsonify({'error': f'Image Prompts prompt "{prompt_name}" not found'}), 404
                
                # Use template version for LLM Prompts Panel display
                system_prompt_for_display = prompt_data['system_prompt_template'] or prompt_data['system_prompt']
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'prompt_text': prompt_data['prompt_text'],
                        'system_prompt': system_prompt_for_display,
                        'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                    }
                })
                
    except Exception as e:
        logger.error(f"Error with image prompts prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-captions', methods=['GET', 'PUT'])
def api_image_captions_prompt():
    """Get or update the Image Captions prompt
    
    Supports category-specific prompts via illustration_method query parameter.
    For process-level variance (Photo-harvesting): uses 'Image Captions Generation (Photo-harvesting)'
    For prompt-level variance: uses content_type_name if provided
    Default: 'Image Captions Generation'
    """
    try:
        # Get illustration_method from query params (for prompt selection)
        illustration_method = request.args.get('illustration_method', 'LLM-creation')
        
        # Get content_type_name if provided (for prompt-level variance)
        content_type_name = request.args.get('content_type_name')
        
        # Use utility function to get category-specific prompt name
        from utils.taxonomy_helpers import get_category_prompt_name
        prompt_name = get_category_prompt_name(
            'Image Captions Generation',
            illustration_method,
            content_type_name
        )
        
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = %s
                """, (system_prompt, prompt_text, prompt_name))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Prompt "{prompt_name}" updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (prompt_name,))
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({
                        'error': f'Image Captions prompt "{prompt_name}" not found. Please configure prompts in the LLM Prompts panel first.'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'prompt_text': prompt_data['prompt_text'],
                        'system_prompt': prompt_data['system_prompt'],
                        'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                    }
                })
                
    except Exception as e:
        logger.error(f"Error with image captions prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-generation', methods=['GET', 'PUT'])
def api_image_generation_prompt():
    """Get or update the Image Generation prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': 'Image Generation prompt not found'}), 404
                
                return jsonify({
                    'name': prompt_data['name'],
                    'prompt_text': prompt_data['prompt_text'],
                    'system_prompt': prompt_data['system_prompt'],
                    'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                })
                
    except Exception as e:
        logger.error(f"Error with image generation prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ui/preferences/<pref_key>', methods=['GET', 'POST'])
def authoring_ui_preferences(pref_key):
    """Handle UI preferences storage and retrieval"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'POST':
                # Save preference
                data = request.get_json()
                value = data.get('value')
                
                cursor.execute("""
                    INSERT INTO ui_user_preferences (preference_key, preference_value, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (preference_key) 
                    DO UPDATE SET preference_value = %s, updated_at = NOW()
                """, (pref_key, value, value))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Preference saved successfully'
                })
            else:
                # Get preference
                cursor.execute("""
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE preference_key = %s
                """, (pref_key,))
                result = cursor.fetchone()
                
                return jsonify({
                    'preference_key': pref_key,
                    'preference_value': result['preference_value'] if result else None
                })
                
    except Exception as e:
        logger.error(f"Error with UI preferences: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-imaging-model-selection', methods=['POST'])
def api_save_imaging_model_selection():
    """Save the selected imaging model for a post"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        model_selection = data.get('model_selection')
        
        if not post_id or not model_selection:
            return jsonify({'error': 'Missing post_id or model_selection'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update post_development table
            cursor.execute("""
                UPDATE post_development 
                SET imaging_model_selection = %s, updated_at = NOW()
                WHERE post_id = %s
            """, (model_selection, post_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Imaging model selection saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving imaging model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/imaging-model-selection', methods=['GET'])
def api_get_imaging_model_selection(post_id):
    """Get the selected imaging model for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT imaging_model_selection 
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            model_selection = result['imaging_model_selection'] if result else 'sdxl-lora'
            
            return jsonify({
                'model_selection': model_selection
            })
            
    except Exception as e:
        logger.error(f"Error getting imaging model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-system-prompt', methods=['POST'])
def api_save_system_prompt():
    """Save system prompt for LLM actions"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name')
        system_prompt = data.get('system_prompt')
        
        if not prompt_name or not system_prompt:
            return jsonify({'error': 'Missing prompt_name or system_prompt'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = %s, updated_at = NOW()
                WHERE name = %s
            """, (system_prompt, prompt_name))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'System prompt saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving system prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-style-guidelines', methods=['POST'])
def api_save_style_guidelines():
    """Save style guidelines for image generation"""
    try:
        data = request.get_json()
        prompt_name = data.get('prompt_name')
        style_guidelines = data.get('style_guidelines')
        
        if not prompt_name or not style_guidelines:
            return jsonify({'error': 'Missing prompt_name or style_guidelines'}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE llm_prompt 
                SET prompt_text = %s, updated_at = NOW()
                WHERE name = %s
            """, (style_guidelines, prompt_name))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Style guidelines saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving style guidelines: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/generate-image-prompt-from-stored-message', methods=['POST'])
def api_generate_image_prompt_from_stored_message():
    """Generate image prompt using stored message from intercept panel"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        stored_message = data.get('stored_message')
        
        if not all([post_id, section_id, stored_message]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        if not llm_service:
            return jsonify({'error': 'LLM service not available'}), 500
        
        # Parse the stored message to extract system and user messages
        messages = []
        
        if 'SYSTEM MESSAGE:' in stored_message and 'USER MESSAGE:' in stored_message:
            parts = stored_message.split('USER MESSAGE:')
            if len(parts) == 2:
                system_part = parts[0].replace('SYSTEM MESSAGE:', '').strip()
                user_part = parts[1].strip()
                
                if system_part:
                    messages.append({'role': 'system', 'content': system_part})
                messages.append({'role': 'user', 'content': user_part})
        else:
            # Fallback: treat entire message as user message
            messages.append({'role': 'user', 'content': stored_message})
        
        # Execute LLM request with intercept context
        intercept_context = {
            'post_id': post_id,
            'section_id': section_id
        }
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, intercept_context=intercept_context)
        
        if 'error' in result:
            return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
        
        # Parse the response
        try:
            response_data = json.loads(result['content'])
            if 'image_prompt' in response_data:
                return jsonify({
                    'success': True,
                    'image_prompt': response_data['image_prompt']
                })
            else:
                return jsonify({'error': 'Invalid response format from LLM'}), 500
        except json.JSONDecodeError:
            return jsonify({'error': 'LLM returned invalid JSON'}), 500
            
    except Exception as e:
        logger.error(f"Error generating image prompt from stored message: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/intercepted-message', methods=['GET'])
def api_get_intercepted_message(post_id, section_id):
    """Get the most recent intercepted LLM message for a post/section"""
    try:
        if not llm_service:
            return jsonify({'error': 'LLM service not available'}), 500
        
        intercepted_data = llm_service.get_intercepted_message(post_id, section_id)
        
        if intercepted_data:
            return jsonify({
                'success': True,
                'message': intercepted_data['message'],
                'raw_messages': intercepted_data['raw_messages'],
                'complete_api_request': intercepted_data['complete_api_request'],
                'raw_http_request': intercepted_data['raw_http_request'],
                'created_at': intercepted_data['created_at'].isoformat() if intercepted_data['created_at'] else None
            })
        else:
            return jsonify({
                'success': True,
                'message': None,
                'raw_messages': None,
                'complete_api_request': None,
                'raw_http_request': None,
                'created_at': None
            })
            
    except Exception as e:
        logger.error(f"Error getting intercepted message: {e}")
        return jsonify({'error': str(e)}), 500
