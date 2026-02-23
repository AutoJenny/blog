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
                    # Use standard recipe sections from utility module
                    from utils.section_headings import get_standard_recipe_sections
                    recipe_sections = get_standard_recipe_sections()
                    
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
                            # Update existing section with section_type if missing, and ensure heading is set
                            # Use COALESCE to handle NULL values properly
                            cursor.execute("""
                                UPDATE post_section
                                SET section_type = COALESCE(NULLIF(section_type, ''), %s),
                                    section_heading = COALESCE(NULLIF(section_heading, ''), %s),
                                    section_description = COALESCE(NULLIF(section_description, ''), %s)
                                WHERE post_id = %s AND section_order = %s
                                  AND (section_type IS NULL OR section_type = '' OR section_heading IS NULL OR section_heading = '')
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

            # W2-FIX-1: Ensure default sections on first authoring visit (legacy posts created before fix)
            if not sections and post_type != 'recipe':
                from utils.posts.post_factory import ensure_default_sections
                created = ensure_default_sections(post_id, variant=post_type if post_type in ('profile', 'generated') else 'generic')
                if created:
                    # Re-fetch sections
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
            
            # CRITICAL: Auto-populate missing section headings for recipe sections
            # This ensures headings are always present, even if they were lost or never set
            if post_type == 'recipe' and sections:
                from utils.section_headings import ensure_section_heading, is_recipe_section_type
                headings_updated = False
                
                for section in sections:
                    section_type = section.get('section_type')
                    current_heading = section.get('section_heading')
                    section_id = section.get('id')
                    
                    # Check if this is a recipe section with missing heading
                    if is_recipe_section_type(section_type) and (not current_heading or not current_heading.strip()):
                        standard_heading = ensure_section_heading(section_type, current_heading)
                        if standard_heading:
                            # Update the section in database
                            cursor.execute("""
                                UPDATE post_section
                                SET section_heading = %s
                                WHERE id = %s
                            """, (standard_heading, section_id))
                            # Update the section dict for immediate use
                            section['section_heading'] = standard_heading
                            headings_updated = True
                            logger.info(f"Auto-populated heading '{standard_heading}' for recipe section {section_id} (type: {section_type})")
                
                if headings_updated:
                    cursor.connection.commit()
                    logger.info(f"Updated missing headings for recipe post {post_id}")
            
            # Get topic allocation data for profile posts (raw data chunks) - fetch early so it's available for both paths
            topic_allocation_data = None
            if post_type == 'profile':
                cursor.execute("""
                    SELECT topic_allocation FROM post_development WHERE post_id = %s
                """, (post_id,))
                topic_result = cursor.fetchone()
                if topic_result and topic_result.get('topic_allocation'):
                    try:
                        topic_allocation_data = json.loads(topic_result['topic_allocation']) if isinstance(topic_result['topic_allocation'], str) else topic_result['topic_allocation']
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Failed to parse topic_allocation for post {post_id}")
                        topic_allocation_data = None
            
            # W2-FIX-1: Do NOT fall back to post_development.sections. Only return real post_section rows
            # (non-numeric IDs from JSON cannot be saved; ensure_default_sections guarantees DB sections at creation)

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
                            section_elements = json.loads(section['post_section_elements']) if isinstance(section['post_section_elements'], str) else section['post_section_elements']
                        except (json.JSONDecodeError, TypeError):
                            logger.warning(f"Failed to parse post_section_elements for section {section['id']}")
                            section_elements = None
                    
                    # Get raw data chunks from topic_allocation for this section (profile posts)
                    data_chunks = []
                    if post_type == 'profile' and topic_allocation_data:
                        try:
                            allocations = topic_allocation_data.get('allocations', [])
                            section_order = section['section_order']
                            # Match by section_order (section_01, section_02, etc.) or section_code (S01, S02, etc.)
                            for allocation in allocations:
                                allocation_section_id = allocation.get('section_id', '')
                                allocation_section_code = allocation.get('section_code', '').replace('{', '').replace('}', '')
                                # Match by order number - try multiple formats
                                section_order_str = str(section_order)
                                section_order_padded = f"{section_order:02d}"
                                
                                # Check if section_id matches (e.g., "section_1" or "section_01")
                                if allocation_section_id:
                                    if (f'section_{section_order}' == allocation_section_id) or \
                                       (f'section_{section_order_padded}' == allocation_section_id):
                                        data_chunks = allocation.get('data_chunks', [])
                                        break
                                
                                # Check if section_code matches (e.g., "S01" or "S1")
                                if allocation_section_code:
                                    if (f'S{section_order_padded}' == allocation_section_code) or \
                                       (f'S{section_order}' == allocation_section_code):
                                        data_chunks = allocation.get('data_chunks', [])
                                        break
                        except (KeyError, TypeError, AttributeError) as e:
                            logger.warning(f"Error extracting data chunks for section {section['id']}: {e}")
                            data_chunks = []
                    
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
                        'topics': [],
                        'data_chunks': data_chunks  # Raw data chunks for profile posts
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
                from utils.posts.status_transitions import require_post_editable
                from utils.posts.workflow_stage import require_workflow_stage
                err, code = require_post_editable(post_id, request=request)
                if err:
                    return jsonify({'error': err, 'status_blocked': True}), code
                gate, gate_code = require_workflow_stage(post_id, 'authoring', request=request)
                if gate:
                    return jsonify({**gate, 'success': False}), gate_code
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

            # W2-FIX-1: Do NOT fall back to post_development.sections for single section (non-numeric IDs cannot be saved)
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            if section:
                # Get detailed description from section_structure
                detailed_description = None
                section_order = section['section_order']
                
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
                
                # Convert to frontend-compatible format (post_section only; W2-FIX-1 no JSON fallback)
                image_concepts_from_json = section.get('image_concepts')
                selected_concept_from_json = section.get('selected_image_concept')

                # Augment image fields from post_development.sections if missing in post_section
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
                    'section_type': section.get('section_type'),
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
                    'image_concepts': image_concepts_from_json,
                    'image_prompts': section['image_prompts'],
                    'image_captions': section['image_captions'],
                    'image_alt_text': section['image_alt_text'],
                    'selected_image_concept': selected_concept_from_json,
                    'topics': []
                }

                return jsonify({
                    'success': True,
                    'section': formatted_section
                })
                
    except Exception as e:
        logger.error(f"Error fetching section: {e}")
        return jsonify({'error': str(e)}), 500
