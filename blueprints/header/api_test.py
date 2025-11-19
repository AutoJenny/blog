"""Test and utility API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .llm_service import LLMService
import logging
import json

logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMService()


def register_routes(bp):
    """Register test/utility API routes"""
    
    @bp.route('/api/posts/<int:post_id>/test-field', methods=['GET'])
    def api_test_field(post_id):
        """New endpoint for Step 4 field - replicates Step 3 content"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get the task prompt (same as Step 3)
                cursor.execute("""
                    SELECT 
                        sp.system_prompt,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                    JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                    WHERE wsp.step_id = 64
                """)
                prompt_result = cursor.fetchone()
                
                if not prompt_result:
                    return jsonify({
                        'success': False,
                        'content': 'Header prompt compilation prompts not found'
                    }), 404
                
                task_prompt = prompt_result['task_prompt']
                
                # Get sections data (same as Step 3)
                cursor.execute("""
                    SELECT sections FROM post_development 
                    WHERE post_id = %s AND sections IS NOT NULL
                """, (post_id,))
                sections_result = cursor.fetchone()
                
                # Replace placeholders with actual data (show the actual prompt sent to LLM)
                formatted_content = task_prompt
                
                if sections_result and sections_result['sections']:
                    try:
                        sections_data = json.loads(sections_result['sections'])
                        if isinstance(sections_data, dict) and 'sections' in sections_data:
                            sections_list = sections_data['sections']
                        elif isinstance(sections_data, list):
                            sections_list = sections_data
                        else:
                            sections_list = []
                        
                        section_prompts_text = ""
                        for section in sections_list:
                            if section.get('image_prompts') and isinstance(section['image_prompts'], dict):
                                image_prompt = section['image_prompts'].get('image_prompt', '')
                                if image_prompt:
                                    section_prompts_text += f"Section {section.get('index', 0)}: {image_prompt}\n\n"
                        
                        # Replace the placeholder with actual section prompts
                        formatted_content = formatted_content.replace('{section_prompts}', section_prompts_text.strip())
                        logger.info(f"Replaced section_prompts with {len(section_prompts_text)} characters")
                    except Exception as e:
                        logger.error(f"Error parsing sections data: {str(e)}")
                else:
                    logger.warning("No sections data found for replacement")
                
                # Highlight placeholders (same as Step 3)
                formatted_content = formatted_content.replace(
                    '{style_guidelines}', 
                    '<span class="template-placeholder">{style_guidelines}</span>'
                )
                formatted_content = formatted_content.replace(
                    '{model}', 
                    '<span class="template-placeholder">{model}</span>'
                )
                
                return jsonify({
                    'success': True,
                    'content': formatted_content
                })
                
        except Exception as e:
            logger.error(f"Error in test-field endpoint: {str(e)}")
            return jsonify({
                'success': False,
                'content': f'Error: {str(e)}'
            }), 500

    @bp.route('/api/execute-llm', methods=['POST'])
    def api_execute_llm():
        """Execute LLM request for header prompt generation."""
        try:
            data = request.get_json()
            
            provider = data.get('provider', 'ollama')
            model = data.get('model', 'llama3.2:latest')
            messages = data.get('messages', [])
            
            if not messages:
                return jsonify({'error': 'No messages provided'}), 400
            
            # Use the LLM service to execute the request
            result = llm_service.execute_llm_request(provider, model, messages)
            
            # ALWAYS save the generated prompt to the database if we have content
            if result.get('content') and data.get('post_id'):
                post_id = data.get('post_id')
                new_prompt = result['content'].strip()
                
                try:
                    with db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Check if header image record exists
                        cursor.execute("""
                            SELECT header_image_id FROM post WHERE id = %s
                        """, (post_id,))
                        
                        existing_image = cursor.fetchone()
                        
                        if existing_image and existing_image['header_image_id']:
                            # UPDATE existing image record - THIS OVERWRITES THE OLD PROMPT
                            cursor.execute("""
                                UPDATE images 
                                SET image_prompt = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (new_prompt, existing_image['header_image_id']))
                            logger.info(f"UPDATED header prompt for post {post_id} in image {existing_image['header_image_id']}")
                        else:
                            # Create new image record with just the prompt
                            cursor.execute("""
                                INSERT INTO images (filename, original_filename, file_path, image_prompt, alt_text, caption)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING id
                            """, (
                                'header.jpg',
                                'placeholder.png',
                                '/static/content/posts/' + str(post_id) + '/header/header.jpg',
                                new_prompt,
                                'Header image prompt',
                                'Generated header image prompt'
                            ))
                            image_id = cursor.fetchone()['id']
                            
                            # Link to post
                            cursor.execute("""
                                UPDATE post SET header_image_id = %s WHERE id = %s
                            """, (image_id, post_id))
                            logger.info(f"CREATED new header prompt for post {post_id}")
                        
                        conn.commit()
                except Exception as e:
                    logger.error(f"Error saving header prompt to database: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return jsonify({'error': str(e)}), 500

