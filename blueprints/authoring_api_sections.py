"""
Authoring API Sections Module

Micro-file for authoring section-related API endpoints
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('authoring_sections', __name__, url_prefix='/authoring')

@bp.route('/api/posts/<int:post_id>/sections', methods=['GET'])
def api_get_sections(post_id):
    """Get all sections for a post from post_section table, with fallback to post_development.sections"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if this is a recipe post and auto-create sections if missing
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            if post_type == 'recipe':
                cursor.execute("""
                    SELECT COUNT(*) as section_count
                    FROM post_section
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                section_count = result.get('section_count', 0) if isinstance(result, dict) else (result[0] if result else 0)
                
                if section_count == 0:
                    # Auto-create default recipe sections with detailed descriptions
                    recipe_sections = [
                        ('recipe_background', 'Background', 'The historic and cultural background of this recipe. Write 2-3 paragraphs (150-200 words) covering the origin story, regional associations, and occasions when traditionally eaten. Use a warm, storytelling voice that evokes place, people, and time.'),
                        ('recipe_ingredients', 'Ingredients', 'List of ingredients needed for this recipe. Format clearly for home cooks, with amounts and any preparation notes. May include regional variations or historical notes.'),
                        ('recipe_method', 'Method', 'Step-by-step cooking instructions. Use numbered steps with clear instructions. Aimed at home cooks, not professional chefs.'),
                        ('recipe_variants', 'Variations', 'Optional twists and regional variations (e.g., "Hebridean version uses smoked haddock only", "Modern twist: add whisky cream"). Not every recipe needs variants - this section is optional.'),
                        ('recipe_serving', 'Serving Suggestions', 'How Scots traditionally serve this dish. Include drinks, sides, or traditional accompaniments. Optional mention of related products available on clan.com.'),
                        ('recipe_further_reading', 'Further Reading', 'Search for 2-5 authoritative sources for background information about this recipe. Focus on: cultural/heritage sites, Wikipedia articles, historical sources, ingredient provenance sites, and tourism/heritage organizations. AVOID competing recipe sites or cooking blogs. For each source, provide: Title & Link, Why It\'s Good (brief explanation of the source\'s value), and Use Case in Your Content (how to reference this source in the recipe sections above). Sources should support the Background, Ingredients, Variations, and Serving Suggestions sections.')
                    ]
                    
                    for section_order, (section_type, section_heading, section_description) in enumerate(recipe_sections, start=1):
                        # Check if section already exists at this order
                        cursor.execute("""
                            SELECT id FROM post_section
                            WHERE post_id = %s AND section_order = %s
                            LIMIT 1
                        """, (post_id, section_order))
                        existing = cursor.fetchone()
                        
                        if not existing:
                            # Insert new section
                            cursor.execute("""
                                INSERT INTO post_section (
                                    post_id, section_order, section_type, section_heading, 
                                    section_description, status
                                )
                                VALUES (%s, %s, %s, %s, %s, 'draft')
                            """, (post_id, section_order, section_type, section_heading, section_description))
                        else:
                            # Update existing section with section_type if missing
                            cursor.execute("""
                                UPDATE post_section
                                SET section_type = %s,
                                    section_heading = COALESCE(NULLIF(section_heading, ''), %s),
                                    section_description = COALESCE(NULLIF(section_description, ''), %s)
                                WHERE post_id = %s AND section_order = %s
                                  AND (section_type IS NULL OR section_type = '')
                            """, (section_type, section_heading, section_description, post_id, section_order))
                    
                    cursor.connection.commit()
                    logger.info(f"Auto-created {len(recipe_sections)} recipe sections for post {post_id}")
            
            # Get sections from post_section table first
            # For recipe posts in image generation or image captions context, only show sections that have images
            # (ingredients and method sections)
            if post_type == 'recipe':
                # Check if we're in image generation or image captions context
                # Check query parameter first, then request path, then referrer
                from flask import request
                is_image_context = False
                
                # Check query parameter
                if request and request.args.get('image_context') == 'true':
                    is_image_context = True
                # Check request path
                elif request and (
                    '/image-generation' in request.path or 
                    '/imaging' in request.path or
                    '/image_captions' in request.path
                ):
                    is_image_context = True
                # Check referrer
                elif request and request.referrer and (
                    '/image-generation' in request.referrer or 
                    '/imaging' in request.referrer or
                    '/image_captions' in request.referrer
                ):
                    is_image_context = True
                
                if is_image_context:
                    # Show ingredients section AND recipe_image_style section for recipe image generation/captions
                    # (recipe_image_style contains hero image prompt needed for generation)
                    cursor.execute("""
                        SELECT id, section_order, section_heading, section_description, 
                               status, draft, polished, ideas_to_include, facts_to_include,
                               highlighting, image_concepts, image_prompts, image_captions,
                               image_alt_text, selected_image_concept, section_type,
                               post_section_elements
                        FROM post_section
                        WHERE post_id = %s 
                          AND (section_type = 'recipe_ingredients' OR section_type = 'recipe_image_style')
                        ORDER BY section_order
                    """, (post_id,))
                else:
                    # Show all sections for other contexts
                    cursor.execute("""
                        SELECT id, section_order, section_heading, section_description, 
                               status, draft, polished, ideas_to_include, facts_to_include,
                               highlighting, image_concepts, image_prompts, image_captions,
                               image_alt_text, selected_image_concept, section_type,
                               post_section_elements
                        FROM post_section
                        WHERE post_id = %s
                        ORDER BY section_order
                    """, (post_id,))
            else:
                # For non-recipe posts, show all sections
                cursor.execute("""
                    SELECT id, section_order, section_heading, section_description, 
                           status, draft, polished, ideas_to_include, facts_to_include,
                           highlighting, image_concepts, image_prompts, image_captions,
                           image_alt_text, selected_image_concept, section_type,
                           post_section_elements
                    FROM post_section
                    WHERE post_id = %s
                    ORDER BY section_order
                """, (post_id,))
            sections = cursor.fetchall()
            
            # If no sections found in post_section table, check post_development.sections
            if not sections:
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if result and result.get('sections'):
                    try:
                        sections_data = json.loads(result['sections'])
                        if isinstance(sections_data, dict) and 'sections' in sections_data:
                            sections_list = sections_data['sections']
                        elif isinstance(sections_data, list):
                            sections_list = sections_data
                        else:
                            sections_list = []
                        
                        # Convert JSON sections to post_section-like format
                        formatted_sections = []
                        for i, section in enumerate(sections_list):
                            formatted_sections.append({
                                'id': section.get('id', i + 1),
                                'section_order': section.get('order', section.get('index', i + 1)),
                                'section_heading': section.get('title', f'Section {i + 1}'),
                                'section_description': section.get('subtitle', ''),
                                'title': section.get('title', f'Section {i + 1}'),
                                'description': section.get('subtitle', ''),
                                'order': section.get('order', section.get('index', i + 1)),
                                'status': 'draft',
                                'draft': None,
                                'polished': None,
                                'ideas_to_include': None,
                                'facts_to_include': None,
                                'highlighting': None,
                                'image_concepts': section.get('image_concepts'),  # Get from JSON, not None
                                'image_prompts': section.get('image_prompts'),
                                'image_captions': section.get('image_captions'),
                                'image_alt_text': None,
                                'selected_image_concept': section.get('selected_image_concept'),
                                'topics': section.get('topics', [])
                            })
                        sections = formatted_sections
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")
                        sections = []
            
            # Convert to frontend-compatible format
            formatted_sections = []
            for section in sections:
                # Check if already formatted (has 'title' key) or from database (has 'section_heading' key)
                if 'title' in section or 'order' in section:
                    # Already formatted (from post_development fallback)
                    formatted_sections.append(section)
                else:
                    # From post_section table - format it
                    # But also check post_development.sections for image fields that might not be in post_section
                    section_id_from_db = section['id']
                    image_concepts_from_json = None
                    selected_concept_from_json = None
                    
                    # Try to get image_concepts from post_development.sections if not in post_section
                    if not section.get('image_concepts'):
                        cursor.execute("""
                            SELECT sections FROM post_development WHERE post_id = %s
                        """, (post_id,))
                        dev_result = cursor.fetchone()
                        if dev_result and dev_result.get('sections'):
                            try:
                                dev_sections_data = json.loads(dev_result['sections'])
                                if isinstance(dev_sections_data, dict) and 'sections' in dev_sections_data:
                                    dev_sections_list = dev_sections_data['sections']
                                elif isinstance(dev_sections_data, list):
                                    dev_sections_list = dev_sections_data
                                else:
                                    dev_sections_list = []
                                
                                # Find matching section
                                for dev_section in dev_sections_list:
                                    if str(dev_section.get('id', '')) == str(section_id_from_db):
                                        image_concepts_from_json = dev_section.get('image_concepts')
                                        selected_concept_from_json = dev_section.get('selected_image_concept')
                                        break
                            except (json.JSONDecodeError, TypeError):
                                pass
                    
                    # Parse post_section_elements JSON if present
                    section_elements = None
                    if section.get('post_section_elements'):
                        try:
                            import json
                            section_elements = json.loads(section['post_section_elements']) if isinstance(section['post_section_elements'], str) else section['post_section_elements']
                        except (json.JSONDecodeError, TypeError):
                            logger.warning(f"Failed to parse post_section_elements for section {section['id']}")
                            section_elements = None
                    
                    formatted_sections.append({
                        'id': section['id'],
                        'section_order': section['section_order'],
                        'section_heading': section['section_heading'],
                        'section_description': section['section_description'],
                        'section_type': section.get('section_type'),  # Include section_type for recipe sections
                        'post_section_elements': section_elements,  # Structured JSON data
                        'title': section['section_heading'],
                        'description': section['section_description'],
                        'order': section['section_order'],
                        'status': section.get('status', 'draft'),
                        'draft': section.get('draft'),
                        'polished': section.get('polished'),
                        'ideas_to_include': section.get('ideas_to_include'),
                        'facts_to_include': section.get('facts_to_include'),
                        'highlighting': section.get('highlighting'),
                        'image_concepts': section.get('image_concepts') or image_concepts_from_json,  # Use JSON if not in DB
                        'image_prompts': section.get('image_prompts'),
                        'image_captions': section.get('image_captions'),
                        'image_alt_text': section.get('image_alt_text'),
                        'selected_image_concept': section.get('selected_image_concept') or selected_concept_from_json,
                        'topics': []
                    })
            
            return jsonify({
                'success': True,
                'sections': formatted_sections
            })
            
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>', methods=['GET', 'PUT'])
def api_get_section(post_id, section_id):
    """Get or update a specific section for a post from post_section table"""
    try:
        with db_manager.get_cursor() as cursor:
            # Only get from post_section table - section_id must be numeric
            if not section_id.isdigit():
                return jsonify({'error': 'Section ID must be numeric'}), 400
            
            # Handle PUT request for updating section
            if request.method == 'PUT':
                data = request.get_json()
                update_fields = []
                update_values = []
                
                if 'section_heading' in data:
                    update_fields.append('section_heading = %s')
                    update_values.append(data['section_heading'])
                
                if 'section_description' in data:
                    update_fields.append('section_description = %s')
                    update_values.append(data['section_description'])
                
                if not update_fields:
                    return jsonify({'error': 'No valid fields to update'}), 400
                
                update_values.append(post_id)
                update_values.append(int(section_id))
                
                cursor.execute(f"""
                    UPDATE post_section
                    SET {', '.join(update_fields)}
                    WHERE post_id = %s AND id = %s
                """, update_values)
                
                cursor.connection.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Section not found'}), 404
                
                return jsonify({
                    'success': True,
                    'message': 'Section updated successfully'
                })
            
            # Handle GET request
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept, section_type
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, int(section_id)))
            section = cursor.fetchone()
            
            # If not found in post_section, check post_development.sections
            section_data = None
            if not section:
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if result and result.get('sections'):
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
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")
                        section_data = None
            
            if section or section_data:
                # Get detailed description from section_structure
                detailed_description = None
                section_order = section['section_order'] if section else section_data.get('order', section_data.get('index', int(section_id)))
                
                try:
                    cursor.execute("""
                        SELECT section_structure 
                        FROM post_development 
                        WHERE post_id = %s
                    """, (post_id,))
                    dev_data = cursor.fetchone()
                    
                    if dev_data and dev_data.get('section_structure'):
                        structure_data = dev_data['section_structure']
                        if isinstance(structure_data, dict) and 'sections' in structure_data:
                            structure_list = structure_data['sections']
                            if isinstance(structure_list, list):
                                section_structure_section = next(
                                    (s for s in structure_list if s.get('id') == f"S{str(section_order).zfill(2)}"), 
                                    None
                                )
                                if section_structure_section:
                                    detailed_description = section_structure_section.get('description')
                except Exception as e:
                    logger.warning(f"Could not fetch detailed description: {e}")
                
                # Convert to frontend-compatible format
                if section:
                    # From post_section table
                    # But also check post_development.sections for image fields that might be saved there
                    image_concepts_from_json = section.get('image_concepts')
                    selected_concept_from_json = section.get('selected_image_concept')
                    
                    # If image_concepts is NULL in post_section, check post_development.sections
                    if not image_concepts_from_json:
                        cursor.execute("""
                            SELECT sections FROM post_development WHERE post_id = %s
                        """, (post_id,))
                        dev_result = cursor.fetchone()
                        if dev_result and dev_result.get('sections'):
                            try:
                                dev_sections_data = json.loads(dev_result['sections'])
                                if isinstance(dev_sections_data, dict) and 'sections' in dev_sections_data:
                                    dev_sections_list = dev_sections_data['sections']
                                elif isinstance(dev_sections_data, list):
                                    dev_sections_list = dev_sections_data
                                else:
                                    dev_sections_list = []
                                
                                # Find matching section
                                for dev_section in dev_sections_list:
                                    if str(dev_section.get('id', '')) == str(section['id']):
                                        image_concepts_from_json = dev_section.get('image_concepts')
                                        selected_concept_from_json = dev_section.get('selected_image_concept') or selected_concept_from_json
                                        break
                            except (json.JSONDecodeError, TypeError):
                                pass
                    
                    formatted_section = {
                        'id': section['id'],
                        'section_order': section['section_order'],
                        'section_heading': section['section_heading'],
                        'section_description': section['section_description'],
                        'section_type': section.get('section_type'),  # Include section_type for recipe sections
                        'title': section['section_heading'],
                        'description': section['section_description'],
                        'detailed_description': detailed_description,
                        'order': section['section_order'],
                        'status': section['status'],
                        'draft': section['draft'],
                        'polished': section['polished'],
                        'ideas_to_include': section['ideas_to_include'],
                        'facts_to_include': section['facts_to_include'],
                        'highlighting': section['highlighting'],
                        'image_concepts': image_concepts_from_json,  # Use from JSON if not in DB
                        'image_prompts': section['image_prompts'],
                        'image_captions': section['image_captions'],
                        'image_alt_text': section['image_alt_text'],
                        'selected_image_concept': selected_concept_from_json,
                        'topics': []
                    }
                else:
                    # From post_development.sections
                    formatted_section = {
                        'id': int(section_id),
                        'section_order': section_order,
                        'section_heading': section_data.get('title', f'Section {section_id}'),
                        'section_description': section_data.get('subtitle', ''),
                        'title': section_data.get('title', f'Section {section_id}'),
                        'description': section_data.get('subtitle', ''),
                        'detailed_description': detailed_description,
                        'order': section_order,
                        'status': 'draft',
                        'draft': None,
                        'polished': None,
                        'ideas_to_include': None,
                        'facts_to_include': None,
                        'highlighting': None,
                        'image_concepts': None,
                        'image_prompts': None,
                        'image_captions': None,
                        'image_alt_text': None,
                        'selected_image_concept': None,
                        'topics': section_data.get('topics', [])
                    }
                
                return jsonify({
                    'success': True,
                    'section': formatted_section
                })
            else:
                return jsonify({'error': 'Section not found'}), 404
                
    except Exception as e:
        logger.error(f"Error fetching section: {e}")
        return jsonify({'error': str(e)}), 500
