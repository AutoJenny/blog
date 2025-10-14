# Authoring Blueprint - Real workflow integration
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config.database import db_manager
import logging
import json
import os
import requests
import re
from bs4 import BeautifulSoup

# Import micro-modules
from blueprints.authoring_api_sections import api_get_sections as sections_api_func, api_get_section as section_api_func

logger = logging.getLogger(__name__)

def generate_dalle_image(image_prompt, post_id, section_id):
    """Generate image using DALL-E API"""
    try:
        # Load OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not found in environment'}
        
        # Call DALL-E API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'dall-e-3',
            'prompt': image_prompt,
            'n': 1,
            'size': '1792x1024',
            'quality': 'standard',
            'style': 'natural'
        }
        
        response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'DALL-E API error: {response.status_code} - {response.text}'}
        
        result = response.json()
        
        if 'data' not in result or not result['data']:
            return {'success': False, 'error': 'No image data returned from DALL-E'}
        
        # Download the image
        image_url = result['data'][0]['url']
        image_response = requests.get(image_url, timeout=30)
        
        if image_response.status_code != 200:
            return {'success': False, 'error': f'Failed to download image: {image_response.status_code}'}
        
        # Create directory structure
        image_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
        os.makedirs(image_dir, exist_ok=True)
        
        # Save image with section-based naming
        image_path = f"{image_dir}/{section_id}.png"
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png",
            'local_path': image_path
        }
        
    except Exception as e:
        logger.error(f"DALL-E generation error: {str(e)}")
        return {'success': False, 'error': str(e)}
    """
    Process LLM HTML content to create both draft (HTML) and section_text (plain text) versions.
    
    Args:
        html_content (str): Raw HTML content from LLM
        
    Returns:
        tuple: (draft_html, section_text_plain)
    """
    try:
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract the h2 heading (if present)
        h2_tag = soup.find('h2')
        section_title = h2_tag.get_text().strip() if h2_tag else ""
        
        # Extract all paragraph content
        p_tags = soup.find_all('p')
        paragraph_texts = [p.get_text().strip() for p in p_tags if p.get_text().strip()]
        
        # Create plain text version by joining paragraphs with double newlines
        plain_text = '\n\n'.join(paragraph_texts)
        
        # Trim any leading/trailing whitespace from the final result
        plain_text = plain_text.strip()
        
        # Clean up the HTML content (keep original structure)
        draft_html = html_content.strip()
        
        logger.info(f"Processed HTML content: Title='{section_title}', Paragraphs={len(paragraph_texts)}, Plain text length={len(plain_text)}")
        
        return draft_html, plain_text
        
    except Exception as e:
        logger.error(f"Error processing HTML content: {e}")
        # Fallback: return original content for both fields
        return html_content, html_content

def build_avoid_topics_text(topic_allocation, current_section_data):
    """Build the avoid topics text from topic allocation data"""
    if not topic_allocation or not topic_allocation.get('allocations'):
        return 'No avoid topics available'
    
    avoid_sections = []
    current_section_id = current_section_data.get('section_id', '')
    
    for allocation in topic_allocation['allocations']:
        # Skip the current section
        if allocation.get('section_id') == current_section_id:
            continue
            
        section_theme = allocation.get('section_theme', 'Untitled Section')
        topics = allocation.get('topics', [])
        
        if topics:
            topics_text = ', '.join(topics)
            avoid_sections.append(f"{section_theme}: {topics_text}")
    
    return '\n'.join(avoid_sections) if avoid_sections else 'No avoid topics available'

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'name': 'OpenAI',
                'base_url': 'https://api.openai.com/v1',
                'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
            },
            'ollama': {
                'name': 'Ollama',
                'base_url': 'http://localhost:11434',
                'models': ['llama2', 'codellama', 'mistral']
            }
        }
    
    def get_available_models(self, provider='openai'):
        """Get available models for a provider."""
        try:
            if provider == 'ollama':
                response = requests.get(f"{self.providers[provider]['base_url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = [model['name'] for model in response.json().get('models', [])]
                    return models
            return self.providers.get(provider, {}).get('models', [])
        except Exception as e:
            logger.error(f"Error getting models for {provider}: {e}")
            return []
    
    def execute_llm_request(self, provider, model, messages, api_key=None):
        """Execute LLM request."""
        try:
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key}',
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

bp = Blueprint('authoring', __name__, url_prefix='/authoring')

@bp.route('/posts/<int:post_id>')
def authoring_post_overview(post_id):
    """Authoring overview for a specific post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/post_overview.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Authoring Overview",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_post_overview: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/drafting')
def authoring_sections_drafting(post_id):
    """Drafting - generate initial content for each section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/drafting.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Drafting",
                                 blueprint_name='authoring',
                                 currentStage='authoring',
                                 currentSubstage='drafting')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_drafting: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/author-first-drafts')
def authoring_sections_author_first_drafts_deprecated(post_id):
    """DEPRECATED: Redirect to new drafting route"""
    return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))

@bp.route('/posts/<int:post_id>/sections')
def authoring_sections(post_id):
    """Sections authoring phase - redirect to author-first-drafts"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Redirect to the proper drafting route
            return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
            
    except Exception as e:
        logger.error(f"Error in authoring_sections: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/ideas_to_include')
def authoring_sections_ideas_to_include(post_id):
    """Ideas to include step - Step 43"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/ideas_to_include.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Ideas to Include",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_ideas_to_include: {e}")
        return f"Error: {e}", 500


@bp.route('/posts/<int:post_id>/sections/fix_language')
def authoring_sections_fix_language(post_id):
    """FIX language step - Step 49"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/fix_language.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Fix Language",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_fix_language: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/image_concepts')
def authoring_sections_image_concepts(post_id):
    """Image concepts step - Step 53"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/image_concepts.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Concepts",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_concepts: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/image_prompts')
def authoring_sections_image_prompts(post_id):
    """Image prompts step - Step 54"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get the image prompts prompt from database
            cursor.execute("""
                SELECT name, prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Prompts Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            # Get style guidelines from image_format table
            cursor.execute("""
                SELECT extra_settings::jsonb->>'style_guidelines' as style_guidelines
                FROM image_format 
                WHERE id = 2
            """)
            style_data = cursor.fetchone()
            
            # Extract prompt data
            prompt_name = prompt_data['name'] if prompt_data else 'Image Prompts Generation'
            system_prompt = prompt_data['system_prompt'] if prompt_data else ''
            user_prompt = prompt_data['prompt_text'] if prompt_data else ''
            style_guidelines = style_data['style_guidelines'] if style_data else ''
            
            return render_template('authoring/sections/image_prompts.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Prompts",
                                 blueprint_name='authoring',
                                 prompt_name=prompt_name,
                                 system_prompt=system_prompt,
                                 user_prompt=user_prompt,
                                 style_guidelines=style_guidelines)
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_prompts: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/image_captions')
def authoring_sections_image_captions(post_id):
    """Image captions step - Step 58"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/image_captions.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Captions",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_captions: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/image_generation')
def authoring_sections_image_generation(post_id):
    """Image generation step - Step 59"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/image_generation.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Generation",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_generation: {e}")
        return f"Error: {e}", 500

@bp.route('/test-sections')
def test_sections():
    """Test page for sections loading"""
    return render_template('test_authoring_sections.html', blueprint_name='authoring')

# API endpoints for section data
@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get all sections for a post from post_section table"""
    return sections_api_func(post_id)

@bp.route('/api/posts/<int:post_id>/sections/<section_id>')
def api_get_section_detail(post_id, section_id):
    """Get details for a specific section"""
    return section_api_func(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>', methods=['PUT'])
def api_save_section_content(post_id, section_id):
    """Save section content (draft, polished, etc.)"""
    try:
        data = request.get_json()
        
        with db_manager.get_cursor() as cursor:
            # Update the appropriate field based on content type
            update_fields = []
            update_values = []
            
            if 'draft_content' in data:
                update_fields.append('draft = %s')
                update_values.append(data['draft_content'])
            
            if 'polished_content' in data:
                update_fields.append('polished = %s')
                update_values.append(data['polished_content'])
            
            if 'ideas_to_include' in data:
                update_fields.append('ideas_to_include = %s')
                update_values.append(data['ideas_to_include'])
            
            if 'status' in data:
                update_fields.append('status = %s')
                update_values.append(data['status'])
            
            if not update_fields:
                return jsonify({
                    'success': False,
                    'error': 'No content to save'
                }), 400
            
            # Add post_id and section_id to values
            update_values.extend([post_id, section_id])
            
            cursor.execute(f"""
                UPDATE post_section 
                SET {', '.join(update_fields)}
                WHERE post_id = %s AND id = %s
            """, update_values)
            
            if cursor.rowcount == 0:
                return jsonify({
                    'success': False,
                    'error': 'Section not found'
                }), 404
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section content saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error in api_save_section_content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate', methods=['POST'])
def api_generate_section_draft(post_id, section_id):
    """Generate draft content for a specific section using LLM"""
    try:
        with db_manager.get_cursor() as cursor:
            # First try post_section table (only if section_id is numeric)
            section = None
            if section_id.isdigit():
                cursor.execute("""
                    SELECT id, section_order, section_heading, section_description, 
                           status, draft, polished
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
                                'status': 'draft',
                                'draft': None,
                                'polished': None
                            }
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")
            
            if not section:
                return jsonify({
                    'success': False,
                    'error': 'Section not found'
                }), 404
            
            # Get post details and sections data from planning
            cursor.execute("""
                SELECT title, summary
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({
                    'success': False,
                    'error': 'Post not found'
                }), 404
            
            # Get sections data from post_development
            cursor.execute("""
                SELECT expanded_idea, sections, topic_allocation
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            dev_data = cursor.fetchone()
            
            if not dev_data or not dev_data['expanded_idea']:
                return jsonify({
                    'success': False,
                    'error': 'No expanded idea found. Please complete the planning phase first.'
                }), 400
            
            # Parse sections data to get current section details
            sections_data = []
            if dev_data['sections']:
                try:
                    sections_json = json.loads(dev_data['sections'])
                    # Handle nested structure: sections_json.sections
                    if isinstance(sections_json, dict) and 'sections' in sections_json:
                        sections_data = sections_json['sections']
                    elif isinstance(sections_json, list):
                        sections_data = sections_json
                except:
                    sections_data = []
            
            # Parse topic allocation data
            topic_allocation = None
            if dev_data['topic_allocation']:
                try:
                    # Check if it's already a dict (parsed by DB driver) or needs JSON parsing
                    if isinstance(dev_data['topic_allocation'], dict):
                        topic_allocation = dev_data['topic_allocation']
                    else:
                        topic_allocation = json.loads(dev_data['topic_allocation'])
                except Exception as e:
                    logger.error(f"Error parsing topic_allocation: {e}")
                    topic_allocation = None
            
            # Find current section in sections data
            current_section_data = None
            for section_data in sections_data:
                if section_data.get('order') == section['section_order']:
                    current_section_data = section_data
                    break
            
            if not current_section_data:
                # Get topics from idea_scope and assign to section based on semantic matching
                topics_for_section = []
                if dev_data and dev_data.get('idea_scope'):
                    try:
                        idea_scope = json.loads(dev_data['idea_scope'])
                        all_topics = idea_scope.get('generated_topics', [])
                        
                        # Improved semantic matching based on section heading/description
                        section_text = f"{section['section_heading']} {section['section_description'] or ''}".lower()
                        
                        # Define section-specific keywords for better matching
                        section_keywords = {
                            1: ['samhain', 'celtic', 'ancient', 'roots', 'ceres', 'festival'],
                            2: ['agriculture', 'crop', 'farming', 'land', 'bounty', 'rotation'],
                            3: ['celebration', 'tradition', 'timeless', 'seasonal', 'hogmanay'],
                            4: ['symbolism', 'mythology', 'autumn', 'folklore', 'symbolic'],
                            5: ['farmer', 'knowledge', 'folk', 'remedy', 'medicine', 'healing'],
                            6: ['christianity', 'christian', 'religion', 'church', 'reformation'],
                            7: ['women', 'female', 'gender', 'role', 'folk']
                        }
                        
                        # Get keywords for this section
                        keywords = section_keywords.get(section['section_order'], [])
                        
                        for topic in all_topics:
                            topic_title = topic.get('title', '').lower()
                            # Match topics that contain section-specific keywords
                            if any(keyword in topic_title for keyword in keywords):
                                topics_for_section.append(topic['title'])
                        
                        # Limit to 3-5 topics per section
                        topics_for_section = topics_for_section[:5]
                            
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # If parsing fails, use empty list
                        topics_for_section = []
                
                # Use section data from post_section table as fallback
                current_section_data = {
                    'title': section['section_heading'],
                    'subtitle': section['section_description'] or '',
                    'topics': topics_for_section,
                    'order': section['section_order']
                }
            
            # Get all other sections to build "avoid topics" list
            avoid_topics = []
            for section_data in sections_data:
                if section_data.get('order') != section['section_order']:
                    topics = section_data.get('topics', [])
                    if isinstance(topics, list):
                        avoid_topics.extend(topics)
            
            # Get Section Drafting prompt
            cursor.execute("""
                SELECT system_prompt, prompt_text
                FROM llm_prompt
                WHERE name = 'Section Drafting'
            """)
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({
                    'success': False,
                    'error': 'Section Drafting prompt not found'
                }), 500
            
            # Prepare prompt variables with rich context from actual database data
            prompt_vars = {
                'SELECTED_IDEA': dev_data.get('idea_seed', ''),
                'EXPANDED_IDEA': dev_data.get('expanded_idea', ''),
                'SECTION_TITLE': section['section_heading'],
                'SECTION_SUBTITLE': section['section_description'] or '',
                'SECTION_GROUP': current_section_data.get('section_theme', f'Section {section["section_order"]}'),
                'GROUP_SUMMARY': current_section_data.get('section_description', ''),
                'SECTION_TOPICS': ', '.join(current_section_data.get('topics', [])),
                'AVOID_SECTIONS_DETAILED': build_avoid_topics_text(topic_allocation, {'section_id': f'section_{section["section_order"]}'})
            }
            
            # Replace placeholders in prompt
            prompt_text = prompt_data['prompt_text']
            for key, value in prompt_vars.items():
                prompt_text = prompt_text.replace(f'[{key}]', str(value))
            
            # Call LLM service
            messages = [
                {'role': 'system', 'content': prompt_data['system_prompt']},
                {'role': 'user', 'content': prompt_text}
            ]
            
            # Construct the full message for debugging
            full_message = f"=== SYSTEM PROMPT ===\n{prompt_data['system_prompt']}\n\n=== USER PROMPT (with placeholders replaced) ===\n{prompt_text}\n\n=== MODEL ===\nollama: llama3.2:latest\n\n=== TEMPERATURE ===\n0.7\n\n=== MAX TOKENS ===\n2000"
            
            logger.info(f"Generating draft for section {section_id} of post {post_id}")
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in llm_response:
                return jsonify({
                    'success': False,
                    'error': f"LLM generation failed: {llm_response['error']}"
                }), 500
            
            # Process the LLM response to create both HTML and plain text versions
            def process_llm_html_content(content):
                """Process LLM content to create HTML and plain text versions"""
                # Simple implementation - just return the content as both HTML and plain text
                return content, content
            
            draft_html, section_text_plain = process_llm_html_content(llm_response['content'])
            
            # Save generated content to database
            # Extract numeric section order from section_id (e.g., "section_2" -> 2)
            if section_id.startswith('section_'):
                section_order = int(section_id.split('_')[1])
            elif section_id.isdigit():
                section_order = int(section_id)
            else:
                section_order = section.get('section_order', 1)
            
            # Try to update existing post_section record
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, polished = %s, status = 'complete'
                WHERE post_id = %s AND section_order = %s
            """, (draft_html, section_text_plain, post_id, section_order))
            
            if cursor.rowcount == 0:
                # Section not found in post_section, create a new record
                cursor.execute("""
                    INSERT INTO post_section (post_id, section_order, section_heading, section_description, draft, polished, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'complete')
                """, (post_id, section_order, section['section_heading'], section['section_description'], draft_html, section_text_plain))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'draft_content': llm_response['content'],
                'message': 'Draft generated successfully',
                'llm_message': full_message
            })
            
    except Exception as e:
        logger.error(f"Error in api_generate_section_draft: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/save-image-concepts', methods=['POST'])
def api_save_image_concepts(post_id, section_id):
    """Save image concepts for a specific section"""
    try:
        data = request.get_json()
        image_concepts = data.get('image_concepts', '')
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_section 
                SET image_concepts = %s
                WHERE post_id = %s AND id = %s
            """, (image_concepts, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image concepts saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving image concepts: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/select-concept', methods=['POST'])
def api_select_concept(post_id, section_id):
    """Save the selected image concept for a specific section"""
    try:
        data = request.get_json()
        concept_id = data.get('concept_id', '')
        
        with db_manager.get_cursor() as cursor:
            if str(section_id).isdigit():
                # Numeric section id -> update post_section
                cursor.execute(
                    """
                    UPDATE post_section 
                    SET selected_image_concept = %s
                    WHERE post_id = %s AND id = %s
                    """,
                    (concept_id, post_id, int(section_id))
                )
                cursor.connection.commit()
            else:
                # String id (e.g., section_1) -> update post_development.sections JSON
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                row = cursor.fetchone()
                if not row or not row['sections']:
                    return jsonify({'error': 'Section data not found'}), 404
                try:
                    sections_data = row['sections'] if isinstance(row['sections'], dict) else json.loads(row['sections'])
                    if isinstance(sections_data, dict) and 'sections' in sections_data:
                        sections_list = sections_data['sections']
                    elif isinstance(sections_data, list):
                        sections_list = sections_data
                    else:
                        sections_list = []
                    # Find by id
                    target = next((s for s in sections_list if s.get('id') == section_id), None)
                    if not target and section_id.startswith('section_'):
                        try:
                            idx = int(section_id.split('_')[1])
                            target = next((s for s in sections_list if s.get('index') == idx), None)
                        except Exception:
                            target = None
                    if not target:
                        return jsonify({'error': 'Section not found'}), 404
                    target['selected_image_concept'] = concept_id
                    # Persist back
                    cursor.execute(
                        """
                        UPDATE post_development 
                        SET sections = %s, updated_at = NOW()
                        WHERE post_id = %s
                        """,
                        (json.dumps(sections_data), post_id)
                    )
                    cursor.connection.commit()
                except Exception as e:
                    logger.error(f"Error updating selected_image_concept in sections JSON: {e}")
                    return jsonify({'error': 'Failed to update section selection'}), 500
            return jsonify({'success': True, 'message': 'Concept selection saved successfully'})
            
    except Exception as e:
        logger.error(f"Error saving concept selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate-image-concepts', methods=['POST'])
def api_generate_image_concepts(post_id, section_id):
    """Generate image concepts for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section data using the same logic as api_get_section
            section = None
            
            # First try post_section table (only if section_id is numeric)
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
            
            # If not found in post_section or section_id is not numeric, try post_development
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
                        
                        # Find the section by ID
                        for i, section_data in enumerate(sections_list):
                            section_id_from_data = section_data.get('id', f'section_{i+1}')
                            if section_id_from_data == section_id:
                                section_order = section_data.get('order', i+1)
                                
                                # Get section content from post_section table
                                cursor.execute("""
                                    SELECT draft, polished, status
                                    FROM post_section
                                    WHERE post_id = %s AND section_order = %s
                                """, (post_id, section_order))
                                post_section_data = cursor.fetchone()
                                
                                section = {
                                    'id': section_id_from_data,
                                    'section_order': section_order,
                                    'section_heading': section_data.get('title', f'Section {i+1}'),
                                    'section_description': section_data.get('original', ''),
                                    'status': post_section_data['status'] if post_section_data else 'draft',
                                    'draft': post_section_data['draft'] if post_section_data else None,
                                    'polished': post_section_data['polished'] if post_section_data else None,
                                    'ideas_to_include': None,
                                    'facts_to_include': None,
                                    'highlighting': None,
                                    'image_concepts': section_data.get('image_concepts'),
                                    'image_prompts': section_data.get('image_prompts'),
                                    'image_captions': section_data.get('image_captions'),
                                    'image_alt_text': section_data.get('image_alt_text'),
                                    'selected_image_concept': section_data.get('selected_image_concept')
                                }
                                break
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse sections from post_development: {e}")
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get post data for context
            cursor.execute("""
                SELECT p.id, pd.idea_seed, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get topic allocation for this section
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            topic_result = cursor.fetchone()
            
            topics = []
            if topic_result and topic_result['topic_allocation']:
                try:
                    if isinstance(topic_result['topic_allocation'], dict):
                        topic_allocation = topic_result['topic_allocation']
                    else:
                        topic_allocation = json.loads(topic_result['topic_allocation'])
                    
                    # Get topics for this section
                    section_topics = topic_allocation.get(str(section['section_order']), [])
                    topics = section_topics if isinstance(section_topics, list) else []
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
            prompt_text = prompt_text.replace('[data:topics]', '\n'.join([f'- {topic}' for topic in topics]))
            
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
                    
                    # JSON is valid, use it
                    image_concepts = raw_content
                    logger.info(f"Valid JSON generated on attempt {attempt + 1}")
                    break
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Invalid JSON on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:  # Last attempt
                        # Return error with the raw content for debugging
                        return jsonify({
                            'error': f'Failed to generate valid JSON after {max_retries} attempts. Last error: {e}',
                            'raw_content': raw_content[:500] + '...' if len(raw_content) > 500 else raw_content
                        }), 500
                    
                    # Add a more explicit instruction for the next attempt
                    messages[-1]['content'] += f"\n\nIMPORTANT: The previous response was invalid JSON. Please ensure you return ONLY a complete, valid JSON object with all required fields. Error: {e}"
            
            if not image_concepts:
                return jsonify({'error': 'Failed to generate valid JSON'}), 500
            
            # Save to database - update post_development.sections JSON
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
                    
                    # Find and update the section
                    for i, section_data in enumerate(sections_list):
                        section_id_from_data = section_data.get('id', f'section_{i+1}')
                        if section_id_from_data == section_id:
                            section_data['image_concepts'] = image_concepts
                            break
                    
                    # Update the database
                    cursor.execute("""
                        UPDATE post_development 
                        SET sections = %s
                        WHERE post_id = %s
                    """, (json.dumps(sections_data), post_id))
                    
                    cursor.connection.commit()
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Error updating sections JSON: {e}")
                    return jsonify({'error': 'Failed to update section data'}), 500
            else:
                # Fallback: try to update post_section if section_id is numeric
                if section_id.isdigit():
                    cursor.execute("""
                        UPDATE post_section 
                        SET image_concepts = %s
                        WHERE post_id = %s AND id = %s
                    """, (image_concepts, post_id, int(section_id)))
                    cursor.connection.commit()
                else:
                    return jsonify({'error': 'No section data found to update'}), 404
            
            return jsonify({
                'success': True,
                'image_concepts': image_concepts,
                'message': 'Image concepts generated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error generating image concepts: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-concepts', methods=['GET', 'PUT'])
def api_image_concepts_prompt():
    """Get or update the Image Concepts prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Concepts Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT prompt_text, system_prompt, created_at, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Concepts Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'name': 'Image Concepts Generation',
                            'prompt_text': result['prompt_text'],
                            'system_prompt': result['system_prompt'],
                            'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                            'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                        },
                        'llm_config': {
                            'provider': 'Ollama',
                            'model': 'llama3.1:8b',
                            'temperature': 0.7,
                            'max_tokens': 4000
                        }
                    })
                else:
                    return jsonify({'error': 'Image Concepts prompt not found'}), 404
                    
    except Exception as e:
        logger.error(f"Error with Image Concepts prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/section-drafting', methods=['GET', 'PUT'])
def api_section_drafting_prompt():
    """Get or update the Section Drafting prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Section Drafting'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            
            else:
                # GET method - return the prompt
                cursor.execute("""
                    SELECT name, system_prompt, prompt_text
                    FROM llm_prompt
                    WHERE name = 'Section Drafting'
                """)
                prompt = cursor.fetchone()
                
                if not prompt:
                    return jsonify({
                        'success': False,
                        'error': 'Section Drafting prompt not found'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt['name'],
                        'system_prompt': prompt['system_prompt'],
                        'prompt_text': prompt['prompt_text']
                    },
                    'llm_config': {
                        'provider': 'ollama',
                        'model': 'llama3.2:latest',
                        'temperature': 0.7,
                        'max_tokens': 2000
                    }
                })
            
    except Exception as e:
        logger.error(f"Error in api_section_drafting_prompt: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/llm/prompts/image-prompts', methods=['GET', 'PUT'])
def api_image_prompts_prompt():
    """Get or update the Image Prompts prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Prompts Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT prompt_text, system_prompt, created_at, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Prompts Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'name': 'Image Prompts Generation',
                            'prompt_text': result['prompt_text'],
                            'system_prompt': result['system_prompt'],
                            'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                            'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                        },
                        'llm_config': {
                            'provider': 'Ollama',
                            'model': 'llama3.2:latest',
                            'temperature': 0.7,
                            'max_tokens': 2000
                        }
                    })
                else:
                    return jsonify({'error': 'Image Prompts prompt not found'}), 404
                    
    except Exception as e:
        logger.error(f"Error with Image Prompts prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-captions', methods=['GET', 'PUT'])
def api_image_captions_prompt():
    """Get or update the Image Captions prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                system_prompt = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt = %s, prompt_text = %s
                    WHERE name = 'Image Captions Generation'
                """, (system_prompt, prompt_text))
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
            
            else:
                # Get the prompt
                cursor.execute("""
                    SELECT prompt_text, system_prompt, created_at, updated_at
                    FROM llm_prompt 
                    WHERE name = 'Image Captions Generation'
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'name': 'Image Captions Generation',
                            'prompt_text': result['prompt_text'],
                            'system_prompt': result['system_prompt'],
                            'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                            'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                        },
                        'llm_config': {
                            'provider': 'Ollama',
                            'model': 'llama3.2:latest',
                            'temperature': 0.7,
                            'max_tokens': 2000
                        }
                    })
                else:
                    return jsonify({'error': 'Image Captions prompt not found'}), 404
                    
    except Exception as e:
        logger.error(f"Error with Image Captions prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/prompts/image-generation', methods=['GET', 'PUT'])
def api_image_generation_prompt():
    """Get or update the image generation prompt"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'GET':
                # Get the prompt
                cursor.execute("""
                    SELECT id, name, prompt_text, description
                    FROM llm_prompt
                    WHERE name = 'Image Generation'
                """)
                prompt = cursor.fetchone()
                
                if prompt:
                    return jsonify({
                        'success': True,
                        'prompt': {
                            'id': prompt['id'],
                            'name': prompt['name'],
                            'text': prompt['prompt_text'],
                            'description': prompt['description']
                        }
                    })
                else:
                    return jsonify({'success': False, 'error': 'Prompt not found'})
            
            elif request.method == 'PUT':
                # Update the prompt
                data = request.get_json()
                prompt_text = data.get('text', '')
                
                cursor.execute("""
                    UPDATE llm_prompt
                    SET prompt_text = %s, updated_at = NOW()
                    WHERE name = 'Image Generation'
                """, (prompt_text,))
                
                return jsonify({'success': True, 'message': 'Prompt updated successfully'})
                
    except Exception as e:
        logger.error(f"Error with Image Generation prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/generate-image', methods=['POST'])
def api_generate_image(post_id, section_id):
    """Generate image for a specific section using DALL-E"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section data including image_prompts
            cursor.execute("""
                SELECT id, section_order, section_heading, image_prompts
                FROM post_section
                WHERE id = %s AND post_id = %s
            """, (section_id, post_id))
            
            section = cursor.fetchone()
            if not section:
                return jsonify({'success': False, 'error': 'Section not found'})
            
            # Parse image_prompts JSON to get the actual prompt
            image_prompts_data = json.loads(section['image_prompts']) if section['image_prompts'] else {}
            image_prompt = image_prompts_data.get('image_prompt', '')
            
            if not image_prompt:
                return jsonify({'success': False, 'error': 'No image prompt found for this section'})
            
            # Generate image using DALL-E
            dalle_result = generate_dalle_image(image_prompt, post_id, section_id)
            
            if dalle_result['success']:
                return jsonify({
                    'success': True,
                    'image_path': dalle_result['image_path'],
                    'message': 'Image generated successfully'
                })
            else:
                return jsonify({'success': False, 'error': dalle_result['error']})
                
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate-image-captions', methods=['POST'])
def api_generate_image_captions(post_id, section_id):
    """Generate image captions and alt text for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Handle both string and integer section IDs
            if section_id.isdigit():
                # Integer section ID - query post_section table
                cursor.execute("""
                    SELECT id, section_order, section_heading, section_description, 
                           draft, polished, ideas_to_include, facts_to_include,
                           highlighting, image_concepts, image_prompts, image_captions,
                           selected_image_concept
                    FROM post_section
                    WHERE post_id = %s AND id = %s
                """, (post_id, int(section_id)))
                section = cursor.fetchone()
            else:
                # String section ID - query post_development.sections JSON
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                row = cursor.fetchone()
                
                if not row or not row['sections']:
                    return jsonify({'error': 'Section not found'}), 404
                
                try:
                    sections_data = json.loads(row['sections']) if isinstance(row['sections'], str) else row['sections']
                    if isinstance(sections_data, dict) and 'sections' in sections_data:
                        sections_list = sections_data['sections']
                    elif isinstance(sections_data, list):
                        sections_list = sections_data
                    else:
                        sections_list = []
                    
                    # Find the specific section
                    section = next((s for s in sections_list if s.get('id') == section_id), None)
                    if not section:
                        # Try mapping section_1, section_2, etc. to index 1, 2, etc.
                        if section_id.startswith('section_'):
                            try:
                                section_index = int(section_id.split('_')[1])
                                section = next((s for s in sections_list if s.get('index') == section_index), None)
                            except (ValueError, IndexError):
                                pass
                    
                    if not section:
                        return jsonify({'error': 'Section not found'}), 404
                        
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Error parsing sections JSON: {e}")
                    return jsonify({'error': 'Failed to parse sections data'}), 500
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get the selected concept details (EXCLUDE the title as it's too metaphorical)
            selected_concept_text = ''
            if section.get('selected_image_concept') and section.get('image_concepts'):
                try:
                    concepts_data = json.loads(section['image_concepts'])
                    if concepts_data.get('concepts'):
                        selected_concept = next(
                            (c for c in concepts_data['concepts'] if c['concept_id'] == section['selected_image_concept']), 
                            None
                        )
                        if selected_concept:
                            # Exclude the concept_title as it's too metaphorical
                            selected_concept_text = f"{selected_concept['concept_description']}\nMood: {selected_concept['concept_mood']}\nKey Elements: {selected_concept['key_visual_elements']}"
                except Exception as e:
                    logger.error(f"Error parsing selected concept: {e}")
                    selected_concept_text = section.get('selected_image_concept', '')
            
            # Get the image captions prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Image Captions Generation'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'Image Captions prompt not found'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Use appropriate field names based on data source
            if section_id.isdigit():
                # From post_section table
                section_title = section['section_heading']
                section_description = section['section_description'] or ''
                section_content = section.get('draft', '') or ''
            else:
                # From JSON data
                section_title = section.get('title', '')
                section_description = section.get('original', '') or ''
                section_content = section.get('draft', '') or ''
            
            # Replace placeholders with actual data
            prompt_text = prompt_text.replace('[data:selected_concept]', selected_concept_text)
            prompt_text = prompt_text.replace('[SECTION_TITLE]', section_title)
            prompt_text = prompt_text.replace('[SECTION_DESCRIPTION]', section_description)
            prompt_text = prompt_text.replace('[SECTION_CONTENT]', section_content)
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            raw_content = result['content']
            
            # Parse JSON response
            try:
                # Strip markdown code blocks if present
                content = raw_content.strip()
                if content.startswith('```') and content.endswith('```'):
                    content = content[3:-3].strip()
                elif content.startswith('```json'):
                    content = content[7:-3].strip()
                elif content.startswith('```'):
                    content = content[3:-3].strip()
                
                # Extract only the JSON part (before any additional text)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    content = content[json_start:json_end]
                
                parsed_json = json.loads(content)
                
                if not isinstance(parsed_json, dict) or 'caption' not in parsed_json or 'alt_text' not in parsed_json:
                    raise ValueError("Missing 'caption' or 'alt_text' keys")
                
                if not parsed_json['caption'] or not parsed_json['caption'].strip():
                    raise ValueError("caption field is empty")
                
                if not parsed_json['alt_text'] or not parsed_json['alt_text'].strip():
                    raise ValueError("alt_text field is empty")
                
                # Save to database
                if section_id.isdigit():
                    # Integer section ID - update post_section table
                    cursor.execute("""
                        UPDATE post_section 
                        SET image_captions = %s, image_alt_text = %s
                        WHERE post_id = %s AND id = %s
                    """, (parsed_json['caption'].strip(), parsed_json['alt_text'].strip(), post_id, int(section_id)))
                else:
                    # String section ID - update post_development.sections JSON
                    cursor.execute("""
                        SELECT sections FROM post_development WHERE post_id = %s
                    """, (post_id,))
                    row = cursor.fetchone()
                    
                    if row and row['sections']:
                        try:
                            sections_data = json.loads(row['sections']) if isinstance(row['sections'], str) else row['sections']
                            if isinstance(sections_data, dict) and 'sections' in sections_data:
                                sections_list = sections_data['sections']
                            elif isinstance(sections_data, list):
                                sections_list = sections_data
                            else:
                                sections_list = []
                            
                            # Find and update the specific section
                            for section in sections_list:
                                if section.get('id') == section_id:
                                    section['image_captions'] = parsed_json['caption'].strip()
                                    section['image_alt_text'] = parsed_json['alt_text'].strip()
                                    break
                            else:
                                # Try mapping section_1, section_2, etc. to index 1, 2, etc.
                                if section_id.startswith('section_'):
                                    try:
                                        section_index = int(section_id.split('_')[1])
                                        for section in sections_list:
                                            if section.get('index') == section_index:
                                                section['image_captions'] = parsed_json['caption'].strip()
                                                section['image_alt_text'] = parsed_json['alt_text'].strip()
                                                break
                                    except (ValueError, IndexError):
                                        pass
                            
                            # Update the database
                            cursor.execute("""
                                UPDATE post_development 
                                SET sections = %s, updated_at = NOW()
                                WHERE post_id = %s
                            """, (json.dumps(sections_data), post_id))
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.error(f"Error updating sections JSON for image captions: {e}")
                            return jsonify({'error': 'Failed to update sections data'}), 500
                
                cursor.connection.commit()
                
                return jsonify({
                    'success': True,
                    'image_captions': parsed_json['caption'].strip(),
                    'image_alt_text': parsed_json['alt_text'].strip(),
                    'message': 'Image captions and alt text generated successfully'
                })
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error processing captions: {e}")
                return jsonify({
                    'error': f'Failed to process generated captions. Error: {e}',
                    'raw_content': raw_content[:500] + '...' if len(raw_content) > 500 else raw_content
                }), 500
            
    except Exception as e:
        logger.error(f"Error generating image captions: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/save-image-captions', methods=['POST'])
def api_save_image_captions(post_id, section_id):
    """Save image captions and alt text for a specific section"""
    try:
        data = request.get_json()
        image_captions = data.get('image_captions', '')
        image_alt_text = data.get('image_alt_text', '')
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_section 
                SET image_captions = %s, image_alt_text = %s
                WHERE post_id = %s AND id = %s
            """, (image_captions, image_alt_text, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image captions and alt text saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving image captions: {e}")
        return jsonify({'error': str(e)}), 500

# ===============================
# UI Preferences (DB-backed state)
# ===============================

@bp.route('/api/ui/preferences/<pref_key>', methods=['GET', 'POST'])
def authoring_ui_preferences(pref_key):
    """Get/Set UI preferences (accordion states, etc.) in ui_user_preferences.
    Note: No auth; store under user_id=0 and is_global=true to respect no-login rule.
    """
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'GET':
                cursor.execute(
                    """
                    SELECT preference_value
                    FROM ui_user_preferences
                    WHERE user_id = 0 AND preference_key = %s
                    """,
                    (pref_key,)
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({'success': True, 'value': None})
                return jsonify({'success': True, 'value': row['preference_value']})

            # POST - upsert
            data = request.get_json() or {}
            value = data.get('value')
            value_json = json.dumps(value) if not isinstance(value, str) else value

            cursor.execute(
                """
                INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category, is_global)
                VALUES (0, %s, %s, 'json', 'authoring_ui', true)
                ON CONFLICT (user_id, preference_key)
                DO UPDATE SET preference_value = EXCLUDED.preference_value, updated_at = NOW()
                """,
                (pref_key, value_json)
            )
            cursor.connection.commit()
            return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error handling UI preference {pref_key}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/save-imaging-model-selection', methods=['POST'])
def api_save_imaging_model_selection():
    """Save imaging model selection for persistence across stages"""
    try:
        data = request.get_json()
        imaging_model = data.get('imaging_model')
        post_id = data.get('post_id')
        
        if not imaging_model or not post_id:
            return jsonify({'error': 'Missing imaging_model or post_id'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Save to post_development table for persistence
            cursor.execute("""
                INSERT INTO post_development (post_id, imaging_model_selection, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (post_id) 
                DO UPDATE SET 
                    imaging_model_selection = EXCLUDED.imaging_model_selection,
                    updated_at = NOW()
            """, (post_id, imaging_model))
            
            cursor.connection.commit()
            
            logger.info(f"Imaging model selection saved: {imaging_model} for post {post_id}")
            
            return jsonify({
                'success': True,
                'imaging_model': imaging_model,
                'message': 'Imaging model selection saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving imaging model selection: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-system-prompt', methods=['POST'])
def api_save_system_prompt():
    """Save system prompt for Image Prompts Generation"""
    try:
        data = request.get_json()
        system_prompt = data.get('system_prompt')
        prompt_name = data.get('prompt_name', 'Image Prompts Generation')
        
        if not system_prompt:
            return jsonify({'error': 'Missing system_prompt'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update the system_prompt in llm_prompt table
            cursor.execute("""
                UPDATE llm_prompt 
                SET system_prompt = %s, updated_at = NOW()
                WHERE name = %s
            """, (system_prompt, prompt_name))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Prompt not found'}), 404
            
            cursor.connection.commit()
            
            logger.info(f"System prompt updated for {prompt_name}")
            
            return jsonify({
                'success': True,
                'message': 'System prompt saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving system prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-style-guidelines', methods=['POST'])
def api_save_style_guidelines():
    """Save style guidelines for image format"""
    try:
        data = request.get_json()
        style_guidelines = data.get('style_guidelines')
        image_format_id = data.get('image_format_id', 2)
        
        if not style_guidelines:
            return jsonify({'error': 'Missing style_guidelines'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Update the style_guidelines in image_format table
            cursor.execute("""
                UPDATE image_format 
                SET extra_settings = extra_settings::jsonb || %s::jsonb, updated_at = NOW()
                WHERE id = %s
            """, (json.dumps({'style_guidelines': style_guidelines}), image_format_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Image format not found'}), 404
            
            cursor.connection.commit()
            
            logger.info(f"Style guidelines updated for image_format {image_format_id}")
            
            return jsonify({
                'success': True,
                'message': 'Style guidelines saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving style guidelines: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/generate-image-prompt-from-builder', methods=['POST'])
def api_generate_image_prompt_from_builder():
    """Generate image prompt using the compiled prompt from Prompt Builder"""
    try:
        data = request.get_json()
        compiled_prompt = data.get('compiled_prompt')
        llm_provider = data.get('llm_provider', 'Ollama')
        llm_model = data.get('llm_model', 'llama3.2:latest')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        
        if not compiled_prompt:
            return jsonify({'error': 'Missing compiled_prompt'}), 400
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
        
        # Prepare messages for LLM
        messages = [
            {'role': 'user', 'content': compiled_prompt}
        ]
        
        # Execute LLM request using the selected provider and model
        result = llm_service.execute_llm_request(llm_provider.lower(), llm_model, messages)
        
        if 'error' in result:
            return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
        
        generated_prompt = result['content'].strip()
        
        # Parse JSON response to extract just the image_prompt
        try:
            response_data = json.loads(generated_prompt)
            if 'image_prompt' in response_data:
                generated_prompt = response_data['image_prompt']
            else:
                # Fallback: if JSON doesn't have image_prompt field, use the whole response
                logger.warning("JSON response missing 'image_prompt' field, using full response")
        except json.JSONDecodeError:
            # Fallback: if not valid JSON, use the whole response
            logger.warning("LLM response is not valid JSON, using full response")
        
        # Enforce imaging-model-specific hard character limit (server-side safety)
        try:
            # Determine imaging model selection for this post
            imaging_limit = None
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT imaging_model_selection 
                    FROM post_development 
                    WHERE post_id = %s
                    """,
                    (post_id,)
                )
                row = cursor.fetchone()
                selected_model = (row.get('imaging_model_selection') if row else None) or 'sdxl-lora'

            model_limits = {
                'dall-e-3': 4000,
                'dall-e-2': 1000,
                'sdxl-lora': 400,
                'gpt-image-1': 2000,
            }
            imaging_limit = model_limits.get(selected_model, 400)

            # If over limit, request a compact rewrite targeting near the cap
            if imaging_limit and len(generated_prompt) > imaging_limit:
                target_min = max(0, imaging_limit - 40)  # e.g., 360-400 for 400 cap
                compact_system = (
                    "You are an expert at compressing image prompts without losing key style and scene cues. "
                    f"Rewrite the user's prompt to be between {target_min} and {imaging_limit} characters (never exceed {imaging_limit}), "
                    "preserving historical period, locality, and at least four distinct Style Guidelines cues (prefer exact phrases). "
                    "Respond ONLY as JSON in the exact format: {\"image_prompt\": \"...\"}. No commentary."
                )
                compact_messages = [
                    { 'role': 'system', 'content': compact_system },
                    { 'role': 'user', 'content': generated_prompt }
                ]
                compact = llm_service.execute_llm_request(llm_provider.lower(), llm_model, compact_messages)
                if 'content' in compact:
                    compact_text = compact['content'].strip()
                    try:
                        compact_json = json.loads(compact_text)
                        compact_prompt = compact_json.get('image_prompt') or compact_text
                    except Exception:
                        compact_prompt = compact_text
                    if len(compact_prompt) <= imaging_limit:
                        generated_prompt = compact_prompt
                    else:
                        # Final safety: soft truncate at nearest word boundary
                        safe = generated_prompt[:imaging_limit].rsplit(' ', 1)[0]
                        generated_prompt = safe if safe else generated_prompt[:imaging_limit]

            # If result is far under budget, try a single expansion pass (still <= cap)
            if imaging_limit and len(generated_prompt) < int(imaging_limit * 0.8):
                target_min = max(0, imaging_limit - 40)
                expand_system = (
                    "You are an expert at expanding image prompts while keeping them within a strict limit. "
                    f"Expand the user's prompt to approach {target_min}-{imaging_limit} characters (do not exceed {imaging_limit}). "
                    "Add concrete detail (subject, setting, composition, lighting, palette, texture/materials, mood, vantage/time) and maintain at least four distinct Style Guidelines cues (prefer exact phrases). "
                    "Respond ONLY as JSON in the exact format: {\"image_prompt\": \"...\"}. No commentary."
                )
                expand_messages = [
                    { 'role': 'system', 'content': expand_system },
                    { 'role': 'user', 'content': generated_prompt }
                ]
                expand = llm_service.execute_llm_request(llm_provider.lower(), llm_model, expand_messages)
                if 'content' in expand:
                    expand_text = expand['content'].strip()
                    try:
                        expand_json = json.loads(expand_text)
                        expanded_prompt = expand_json.get('image_prompt') or expand_text
                    except Exception:
                        expanded_prompt = expand_text
                    # Accept if within cap
                    if len(expanded_prompt) <= imaging_limit:
                        generated_prompt = expanded_prompt
        except Exception as _limit_err:
            logger.warning(f"Image prompt length enforcement failed: {_limit_err}")

        # Save to database
        with db_manager.get_cursor() as cursor:
            # Create a JSON structure similar to the existing image_prompts format
            image_prompt_json = {
                "image_prompt": generated_prompt,
                "dimensions": "1792x1024",  # Default dimensions
                "style": "inkwash and watercolour",
                "base_concept": generated_prompt
            }
            
            # Handle both string and integer section IDs
            if section_id.isdigit():
                # Integer section ID - update post_section table
                cursor.execute("""
                    UPDATE post_section 
                    SET image_prompts = %s
                    WHERE post_id = %s AND id = %s
                """, (json.dumps(image_prompt_json), post_id, int(section_id)))
            else:
                # String section ID - update post_development.sections JSON
                cursor.execute("""
                    SELECT sections FROM post_development WHERE post_id = %s
                """, (post_id,))
                row = cursor.fetchone()
                
                if row and row['sections']:
                    try:
                        sections_data = json.loads(row['sections']) if isinstance(row['sections'], str) else row['sections']
                        if isinstance(sections_data, dict) and 'sections' in sections_data:
                            sections_list = sections_data['sections']
                        elif isinstance(sections_data, list):
                            sections_list = sections_data
                        else:
                            sections_list = []
                        
                        # Find and update the specific section
                        for section in sections_list:
                            if section.get('id') == section_id:
                                section['image_prompts'] = image_prompt_json
                                break
                        else:
                            # Try mapping section_1, section_2, etc. to index 1, 2, etc.
                            if section_id.startswith('section_'):
                                try:
                                    section_index = int(section_id.split('_')[1])
                                    for section in sections_list:
                                        if section.get('index') == section_index:
                                            section['image_prompts'] = image_prompt_json
                                            break
                                except (ValueError, IndexError):
                                    pass
                        
                        # Update the database
                        cursor.execute("""
                            UPDATE post_development 
                            SET sections = %s, updated_at = NOW()
                            WHERE post_id = %s
                        """, (json.dumps(sections_data), post_id))
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Error updating sections JSON for image prompts: {e}")
                        return jsonify({'error': 'Failed to update sections data'}), 500
            
            cursor.connection.commit()
            
            logger.info(f"Generated image prompt saved for post {post_id}, section {section_id}")
            
            return jsonify({
                'success': True,
                'generated_prompt': generated_prompt,
                'message': 'Image prompt generated and saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error generating image prompt from builder: {e}")
        return jsonify({'error': str(e)}), 500