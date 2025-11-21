"""
Planning Profile API Module

Profile-specific API endpoints for product profile posts.
Completely isolated from themed post logic.
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_llm import LLMService
import logging
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMService()


def api_profile_section_structure():
    """
    Generate section structure for product profile posts.
    
    Completely isolated from themed post section structure generation.
    Generates 11-section structure with conditional optional sections.
    """
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        product_data = data.get('product_data')
        
        # Validate required parameters
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        if not product_data:
            return jsonify({
                'success': False,
                'error': 'Product data is required'
            }), 400
        
        # Validate post exists and is profile type
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.profile_product_id, p.profile_type
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({
                    'success': False,
                    'error': f'Post {post_id} not found'
                }), 404
            
            # Verify it's a profile post
            if not post.get('profile_product_id'):
                return jsonify({
                    'success': False,
                    'error': f'Post {post_id} is not a profile post (missing profile_product_id)'
                }), 400
            
            # Verify product_id matches
            if post.get('profile_product_id') != product_data.get('product_id'):
                return jsonify({
                    'success': False,
                    'error': f'Product ID mismatch: post has {post.get("profile_product_id")}, provided {product_data.get("product_id")}'
                }), 400
            
            post_title = post.get('title', 'Untitled Post')
            product_id = post.get('profile_product_id')
            product_name = product_data.get('name', 'Unknown Product')
        
        # Note: With the new 8-section structure:
        # - profile_heritage is optional (included if heritage data exists)
        # - profile_gallery is optional and provisional (always included but marked provisional)
        # - profile_materials_maker is always required (The Maker content within it is optional)
        # - profile_object_context is always required (combined section)
        
        # Heritage & Origins: Include if heritage_data exists OR category has heritage
        has_heritage = product_data.get('has_heritage_data', False)
        category_heritage = False
        if product_data.get('categories'):
            for category in product_data.get('categories', []):
                if category.get('heritage_data'):
                    category_heritage = True
                    break
        
        # Load prompt from database
        prompt_name = None
        try:
            with db_manager.get_cursor() as cursor:
                # Get selected prompt name from post settings
                cursor.execute("""
                    SELECT extra_settings FROM post WHERE id = %s
                """, (post_id,))
                post_result = cursor.fetchone()
                
                if post_result and post_result.get('extra_settings'):
                    settings = post_result['extra_settings']
                    prompt_name = settings.get('profile_section_structure_prompt_name')
                
                # Default to "Product Profile Section Structure" if no selection
                if not prompt_name:
                    prompt_name = 'Product Profile Section Structure'
                
                # Get the prompt
                cursor.execute("""
                    SELECT system_prompt, prompt_text
                    FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (prompt_name,))
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    logger.error(f'Prompt "{prompt_name}" not found for post {post_id}')
                    return jsonify({
                        'success': False,
                        'error': f'Prompt "{prompt_name}" not found. Please create this prompt in the database.'
                    }), 404
                
                system_prompt = prompt_data['system_prompt']
                prompt_text = prompt_data['prompt_text']
                
                # If prompt doesn't exist, use hardcoded fallback
                if not system_prompt or not prompt_text:
                    logger.warning(f'Prompt "{prompt_name}" missing content, using fallback')
                    system_prompt = """You are a blog structure specialist. Design an 8-section product profile blog post structure.

CRITICAL CONTEXT:
- You are generating a section structure for POST ID {post_id}
- POST TITLE: {post_title}
- PRODUCT: {product_name}
- PRODUCT ID: {product_id}

This structure is SPECIFICALLY for this post and product. Do not use any other context.

CONSTRAINTS:
- Create exactly 8 sections
- 6 required sections: Hero Block, The Object/In Context (combined), Features & Specifications, Materials & Making/The Maker (combined), Care & Maintenance, Explore Further
- 2 optional sections: Heritage & Origins (if heritage data available), Gallery (always provisional)
- Each section should have a clear purpose and flow
- Sections should build logically from introduction to conclusion
- Use the provided product data to inform section content

OUTPUT:
- STRICT JSON ONLY - NO MARKDOWN, NO CODE BLOCKS, NO EXPLANATORY TEXT
- Start your response with {{ and end with }}
- Exactly 8 sections with clear purposes
- Return ONLY the JSON object, nothing before or after
- Each section must include: section_code, section_type, title, description, optional (boolean), provisional (boolean), data_sources (array), conditional_logic (string or null)

FORMAT:
{{
  "sections": [
    {{ "section_code": "S01", "section_type": "profile_hero", "title": "Hero Block", "description": "...", "optional": false, "provisional": false, "data_sources": ["product_data.name"], "conditional_logic": null }},
    ...
  ]
}}

CRITICAL: Your response must be valid JSON that can be parsed directly. Do not wrap it in markdown code blocks or add any explanatory text."""
                    
                    prompt_text = """Design an 8-section product profile blog structure for this SPECIFIC post and product.

POST CONTEXT:
- Post ID: {post_id}
- Post Title: {post_title}
- Product: {product_name}
- Product ID: {product_id}

PRODUCT DATA:
{product_data_summary}

STANDARD PRODUCT PROFILE SECTIONS (8 total):
1. Hero Block (Required) - Visual introduction with headline and standfirst
2. The Object / In Context (Required, Combined) - Product concept, design, distinctive qualities, usage, occasions, styling, cultural fit
3. Features & Specifications (Required) - Features, options, technical details
4. Heritage & Origins (Optional) - Historical context if heritage data exists
5. Materials & Making / The Maker (Required, Combined) - Materials, processes, craftsmanship, and producer/workshop story. The Maker content is optional within this section.
6. Care & Maintenance (Required) - Care instructions, cleaning, storage
7. Gallery (Optional, Provisional) - Visual showcase (depends on image availability)
8. Explore Further (Required, Final) - Commerce links

VALIDATION RULES:
- Create exactly 8 sections
- Mark optional sections with "optional": true
- Mark Gallery as both "optional": true and "provisional": true
- Each section needs section_code, section_type, title, description, optional, provisional, data_sources, conditional_logic
- Output STRICT JSON ONLY - NO MARKDOWN CODE BLOCKS, NO EXPLANATORY TEXT
- Start response with {{ and end with }}
- Return ONLY the JSON object, nothing before or after

CRITICAL: Your response must be valid JSON that can be parsed directly. Do not wrap it in ```json code blocks or add any explanatory text."""
        
        except Exception as e:
            logger.error(f"Error loading prompt: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to load prompt: {str(e)}'
            }), 500
        
        # Format product data summary
        try:
            product_type_data = product_data.get('product_type_data', {}) or {}
            materials = product_type_data.get('materials', []) or []
            decorations = product_type_data.get('decorations', []) or []
            occasions = product_type_data.get('occasions', []) or []
            categories = product_data.get('categories', []) or []
            
            product_data_summary = f"""
PRODUCT NAME: {product_data.get('name', 'Unknown')}
PRODUCT ID: {product_id}
PRODUCT TYPE: {product_type_data.get('core_type', 'Unknown')}
MATERIALS: {', '.join(materials) if materials else 'Not specified'}
DECORATIONS: {', '.join(decorations) if decorations else 'None'}
OCCASIONS: {', '.join(occasions) if occasions else 'Not specified'}
SUPPLIER: {product_data.get('supplier_name', 'Unknown')}
HERITAGE DATA: {'Available' if has_heritage or category_heritage else 'Not available'}
CATEGORIES: {', '.join([c.get('name', '') for c in categories if c and isinstance(c, dict)]) if categories else 'Not specified'}
DESCRIPTION: {product_data.get('description', 'No description available')[:500]}
"""
        except Exception as e:
            logger.error(f"Error formatting product data: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Error formatting product data: {str(e)}'
            }), 500
        
        # Format prompts with explicit post/product identification
        formatted_system_prompt = system_prompt.format(
            post_id=post_id,
            post_title=post_title,
            product_name=product_name,
            product_id=product_id
        )
        
        formatted_prompt_text = prompt_text.format(
            post_id=post_id,
            post_title=post_title,
            product_name=product_name,
            product_id=product_id,
            product_data_summary=product_data_summary
        )
        
        # Call LLM service
        try:
            messages = [
                {'role': 'system', 'content': formatted_system_prompt},
                {'role': 'user', 'content': formatted_prompt_text}
            ]
            
            logger.info(f"Generating section structure for post {post_id}, product {product_id} ({product_name})")
            
            response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=4000)
            
            # Check for errors
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
            
            # Parse JSON response
            try:
                content = response['content'].strip()
                
                # Extract JSON from markdown code blocks or plain text
                json_text = None
                json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
                if json_match and json_match.groups():
                    json_text = json_match.group(1)
                else:
                    json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', content)
                    if json_match and json_match.groups():
                        json_text = json_match.group(1)
                
                if not json_text:
                    json_match = re.search(r'(\{[\s\S]*\})', content)
                    if json_match and json_match.groups():
                        json_text = json_match.group(1)
                    else:
                        json_match = re.search(r'(\[[\s\S]*\])', content)
                        if json_match and json_match.groups():
                            json_text = json_match.group(1)
                
                if json_text:
                    result = json.loads(json_text)
                else:
                    result = json.loads(content)
                
                # Handle both array and object formats
                if isinstance(result, list):
                    sections = result
                elif 'sections' in result:
                    sections = result['sections']
                else:
                    raise ValueError("Response must be a JSON array or contain 'sections' key")
                
                if not isinstance(sections, list):
                    raise ValueError("'sections' must be a list")
                
                # Validate section count (should be 8)
                if len(sections) != 8:
                    logger.warning(f"Expected 8 sections, got {len(sections)}. Proceeding with validation.")
                
                # Define valid section types (6 required + 2 optional = 8 total)
                required_types = ['profile_hero', 'profile_object_context', 'profile_features', 
                               'profile_materials_maker', 'profile_care', 'profile_explore']
                optional_types = ['profile_heritage', 'profile_gallery']
                all_valid_types = required_types + optional_types
                
                found_types = [s.get('section_type') for s in sections if isinstance(s, dict)]
                missing_required = [t for t in required_types if t not in found_types]
                invalid_types = [t for t in found_types if t not in all_valid_types]
                
                if missing_required:
                    # Log what was actually generated for debugging
                    logger.error(f"Missing required sections for post {post_id}, product {product_id}")
                    logger.error(f"Required types: {required_types}")
                    logger.error(f"Found types: {found_types}")
                    logger.error(f"Missing: {missing_required}")
                    logger.error(f"Generated sections (first 500 chars): {json.dumps(sections, indent=2)[:500]}")
                    raise ValueError(f"Missing required sections: {', '.join(missing_required)}. Found: {', '.join(found_types) if found_types else 'none'}")
                
                if invalid_types:
                    logger.warning(f"Invalid section types found: {invalid_types}. Valid types are: {all_valid_types}")
                
                # Validate and normalize sections
                normalized_sections = []
                for i, section in enumerate(sections):
                    if not isinstance(section, dict):
                        raise ValueError(f"Section {i} must be a dictionary")
                    
                    # Normalize section structure
                    normalized = {
                        'section_code': section.get('section_code') or f"S{str(i+1).zfill(2)}",
                        'section_type': section.get('section_type'),
                        'title': section.get('title') or 'Untitled Section',
                        'description': section.get('description') or '',
                        'optional': section.get('optional', False),
                        'provisional': section.get('provisional', False),
                        'data_sources': section.get('data_sources', []),
                        'conditional_logic': section.get('conditional_logic')
                    }
                    
                    # Set optional/provisional flags based on section type
                    if normalized['section_type'] in ['profile_heritage', 'profile_gallery']:
                        normalized['optional'] = True
                    if normalized['section_type'] == 'profile_gallery':
                        normalized['provisional'] = True
                    
                    # Ensure required sections are not marked as optional
                    if normalized['section_type'] in required_types:
                        normalized['optional'] = False
                        normalized['provisional'] = False
                    
                    normalized_sections.append(normalized)
                
                # Save to database with explicit post/product identification
                structure_data = {
                    'sections': normalized_sections,
                    'generated_at': datetime.now().isoformat(),
                    'post_id': post_id,
                    'product_id': product_id,
                    'product_name': product_name,
                    'post_title': post_title
                }
                
                with db_manager.get_cursor() as cursor:
                    # Check if post_development row exists
                    cursor.execute("""
                        SELECT id FROM post_development WHERE post_id = %s
                    """, (post_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        cursor.execute("""
                            UPDATE post_development 
                            SET section_structure = %s::jsonb, structure_design_at = %s, updated_at = %s
                            WHERE post_id = %s
                        """, (json.dumps(structure_data), datetime.now(), datetime.now(), post_id))
                    else:
                        cursor.execute("""
                            INSERT INTO post_development (post_id, section_structure, structure_design_at, updated_at)
                            VALUES (%s, %s::jsonb, %s, %s)
                        """, (post_id, json.dumps(structure_data), datetime.now(), datetime.now()))
                    
                    cursor.connection.commit()
                
                logger.info(f"Section structure saved for post {post_id}, product {product_id}")
                
                return jsonify({
                    'success': True,
                    'section_structure': structure_data,
                    'raw_response': response['content']
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response content (first 500 chars): {content[:500] if 'content' in locals() else 'N/A'}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON response from LLM: {str(e)}. Response preview: {content[:200] if "content" in locals() else "N/A"}...'
                }), 500
                
            except ValueError as e:
                logger.error(f"Invalid response structure: {e}")
                logger.error(f"Response content: {response.get('content', '')[:500]}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid response structure: {str(e)}'
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
        logger.error(f"Error in api_profile_section_structure: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def api_get_profile_section_structure_prompt_selection(post_id):
    """Get available prompt options and current selection for profile section structure"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get available prompts
            available_prompts = []
            
            # Default prompt
            cursor.execute("""
                SELECT name, id FROM llm_prompt 
                WHERE name = 'Product Profile Section Structure'
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
            
            # Get current selection (from post settings)
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            current_selection = None
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                current_selection = settings.get('profile_section_structure_prompt_name')
            
            # If no selection exists, set to default
            if not current_selection and available_prompts:
                default_prompt_obj = next((p for p in available_prompts if p.get('is_default')), None)
                if default_prompt_obj:
                    current_selection = default_prompt_obj['name']
                    # Save this selection to the post
                    if post_result and post_result.get('extra_settings'):
                        settings = post_result['extra_settings']
                    else:
                        settings = {}
                    settings['profile_section_structure_prompt_name'] = current_selection
                    
                    cursor.execute("""
                        UPDATE post 
                        SET extra_settings = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(settings), post_id))
                    cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'available_prompts': available_prompts,
                'current_selection': current_selection
            })
    except Exception as e:
        logger.error(f"Error fetching profile section structure prompt selection: {e}")
        return jsonify({'error': str(e)}), 500


def api_set_profile_section_structure_prompt_selection(post_id):
    """Set the selected prompt for profile section structure design"""
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
            
            # Get current settings
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
            else:
                settings = {}
            
            settings['profile_section_structure_prompt_name'] = prompt_name
            
            cursor.execute("""
                UPDATE post 
                SET extra_settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), post_id))
            cursor.connection.commit()
            
            return jsonify({'success': True, 'prompt_name': prompt_name})
    except Exception as e:
        logger.error(f"Error setting profile section structure prompt selection: {e}")
        return jsonify({'error': str(e)}), 500


def api_get_profile_section_structure_prompt(post_id):
    """Get the profile section structure prompt for a post"""
    try:
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
                    prompt_name = settings.get('profile_section_structure_prompt_name')
                
                # Default if still no prompt_name
                if not prompt_name:
                    prompt_name = 'Product Profile Section Structure'
            
            # Get the prompt
            cursor.execute("""
                SELECT id, name, description, prompt_text, system_prompt, created_at, updated_at
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (prompt_name,))
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
                }), 404
            
            return jsonify({
                'success': True,
                'prompt': {
                    'id': prompt_data['id'],
                    'name': prompt_data['name'],
                    'description': prompt_data.get('description'),
                    'prompt_text': prompt_data['prompt_text'],
                    'system_prompt': prompt_data['system_prompt'],
                    'created_at': prompt_data['created_at'].isoformat() if prompt_data['created_at'] else None,
                    'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                }
            })
    except Exception as e:
        logger.error(f"Error fetching profile section structure prompt: {e}")
        return jsonify({'error': str(e)}), 500


def api_update_profile_section_structure_prompt(post_id):
    """Update the profile section structure prompt for a post"""
    try:
        data = request.get_json()
        prompt_text = data.get('prompt_text')
        system_prompt = data.get('system_prompt')
        
        if not prompt_text and not system_prompt:
            return jsonify({'error': 'prompt_text or system_prompt is required'}), 400
        
        # Get current prompt selection
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT extra_settings FROM post WHERE id = %s
            """, (post_id,))
            post_result = cursor.fetchone()
            
            prompt_name = None
            if post_result and post_result.get('extra_settings'):
                settings = post_result['extra_settings']
                prompt_name = settings.get('profile_section_structure_prompt_name')
            
            if not prompt_name:
                prompt_name = 'Product Profile Section Structure'
            
            # Update the prompt
            update_fields = []
            update_values = []
            
            if prompt_text is not None:
                update_fields.append('prompt_text = %s')
                update_values.append(prompt_text)
            
            if system_prompt is not None:
                update_fields.append('system_prompt = %s')
                update_values.append(system_prompt)
            
            if update_fields:
                update_values.append(prompt_name)
                cursor.execute(f"""
                    UPDATE llm_prompt 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE name = %s
                """, tuple(update_values))
                cursor.connection.commit()
            
            return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating profile section structure prompt: {e}")
        return jsonify({'error': str(e)}), 500

