# Header Blueprint - Blog post header and metadata generation
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging
import json
import re
import requests
import os

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'base_url': 'https://api.openai.com/v1',
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            'ollama': {
                'base_url': 'http://localhost:11434'
            }
        }
    
    def execute_llm_request(self, provider, model, messages, api_key=None):
        """Execute LLM request."""
        try:
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key or self.providers["openai"]["api_key"]}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
            elif provider == 'ollama':
                data = {
                    'model': model,
                    'messages': messages,
                    'stream': False,
                    'options': {
                        'num_predict': 4000
                    }
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=60
                )
            else:
                return {'error': f'Unknown provider: {provider}'}
            
            if response.status_code == 200:
                result = response.json()
                if provider == 'openai':
                    return {'content': result['choices'][0]['message']['content']}
                elif provider == 'ollama':
                    return {'content': result['message']['content']}
            else:
                return {'error': f'API request failed: {response.status_code} - {response.text}'}
                
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return {'error': str(e)}

# Initialize LLM service
llm_service = LLMService()

bp = Blueprint('header', __name__, url_prefix='/header')

# Main routes
@bp.route('/posts/<int:post_id>/title-summary')
def header_title_summary(post_id):
    """Title & Summary substage - Generate post title, subtitle, slug, and summary"""
    return render_template('header/title_summary.html', post_id=post_id, blueprint_name='header')

@bp.route('/posts/<int:post_id>/header-image')
def header_header_image(post_id):
    """Header Image substage - Create header image with caption and alt text"""
    return render_template('header/header_image.html', post_id=post_id, blueprint_name='header')

@bp.route('/posts/<int:post_id>/seo-meta')
def header_seo_meta(post_id):
    """SEO & Meta substage - Generate SEO metadata including meta title, description, and tags"""
    return render_template('header/seo_meta.html', post_id=post_id, blueprint_name='header')

@bp.route('/posts/<int:post_id>/publishing-details')
def header_publishing_details(post_id):
    """Publishing Details substage - Set author, word count, publish date, and status"""
    return render_template('header/publishing_details.html', post_id=post_id, blueprint_name='header')

@bp.route('/posts/<int:post_id>/final-review')
def header_final_review(post_id):
    """Final Review substage - Review and finalize all header elements before publishing"""
    return render_template('header/final_review.html', post_id=post_id, blueprint_name='header')

# API endpoints
@bp.route('/api/prompts/<int:step_id>')
def api_get_prompts(step_id):
    """Get system and task prompts for a workflow step"""
    try:
        logger.info(f"Getting prompts for step_id: {step_id}")
        with db_manager.get_cursor() as cursor:
            # Get prompts from workflow_step_prompt table
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                WHERE wsp.step_id = %s
            """, (step_id,))
            
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'system_prompt': result.get('system_prompt', '') or '',
                    'task_prompt': result.get('task_prompt', '') or ''
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No prompts found for this step'
                }), 404
                
    except Exception as e:
        logger.error(f"Error getting prompts for step {step_id}: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prompts/<int:step_id>', methods=['POST'])
def api_save_prompts(step_id):
    """Save system and task prompts for a workflow step"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt', '')
        task_prompt = data.get('task_prompt', '')
        
        with db_manager.get_cursor() as cursor:
            # Get current prompt IDs
            cursor.execute("""
                SELECT system_prompt_id, task_prompt_id
                FROM workflow_step_prompt
                WHERE step_id = %s
            """, (step_id,))
            
            result = cursor.fetchone()
            
            if result:
                system_prompt_id, task_prompt_id = result
                
                # Update system prompt
                if system_prompt_id:
                    cursor.execute("""
                        UPDATE llm_prompt 
                        SET system_prompt = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (system_prompt, system_prompt_id))
                else:
                    # Create new system prompt
                    cursor.execute("""
                        INSERT INTO llm_prompt (name, description, system_prompt)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (f'System Prompt Step {step_id}', f'System prompt for step {step_id}', system_prompt))
                    system_prompt_id = cursor.fetchone()[0]
                
                # Update task prompt
                if task_prompt_id:
                    cursor.execute("""
                        UPDATE llm_prompt 
                        SET prompt_text = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (task_prompt, task_prompt_id))
                else:
                    # Create new task prompt
                    cursor.execute("""
                        INSERT INTO llm_prompt (name, description, prompt_text, step_id)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (f'Task Prompt Step {step_id}', f'Task prompt for step {step_id}', task_prompt, step_id))
                    task_prompt_id = cursor.fetchone()[0]
                
                # Update workflow_step_prompt link
                cursor.execute("""
                    UPDATE workflow_step_prompt
                    SET system_prompt_id = %s, task_prompt_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE step_id = %s
                """, (system_prompt_id, task_prompt_id, step_id))
                
                return jsonify({'success': True})
            else:
                return jsonify({
                    'success': False,
                    'error': 'No workflow step found'
                }), 404
                
    except Exception as e:
        logger.error(f"Error saving prompts for step {step_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-titles', methods=['POST'])
def api_generate_titles(post_id):
    """Generate three title options based on Development tab content using LLM"""
    try:
        data = request.get_json()
        idea_seed = data.get('idea_seed', '')
        expanded_idea = data.get('expanded_idea', '')
        section_content = data.get('section_content', '')
        
        logger.info(f"Generating titles for post {post_id} with content: idea_seed={idea_seed[:50]}...")
        
        # Get prompts from database for step 60 (Title Generation)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                WHERE wsp.step_id = 60
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No prompts found for title generation'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Replace placeholders in task prompt with actual data
        prompt_vars = {
            'idea_seed': idea_seed,
            'expanded_idea': expanded_idea,
            'section_content': section_content
        }
        
        # Replace [data:field] placeholders
        for key, value in prompt_vars.items():
            task_prompt = task_prompt.replace(f'[data:{key}]', str(value))
        
        # Prepare messages for LLM
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': task_prompt}
        ]
        
        # Execute LLM request
        logger.info(f"Calling LLM for title generation with system prompt: {system_prompt[:100]}...")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            logger.error(f"LLM generation failed: {llm_response['error']}")
            return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
        
        generated_content = llm_response['content'].strip()
        logger.info(f"LLM response: {generated_content[:200]}...")
        
        # Parse JSON response
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                title_options = json.loads(json_str)
                
                if not isinstance(title_options, list) or len(title_options) != 3:
                    raise ValueError("Response must be an array of exactly 3 titles")
                
                # Clean up titles
                title_options = [title.strip().strip('"').strip("'") for title in title_options]
                
                return jsonify({
                    'success': True,
                    'title_options': title_options,
                    'selected_index': 0
                })
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {generated_content}")
            return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error generating titles for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-subtitle', methods=['POST'])
def api_generate_subtitle(post_id):
    """Generate subtitle based on Development tab content and selected title using LLM"""
    try:
        data = request.get_json()
        idea_seed = data.get('idea_seed', '')
        expanded_idea = data.get('expanded_idea', '')
        selected_title = data.get('selected_title', '')
        section_content = data.get('section_content', '')
        
        logger.info(f"Generating subtitle for post {post_id} with title: {selected_title[:50]}...")
        
        # Get prompts from database for step 61 (Subtitle Generation)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                WHERE wsp.step_id = 61
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No prompts found for subtitle generation'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Replace placeholders in task prompt with actual data
        prompt_vars = {
            'idea_seed': idea_seed,
            'expanded_idea': expanded_idea,
            'selected_title': selected_title,
            'section_content': section_content
        }
        
        # Replace [data:field] placeholders
        for key, value in prompt_vars.items():
            task_prompt = task_prompt.replace(f'[data:{key}]', str(value))
        
        # Prepare messages for LLM
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': task_prompt}
        ]
        
        # Execute LLM request
        logger.info(f"Calling LLM for subtitle generation with system prompt: {system_prompt[:100]}...")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            logger.error(f"LLM generation failed: {llm_response['error']}")
            return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
        
        generated_subtitle = llm_response['content'].strip()
        logger.info(f"LLM response: {generated_subtitle}")
        
        return jsonify({
            'success': True,
            'subtitle': generated_subtitle
        })
        
    except Exception as e:
        logger.error(f"Error generating subtitle for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-title-summary', methods=['POST'])
def api_generate_title_summary(post_id):
    """Generate all header elements (title, subtitle, summary, slug) in one call"""
    try:
        # Get content from Development tab
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pd.idea_seed,
                    pd.expanded_idea,
                    p.title,
                    p.title_choices
                FROM post_development pd
                JOIN post p ON p.id = pd.post_id
                WHERE pd.post_id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No post development data found'}), 404
            
            idea_seed = result.get('idea_seed', '')
            expanded_idea = result.get('expanded_idea', '')
            current_title = result.get('title', '')
            title_choices = result.get('title_choices', '[]')
            
            # Get section content
            cursor.execute("""
                SELECT section_heading, draft
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            section_content = '\n'.join([f"{s.get('section_heading', '')}: {s.get('draft', '')}" for s in sections])
        
        logger.info(f"Generating all header elements for post {post_id}")
        
        # Generate titles using the same logic as api_generate_titles
        # Get prompts from database for step 60 (Title Generation)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                WHERE wsp.step_id = 60
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No prompts found for title generation'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Replace placeholders in task prompt with actual data
        prompt_vars = {
            'idea_seed': idea_seed,
            'expanded_idea': expanded_idea,
            'section_content': section_content
        }
        
        # Replace [data:field] placeholders
        for key, value in prompt_vars.items():
            task_prompt = task_prompt.replace(f'[data:{key}]', str(value))
        
        # Prepare messages for LLM
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': task_prompt}
        ]
        
        # Execute LLM request for titles
        logger.info(f"Calling LLM for title generation")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            logger.error(f"LLM generation failed: {llm_response['error']}")
            return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
        
        generated_content = llm_response['content'].strip()
        
        # Parse JSON response for titles
        try:
            json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                title_options = json.loads(json_str)
                
                if not isinstance(title_options, list) or len(title_options) != 3:
                    raise ValueError("Response must be an array of exactly 3 titles")
                
                # Clean up titles
                title_options = [title.strip().strip('"').strip("'") for title in title_options]
                selected_title = title_options[0]
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
        
        # Generate subtitle using the same logic as api_generate_subtitle
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                WHERE wsp.step_id = 61
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No prompts found for subtitle generation'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Replace placeholders in task prompt with actual data
        prompt_vars = {
            'idea_seed': idea_seed,
            'expanded_idea': expanded_idea,
            'selected_title': selected_title,
            'section_content': section_content
        }
        
        # Replace [data:field] placeholders
        for key, value in prompt_vars.items():
            task_prompt = task_prompt.replace(f'[data:{key}]', str(value))
        
        # Prepare messages for LLM
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': task_prompt}
        ]
        
        # Execute LLM request for subtitle
        logger.info(f"Calling LLM for subtitle generation")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            logger.error(f"LLM generation failed: {llm_response['error']}")
            return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
        
        subtitle = llm_response['content'].strip()
        
        # TODO: Generate summary and slug
        summary = "Generated summary placeholder"
        slug = "generated-slug-placeholder"
        
        return jsonify({
            'success': True,
            'title_options': title_options,
            'subtitle': subtitle,
            'summary': summary,
            'slug': slug
        })
        
    except Exception as e:
        logger.error(f"Error generating all header elements for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/save-selected-title', methods=['POST'])
def api_save_selected_title(post_id):
    """Save the selected title and title options to database"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        title_index = data.get('title_index', 0)
        title_options = data.get('title_options', [])
        
        with db_manager.get_cursor() as cursor:
            # Update post table with selected title and options
            cursor.execute("""
                UPDATE post 
                SET title = %s, title_choices = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (title, json.dumps(title_options), post_id))
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error saving selected title for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-titles')
def api_get_titles(post_id):
    """Get existing title options and selected title"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, title_choices
                FROM post 
                WHERE id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if result:
                title = result.get('title', '') or ''
                title_choices = result.get('title_choices', '') or '[]'
                
                try:
                    title_options = json.loads(title_choices)
                except:
                    title_options = []
                
                # Find selected index
                selected_index = 0
                if title and title_options:
                    try:
                        selected_index = title_options.index(title)
                    except ValueError:
                        selected_index = 0
                
                return jsonify({
                    'success': True,
                    'title_options': title_options,
                    'selected_title': title,
                    'selected_index': selected_index
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Post not found'
                }), 404
                
    except Exception as e:
        logger.error(f"Error getting titles for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-header-image', methods=['POST'])
def api_generate_header_image(post_id):
    """Generate header image with caption and alt text"""
    try:
        data = request.get_json()
        
        # TODO: Implement header image generation
        # For now, return empty data that will be populated by actual generation
        return jsonify({
            'success': True,
            'image_path': '',
            'caption': '',
            'alt_text': '',
            'title': ''
        })
        
    except Exception as e:
        logger.error(f"Error generating header image: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-seo-meta', methods=['POST'])
def api_generate_seo_meta(post_id):
    """Generate meta title, description, tags"""
    try:
        data = request.get_json()
        
        # Get post data for context
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, summary, idea_seed
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # TODO: Implement LLM generation for SEO meta
            # For now, return empty data that will be populated by actual generation
            meta_title = ""
            meta_description = ""
            meta_tags = ""
            
            return jsonify({
                'success': True,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'meta_tags': meta_tags
            })
            
    except Exception as e:
        logger.error(f"Error generating SEO meta: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/calculate-word-count', methods=['GET'])
def api_calculate_word_count(post_id):
    """Calculate total word count from all sections + header + summary"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post title and summary
            cursor.execute("""
                SELECT title, summary FROM post WHERE id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            # Get all section content
            cursor.execute("""
                SELECT sections FROM post_development WHERE post_id = %s
            """, (post_id,))
            sections_data = cursor.fetchone()
            
            word_count = 0
            
            # Count words in post title and summary
            if post_data:
                if post_data['title']:
                    word_count += len(post_data['title'].split())
                if post_data['summary']:
                    word_count += len(post_data['summary'].split())
            
            # Count words in sections
            if sections_data and sections_data['sections']:
                try:
                    sections = json.loads(sections_data['sections']) if isinstance(sections_data['sections'], str) else sections_data['sections']
                    if isinstance(sections, dict) and 'sections' in sections:
                        sections_list = sections['sections']
                    elif isinstance(sections, list):
                        sections_list = sections
                    else:
                        sections_list = []
                    
                    for section in sections_list:
                        if section.get('draft'):
                            word_count += len(section['draft'].split())
                        elif section.get('polished'):
                            word_count += len(section['polished'].split())
                        elif section.get('original'):
                            word_count += len(section['original'].split())
                            
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Could not parse sections JSON for post {post_id}")
            
            return jsonify({
                'success': True,
                'word_count': word_count
            })
            
    except Exception as e:
        logger.error(f"Error calculating word count: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/authors', methods=['GET'])
def api_get_authors(post_id):
    """Get list of available authors"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, bio, avatar_url, is_active
                FROM author 
                WHERE is_active = true
                ORDER BY name
            """)
            
            authors = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'authors': authors
            })
            
    except Exception as e:
        logger.error(f"Error getting authors: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/save-header-data', methods=['POST'])
def api_save_header_data(post_id):
    """Save any header field updates"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Build dynamic update query based on provided fields
            update_fields = []
            update_values = []
            
            allowed_fields = [
                'title', 'subtitle', 'summary', 'slug', 'author_id',
                'meta_title', 'meta_description', 'meta_tags',
                'header_image_caption', 'header_image_title', 'header_image_alt_text',
                'publish_at', 'status'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[field])
            
            if update_fields:
                update_values.append(post_id)
                query = f"""
                    UPDATE post 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                
                cursor.execute(query, update_values)
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Header data saved successfully'
                })
            else:
                return jsonify({'error': 'No valid fields provided'}), 400
                
    except Exception as e:
        logger.error(f"Error saving header data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-header-data', methods=['GET'])
def api_get_header_data(post_id):
    """Get current header data for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.*, a.name as author_name
                FROM post p
                LEFT JOIN author a ON p.author_id = a.id
                WHERE p.id = %s
            """, (post_id,))
            
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'post_data': dict(post_data)
            })
            
    except Exception as e:
        logger.error(f"Error getting header data: {e}")
        return jsonify({'error': str(e)}), 500
