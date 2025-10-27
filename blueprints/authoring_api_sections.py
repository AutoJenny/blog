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
    """Get all sections for a post from post_section table only"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get sections from post_section table only
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
            
            # Convert to frontend-compatible format
            formatted_sections = []
            for section in sections:
                formatted_sections.append({
                    'id': section['id'],  # Always numeric ID from database
                    'section_order': section['section_order'],
                    'section_heading': section['section_heading'],
                    'section_description': section['section_description'],
                    'title': section['section_heading'],  # Frontend-compatible field
                    'description': section['section_description'],  # Frontend-compatible field
                    'order': section['section_order'],  # Frontend-compatible field
                    'status': section['status'],
                    'draft': section['draft'],
                    'polished': section['polished'],
                    'ideas_to_include': section['ideas_to_include'],
                    'facts_to_include': section['facts_to_include'],
                    'highlighting': section['highlighting'],
                    'image_concepts': section['image_concepts'],
                    'image_prompts': section['image_prompts'],
                    'image_captions': section['image_captions'],
                    'image_alt_text': section['image_alt_text'],
                    'selected_image_concept': section['selected_image_concept'],
                    'topics': []  # Topics will be populated separately if needed
                })
            
            return jsonify({
                'success': True,
                'sections': formatted_sections
            })
            
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_section(post_id, section_id):
    """Get a specific section for a post from post_section table only"""
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
            
            if section:
                # Get detailed description from section_structure
                detailed_description = None
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
                                    (s for s in structure_list if s.get('id') == f"S{str(section['section_order']).zfill(2)}"), 
                                    None
                                )
                                if section_structure_section:
                                    detailed_description = section_structure_section.get('description')
                except Exception as e:
                    logger.warning(f"Could not fetch detailed description: {e}")
                
                # Convert to frontend-compatible format
                formatted_section = {
                    'id': section['id'],  # Always numeric ID from database
                    'section_order': section['section_order'],
                    'section_heading': section['section_heading'],
                    'section_description': section['section_description'],
                    'title': section['section_heading'],  # Frontend-compatible field
                    'description': section['section_description'],  # Frontend-compatible field
                    'detailed_description': detailed_description,  # From section_structure
                    'order': section['section_order'],  # Frontend-compatible field
                    'status': section['status'],
                    'draft': section['draft'],
                    'polished': section['polished'],
                    'ideas_to_include': section['ideas_to_include'],
                    'facts_to_include': section['facts_to_include'],
                    'highlighting': section['highlighting'],
                    'image_concepts': section['image_concepts'],
                    'image_prompts': section['image_prompts'],
                    'image_captions': section['image_captions'],
                    'image_alt_text': section['image_alt_text'],
                    'selected_image_concept': section['selected_image_concept'],
                    'topics': []  # Topics will be populated separately if needed
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
