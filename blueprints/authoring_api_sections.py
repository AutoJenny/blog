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
            # Get sections from post_section table first
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
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
                    
                    formatted_sections.append({
                        'id': section['id'],
                        'section_order': section['section_order'],
                        'section_heading': section['section_heading'],
                        'section_description': section['section_description'],
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

@bp.route('/api/posts/<int:post_id>/sections/<section_id>', methods=['GET'])
def api_get_section(post_id, section_id):
    """Get a specific section for a post from post_section table, with fallback to post_development.sections"""
    try:
        with db_manager.get_cursor() as cursor:
            # Only get from post_section table - section_id must be numeric
            if not section_id.isdigit():
                return jsonify({'error': 'Section ID must be numeric'}), 400
                
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions,
                       image_alt_text, selected_image_concept
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
