# Authoring Blueprint - Real workflow integration
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config.database import db_manager
import logging
import json
import requests
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def process_llm_html_content(html_content):
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
                    'stream': False
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

@bp.route('/posts/<int:post_id>/sections/author-first-drafts')
def authoring_sections_author_first_drafts(post_id):
    """Author First Drafts - generate initial content for each section"""
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
                                 page_title="Author First Drafts",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_author_first_drafts: {e}")
        return f"Error: {e}", 500

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
            
            # Redirect to the proper author-first-drafts route
            return redirect(url_for('authoring.authoring_sections_author_first_drafts', post_id=post_id))
            
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
            
            return render_template('authoring/sections/image_prompts.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Prompts",
                                 blueprint_name='authoring')
            
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

# API endpoints for section data
@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get all sections for a post from post_section table"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get sections from post_section table
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            sections = cursor.fetchall()
            
            # Get topic allocation data to populate topics
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            topic_result = cursor.fetchone()
            
            topic_allocation = None
            if topic_result and topic_result['topic_allocation']:
                try:
                    if isinstance(topic_result['topic_allocation'], dict):
                        topic_allocation = topic_result['topic_allocation']
                    else:
                        import json
                        topic_allocation = json.loads(topic_result['topic_allocation'])
                except Exception as e:
                    logger.error(f"Error parsing topic_allocation: {e}")
                    topic_allocation = None
            
            # Convert to list of dictionaries
            sections_list = []
            for section in sections:
                # Get topics for this section from topic_allocation
                section_topics = []
                if topic_allocation and topic_allocation.get('allocations'):
                    for allocation in topic_allocation['allocations']:
                        if allocation.get('section_id') == f"section_{section['section_order']}":
                            section_topics = allocation.get('topics', [])
                            break
                
                sections_list.append({
                    'id': section['id'],
                    'order': section['section_order'],
                    'title': section['section_heading'],
                    'subtitle': section['section_description'],
                    'status': section['status'] or 'draft',
                    'draft': section['draft'] or '',
                    'polished': section['polished'] or '',
                    'section_text': section['polished'] or '',  # Map polished to section_text for frontend consistency
                    'topics': section_topics,  # Use topics from topic_allocation
                    'facts_to_include': section['facts_to_include'] or '',
                    'highlighting': section['highlighting'] or '',
                    'image_concepts': section['image_concepts'] or '',
                    'image_prompts': section['image_prompts'] or '',
                    'image_captions': section['image_captions'] or '',
                    'progress': 100 if section['polished'] else (50 if section['draft'] else 0)
                })
            
            return jsonify({
                'success': True,
                'sections': sections_list
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_sections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>')
def api_get_section_detail(post_id, section_id):
    """Get details for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section from post_section table
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({
                    'success': False,
                    'error': 'Section not found'
                }), 404
            
            section_data = {
                'id': section['id'],
                'order': section['section_order'],
                'title': section['section_heading'],
                'subtitle': section['section_description'],
                'status': section['status'] or 'draft',
                'draft': section['draft'] or '',
                'polished': section['polished'] or '',
                'section_text': section['polished'] or '',  # Map polished to section_text for frontend consistency
                'topics': section['ideas_to_include'] or [],
                'facts_to_include': section['facts_to_include'] or '',
                'highlighting': section['highlighting'] or '',
                'image_concepts': section['image_concepts'] or '',
                'image_prompts': section['image_prompts'] or '',
                'image_captions': section['image_captions'] or '',
                'progress': 100 if section['polished'] else (50 if section['draft'] else 0)
            }
            
            return jsonify({
                'success': True,
                'section': section_data
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_section_detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/generate', methods=['POST'])
def api_generate_section_draft(post_id, section_id):
    """Generate draft content for a specific section using LLM"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section details
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       status, draft, polished
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
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
            import json
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
                        import json
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
            
            # Prepare prompt variables with rich context
            prompt_vars = {
                'SELECTED_IDEA': dev_data.get('idea_seed', 'Scottish autumn folklore and traditions'),
                'SECTION_TITLE': section['section_heading'],
                'SECTION_SUBTITLE': section['section_description'] or '',
                'SECTION_GROUP': 'Historical Foundations of Autumnal Traditions',  # This should come from planning data
                'GROUP_SUMMARY': 'This group explores the Celtic roots and historical developments that shaped Scotland\'s autumnal customs, highlighting their significance in understanding the country\'s identity.',
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
            draft_html, section_text_plain = process_llm_html_content(llm_response['content'])
            
            # Save generated content to database (draft=HTML, polished=plain text)
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, polished = %s, status = 'complete'
                WHERE post_id = %s AND id = %s
            """, (draft_html, section_text_plain, post_id, section_id))
            
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

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/generate-image-concepts', methods=['POST'])
def api_generate_image_concepts(post_id, section_id):
    """Generate image concepts for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get section data
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description, 
                       draft, polished, ideas_to_include, facts_to_include,
                       highlighting, image_concepts, image_prompts, image_captions
                FROM post_section
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            
            section = cursor.fetchone()
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
                        import json
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
            
            # Execute LLM request
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            image_concepts = result['content']
            
            # Save to database
            cursor.execute("""
                UPDATE post_section 
                SET image_concepts = %s
                WHERE post_id = %s AND id = %s
            """, (image_concepts, post_id, section_id))
            
            cursor.connection.commit()
            
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