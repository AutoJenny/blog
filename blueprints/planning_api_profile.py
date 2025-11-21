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
8. Explore Further (Required, Final Section) - Commerce links

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


def api_profile_topic_allocation():
    """
    Populate sections with raw data from product sources for profile posts.
    
    Instead of generating topics, extracts and maps raw data chunks to each section
    based on section_type and data_sources.
    """
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID is required'
            }), 400
        
        # Get post and verify it's a profile post
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.profile_product_id, pd.section_structure
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({
                    'success': False,
                    'error': f'Post {post_id} not found'
                }), 404
            
            if not post.get('profile_product_id'):
                return jsonify({
                    'success': False,
                    'error': f'Post {post_id} is not a profile post'
                }), 400
            
            product_id = post.get('profile_product_id')
            section_structure = post.get('section_structure')
        
        # Parse section structure
        if not section_structure:
            return jsonify({
                'success': False,
                'error': 'No section structure found. Please design section structure first.'
            }), 400
        
        try:
            if isinstance(section_structure, str):
                section_structure = json.loads(section_structure)
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'error': 'Invalid section structure format'
            }), 400
        
        # Get sections from structure
        if isinstance(section_structure, dict):
            sections = section_structure.get('sections', [])
        elif isinstance(section_structure, list):
            sections = section_structure
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid section structure format'
            }), 400
        
        if not sections:
            return jsonify({
                'success': False,
                'error': 'No sections found in structure'
            }), 400
        
        # Fetch full product data
        try:
            from utils.content_generation.clan_data_extractor import ClanDataExtractor
            extractor = ClanDataExtractor()
            product_data = extractor.extract_product_data(product_id)
        except Exception as e:
            logger.error(f"Error fetching product data: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to fetch product data: {str(e)}'
            }), 500
        
        # Extract raw data for each section
        allocations = []
        
        for section in sections:
            section_type = section.get('section_type')
            section_code = section.get('section_code', '')
            section_title = section.get('title', 'Untitled Section')
            data_sources = section.get('data_sources', [])
            
            # Extract raw data chunks based on section type and data sources
            raw_data_chunks = extract_raw_data_for_section(
                section_type, data_sources, product_data
            )
            
            # Format as "topics" (data chunks) for compatibility with existing frontend
            formatted_chunks = []
            for i, chunk in enumerate(raw_data_chunks):
                formatted_chunks.append({
                    'idea_code': f"{{{section_code}{str(i+1).zfill(2)}}}",
                    'topic_title': chunk.get('title', f'Data Chunk {i+1}'),
                    'section_code': f"{{{section_code}}}",
                    'description': chunk.get('content', ''),
                    'category': chunk.get('category', 'data'),
                    'source': chunk.get('source', 'unknown'),
                    'raw_data': chunk.get('raw_data', {})
                })
            
            allocations.append({
                'section_id': f"section_{section_code.replace('S', '')}",
                'section_code': section_code,
                'section_theme': section_title,
                'section_type': section_type,
                'topics': [chunk.get('topic_title', '') for chunk in formatted_chunks],
                'data_chunks': formatted_chunks
            })
        
        # Save to database
        allocation_data = {
            'allocations': allocations,
            'metadata': {
                'total_chunks': sum(len(a.get('data_chunks', [])) for a in allocations),
                'sections_count': len(allocations),
                'generated_at': datetime.now().isoformat(),
                'method': 'raw_data_extraction',
                'post_id': post_id,
                'product_id': product_id
            }
        }
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET topic_allocation = %s::jsonb, allocation_completed_at = %s, updated_at = %s
                WHERE post_id = %s
            """, (json.dumps(allocation_data), datetime.now(), datetime.now(), post_id))
            
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO post_development (post_id, topic_allocation, allocation_completed_at, updated_at)
                    VALUES (%s, %s::jsonb, %s, %s)
                """, (post_id, json.dumps(allocation_data), datetime.now(), datetime.now()))
            
            cursor.connection.commit()
        
        logger.info(f"Topic allocation (raw data) saved for post {post_id}, product {product_id}")
        
        return jsonify({
            'success': True,
            'message': f'Raw data extracted and allocated to {len(allocations)} sections',
            'allocations': allocation_data,
            'results': allocation_data
        })
        
    except Exception as e:
        logger.error(f"Error in api_profile_topic_allocation: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def extract_raw_data_for_section(section_type, data_sources, product_data):
    """
    Extract raw data chunks for a specific section based on section_type and data_sources.
    
    Returns a list of data chunks, each with:
    - title: Short title for the chunk
    - content: The actual data content
    - category: Type of data (description, specification, heritage, etc.)
    - source: Where the data came from (product_data, supplier_data, etc.)
    - raw_data: The original raw data object
    """
    chunks = []
    
    # Map section types to data extraction functions
    extraction_map = {
        'profile_hero': extract_hero_data,
        'profile_object_context': extract_object_context_data,
        'profile_features': extract_features_data,
        'profile_heritage': extract_heritage_data,
        'profile_materials_maker': extract_materials_maker_data,
        'profile_care': extract_care_data,
        'profile_gallery': extract_gallery_data,
        'profile_explore': extract_explore_data
    }
    
    extractor_func = extraction_map.get(section_type)
    if extractor_func:
        chunks = extractor_func(product_data, data_sources)
    else:
        logger.warning(f"Unknown section type: {section_type}, using generic extraction")
        chunks = extract_generic_data(product_data, data_sources)
    
    return chunks


def extract_hero_data(product_data, data_sources):
    """Extract data for Hero Block section"""
    chunks = []
    
    # Product name
    if product_data.get('name'):
        chunks.append({
            'title': 'Product Name',
            'content': product_data['name'],
            'category': 'name',
            'source': 'product_data.name',
            'raw_data': {'name': product_data['name']}
        })
    
    # Short description
    if product_data.get('short_description'):
        chunks.append({
            'title': 'Short Description',
            'content': product_data['short_description'],
            'category': 'description',
            'source': 'product_data.short_description',
            'raw_data': {'short_description': product_data['short_description']}
        })
    
    # Image URL
    if product_data.get('image_url'):
        chunks.append({
            'title': 'Hero Image',
            'content': product_data['image_url'],
            'category': 'image',
            'source': 'product_data.image_url',
            'raw_data': {'image_url': product_data['image_url']}
        })
    
    # Product type for headline context
    product_type_data = product_data.get('product_type_data', {})
    if product_type_data.get('core_type'):
        chunks.append({
            'title': 'Product Type',
            'content': product_type_data['core_type'],
            'category': 'classification',
            'source': 'product_data.product_type_data.core_type',
            'raw_data': {'core_type': product_type_data['core_type']}
        })
    
    return chunks


def extract_object_context_data(product_data, data_sources):
    """Extract data for The Object / In Context combined section"""
    chunks = []
    
    # Main description
    if product_data.get('description'):
        chunks.append({
            'title': 'Product Description',
            'content': product_data['description'],
            'category': 'description',
            'source': 'product_data.description',
            'raw_data': {'description': product_data['description']}
        })
    
    # Product type data
    product_type_data = product_data.get('product_type_data', {})
    
    # Occasions (In Context)
    if product_type_data.get('occasions'):
        chunks.append({
            'title': 'Gift Occasions',
            'content': ', '.join(product_type_data['occasions']),
            'category': 'context',
            'source': 'product_data.product_type_data.occasions',
            'raw_data': {'occasions': product_type_data['occasions']}
        })
    
    # Decorations/motifs (The Object)
    if product_type_data.get('decorations'):
        chunks.append({
            'title': 'Decorations & Motifs',
            'content': ', '.join(product_type_data['decorations']),
            'category': 'design',
            'source': 'product_data.product_type_data.decorations',
            'raw_data': {'decorations': product_type_data['decorations']}
        })
    
    # Specifications for object details
    if product_data.get('specifications'):
        chunks.append({
            'title': 'Specifications',
            'content': json.dumps(product_data['specifications'], indent=2) if isinstance(product_data['specifications'], dict) else str(product_data['specifications']),
            'category': 'specification',
            'source': 'product_data.specifications',
            'raw_data': {'specifications': product_data['specifications']}
        })
    
    # Dimensions
    if product_data.get('dimensions'):
        chunks.append({
            'title': 'Dimensions',
            'content': json.dumps(product_data['dimensions'], indent=2) if isinstance(product_data['dimensions'], dict) else str(product_data['dimensions']),
            'category': 'specification',
            'source': 'product_data.dimensions',
            'raw_data': {'dimensions': product_data['dimensions']}
        })
    
    return chunks


def extract_features_data(product_data, data_sources):
    """Extract data for Features & Specifications section"""
    chunks = []
    
    # Specifications
    if product_data.get('specifications'):
        chunks.append({
            'title': 'Technical Specifications',
            'content': json.dumps(product_data['specifications'], indent=2) if isinstance(product_data['specifications'], dict) else str(product_data['specifications']),
            'category': 'specification',
            'source': 'product_data.specifications',
            'raw_data': {'specifications': product_data['specifications']}
        })
    
    # Configurable options
    if product_data.get('configurable_options'):
        chunks.append({
            'title': 'Configurable Options',
            'content': json.dumps(product_data['configurable_options'], indent=2) if isinstance(product_data['configurable_options'], dict) else str(product_data['configurable_options']),
            'category': 'options',
            'source': 'product_data.configurable_options',
            'raw_data': {'configurable_options': product_data['configurable_options']}
        })
    
    # Dimensions
    if product_data.get('dimensions'):
        chunks.append({
            'title': 'Dimensions',
            'content': json.dumps(product_data['dimensions'], indent=2) if isinstance(product_data['dimensions'], dict) else str(product_data['dimensions']),
            'category': 'specification',
            'source': 'product_data.dimensions',
            'raw_data': {'dimensions': product_data['dimensions']}
        })
    
    return chunks


def extract_heritage_data(product_data, data_sources):
    """Extract data for Heritage & Origins section"""
    chunks = []
    
    # Product heritage data
    if product_data.get('heritage_data'):
        heritage = product_data['heritage_data']
        if isinstance(heritage, dict):
            for key, value in heritage.items():
                if value:
                    chunks.append({
                        'title': f'Heritage: {key.replace("_", " ").title()}',
                        'content': json.dumps(value, indent=2) if isinstance(value, (dict, list)) else str(value),
                        'category': 'heritage',
                        'source': f'product_data.heritage_data.{key}',
                        'raw_data': {key: value}
                    })
        else:
            chunks.append({
                'title': 'Heritage Data',
                'content': str(heritage),
                'category': 'heritage',
                'source': 'product_data.heritage_data',
                'raw_data': {'heritage_data': heritage}
            })
    
    # Category heritage data
    categories = product_data.get('categories', [])
    for category in categories:
        if category and isinstance(category, dict) and category.get('heritage_data'):
            chunks.append({
                'title': f'Category Heritage: {category.get("name", "Unknown")}',
                'content': json.dumps(category['heritage_data'], indent=2) if isinstance(category['heritage_data'], (dict, list)) else str(category['heritage_data']),
                'category': 'heritage',
                'source': f'category.heritage_data',
                'raw_data': {'category_name': category.get('name'), 'heritage_data': category['heritage_data']}
            })
    
    return chunks


def extract_materials_maker_data(product_data, data_sources):
    """Extract data for Materials & Making / The Maker combined section"""
    chunks = []
    
    # Materials
    product_type_data = product_data.get('product_type_data', {})
    if product_type_data.get('materials'):
        chunks.append({
            'title': 'Materials',
            'content': ', '.join(product_type_data['materials']),
            'category': 'materials',
            'source': 'product_data.product_type_data.materials',
            'raw_data': {'materials': product_type_data['materials']}
        })
    
    # Supplier/Maker information
    if product_data.get('supplier_name'):
        chunks.append({
            'title': 'Supplier/Maker Name',
            'content': product_data['supplier_name'],
            'category': 'maker',
            'source': 'product_data.supplier_name',
            'raw_data': {'supplier_name': product_data['supplier_name']}
        })
    
    if product_data.get('supplier_description'):
        chunks.append({
            'title': 'Supplier/Maker Description',
            'content': product_data['supplier_description'],
            'category': 'maker',
            'source': 'product_data.supplier_description',
            'raw_data': {'supplier_description': product_data['supplier_description']}
        })
    
    # Producer data
    if product_data.get('producer_data'):
        chunks.append({
            'title': 'Producer Data',
            'content': json.dumps(product_data['producer_data'], indent=2) if isinstance(product_data['producer_data'], dict) else str(product_data['producer_data']),
            'category': 'maker',
            'source': 'product_data.producer_data',
            'raw_data': {'producer_data': product_data['producer_data']}
        })
    
    return chunks


def extract_care_data(product_data, data_sources):
    """Extract data for Care & Maintenance section"""
    chunks = []
    
    # Product type data may contain care information
    product_type_data = product_data.get('product_type_data', {})
    if product_type_data:
        chunks.append({
            'title': 'Product Type Data',
            'content': json.dumps(product_type_data, indent=2),
            'category': 'care',
            'source': 'product_data.product_type_data',
            'raw_data': {'product_type_data': product_type_data}
        })
    
    # Additional data may contain care instructions
    if product_data.get('additional_data'):
        chunks.append({
            'title': 'Additional Data',
            'content': json.dumps(product_data['additional_data'], indent=2) if isinstance(product_data['additional_data'], dict) else str(product_data['additional_data']),
            'category': 'care',
            'source': 'product_data.additional_data',
            'raw_data': {'additional_data': product_data['additional_data']}
        })
    
    return chunks


def extract_gallery_data(product_data, data_sources):
    """Extract data for Gallery section"""
    chunks = []
    
    # Main image
    if product_data.get('image_url'):
        chunks.append({
            'title': 'Main Product Image',
            'content': product_data['image_url'],
            'category': 'image',
            'source': 'product_data.image_url',
            'raw_data': {'image_url': product_data['image_url']}
        })
    
    # Additional images if available
    if product_data.get('additional_images'):
        for i, img_url in enumerate(product_data.get('additional_images', [])):
            chunks.append({
                'title': f'Additional Image {i+1}',
                'content': img_url,
                'category': 'image',
                'source': 'product_data.additional_images',
                'raw_data': {'image_index': i, 'image_url': img_url}
            })
    
    return chunks


def extract_explore_data(product_data, data_sources):
    """Extract data for Explore Further section"""
    chunks = []
    
    # Product URL
    if product_data.get('url'):
        chunks.append({
            'title': 'Product URL',
            'content': product_data['url'],
            'category': 'link',
            'source': 'product_data.url',
            'raw_data': {'url': product_data['url']}
        })
    
    # Categories for navigation
    categories = product_data.get('categories', [])
    if categories:
        category_names = [c.get('name', '') for c in categories if c and isinstance(c, dict)]
        chunks.append({
            'title': 'Related Categories',
            'content': ', '.join(category_names),
            'category': 'navigation',
            'source': 'product_data.categories',
            'raw_data': {'categories': categories}
        })
    
    return chunks


def extract_generic_data(product_data, data_sources):
    """Generic extraction for unknown section types"""
    chunks = []
    
    # Try to extract based on data_sources
    for source in data_sources:
        if '.' in source:
            parts = source.split('.')
            value = product_data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            if value:
                chunks.append({
                    'title': source.replace('_', ' ').title(),
                    'content': json.dumps(value, indent=2) if isinstance(value, (dict, list)) else str(value),
                    'category': 'generic',
                    'source': source,
                    'raw_data': {source: value}
                })
    
    return chunks


# ... (keep all the existing prompt selection functions) ...

def api_get_profile_section_structure_prompt_selection(post_id):
    """Get available prompt options and current selection for profile section structure design"""
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
