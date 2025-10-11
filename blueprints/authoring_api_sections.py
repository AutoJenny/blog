"""
Authoring API Sections Module

Micro-file for authoring section-related API endpoints
"""

from flask import request, jsonify
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)

def api_get_sections(post_id):
    """Get all sections for a post - checks both post_section and post_development tables"""
    try:
        with db_manager.get_cursor() as cursor:
            # First try to get sections from post_section table
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
            
            # Always check post_development.sections for complete section list
            # (post_section might only have generated sections)
            cursor.execute("""
                SELECT sections FROM post_development 
                WHERE post_id = %s AND sections IS NOT NULL
            """, (post_id,))
            result = cursor.fetchone()
            
            if result and result['sections']:
                try:
                    sections_data = json.loads(result['sections'])
                    if isinstance(sections_data, dict) and 'sections' in sections_data:
                        sections_list = sections_data['sections']
                    elif isinstance(sections_data, list):
                        sections_list = sections_data
                    else:
                        sections_list = []
                    
                    # Convert to post_section format and add frontend-compatible fields
                    sections = []
                    for i, section in enumerate(sections_list):
                        sections.append({
                            'id': section.get('id', f'section_{i+1}'),
                            'section_order': section.get('order', i+1),
                            'section_heading': section.get('title', f'Section {i+1}'),
                            'section_description': section.get('original', ''),
                            'title': section.get('title', f'Section {i+1}'),  # Frontend-compatible field
                            'description': section.get('original', ''),  # Frontend-compatible field
                            'order': section.get('order', i+1),  # Frontend-compatible field
                            'status': 'draft',
                            'draft': None,
                            'polished': None,
                            'ideas_to_include': None,
                            'facts_to_include': None,
                            'highlighting': None,
                            'image_concepts': section.get('image_concepts'),
                            'image_prompts': section.get('image_prompts'),
                            'image_captions': section.get('image_captions'),
                            'image_alt_text': section.get('image_alt_text'),
                            'selected_image_concept': section.get('selected_image_concept')
                        })
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse sections from post_development: {e}")
                    sections = []
            
            # Get topic allocation data to populate topics
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            topic_result = cursor.fetchone()
            
            topic_allocation = {}
            if topic_result and topic_result['topic_allocation']:
                try:
                    topic_allocation = json.loads(topic_result['topic_allocation'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Failed to parse topic allocation")
            
            # Add topics to sections if available
            if topic_allocation and 'allocations' in topic_allocation:
                allocations = topic_allocation['allocations']
                for section in sections:
                    section_id = section['id']
                    # Find matching allocation
                    for allocation in allocations:
                        if allocation.get('section_id') == section_id:
                            section['topics'] = allocation.get('topics', [])
                            break
                    if 'topics' not in section:
                        section['topics'] = []
            
            return jsonify({
                'success': True,
                'sections': sections
            })
            
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        return jsonify({'error': str(e)}), 500

def api_get_section(post_id, section_id):
    """Get a specific section for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            # First try post_section table (only if section_id is numeric)
            section = None
            if section_id.isdigit():
                cursor.execute("""
                    SELECT id, section_order, section_heading, section_description, 
                           status, draft, polished, ideas_to_include, facts_to_include,
                           highlighting, image_concepts, image_prompts, image_captions,
                           image_alt_text, selected_image_concept
                    FROM post_section
                    WHERE post_id = %s AND id = %s
                """, (post_id, int(section_id)))
                section = cursor.fetchone()
            
            # If not found, check post_development.sections
            if not section:
                cursor.execute("""
                    SELECT sections FROM post_development 
                    WHERE post_id = %s AND sections IS NOT NULL
                """, (post_id,))
                result = cursor.fetchone()
                
                if result and result['sections']:
                    try:
                        sections_data = json.loads(result['sections'])
                        if isinstance(sections_data, dict) and 'sections' in sections_data:
                            sections_list = sections_data['sections']
                        elif isinstance(sections_data, list):
                            sections_list = sections_data
                        else:
                            sections_list = []
                        
                        # Find the specific section by ID or index
                        target_section = None
                        for i, sec in enumerate(sections_list):
                            # Handle both string IDs (section_1) and integer IDs (1)
                            if (sec.get('id') == section_id or 
                                sec.get('id') == str(section_id)):
                                target_section = sec
                                break
                            # Also try to match by index if section_id is numeric
                            elif section_id.isdigit() and sec.get('index') == int(section_id):
                                target_section = sec
                                break
                            # Handle section_1 format
                            elif section_id.startswith('section_') and section_id.replace('section_', '').isdigit():
                                section_num = int(section_id.replace('section_', ''))
                                if sec.get('index') == section_num:
                                    target_section = sec
                                    break
                        
                        if target_section:
                            section = {
                                'id': target_section.get('id', f'section_{i+1}'),
                                'section_order': target_section.get('order', i+1),
                                'section_heading': target_section.get('title', f'Section {i+1}'),
                                'section_description': target_section.get('original', ''),
                                'title': target_section.get('title', f'Section {i+1}'),  # Add frontend-compatible field
                                'description': target_section.get('original', ''),  # Add frontend-compatible field
                                'order': target_section.get('order', i+1),  # Add frontend-compatible field
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
                                'selected_image_concept': None
                            }
                            
                            # Try to get draft content from post_section table
                            cursor.execute("""
                                SELECT draft, polished, status
                                FROM post_section
                                WHERE post_id = %s AND section_order = %s
                            """, (post_id, section['section_order']))
                            post_section_data = cursor.fetchone()
                            
                            if post_section_data:
                                section['draft'] = post_section_data['draft']
                                section['polished'] = post_section_data['polished']
                                section['status'] = post_section_data['status']
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")
            
            if section:
                return jsonify({
                    'success': True,
                    'section': section
                })
            else:
                return jsonify({'error': 'Section not found'}), 404
                
    except Exception as e:
        logger.error(f"Error fetching section: {e}")
        return jsonify({'error': str(e)}), 500
