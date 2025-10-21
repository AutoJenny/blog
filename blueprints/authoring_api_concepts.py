"""
Authoring API - Image Concepts

Handles image concept generation and management for the authoring stage.
Keeps file size under 300 lines as per user requirements.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from modules.llm_service import llm_service
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('authoring_concepts', __name__, url_prefix='/authoring')


@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/save-image-concepts', methods=['POST'])
def api_save_image_concepts(post_id, section_id):
    """Save image concepts for a specific section"""
    try:
        data = request.get_json()
        image_concepts = data.get('image_concepts', '')
        
        with db_manager.get_cursor() as cursor:
            # Get current sections data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row:
                return jsonify({'error': 'Post development data not found'}), 404
            
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                for s in sections_list:
                    if s.get('id') == section_id:
                        s['image_concepts'] = image_concepts
                        break
                
                # Update database
                cursor.execute("""
                    UPDATE post_development 
                    SET sections = %s 
                    WHERE post_id = %s
                """, (json.dumps(sections_data), post_id))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Image concepts saved successfully'
                })
            else:
                return jsonify({'error': 'Invalid sections data structure'}), 500
                
    except Exception as e:
        logger.error(f"Error saving image concepts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/sections/<section_id>/select-concept', methods=['POST'])
def api_select_concept(post_id, section_id):
    """Save the selected image concept for a specific section"""
    try:
        data = request.get_json()
        concept_id = data.get('concept_id', '')
        
        with db_manager.get_cursor() as cursor:
            # Get current sections data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row:
                return jsonify({'error': 'Post development data not found'}), 404
            
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                for s in sections_list:
                    if str(s.get('id')) == str(section_id):
                        s['selected_image_concept'] = concept_id
                        break
                
                # Update database
                cursor.execute("""
                    UPDATE post_development 
                    SET sections = %s 
                    WHERE post_id = %s
                """, (json.dumps(sections_data), post_id))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Concept selected successfully'
                })
            else:
                return jsonify({'error': 'Invalid sections data structure'}), 500
                
    except Exception as e:
        logger.error(f"Error selecting concept: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate-image-concepts', methods=['POST'])
def api_generate_image_concepts(post_id, section_id):
    """Generate image concepts for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data for context
            cursor.execute("""
                SELECT idea_seed, expanded_idea, title FROM post WHERE id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get section data
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            dev_row = cursor.fetchone()
            
            if not dev_row or not dev_row['sections']:
                return jsonify({'error': 'Section data not found'}), 404
            
            # Parse sections data
            sections_data = dev_row['sections']
            if isinstance(sections_data, str):
                sections_data = json.loads(sections_data)
            
            if isinstance(sections_data, dict) and 'sections' in sections_data:
                sections_list = sections_data['sections']
                section = None
                for s in sections_list:
                    if str(s.get('id')) == str(section_id):
                        section = s
                        break
                
                if not section:
                    return jsonify({'error': 'Section not found'}), 404
            else:
                return jsonify({'error': 'Invalid sections data'}), 500
            
            # Get topics from topic_allocation
            topics = []
            try:
                if 'topic_allocation' in sections_data:
                    allocation = sections_data['topic_allocation']
                    if isinstance(allocation, dict) and 'sections' in allocation:
                        for s in allocation['sections']:
                            if str(s.get('id')) == str(section_id):
                                topics = allocation.get('topics', [])
                                break
            except Exception as e:
                logger.error(f"Error parsing topic_allocation: {e}")
            
            # Get the image concepts prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Concepts Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'Image Concepts prompt not found'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:idea_seed]', post_data['idea_seed'] or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['expanded_idea'] or '')
            prompt_text = prompt_text.replace('[data:title]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:subtitle]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:section_text]', section['polished'] or section['draft'] or '')
            topics_text = '\n'.join([f'- {topic}' for topic in topics])
            prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Execute LLM request with retry logic for valid JSON
            max_retries = 3
            image_concepts = None
            
            for attempt in range(max_retries):
                result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                
                if 'error' in result:
                    if attempt == max_retries - 1:  # Last attempt
                        return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
                    continue
                
                raw_content = result['content']
                
                # Validate JSON
                try:
                    parsed_json = json.loads(raw_content)
                    
                    # Check if it has the expected structure
                    if not isinstance(parsed_json, dict) or 'concepts' not in parsed_json:
                        raise ValueError("Missing 'concepts' key")
                    
                    if not isinstance(parsed_json['concepts'], list) or len(parsed_json['concepts']) == 0:
                        raise ValueError("Concepts must be a non-empty list")
                    
                    # Check each concept has required fields
                    required_fields = ['concept_id', 'concept_title', 'concept_description', 'concept_mood', 'key_visual_elements']
                    for i, concept in enumerate(parsed_json['concepts']):
                        for field in required_fields:
                            if field not in concept or not concept[field]:
                                raise ValueError(f"Concept {i+1} missing or empty field: {field}")
                    
                    image_concepts = raw_content
                    break
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Attempt {attempt + 1}: Invalid JSON response: {e}")
                    if attempt == max_retries - 1:  # Last attempt
                        return jsonify({'error': f'LLM returned invalid JSON after {max_retries} attempts'}), 500
            
            if not image_concepts:
                return jsonify({'error': 'Failed to generate valid concepts'}), 500
            
            # Save to database
            try:
                sections_data = dev_row['sections']
                if isinstance(sections_data, str):
                    sections_data = json.loads(sections_data)
                
                if isinstance(sections_data, dict) and 'sections' in sections_data:
                    sections_list = sections_data['sections']
                    for s in sections_list:
                        if str(s.get('id')) == str(section_id):
                            s['image_concepts'] = image_concepts
                            break
                    
                    # Update the database
                    cursor.execute("""
                        UPDATE post_development 
                        SET sections = %s 
                        WHERE post_id = %s
                    """, (json.dumps(sections_data), post_id))
                else:
                    logger.error("Invalid sections data structure")
                    return jsonify({'error': 'Failed to update sections data'}), 500
                    
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error updating sections JSON for image concepts: {e}")
                return jsonify({'error': 'Failed to update sections data'}), 500
            
            cursor.connection.commit()
            
            logger.info(f"[DEBUG] Generated concepts for post {post_id}, section {section_id}")
            
            return jsonify({
                'success': True,
                'message': 'Image concepts generated and saved successfully',
                'image_concepts': image_concepts
            })
            
    except Exception as e:
        logger.error(f"Error generating image concepts: {e}")
        return jsonify({'error': str(e)}), 500
