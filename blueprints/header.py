# Header Blueprint - Blog post header and metadata generation
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
from blueprints.imaging import imaging_generate_dalle_image, imaging_generate_gpt_image_1, imaging_generate_sdxl_image
import logging
import json
import re
import requests
import os
from slugify import slugify

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

@bp.route('/posts/<int:post_id>/preview')
def header_preview(post_id):
    """Preview the blog post in its final format (matches clan.com/blog)"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT id, title, subtitle, summary, slug, status, 
                       created_at, updated_at, header_image_id, author_id
                FROM post
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get header image if exists
            header_image = None
            if post['header_image_id']:
                cursor.execute("""
                    SELECT id, filename, path, alt_text, caption
                    FROM image
                    WHERE id = %s
                """, (post['header_image_id'],))
                header_image = cursor.fetchone()
                if header_image and header_image['path']:
                    # Use optimized image path instead of raw
                    # Replace /static/content/posts/X/header/raw/header.png with optimized version
                    optimized_path = header_image['path'].replace('/raw/', '/optimized/').replace('.png', '.jpg')
                    header_image['path'] = optimized_path
            
            # Get sections with images via post_images linking table
            cursor.execute("""
                SELECT ps.id, ps.section_heading, ps.section_description, 
                       ps.draft, ps.polished,
                       i.id as image_id, i.filename, i.path as image_path, 
                       i.alt_text, i.caption
                FROM post_section ps
                LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
                LEFT JOIN image i ON pi.image_id = i.id
                WHERE ps.post_id = %s
                ORDER BY ps.section_order
            """, (post_id,))
            sections = cursor.fetchall()
            
            # Format sections for template
            formatted_sections = []
            for section in sections:
                formatted_section = {
                    'id': section['id'],
                    'section_heading': section['section_heading'],
                    'section_description': section['section_description'],
                    'content': section['polished'] or section['draft'] or '',
                }
                
                # Add image if exists
                if section['image_path']:
                    # Use optimized image path, and handle double /static prefix
                    image_path = section['image_path']
                    if not image_path.startswith('http'):
                        # Remove double /static if present
                        if image_path.startswith('/static/'):
                            image_path = image_path  # Already has /static
                        else:
                            image_path = f"/static{image_path}"  # Add /static
                        
                        # Replace raw with optimized
                        image_path = image_path.replace('/raw/', '/optimized/').replace('.png', '.jpg')
                    
                    formatted_section['image'] = {
                        'path': image_path,
                        'alt_text': section['alt_text'] or '',
                        'caption': section['caption'] or ''
                    }
                
                formatted_sections.append(formatted_section)
            
            # Pass data to template
            return render_template('header/preview.html', 
                                 post=post, 
                                 header_image=header_image,
                                 sections=formatted_sections,
                                 post_id=post_id,
                                 blueprint_name='header')
    
    except Exception as e:
        logger.error(f"Error loading preview for post {post_id}: {e}")
        return f"Error loading preview: {str(e)}", 500

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
    """Generate multiple subtitle options based on Development tab content and selected title using LLM"""
    try:
        data = request.get_json()
        idea_seed = data.get('idea_seed', '')
        expanded_idea = data.get('expanded_idea', '')
        selected_title = data.get('selected_title', '')
        section_content = data.get('section_content', '')
        
        logger.info(f"Generating subtitles for post {post_id} with title: {selected_title[:50]}...")
        
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
        
        # Modify the task prompt to request multiple subtitle options
        task_prompt = task_prompt.replace(
            'CRITICAL: Return ONLY the subtitle text.',
            'CRITICAL: Return ONLY a JSON array of exactly 3 subtitle options. Format: ["subtitle1", "subtitle2", "subtitle3"]'
        )
        
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
        
        generated_content = llm_response['content'].strip()
        logger.info(f"LLM response: {generated_content}")
        
        # Parse JSON response for subtitles
        try:
            json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                subtitle_options = json.loads(json_str)
                
                if not isinstance(subtitle_options, list) or len(subtitle_options) != 3:
                    raise ValueError("Response must be an array of exactly 3 subtitles")
                
                # Clean up subtitles
                subtitle_options = [subtitle.strip().strip('"').strip("'") for subtitle in subtitle_options]
                selected_subtitle = subtitle_options[0]
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'subtitle_options': subtitle_options,
            'selected_index': 0
        })
        
    except Exception as e:
        logger.error(f"Error generating subtitles for post {post_id}: {e}")
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
        
        # Modify the task prompt to request multiple subtitle options
        task_prompt = task_prompt.replace(
            'CRITICAL: Return ONLY the subtitle text.',
            'CRITICAL: Return ONLY a JSON array of exactly 3 subtitle options. Format: ["subtitle1", "subtitle2", "subtitle3"]'
        )
        
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
        
        generated_content = llm_response['content'].strip()
        
        # Parse JSON response for subtitles
        try:
            json_match = re.search(r'\[.*?\]', generated_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                subtitle_options = json.loads(json_str)
                
                if not isinstance(subtitle_options, list) or len(subtitle_options) != 3:
                    raise ValueError("Response must be an array of exactly 3 subtitles")
                
                # Clean up subtitles
                subtitle_options = [subtitle.strip().strip('"').strip("'") for subtitle in subtitle_options]
                selected_subtitle = subtitle_options[0]
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return jsonify({'error': f'Failed to parse LLM response: {str(e)}'}), 500
        
        # Generate summary using the same logic as api_generate_summary
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                WHERE wsp.step_id = 62
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No prompts found for summary generation'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Prepare content for summary generation
        summary_content = f"Selected Idea: {idea_seed}\n\nExpanded Idea: {expanded_idea}\n\nSection Content:\n{section_content}"
        
        # Format the prompt with the content
        formatted_prompt = task_prompt.format(content=summary_content)
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_prompt}
        ]
        
        # Execute LLM request for summary
        logger.info(f"Calling LLM for summary generation")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            logger.error(f"LLM generation failed: {llm_response['error']}")
            return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
        
        summary = llm_response.get('content', '').strip()
        
        if not summary:
            logger.error("Empty summary response from LLM")
            return jsonify({'error': 'Empty summary response from LLM'}), 500
        
        # Generate slug from the selected title
        slug = slugify(title_options[0] if title_options else "default-title")
        
        return jsonify({
            'success': True,
            'title_options': title_options,
            'subtitle_options': subtitle_options,
            'subtitle_selected_index': 0,
            'summary': summary,
            'slug': slug
        })
        
    except Exception as e:
        logger.error(f"Error generating all header elements for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/save-selected-subtitle', methods=['POST'])
def api_save_selected_subtitle(post_id):
    """Save the selected subtitle and subtitle options to database"""
    try:
        data = request.get_json()
        subtitle = data.get('subtitle', '')
        subtitle_index = data.get('subtitle_index', 0)
        
        logger.info(f"Saving selected subtitle for post {post_id}: {subtitle[:50]}...")
        
        with db_manager.get_cursor() as cursor:
            # Update post table with selected subtitle
            cursor.execute("""
                UPDATE post 
                SET subtitle = %s, updated_at = NOW()
                WHERE id = %s
            """, (subtitle, post_id))
            
            cursor.connection.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error saving selected subtitle for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-subtitles', methods=['GET'])
def api_get_subtitles(post_id):
    """Get existing subtitles from database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT subtitle
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'success': True, 'subtitle_options': [], 'selected_index': 0})
            
            subtitle = result.get('subtitle', '')
            
            if subtitle:
                # For now, return a single subtitle as the first option
                # In the future, we could store subtitle_options in a separate field
                return jsonify({
                    'success': True,
                    'subtitle_options': [subtitle],
                    'selected_index': 0
                })
            else:
                return jsonify({'success': True, 'subtitle_options': [], 'selected_index': 0})
        
    except Exception as e:
        logger.error(f"Error getting subtitles for post {post_id}: {e}")
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

@bp.route('/api/posts/<int:post_id>/generate-seo-meta', methods=['POST'])
def api_generate_seo_meta(post_id):
    """Generate meta title, description, tags"""
    try:
        from modules.llm_service import llm_service
        
        # Get post title and summary from post table
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, summary
                FROM post 
                WHERE id = %s
            """, (post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get section titles from planning/concept/titling
            cursor.execute("""
                SELECT section_heading
                FROM post_section 
                WHERE post_id = %s 
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            # Build context for LLM
            post_title = post_data['title'] or ''
            post_summary = post_data['summary'] or ''
            
            section_titles = []
            for section in sections:
                title = section['section_heading'] or ''
                if title:
                    section_titles.append(title)
            
            sections_text = "\n".join(section_titles)
            
            # Call LLM to generate SEO metadata
            task_prompt = f"""Generate SEO metadata for this blog post:

Post Title: {post_title}

Summary: {post_summary}

Section Structure:
{sections_text}

Generate:
1. A compelling HTML meta title (max 60 characters)
2. A concise HTML meta description (max 160 characters)
3. Relevant meta tags (comma-separated, 5-8 tags)

Return in JSON format:
{{
  "meta_title": "Short compelling title",
  "meta_description": "Brief engaging description",
  "meta_tags": "tag1, tag2, tag3, tag4, tag5"
}}"""
            
            # Call LLM with intercept_context
            intercept_context = {
                'post_id': post_id,
                'step_id': 66,  # SEO meta generation step
                'context_type': 'seo_meta_generation'
            }
            
            llm_response = llm_service.execute_llm_request(
                provider='ollama',
                model='llama3.2:latest',
                messages=[{'role': 'user', 'content': task_prompt}],
                intercept_context=intercept_context
            )
            
            if 'error' in llm_response:
                logger.error(f"LLM call failed: {llm_response}")
                return jsonify({'error': 'Failed to generate SEO metadata'}), 500
            
            content = llm_response.get('content', '')
            
            logger.info(f"LLM response content: {content}")
            
            # Parse JSON response
            import re
            import json
            
            # Try to extract JSON from code blocks first
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
            if not json_match:
                # Fallback: try to find JSON without code blocks
                json_match = re.search(r'\{[\s\S]*\}', content)
            
            if json_match:
                json_text = json_match.group(1) if json_match.lastindex else json_match.group(0)
                # Clean up the JSON text
                json_text = json_text.strip()
                try:
                    seo_data = json.loads(json_text)
                    
                    meta_title = seo_data.get('meta_title', '')
                    meta_description = seo_data.get('meta_description', '')
                    meta_tags = seo_data.get('meta_tags', '')
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}, text: {repr(json_text)}")
                    meta_title = ""
                    meta_description = ""
                    meta_tags = ""
            else:
                logger.error(f"Failed to find JSON in LLM response: {content}")
                # Fallback if JSON parsing fails
                meta_title = ""
                meta_description = ""
                meta_tags = ""
            
            # Get header image path for OG image
            cursor.execute("""
                SELECT i.path 
                FROM post p
                JOIN image i ON p.header_image_id = i.id
                WHERE p.id = %s
            """, (post_id,))
            
            image_result = cursor.fetchone()
            meta_image = f"https://clan.com{image_result['path']}" if image_result and image_result['path'] else "https://clan.com/images/default-scottish-heritage.jpg"
            
            # Save to database
            cursor.execute("""
                UPDATE post 
                SET meta_title = %s,
                    meta_description = %s,
                    meta_tags = %s,
                    meta_image = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (meta_title, meta_description, meta_tags, meta_image, post_id))
            
            return jsonify({
                'success': True,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'meta_tags': meta_tags,
                'meta_image': meta_image,
                'meta_type': 'article',
                'meta_site_name': 'Clan.com Blog'
            })
            
    except Exception as e:
        logger.error(f"Error generating SEO meta: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-meta-data', methods=['GET'])
def api_get_meta_data(post_id):
    """Get current meta data for post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT meta_title, meta_description, meta_tags, 
                       meta_image, meta_type, meta_site_name
                FROM post 
                WHERE id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'meta_title': result['meta_title'] or '',
                'meta_description': result['meta_description'] or '',
                'meta_tags': result['meta_tags'] or '',
                'meta_image': result['meta_image'] or '',
                'meta_type': result['meta_type'] or 'article',
                'meta_site_name': result['meta_site_name'] or 'Clan.com Blog'
            })
            
    except Exception as e:
        logger.error(f"Error getting meta data: {e}")
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

@bp.route('/api/posts/<int:post_id>/generate-summary', methods=['POST'])
def api_generate_summary(post_id):
    """Generate summary for a post using LLM"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({'error': 'No content provided'}), 400
        
        # Get prompts from database for step 62 (Summary Generation)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                WHERE wsp.step_id = 62
            """)
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Summary generation prompts not found'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Use LLM service to generate summary
        llm_service = LLMService()
        
        # Format the prompt with the content
        formatted_prompt = task_prompt.format(content=content)
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_prompt}
        ]
        
        # Generate summary using LLM
        try:
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                raise Exception("LLM failed")
            
            summary = llm_response.get('content', '').strip()
            
            if not summary:
                raise Exception("Empty response")
                
        except Exception as e:
            logger.error(f"LLM service error: {e}")
            # NO FALLBACK - fail cleanly instead of generating generic fluff
            return jsonify({'error': f'LLM generation failed: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'summary': summary.strip()
        })
        
    except Exception as e:
        logger.error(f"Error generating summary for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-summary', methods=['GET'])
def api_get_summary(post_id):
    """Get summary from post table"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT summary FROM post WHERE id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'summary': result.get('summary', '')
            })
            
    except Exception as e:
        logger.error(f"Error getting summary for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/save-summary', methods=['POST'])
def api_save_summary(post_id):
    """Save summary to post table"""
    try:
        data = request.get_json()
        summary = data.get('summary', '')
        
        if not summary:
            return jsonify({'error': 'No summary provided'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update post table with summary
            cursor.execute("""
                UPDATE post 
                SET summary = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (summary, post_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error saving summary for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-slug', methods=['POST'])
def api_generate_slug(post_id):
    """Generate slug from selected title using Python slugify"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get the selected title from the post
            cursor.execute("""
                SELECT title FROM post WHERE id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            title = result.get('title', '')
            if not title:
                return jsonify({'error': 'No title found to generate slug from'}), 400
            
            # Generate slug from title using Python slugify
            generated_slug = slugify(title)
            
            return jsonify({
                'success': True,
                'slug': generated_slug
            })
            
    except Exception as e:
        logger.error(f"Error generating slug for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-slug', methods=['GET'])
def api_get_slug(post_id):
    """Get slug from post table"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT slug FROM post WHERE id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'slug': result.get('slug', '')
            })
            
    except Exception as e:
        logger.error(f"Error getting slug for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/save-slug', methods=['POST'])
def api_save_slug(post_id):
    """Save slug to post table"""
    try:
        data = request.get_json()
        slug = data.get('slug', '')
        
        if not slug:
            return jsonify({'error': 'No slug provided'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update post table with slug
            cursor.execute("""
                UPDATE post 
                SET slug = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (slug, post_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Post not found'}), 404
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error saving slug for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/compile-header-prompt', methods=['POST'])
def api_compile_header_prompt(post_id):
    """Compile all section image prompts into a single header prompt using LLM"""
    try:
        # Get the selected model from request data
        data = request.get_json() or {}
        selected_model = data.get('model', 'dall-e-3')
        with db_manager.get_cursor() as cursor:
            # Get all section image prompts for this post from post_development.sections JSON
            cursor.execute("""
                SELECT sections FROM post_development 
                WHERE post_id = %s AND sections IS NOT NULL
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result or not result['sections']:
                return jsonify({'error': 'No section data found'}), 404
            
            try:
                sections_data = json.loads(result['sections'])
                if isinstance(sections_data, dict) and 'sections' in sections_data:
                    sections_list = sections_data['sections']
                elif isinstance(sections_data, list):
                    sections_list = sections_data
                else:
                    return jsonify({'error': 'Invalid sections format'}), 404
            except (json.JSONDecodeError, TypeError) as e:
                return jsonify({'error': f'Failed to parse sections: {str(e)}'}), 404
            
            # Extract image prompts from sections
            sections_with_prompts = []
            for section in sections_list:
                if section.get('image_prompts') and isinstance(section['image_prompts'], dict):
                    image_prompt = section['image_prompts'].get('image_prompt', '')
                    if image_prompt:
                        sections_with_prompts.append({
                            'section_order': section.get('index', 0),
                            'image_prompts': image_prompt
                        })
            
            if not sections_with_prompts:
                return jsonify({'error': 'No section image prompts found'}), 404
            
            # Get prompts from database for header compilation (step 64)
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                WHERE wsp.step_id = 64
            """)
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Header prompt compilation prompts not found'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
            
            # Format section prompts for LLM
            section_prompts_text = ""
            for section in sections_with_prompts:
                section_prompts_text += f"Section {section['section_order']}: {section['image_prompts']}\n\n"
            
            # Determine style guidelines based on selected model
            style_guidelines = ""
            if selected_model == 'dall-e-3':
                style_guidelines = "Use 'photorealistic' style with brushstrokes fading to white edges"
            elif selected_model == 'sdxl':
                style_guidelines = "Use 'inkwash and watercolour' style with brushstrokes fading to white edges"
            else:
                style_guidelines = "Use 'photorealistic' style with brushstrokes fading to white edges"  # Default
            
            # Use LLM service to compile prompts
            llm_service = LLMService()
            
            # Format the prompt with the section prompts and style guidelines
            formatted_prompt = task_prompt.format(
                section_prompts=section_prompts_text.strip(),
                style_guidelines=style_guidelines,
                model=selected_model
            )
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_prompt}
            ]
            
            # Generate compiled prompt using LLM
            try:
                llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                
                if 'error' in llm_response:
                    logger.error(f"LLM compilation failed: {llm_response['error']}")
                    raise Exception("LLM failed")
                
                compiled_prompt = llm_response.get('content', '').strip()
                
                if not compiled_prompt:
                    raise Exception("Empty response")
                    
                # Ensure brushstrokes fading to white edges is included
                if "brushstrokes fading to white edges" not in compiled_prompt.lower():
                    compiled_prompt += " with brushstrokes fading to white edges"
                    
            except Exception as e:
                logger.error(f"LLM service error: {e}")
                return jsonify({'error': f'LLM compilation failed: {str(e)}'}), 500
            
            return jsonify({
                'success': True,
                'compiled_prompt': compiled_prompt,
                'source_sections': len(sections_with_prompts)
            })
            
    except Exception as e:
        logger.error(f"Error compiling header prompt for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/prompt-assembly-data', methods=['GET'])
def api_get_prompt_assembly_data(post_id):
    """Get system/task prompts and section data for Prompt Assembly display"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get system and task prompts for header compilation (step 64)
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
                return jsonify({'error': 'Header prompt compilation prompts not found'}), 404
            
            # Get section image prompts from post_section table (correct source)
            cursor.execute("""
                SELECT 
                    section_order,
                    section_heading,
                    image_prompts
                FROM post_section 
                WHERE post_id = %s 
                AND image_prompts IS NOT NULL
                ORDER BY section_order
            """, (post_id,))
            sections_result = cursor.fetchall()
            
            sections_with_prompts = []
            if sections_result:
                for section in sections_result:
                    # Handle both string and dict formats for image_prompts
                    prompt_data = section['image_prompts']
                    image_prompt = ''
                    
                    if isinstance(prompt_data, str):
                        try:
                            prompt_dict = json.loads(prompt_data)
                            if isinstance(prompt_dict, dict):
                                image_prompt = prompt_dict.get('image_prompt', '')
                        except (json.JSONDecodeError, TypeError):
                            image_prompt = prompt_data.strip()
                    elif isinstance(prompt_data, dict):
                        image_prompt = prompt_data.get('image_prompt', '')
                    
                    if image_prompt:
                        sections_with_prompts.append({
                            'section_order': section['section_order'],
                            'section_title': section['section_heading'],
                            'image_prompt': image_prompt
                        })
            
            return jsonify({
                'success': True,
                'system_prompt': prompt_result.get('system_prompt', ''),
                'task_prompt': prompt_result.get('task_prompt', ''),
                'sections': sections_with_prompts
            })
            
    except Exception as e:
        logger.error(f"Error getting prompt assembly data for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/model-specs', methods=['GET'])
def header_get_model_specs():
    """Get model specifications for header imaging (shared with imaging blueprint)"""
    try:
        # Reuse the imaging blueprint's model specs endpoint
        from blueprints.imaging import imaging_get_model_specs
        return imaging_get_model_specs()
    except Exception as e:
        logger.error(f"Error getting model specs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/model-selection', methods=['GET', 'POST'])
def header_model_selection():
    """Get or save model selection configuration (shared with imaging blueprint)"""
    try:
        # Reuse the imaging blueprint's model selection endpoint
        from blueprints.imaging import imaging_model_selection
        return imaging_model_selection()
    except Exception as e:
        logger.error(f"Error with model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-header-image', methods=['POST'])
def api_generate_header_image(post_id):
    """Generate header image with custom dimensions and automatic watermarking using model-aware renderers"""
    try:
        import time
        from modules.prompt_service import prompt_service
        
        data = request.get_json()
        model_name = data.get('model_name', 'dall-e-3')
        parameters = data.get('parameters', {})
        use_renderer = data.get('use_renderer', True)  # Feature flag
        
        # Get rendered prompt using the new system
        if use_renderer:
            # For header images, we need to compile a collage prompt from all sections
            rendered_prompt, debug_info = prompt_service.render_header_prompt_for_model(
                post_id, model_name, use_override=True
            )
            
            if not rendered_prompt:
                return jsonify({'error': 'No sections available to create header prompt'}), 400
            
            image_prompt = rendered_prompt
        else:
            # Fallback to original prompt from request
            image_prompt = data.get('image_prompt', '')
            debug_info = {'source': 'fallback', 'model_key': model_name}
        
        if not image_prompt:
            return jsonify({'error': 'No image prompt provided'}), 400
        
        # Import imaging functions
        from blueprints.imaging import imaging_generate_dalle_image, imaging_generate_sdxl_image, optimize_image_with_watermark
        
        # Set custom dimensions for header image
        if model_name == 'dall-e-3':
            # DALL-E uses predefined sizes, closest to 2358x1048 is 1792x1024
            parameters['size'] = '1792x1024'
            # Fix quality parameter for DALL-E (must be string, not number)
            if 'quality' in parameters and isinstance(parameters['quality'], int):
                parameters['quality'] = 'hd' if parameters['quality'] > 50 else 'standard'
            else:
                parameters['quality'] = 'standard'
            # Set style parameter
            parameters['style'] = 'natural'
        else:
            # SDXL can use custom dimensions
            parameters['width'] = 2358
            parameters['height'] = 1048
        
        # Start timing
        start_time = time.time()
        
        # Generate raw image
        if model_name == 'dall-e-3':
            result = imaging_generate_dalle_image(image_prompt, post_id, 'header', parameters)
        elif model_name == 'gpt-image-1':
            result = imaging_generate_gpt_image_1(image_prompt, post_id, 'header', parameters)
        else:
            # For SDXL, use a special section_id for headers (use post_id as section_id)
            result = imaging_generate_sdxl_image(image_prompt, post_id, post_id, parameters)
        
        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        if not result.get('success'):
            # Log failed generation event
            prompt_service.log_generation_event(
                post_id=post_id,
                section_id=None,  # Header images don't have section_id
                model_key=model_name,
                params=parameters,
                prompt_text=image_prompt,
                rendered_prompt=image_prompt,
                result_path='',
                success=False,
                error_message=result.get('error', 'Image generation failed'),
                generation_time_ms=generation_time_ms
            )
            return jsonify({'error': result.get('error', 'Image generation failed')}), 500
        
        # Skip watermarking/optimization - that's a separate stage
        # watermark_result = optimize_image_with_watermark(post_id, 'header', parameters)
        watermark_result = {'success': True, 'optimized_path': result.get('image_path')}
        
        # Create or update image table record
        with db_manager.get_cursor() as cursor:
            # Check if header image already exists
            cursor.execute("""
                SELECT header_image_id FROM post WHERE id = %s
            """, (post_id,))
            
            existing_image_id = cursor.fetchone()
            
            # Get the new optimized path
            new_path = watermark_result.get('optimized_path', result.get('image_path'))
            
            if existing_image_id and existing_image_id['header_image_id']:
                # Delete any other image records with the same path to avoid conflict
                cursor.execute("""
                    DELETE FROM image WHERE path = %s AND id != %s
                """, (new_path, existing_image_id['header_image_id']))
                
                # Update existing image record
                cursor.execute("""
                    UPDATE image 
                    SET filename = %s, original_filename = %s, path = %s, 
                        image_prompt = %s, alt_text = %s, caption = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    'header.jpg',
                    'original_header.png', 
                    new_path,
                    image_prompt,
                    'Header image for blog post',
                    'Generated header image',
                    existing_image_id['header_image_id']
                ))
                
                image_id = existing_image_id['header_image_id']
            else:
                # Create new image record
                cursor.execute("""
                    INSERT INTO image (filename, original_filename, path, image_prompt, alt_text, caption)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    'header.jpg',
                    'original_header.png', 
                    watermark_result.get('optimized_path', result.get('image_path')),
                    image_prompt,
                    'Header image for blog post',
                    'Generated header image'
                ))
                
                image_id = cursor.fetchone()['id']
                
                # Update post table with header image reference
                cursor.execute("""
                    UPDATE post 
                    SET header_image_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (image_id, post_id))
            
            # Log successful generation event
            prompt_service.log_generation_event(
                post_id=post_id,
                section_id=None,  # Header images don't have section_id
                model_key=model_name,
                params=parameters,
                prompt_text=image_prompt,
                rendered_prompt=image_prompt,
                result_path=watermark_result.get('optimized_path', result.get('image_path')),
                success=True,
                generation_time_ms=generation_time_ms
            )
            
            return jsonify({
                'success': True,
                'image_id': image_id,
                'raw_path': result.get('image_path'),
                'optimized_path': watermark_result.get('optimized_path', result.get('image_path')),
                'dimensions': {'width': 2358, 'height': 1048},
                'debug_info': debug_info,
                'generation_time_ms': generation_time_ms
            })
            
    except Exception as e:
        logger.error(f"Error generating header image for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-header-image', methods=['GET'])
def api_get_header_image(post_id):
    """Get existing header image from database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT i.id, i.filename, i.path, 
                       i.alt_text, i.caption, i.image_prompt
                FROM post p
                JOIN image i ON p.header_image_id = i.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No header image found'}), 404
            
            return jsonify({
                'success': True,
                'image_id': result['id'],
                'filename': result['filename'],
                'file_path': result['path'],
                'alt_text': result['alt_text'],
                'caption': result['caption'],
                'image_prompt': result['image_prompt']
            })
            
    except Exception as e:
        logger.error(f"Error getting header image for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-image-details', methods=['POST'])
def api_generate_image_details(post_id):
    """Generate caption, alt text, and title for header image using LLM"""
    try:
        # Get the image prompt from the database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT i.image_prompt 
                FROM post p
                JOIN image i ON p.header_image_id = i.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result or not result['image_prompt']:
                return jsonify({'error': 'No header image found or no image prompt available'}), 404
            
            image_prompt = result['image_prompt']
        
        # Get prompts from database for image details generation (step 65)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    sp.system_prompt,
                    tp.prompt_text as task_prompt
                FROM workflow_step_prompt wsp
                JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                WHERE wsp.step_id = 65
            """)
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Image details generation prompts not found'}), 404
            
            system_prompt = result.get('system_prompt', '')
            task_prompt = result.get('task_prompt', '')
        
        # Use LLM service to generate details
        llm_service = LLMService()
        
        # Format the prompt with the image prompt
        formatted_prompt = task_prompt.format(image_prompt=image_prompt)
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_prompt}
        ]
        
        # Generate details using LLM
        try:
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                logger.error(f"LLM generation failed: {llm_response['error']}")
                raise Exception("LLM failed")
            
            details_text = llm_response.get('content', '').strip()
            
            if not details_text:
                raise Exception("Empty response")
            
            # Parse JSON response - clean up the text first
            import json
            import re
            
            # Try to extract JSON from the response (handle cases where LLM adds extra text)
            json_match = re.search(r'\{[\s\S]*\}', details_text)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = details_text
            
            # Remove any extra escaping and clean up
            json_text = json_text.replace('\\\\', '\\').replace('\\"', '"')
            
            # Try to parse
            try:
                details_json = json.loads(json_text)
                caption = details_json.get('caption', '')
                alt_text = details_json.get('alt_text', '')
                title = details_json.get('title', '')
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {je}, text: {repr(json_text)}")
                raise je
                
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing LLM response: {e}, text: {repr(details_text)}")
            # Fallback to simple generation based on image prompt
            caption = f"Header image collage"
            alt_text = f"Blog header image collage featuring multiple visual elements"
            title = "Blog Header Image"
        
        # Auto-save to database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE image 
                SET caption = %s, alt_text = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT header_image_id FROM post WHERE id = %s
                )
            """, (caption, alt_text, post_id))
        
        return jsonify({
            'success': True,
            'caption': caption,
            'alt_text': alt_text,
            'title': title
        })
        
    except Exception as e:
        logger.error(f"Error generating image details for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/save-image-details', methods=['POST'])
def api_save_image_details(post_id):
    """Save image details to database"""
    try:
        data = request.get_json()
        caption = data.get('caption', '')
        alt_text = data.get('alt_text', '')
        title = data.get('title', '')
        
        with db_manager.get_cursor() as cursor:
            # Update image table with details
            cursor.execute("""
                UPDATE image 
                SET caption = %s, alt_text = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT header_image_id FROM post WHERE id = %s
                )
            """, (caption, alt_text, post_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'No header image found to update'}), 404
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error saving image details for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/optimize-header-image', methods=['POST'])
def api_optimize_header_image(post_id):
    """Optimize header image with watermark"""
    try:
        # Import the optimization function
        from blueprints.imaging import optimize_image_with_watermark
        
        # Get parameters from request (optional)
        params = request.get_json() or {}
        
        # Optimize the header image
        result = optimize_image_with_watermark(post_id, 'header', params)
        
        if result['success']:
            return jsonify({
                'success': True,
                'optimized_path': result['optimized_path'],
                'message': 'Image optimized successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Optimization failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error optimizing header image for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ui/preferences/<key>', methods=['GET', 'POST'])
def api_ui_preferences(key):
    """Handle UI preferences for header stage"""
    try:
        if request.method == 'GET':
            # Get preference value
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT preference_value FROM ui_user_preferences 
                    WHERE user_id = 0 AND preference_key = %s
                """, (key,))
                result = cursor.fetchone()
                
                if result:
                    return jsonify({
                        'success': True,
                        'value': result['preference_value']
                    })
                else:
                    return jsonify({
                        'success': True,
                        'value': None
                    })
        
        elif request.method == 'POST':
            # Save preference value
            data = request.get_json()
            value = data.get('value')
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, created_at, updated_at)
                    VALUES (0, %s, %s, 'string', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, preference_key) 
                    DO UPDATE SET preference_value = %s, updated_at = CURRENT_TIMESTAMP
                """, (key, value, value))
            
            return jsonify({
                'success': True,
                'message': 'Preference saved'
            })
            
    except Exception as e:
        logger.error(f"Error handling UI preference {key}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to handle preference: {str(e)}'
        }), 500

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
                    import json
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
                            UPDATE image 
                            SET image_prompt = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (new_prompt, existing_image['header_image_id']))
                        logger.info(f"UPDATED header prompt for post {post_id} in image {existing_image['header_image_id']}")
                    else:
                        # Create new image record with just the prompt
                        cursor.execute("""
                            INSERT INTO image (filename, original_filename, path, image_prompt, alt_text, caption)
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
