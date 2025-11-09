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
from urllib import request as urlrequest, parse as urlparse

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
                # Try to parse JSON - catch decode errors that occur when response.content is None
                # The error "decoding to str: need a bytes-like object, NoneType found" happens
                # when response.json() internally calls response.text which tries to decode None
                try:
                    result = response.json()
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    # Check if this is the specific decode error we're trying to fix
                    if 'decoding to str' in error_msg or 'NoneType' in error_msg or 'bytes-like object' in error_msg:
                        logger.error(f"LLM response decode error (content is None): {error_type}: {error_msg}")
                        return {'error': 'LLM provider returned empty or invalid response (content is None)'}
                    logger.error(f"Failed to parse JSON response: {error_type}: {error_msg}, response status: {response.status_code}")
                    return {'error': f'Invalid JSON response from LLM provider: {error_msg}'}
                
                if provider == 'openai':
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if not content:
                        return {'error': 'Empty response from OpenAI'}
                    return {'content': content}
                elif provider == 'ollama':
                    content = result.get('message', {}).get('content', '')
                    if not content:
                        return {'error': 'Empty response from Ollama'}
                    return {'content': content}
            else:
                # Safely get error text without triggering decode errors
                try:
                    if hasattr(response, 'text') and response.text is not None:
                        error_text = str(response.text)
                    else:
                        error_text = f'HTTP {response.status_code}'
                except Exception as e:
                    error_text = f'HTTP {response.status_code} (error getting response text: {str(e)})'
                return {'error': f'API request failed: {response.status_code} - {error_text}'}
                
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return {'error': str(e)}

# Initialize LLM service
llm_service = LLMService()

bp = Blueprint('header', __name__, url_prefix='/header')

def resolve_target_post_id(post_id, year=None, week=None, require_week=False):
    """
    Resolve target_post_id from week context, preserving post_id for recipe/profile posts.
    
    Args:
        post_id: Original post_id from URL
        year: Year from query params (optional)
        week: Week from query params (optional)
        require_week: If True, return error if year/week not provided
    
    Returns:
        tuple: (target_post_id, error_message)
        If error_message is not None, target_post_id should be ignored
    """
    from utils.taxonomy_helpers import get_post_type
    from utils.week_post_resolver import resolve_post_for_week
    
    # Get post type for the original post_id first
    original_post_type = get_post_type(post_id)
    
    # For recipe/profile posts, always preserve original post_id
    if original_post_type in ('recipe', 'profile'):
        return (post_id, None)
    
    # For themed posts, resolve from week context
    if require_week and (not year or not week):
        return (None, 'Week context (year and week) is required')
    
    if year and week:
        target_post_id = resolve_post_for_week(year, week)
        if not target_post_id:
            return (None, f'No post scheduled for week {week}, {year}')
        return (target_post_id, None)
    
    # No week context and not required - use provided post_id
    return (post_id, None)

# Main routes
@bp.route('/posts/<int:post_id>/title-summary')
def header_title_summary(post_id):
    """Title & Summary substage - Generate post title, subtitle, slug, and summary
    Week-persistence compliance: resolve target_post_id from ?year&?week and pass illustration_method.
    """
    try:
        # Resolve week context
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)

        # Get post type for the original post_id first
        from utils.taxonomy_helpers import get_post_type
        original_post_type = get_post_type(post_id)

        # Resolve post_id from week context (required for generation, but allow page to render)
        # BUT: For recipe/profile posts, preserve the original post_id to maintain recipe/profile association
        from utils.week_post_resolver import resolve_post_for_week
        target_post_id = None
        week_has_post = False
        
        if year and week:
            if original_post_type in ('recipe', 'profile'):
                # For recipe/profile posts, preserve original post_id - don't resolve to different post
                target_post_id = post_id
                week_has_post = True  # Assume has post if we're preserving it
            else:
                # Only resolve for themed posts
                resolved = resolve_post_for_week(year, week)
                if resolved:
                    target_post_id = resolved
                    week_has_post = True
                else:
                    logger.warning(f"No post scheduled for year={year}, week={week}")
                    target_post_id = post_id
        else:
            # No week context provided - use provided post_id but flag as invalid for generation
            target_post_id = post_id
            logger.warning(f"Title-summary route called without week context: year={year}, week={week}")

        # Use utility function to get illustration_method and post_type
        from utils.taxonomy_helpers import get_illustration_method
        illustration_method = get_illustration_method(target_post_id)
        # Use original post_type for recipe/profile, otherwise get from resolved post
        post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(target_post_id)

        return render_template(
            'header/title_summary.html',
            post_id=target_post_id,
            original_post_id=post_id,
            year=year,
            week=week,
            illustration_method=illustration_method,
            week_has_post=week_has_post,
            post_type=post_type,
            blueprint_name='header'
        )
    except Exception as e:
        logger.error(f"Error loading header title-summary: {e}")
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(post_id)
        return render_template('header/title_summary.html', post_id=post_id, post_type=post_type, blueprint_name='header')

@bp.route('/posts/<int:post_id>/header-image')
def header_header_image(post_id):
    """Header Image substage - Create header image with caption and alt text"""
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)

    from utils.week_post_resolver import resolve_post_for_week
    # Get post type for the original post_id first
    from utils.taxonomy_helpers import get_post_type
    original_post_type = get_post_type(post_id)
    
    # NO FALLBACKS: Only use resolved post_id from week context
    # BUT: For recipe/profile posts, preserve the original post_id
    if not year or not week:
        logger.error(f"Header image route called without week context: year={year}, week={week}")
        return "Week context (year and week) is required.", 400
    
    if original_post_type in ('recipe', 'profile'):
        # For recipe/profile posts, preserve original post_id
        target_post_id = post_id
    else:
        # Only resolve for themed posts
        target_post_id = resolve_post_for_week(year, week)
        if not target_post_id:
            logger.error(f"No post scheduled for year={year}, week={week}")
            return f"No post scheduled for week {week}, {year}. Please schedule a post for this week first.", 404
    
    # Use utility function to get illustration_method and post_type
    from utils.taxonomy_helpers import get_illustration_method
    illustration_method = get_illustration_method(target_post_id)
    # Use original post_type for recipe/profile, otherwise get from resolved post
    post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(target_post_id)

    return render_template(
        'header/header_image.html', 
        post_id=target_post_id, 
        blueprint_name='header',
        year=year,
        week=week,
        illustration_method=illustration_method,
        post_type=post_type
    )

@bp.route('/posts/<int:post_id>/seo-meta')
def header_seo_meta(post_id):
    """SEO & Meta substage - Generate SEO metadata including meta title, description, and tags"""
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)

    from utils.week_post_resolver import resolve_post_for_week
    
    # Get post type for the original post_id first
    from utils.taxonomy_helpers import get_post_type
    original_post_type = get_post_type(post_id)
    
    # Resolve post_id from week context (required for generation, but allow page to render)
    # BUT: For recipe/profile posts, preserve the original post_id
    target_post_id = None
    week_has_post = False
    
    if year and week:
        if original_post_type in ('recipe', 'profile'):
            # For recipe/profile posts, preserve original post_id
            target_post_id = post_id
            week_has_post = True
        else:
            # Only resolve for themed posts
            resolved = resolve_post_for_week(year, week)
            if resolved:
                target_post_id = resolved
                week_has_post = True
            else:
                logger.warning(f"No post scheduled for year={year}, week={week}")
                target_post_id = post_id
    else:
        # No week context provided - use provided post_id but flag as invalid for generation
        target_post_id = post_id
        logger.warning(f"SEO meta route called without week context: year={year}, week={week}")
    
    # Use original post_type for recipe/profile, otherwise get from resolved post
    post_type = original_post_type if original_post_type in ('recipe', 'profile') else get_post_type(target_post_id)
    
    return render_template(
        'header/seo_meta.html', 
        post_id=target_post_id, 
        blueprint_name='header',
        year=year,
        week=week,
        week_has_post=week_has_post,
        post_type=post_type
    )

@bp.route('/posts/<int:post_id>/publishing-details')
def header_publishing_details(post_id):
    """Deprecated route: Publishing Details substage removed. Redirect to SEO & Meta."""
    from flask import redirect, url_for
    return redirect(url_for('header.header_seo_meta', post_id=post_id))

@bp.route('/posts/<int:post_id>/final-review')
def header_final_review(post_id):
    from flask import redirect, url_for
    return redirect(url_for('header.header_preview', post_id=post_id))

@bp.route('/posts/<int:post_id>/preview')
def header_preview(post_id):
    """Preview the blog post in its final format (matches clan.com/blog)"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data with author name from author table
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, p.summary, p.slug, p.status, 
                       p.clan_post_id, p.clan_uploaded_url,
                       p.created_at, p.updated_at, p.header_image_id, p.author_id,
                       a.name as author_name
                FROM post p
                LEFT JOIN author a ON p.author_id = a.id
                WHERE p.id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get post type early - needed for image selection logic
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            # If no author and this is a recipe post, default to Marion MacLeod
            if not post.get('author_name') and post_type == 'recipe':
                post['author_name'] = 'Marion MacLeod'
            
            # Get header image if exists - use image table (singular) - foreign keys point here
            header_image = None
            # Use post_images -> images table (plural) - same for ALL post types
            cursor.execute("""
                SELECT i.file_path as path, i.filename, i.alt_text, i.caption, i.width, i.height, pi.image_type
                FROM post_images pi
                JOIN images i ON pi.image_id = i.id
                WHERE pi.post_id = %s AND pi.image_type LIKE 'header%%'
                ORDER BY CASE WHEN pi.image_type = 'header_optimized' THEN 1 
                              WHEN pi.image_type = 'header_watermarked' THEN 2
                              ELSE 3 END
                LIMIT 1
            """, (post_id,))
            img_row = cursor.fetchone()
            if img_row and img_row.get('path'):
                # CRITICAL: Normalize path to ALWAYS be /static/content/posts/... format
                header_path = img_row['path']
                header_path = header_path.lstrip('/')
                if not header_path.startswith('static/'):
                    header_path = 'static/' + header_path.lstrip('/')
                header_path = '/' + header_path  # Add leading slash
                
                header_image = {
                    'path': header_path,
                    'filename': img_row.get('filename'),
                    'alt_text': img_row.get('alt_text'),
                    'caption': img_row.get('caption'),
                    'width': img_row.get('width'),
                    'height': img_row.get('height')
                }
            elif post.get('header_image_id'):
                # Fallback to legacy images table (should not be needed, but handle gracefully)
                cursor.execute("""
                    SELECT id, filename, file_path as path, alt_text, caption
                    FROM images
                    WHERE id = %s
                """, (post['header_image_id'],))
                header_image = cursor.fetchone()
                if header_image and header_image.get('path'):
                    # ONLY show optimized images - no fallback to raw
                    import os
                    raw_path = header_image.get('path', '')
                    if raw_path:
                        optimized_path = raw_path.replace('/raw/', '/optimized/').replace('.png', '.jpg')
                        
                        # Check if optimized version exists on filesystem
                        filesystem_optimized = optimized_path.lstrip('/')
                        if os.path.exists(filesystem_optimized):
                            header_image['path'] = optimized_path
                        else:
                            # No optimized version - don't show image (no fallback to raw)
                            logger.warning(f"Header image optimized version not found: {optimized_path}")
                            header_image = None
                    else:
                        # No path in database - set header_image to None
                        logger.warning(f"Header image {post['header_image_id']} has no path")
                        header_image = None
                else:
                    # No header_image or no path - set to None
                    header_image = None
            
            # Get sections with images via post_images linking table
            # Exclude recipe_image_style section (internal use only)
            # Exclude recipe_method section (method image deprecated - no third image)
            cursor.execute("""
                SELECT ps.id,
                       ps.section_heading,
                       ps.section_description,
                       ps.section_type,
                       ps.draft,
                       ps.polished,
                       ps.post_section_elements,
                       ps.image_captions AS section_image_captions,
                       ps.image_alt_text AS section_image_alt,
                       i.id AS image_id,
                       i.filename,
                       i.file_path AS image_path,
                       i.alt_text,
                       i.caption
                FROM post_section ps
                LEFT JOIN post_images pi
                  ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
                LEFT JOIN images i ON pi.image_id = i.id
                WHERE ps.post_id = %s
                  AND ps.section_type != 'recipe_image_style'
                  AND ps.section_type != 'recipe_method'
                ORDER BY ps.section_order
            """, (post_id,))
            sections = cursor.fetchall()
            
            # Format sections for template
            # IMPORTANT: Use polished field directly - no transformations here!
            # Recipe sections should have HTML already rendered and saved to polished during content generation
            formatted_sections = []
            for section in sections:
                # Use polished if available, otherwise draft, otherwise empty
                content = section.get('polished') or section.get('draft') or ''
                
                # Safety check: filter out raw JSON (should never happen if rendering works correctly)
                if content:
                    content_stripped = content.strip()
                    if content_stripped.startswith('{') or content_stripped.startswith('[') or '```json' in content_stripped.lower():
                        logger.warning(f"Section {section['id']} contains raw JSON in polished/draft - this should not happen!")
                        content = '<p><em>No content available for this section.</em></p>'
                
                formatted_section = {
                    'id': section['id'],
                    'section_heading': section['section_heading'],
                    'section_description': section['section_description'],
                    'section_type': section.get('section_type') or '',
                    'content': content,
                }
                
                # Add image if exists - for recipe posts, skip Photo-harvesting and use LLM-generated images only
                # For recipe posts, also skip recipe_method section (method image deprecated)
                image_path = None
                caption_text = ''
                alt_text = section.get('section_image_alt') or section.get('alt_text') or ''
                
                # Priority 1: Database link (post_images) - for all post types
                if not image_path and section['image_path']:
                    image_path = section['image_path']
                    if not image_path.startswith('http'):
                        if not image_path.startswith('/static'):
                            image_path = f"/static{image_path}"
                        image_path = image_path.replace('/raw/', '/optimized/').replace('.png', '.jpg')
                
                # Use database captions
                if not caption_text:
                    caption_text = section.get('section_image_captions') or section.get('caption') or ''
                
                # Priority 2: Filesystem check - ONLY optimized images, no fallback to raw
                if not image_path:
                    try:
                        import os
                        # ONLY check optimized version - no fallback to raw
                        candidate_optimized = f"/static/content/posts/{post_id}/sections/{section['id']}/optimized/{section['id']}.jpg"
                        filesystem_path_opt = candidate_optimized.lstrip('/')
                        if os.path.exists(filesystem_path_opt):
                            image_path = candidate_optimized
                        # If optimized doesn't exist, image_path remains None (no fallback)
                    except Exception:
                        pass

                if image_path:
                    formatted_section['image'] = {
                        'path': image_path,
                        'alt_text': alt_text,
                        'caption': caption_text
                    }
                
                formatted_sections.append(formatted_section)
            
            # Pass data to template (post_type already retrieved above)
            return render_template('header/preview.html', 
                                 post=post, 
                                 header_image=header_image,
                                 sections=formatted_sections,
                                 post_id=post_id,
                                 post_type=post_type,
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
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
    if error:
        return jsonify({'error': error}), 400 if 'required' in error else 404
    
    # Replace post_id with target_post_id for all operations
    post_id = target_post_id
    
    try:
        # Check if this is a recipe post
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(post_id)
        
        # For recipe posts, use recipe title directly and generate subtitle only
        if post_type == 'recipe':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cr.recipe_title, cr.recipe_description
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                recipe_data = cursor.fetchone()
                
                if recipe_data and recipe_data.get('recipe_title'):
                    recipe_title = recipe_data['recipe_title']
                    recipe_description = recipe_data.get('recipe_description', '')
                    
                    # For recipes, title is just the recipe name - simple and clean
                    title_options = [recipe_title, recipe_title, recipe_title]  # All same, user can edit if needed
                    
                    # Generate subtitle using recipe description
                    # Get subtitle generation prompt (step 61)
                    cursor.execute("""
                        SELECT 
                            sp.system_prompt,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                        LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                        WHERE wsp.step_id = 61
                    """)
                    subtitle_result = cursor.fetchone()
                    
                    if subtitle_result:
                        subtitle_system = subtitle_result.get('system_prompt', '')
                        subtitle_task = subtitle_result.get('task_prompt', '')
                        
                        # Modify subtitle prompt for recipes - evocative phrase without repeating recipe name
                        subtitle_task = f"""Generate a short, evocative subtitle (8-12 words) for this Scottish recipe blog post.

Recipe Name: {recipe_title}
Recipe Description: {recipe_description}

CRITICAL REQUIREMENTS:
- Do NOT repeat the recipe name "{recipe_title}" in the subtitle
- Create a warm, inviting phrase that captures the essence, tradition, or appeal of this dish
- Focus on what makes it special: its heritage, when it's enjoyed, its comforting nature, or its regional significance
- Keep it poetic and evocative, not descriptive or instructional
- Examples of good subtitles: "A warming bowl of coastal comfort" or "Traditional fare for cold winter evenings" or "A taste of Highland heritage"

Return ONLY a single subtitle string, not an array. Do not use quotes or brackets."""
                        
                        messages = [
                            {'role': 'system', 'content': subtitle_system},
                            {'role': 'user', 'content': subtitle_task}
                        ]
                        
                        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                        
                        if 'error' not in llm_response and llm_response.get('content'):
                            generated_subtitle = llm_response['content'].strip()
                            # Remove quotes and brackets
                            generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                            
                            # Clean up any JSON array if LLM returned one
                            import re
                            json_match = re.search(r'\[.*?\]', generated_subtitle, re.DOTALL)
                            if json_match:
                                try:
                                    import json
                                    subtitle_array = json.loads(json_match.group(0))
                                    if isinstance(subtitle_array, list) and len(subtitle_array) > 0:
                                        generated_subtitle = subtitle_array[0].strip().strip('"').strip("'")
                                except:
                                    pass
                            
                            # Remove any remaining quotes or brackets
                            generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                            
                            # If subtitle still contains the recipe name, try to extract just the evocative part
                            if recipe_title.lower() in generated_subtitle.lower():
                                # Try to find a phrase that doesn't include the recipe name
                                # Split by common separators and take the most evocative part
                                parts = re.split(r'[:\-–—]', generated_subtitle)
                                for part in parts:
                                    part = part.strip()
                                    if part and recipe_title.lower() not in part.lower() and len(part) > 10:
                                        generated_subtitle = part
                                        break
                            
                            # Final validation: if it still contains the recipe name, generate a simple fallback
                            if recipe_title.lower() in generated_subtitle.lower() or len(generated_subtitle) < 5:
                                # Generate a simple evocative phrase manually
                                if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                    generated_subtitle = "A warming bowl of coastal comfort"
                                elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                    generated_subtitle = "Traditional fare for cold winter evenings"
                                else:
                                    generated_subtitle = "A taste of Highland heritage"
                        else:
                            # If LLM fails, use a simple evocative phrase instead of recipe description
                            if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                generated_subtitle = "A warming bowl of coastal comfort"
                            elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                generated_subtitle = "Traditional fare for cold winter evenings"
                            else:
                                generated_subtitle = "A taste of Highland heritage"
                    else:
                        # If no subtitle prompt found, use a simple evocative phrase
                        if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                            generated_subtitle = "A warming bowl of coastal comfort"
                        elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                            generated_subtitle = "Traditional fare for cold winter evenings"
                        else:
                            generated_subtitle = "A taste of Highland heritage"
                    
                    return jsonify({
                        'success': True,
                        'title_options': title_options,
                        'selected_index': 0,
                        'subtitle': generated_subtitle
                    })
        
        # For non-recipe posts, use normal title generation
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
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
    if error:
        return jsonify({'error': error}), 400 if 'required' in error else 404
    
    # Replace post_id with target_post_id for all operations
    post_id = target_post_id
    
    try:
        # Check if this is a recipe post
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(post_id)
        
        # For recipe posts, use the same logic as title generation
        if post_type == 'recipe':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cr.recipe_title, cr.recipe_description
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                recipe_data = cursor.fetchone()
                
                if recipe_data and recipe_data.get('recipe_title'):
                    recipe_title = recipe_data['recipe_title']
                    recipe_description = recipe_data.get('recipe_description', '')
                    
                    # Generate subtitle (same logic as api_generate_titles)
                    cursor.execute("""
                        SELECT 
                            sp.system_prompt,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                        LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                        WHERE wsp.step_id = 61
                    """)
                    subtitle_result = cursor.fetchone()
                    
                    generated_subtitle = ''
                    if subtitle_result:
                        subtitle_system = subtitle_result.get('system_prompt', '')
                        subtitle_task = subtitle_result.get('task_prompt', '')
                        
                        # Modify subtitle prompt for recipes - evocative phrase without repeating recipe name
                        subtitle_task = f"""Generate a short, evocative subtitle (8-12 words) for this Scottish recipe blog post.

Recipe Name: {recipe_title}
Recipe Description: {recipe_description}

CRITICAL REQUIREMENTS:
- Do NOT repeat the recipe name "{recipe_title}" in the subtitle
- Create a warm, inviting phrase that captures the essence, tradition, or appeal of this dish
- Focus on what makes it special: its heritage, when it's enjoyed, its comforting nature, or its regional significance
- Keep it poetic and evocative, not descriptive or instructional
- Examples of good subtitles: "A warming bowl of coastal comfort" or "Traditional fare for cold winter evenings" or "A taste of Highland heritage"

Return ONLY a single subtitle string, not an array. Do not use quotes or brackets."""
                        
                        messages = [
                            {'role': 'system', 'content': subtitle_system},
                            {'role': 'user', 'content': subtitle_task}
                        ]
                        
                        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                        
                        if 'error' not in llm_response and llm_response.get('content'):
                            generated_subtitle = llm_response['content'].strip()
                            # Remove quotes and brackets
                            generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                            
                            # Clean up any JSON array if LLM returned one
                            import re
                            json_match = re.search(r'\[.*?\]', generated_subtitle, re.DOTALL)
                            if json_match:
                                try:
                                    import json
                                    subtitle_array = json.loads(json_match.group(0))
                                    if isinstance(subtitle_array, list) and len(subtitle_array) > 0:
                                        generated_subtitle = subtitle_array[0].strip().strip('"').strip("'")
                                except:
                                    pass
                            
                            # Remove any remaining quotes or brackets
                            generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                            
                            # If subtitle still contains the recipe name, try to extract just the evocative part
                            if recipe_title.lower() in generated_subtitle.lower():
                                # Try to find a phrase that doesn't include the recipe name
                                # Split by common separators and take the most evocative part
                                parts = re.split(r'[:\-–—]', generated_subtitle)
                                for part in parts:
                                    part = part.strip()
                                    if part and recipe_title.lower() not in part.lower() and len(part) > 10:
                                        generated_subtitle = part
                                        break
                            
                            # Final validation: if it still contains the recipe name, generate a simple fallback
                            if recipe_title.lower() in generated_subtitle.lower() or len(generated_subtitle) < 5:
                                # Generate a simple evocative phrase manually
                                if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                    generated_subtitle = "A warming bowl of coastal comfort"
                                elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                    generated_subtitle = "Traditional fare for cold winter evenings"
                                else:
                                    generated_subtitle = "A taste of Highland heritage"
                        else:
                            # If LLM fails, use a simple evocative phrase instead of recipe description
                            if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                generated_subtitle = "A warming bowl of coastal comfort"
                            elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                generated_subtitle = "Traditional fare for cold winter evenings"
                            else:
                                generated_subtitle = "A taste of Highland heritage"
                    else:
                        # If no subtitle prompt found, use a simple evocative phrase
                        if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                            generated_subtitle = "A warming bowl of coastal comfort"
                        elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                            generated_subtitle = "Traditional fare for cold winter evenings"
                        else:
                            generated_subtitle = "A taste of Highland heritage"
                    
                    # Return as a single-item array for consistency with the API
                    return jsonify({
                        'success': True,
                        'subtitle_options': [generated_subtitle],
                        'selected_index': 0
                    })
        
        # For non-recipe posts, use normal subtitle generation
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
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
    if error:
        return jsonify({'error': error}), 400 if 'required' in error else 404
    
    # Replace post_id with target_post_id for all operations
    post_id = target_post_id
    
    try:
        # Check if this is a recipe post
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(post_id)
        
        # For recipe posts, use recipe title directly and generate subtitle only
        if post_type == 'recipe':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT cr.recipe_title, cr.recipe_description
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                recipe_data = cursor.fetchone()
                
                if recipe_data and recipe_data.get('recipe_title'):
                    recipe_title = recipe_data['recipe_title']
                    recipe_description = recipe_data.get('recipe_description', '')
                    
                    # For recipes, title is just the recipe name - simple and clean
                    title_options = [recipe_title, recipe_title, recipe_title]
                    
                    # Generate subtitle (same logic as api_generate_titles)
                    cursor.execute("""
                        SELECT 
                            sp.system_prompt,
                            tp.prompt_text as task_prompt
                        FROM workflow_step_prompt wsp
                        LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
                        LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
                        WHERE wsp.step_id = 61
                    """)
                    subtitle_result = cursor.fetchone()
                    
                    generated_subtitle = ''
                    if subtitle_result:
                        subtitle_system = subtitle_result.get('system_prompt', '')
                        subtitle_task = subtitle_result.get('task_prompt', '')
                        
                        # Modify subtitle prompt for recipes - evocative phrase without repeating recipe name
                        subtitle_task = f"""Generate a short, evocative subtitle (8-12 words) for this Scottish recipe blog post.

Recipe Name: {recipe_title}
Recipe Description: {recipe_description}

CRITICAL REQUIREMENTS:
- Do NOT repeat the recipe name "{recipe_title}" in the subtitle
- Create a warm, inviting phrase that captures the essence, tradition, or appeal of this dish
- Focus on what makes it special: its heritage, when it's enjoyed, its comforting nature, or its regional significance
- Keep it poetic and evocative, not descriptive or instructional
- Examples of good subtitles: "A warming bowl of coastal comfort" or "Traditional fare for cold winter evenings" or "A taste of Highland heritage"

Return ONLY a single subtitle string, not an array. Do not use quotes or brackets."""
                        
                        messages = [
                            {'role': 'system', 'content': subtitle_system},
                            {'role': 'user', 'content': subtitle_task}
                        ]
                        
                        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
                        
                        if 'error' not in llm_response and llm_response.get('content'):
                            generated_subtitle = llm_response['content'].strip()
                            # Remove quotes and brackets
                            generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                            
                            # Clean up any JSON array if LLM returned one
                            import re
                            json_match = re.search(r'\[.*?\]', generated_subtitle, re.DOTALL)
                            if json_match:
                                try:
                                    import json
                                    subtitle_array = json.loads(json_match.group(0))
                                    if isinstance(subtitle_array, list) and len(subtitle_array) > 0:
                                        generated_subtitle = subtitle_array[0].strip().strip('"').strip("'")
                                except:
                                    pass
                            
                            # Remove any remaining quotes or brackets
                            generated_subtitle = generated_subtitle.strip('"').strip("'").strip('[').strip(']')
                            
                            # If subtitle still contains the recipe name, try to extract just the evocative part
                            if recipe_title.lower() in generated_subtitle.lower():
                                # Try to find a phrase that doesn't include the recipe name
                                # Split by common separators and take the most evocative part
                                parts = re.split(r'[:\-–—]', generated_subtitle)
                                for part in parts:
                                    part = part.strip()
                                    if part and recipe_title.lower() not in part.lower() and len(part) > 10:
                                        generated_subtitle = part
                                        break
                            
                            # Final validation: if it still contains the recipe name, generate a simple fallback
                            if recipe_title.lower() in generated_subtitle.lower() or len(generated_subtitle) < 5:
                                # Generate a simple evocative phrase manually
                                if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                    generated_subtitle = "A warming bowl of coastal comfort"
                                elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                    generated_subtitle = "Traditional fare for cold winter evenings"
                                else:
                                    generated_subtitle = "A taste of Highland heritage"
                        else:
                            # If LLM fails, use a simple evocative phrase instead of recipe description
                            if 'soup' in recipe_title.lower() or 'skink' in recipe_title.lower():
                                generated_subtitle = "A warming bowl of coastal comfort"
                            elif 'stew' in recipe_title.lower() or 'casserole' in recipe_title.lower():
                                generated_subtitle = "Traditional fare for cold winter evenings"
                            else:
                                generated_subtitle = "A taste of Highland heritage"
                    
                    # Generate summary and slug (simplified for recipes)
                    # For now, return what we have - summary and slug can be generated separately if needed
                    return jsonify({
                        'success': True,
                        'title_options': title_options,
                        'selected_index': 0,
                        'subtitle': generated_subtitle,
                        'summary': '',  # Can be generated separately
                        'slug': recipe_title.lower().replace(' ', '-').replace("'", '').replace(':', '')
                    })
        
        # For non-recipe posts, use normal generation
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
        
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
        if error:
            return jsonify({'error': error}), 400 if 'required' in error else 404
        
        # Get post title and summary from post table (use target_post_id)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, summary
                FROM post 
                WHERE id = %s
            """, (target_post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get section titles from planning/concept/titling (use resolved post_id)
            cursor.execute("""
                SELECT section_heading
                FROM post_section 
                WHERE post_id = %s 
                ORDER BY section_order
            """, (target_post_id,))
            
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
            
            # Call LLM with intercept_context (use resolved post_id)
            intercept_context = {
                'post_id': target_post_id,
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
                SELECT i.file_path as path 
                FROM post p
                JOIN images i ON p.header_image_id = i.id
                WHERE p.id = %s
            """, (post_id,))
            
            image_result = cursor.fetchone()
            raw_path = image_result['path'] if image_result and image_result['path'] else None
            
            if raw_path:
                # Convert to optimized path: replace /raw/ with /optimized/ and .png with .jpg
                optimized_path = raw_path.replace('/raw/', '/optimized/').replace('.png', '.jpg')
                meta_image = f"https://clan.com{optimized_path}"
            else:
                meta_image = "https://clan.com/images/default-scottish-heritage.jpg"
            
            # Save to database (use resolved post_id)
            cursor.execute("""
                UPDATE post 
                SET meta_title = %s,
                    meta_description = %s,
                    meta_tags = %s,
                    meta_image = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (meta_title, meta_description, meta_tags, meta_image, target_post_id))
            
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

@bp.route('/api/posts/<int:post_id>/save-author', methods=['POST'])
def api_save_author(post_id):
    """Save author name to post"""
    try:
        data = request.get_json()
        author_name = data.get('author_name', '')
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post 
                SET author_name = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (author_name, post_id))
            
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error saving author for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/title-summary-prompt', methods=['GET', 'PUT'])
def api_title_summary_prompt(post_id):
    """Get or update the Title Generation prompt for title-summary page"""
    try:
        with db_manager.get_cursor() as cursor:
            if request.method == 'GET':
                # Get prompt from workflow_step_prompt for step 60 (Title Generation)
                cursor.execute("""
                    SELECT 
                        sp.id as system_prompt_id,
                        sp.name as system_prompt_name,
                        sp.system_prompt,
                        tp.id as task_prompt_id,
                        tp.name as task_prompt_name,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                    JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                    WHERE wsp.step_id = 60
                """)
                
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'Title Generation prompt not found'}), 404
                
                # Return system_prompt and prompt_text separately for LLM Prompts Panel
                return jsonify({
                    'success': True,
                    'prompt': {
                        'id': result['task_prompt_id'],  # Use task prompt ID for editing
                        'name': result['task_prompt_name'],
                        'system_prompt': result['system_prompt'] or '',
                        'prompt_text': result['task_prompt'] or '',
                        'system_prompt_id': result['system_prompt_id'],
                        'task_prompt_id': result['task_prompt_id']
                    }
                })
            
            elif request.method == 'PUT':
                # Update the prompt
                # LLM Prompts Panel sends: { system_prompt, prompt_text }
                # But we display combined, so we need to handle both formats
                data = request.get_json()
                
                # Get current prompts first
                cursor.execute("""
                    SELECT 
                        sp.id as system_prompt_id,
                        sp.system_prompt,
                        tp.id as task_prompt_id,
                        tp.prompt_text as task_prompt
                    FROM workflow_step_prompt wsp
                    JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
                    JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
                    WHERE wsp.step_id = 60
                """)
                
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'Title Generation prompt not found'}), 404
                
                # Handle two formats:
                # 1. LLM Prompts Panel format: { system_prompt, prompt_text }
                # 2. Direct content format: { content }
                if 'prompt_text' in data:
                    # Format from LLM Prompts Panel - update task prompt
                    task_prompt = data.get('prompt_text', '').strip()
                    # Only update if substantial content (more than 100 chars to avoid test data)
                    # Check against original to avoid overwriting with stale/test data
                    original_task = result.get('task_prompt', '').strip()
                    if task_prompt and len(task_prompt) > 100 and task_prompt != original_task:
                        # Ensure we're using integer IDs
                        task_prompt_id = int(result['task_prompt_id'])
                        cursor.execute("""
                            UPDATE llm_prompt
                            SET prompt_text = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (task_prompt, task_prompt_id))
                        cursor.connection.commit()
                        logger.info(f"Updated Title Generation task prompt (task_prompt_id={task_prompt_id}) for post {post_id}")
                    elif task_prompt and len(task_prompt) <= 100:
                        logger.warning(f"Ignored task prompt update - too short (likely test data): {len(task_prompt)} chars")
                    elif task_prompt == original_task:
                        logger.info(f"Ignored task prompt update - no changes detected")
                    
                    # Optionally update system prompt if provided AND substantial
                    # Only update if it's actually meaningful content (not empty or test data)
                    if 'system_prompt' in data:
                        system_prompt = data.get('system_prompt', '').strip()
                        # Only update if it's substantial (more than just "Test system" or empty)
                        # Check against the original to avoid overwriting with test/stale data
                        original_system = result.get('system_prompt', '').strip()
                        if system_prompt and len(system_prompt) > 50 and system_prompt != original_system:
                            # Ensure we're using integer IDs
                            system_prompt_id = int(result['system_prompt_id'])
                            cursor.execute("""
                                UPDATE llm_prompt
                                SET system_prompt = %s,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (system_prompt, system_prompt_id))
                            cursor.connection.commit()
                            logger.info(f"Updated Title Generation system prompt (system_prompt_id={system_prompt_id}) for post {post_id}")
                        elif system_prompt and len(system_prompt) <= 50:
                            logger.warning(f"Ignored system prompt update - too short (likely test data): {len(system_prompt)} chars")
                
                elif 'content' in data:
                    # Direct content format - user is editing combined prompt
                    prompt_content = data.get('content', '').strip()
                    
                    if not prompt_content:
                        return jsonify({'error': 'Prompt content is required'}), 400
                    
                    # Try to extract task part from combined prompt
                    system_prompt = result['system_prompt']
                    combined_pattern = f"{system_prompt}\n\n"
                    
                    if prompt_content.startswith(combined_pattern):
                        task_prompt = prompt_content[len(combined_pattern):]
                    elif prompt_content.startswith(system_prompt):
                        task_prompt = prompt_content[len(system_prompt):].lstrip()
                    else:
                        # If it doesn't match, assume user is editing just the task prompt
                        task_prompt = prompt_content
                    
                    # Ensure we're using integer ID
                    task_prompt_id = int(result['task_prompt_id'])
                    cursor.execute("""
                        UPDATE llm_prompt
                        SET prompt_text = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (task_prompt, task_prompt_id))
                    cursor.connection.commit()
                    logger.info(f"Updated Title Generation prompt from content (task_prompt_id={task_prompt_id}) for post {post_id}")
                else:
                    return jsonify({'error': 'Either prompt_text or content is required'}), 400
                
                return jsonify({
                    'success': True,
                    'message': 'Prompt updated successfully'
                })
                
    except Exception as e:
        logger.error(f"Error with title-summary prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/get-title-summary', methods=['GET'])
def api_get_title_summary(post_id):
    """Get post title, subtitle, summary, and author"""
    try:
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(post_id)
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, p.subtitle, p.summary, a.name as author_name
                FROM post p
                LEFT JOIN author a ON p.author_id = a.id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            
            if result:
                author_name = result.get('author_name', '') or ''
                # If no author and this is a recipe post, default to Marion MacLeod
                if not author_name and post_type == 'recipe':
                    author_name = 'Marion MacLeod'
                
                return jsonify({
                    'title': result.get('title', '') or '',
                    'subtitle': result.get('subtitle', '') or '',
                    'summary': result.get('summary', '') or '',
                    'author_name': author_name,
                    'post_type': post_type
                })
            else:
                return jsonify({'error': 'Post not found'}), 404
                
    except Exception as e:
        logger.error(f"Error getting title-summary for post {post_id}: {e}")
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
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    target_post_id, error = resolve_target_post_id(post_id, year, week, require_week=True)
    if error:
        return jsonify({'error': error}), 400 if 'required' in error else 404
    
    # Replace post_id with target_post_id for all operations
    post_id = target_post_id
    
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
    """Compile header prompt from theme name and expanded idea using LLM"""
    try:
        # Check if this is a recipe post - if so, return hero_image_prompt directly
        from utils.taxonomy_helpers import get_post_type
        post_type = get_post_type(post_id)
        
        if post_type == 'recipe':
            # For recipe posts, use the hero_image_prompt from recipe_image_style section
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT post_section_elements
                    FROM post_section
                    WHERE post_id = %s AND section_type = 'recipe_image_style'
                    LIMIT 1
                """, (post_id,))
                style_section = cursor.fetchone()
                
                if style_section and style_section.get('post_section_elements'):
                    import json
                    try:
                        elements = style_section['post_section_elements']
                        if isinstance(elements, str):
                            elements = json.loads(elements)
                        
                        if elements and elements.get('hero_image_prompt'):
                            hero_prompt = elements['hero_image_prompt']
                            # Extract description if it's an object
                            if isinstance(hero_prompt, dict):
                                prompt_text = hero_prompt.get('description') or hero_prompt.get('image_prompt') or hero_prompt.get('prompt') or ''
                            elif isinstance(hero_prompt, str):
                                prompt_text = hero_prompt
                            else:
                                prompt_text = str(hero_prompt)
                            
                            if prompt_text and prompt_text.strip():
                                return jsonify({
                                    'success': True,
                                    'compiled_prompt': prompt_text.strip(),
                                    'source': 'recipe_hero_prompt'
                                })
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        logger.warning(f"Failed to extract hero prompt from recipe_image_style: {e}")
            
            # If we couldn't get the recipe prompt, return an error
            return jsonify({
                'success': False,
                'error': 'No hero image prompt found. Please generate prompts at the Image Style & Prompts stage first.'
            }), 400
        
        # Get the selected model and illustration method from request data
        data = request.get_json() or {}
        selected_model = data.get('model', 'gpt-image-1')
        illustration_method = request.args.get('illustration_method', 'LLM-creation')
        
        # Get year/week from query parameters for week persistence
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        # Get theme_name and expanded_idea from request body or resolve from week context
        theme_name = data.get('theme_name')
        expanded_idea = data.get('expanded_idea')
        
        with db_manager.get_cursor() as cursor:
            # If not provided, resolve from week context
            if not theme_name or not expanded_idea:
                if year and week:
                    from utils.week_post_resolver import resolve_post_for_week
                    target_post_id = resolve_post_for_week(year, week)
                    
                    if target_post_id:
                        # Get selected theme for this week
                        cursor.execute("""
                            SELECT ct.theme_title
                            FROM calendar_week_selection cws
                            JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                            WHERE cws.year = %s AND cws.week_number = %s
                        """, (year, week))
                        theme_result = cursor.fetchone()
                        if theme_result and not theme_name:
                            theme_name = theme_result.get('theme_title')
                        
                        # Get expanded idea from post_development
                        cursor.execute("""
                            SELECT expanded_idea
                            FROM post_development
                            WHERE post_id = %s
                        """, (target_post_id,))
                        idea_result = cursor.fetchone()
                        if idea_result and not expanded_idea:
                            expanded_idea = idea_result.get('expanded_idea')
            
            if not theme_name or not expanded_idea:
                return jsonify({'error': 'Theme name and expanded idea are required'}), 400
            
            # Get prompts from database - use Photo-harvesting prompt if applicable
            if illustration_method == 'Photo-harvesting':
                cursor.execute("""
                    SELECT 
                        system_prompt,
                        prompt_text as task_prompt
                    FROM llm_prompt
                    WHERE name = 'Header Image Generation Prompt (Photo-harvesting)'
                """)
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'error': 'Header Image Generation Prompt (Photo-harvesting) not found'}), 404
            else:
                # For LLM-creation route, use workflow step prompts (step 64)
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
            
            # Determine style guidelines based on selected model and illustration method
            style_guidelines = ""
            if illustration_method == 'Photo-harvesting':
                style_guidelines = "Professional photography style, high-resolution quality, natural lighting, photorealistic representation"
            elif selected_model == 'dall-e-3':
                style_guidelines = "Use 'photorealistic' style with brushstrokes fading to white edges"
            elif selected_model == 'sdxl':
                style_guidelines = "Use 'inkwash and watercolour' style with brushstrokes fading to white edges"
            else:
                style_guidelines = "Use 'photorealistic' style with brushstrokes fading to white edges"  # Default
            
            # Use LLM service to compile prompts
            llm_service = LLMService()
            
            # Format the prompt with theme name and expanded idea
            formatted_prompt = task_prompt.replace('[data:theme_name]', theme_name or '')
            formatted_prompt = formatted_prompt.replace('[data:expanded_idea]', expanded_idea or '')
            formatted_prompt = formatted_prompt.replace('{theme_name}', theme_name or '')
            formatted_prompt = formatted_prompt.replace('{expanded_idea}', expanded_idea or '')
            
            # Remove any section_prompts placeholder - header images don't use sections
            if '{section_prompts}' in formatted_prompt:
                formatted_prompt = formatted_prompt.replace('{section_prompts}', '')
            if '[data:section_prompts]' in formatted_prompt:
                formatted_prompt = formatted_prompt.replace('[data:section_prompts]', '')
            
            # Replace style_guidelines and model placeholders
            formatted_prompt = formatted_prompt.replace('{style_guidelines}', style_guidelines)
            formatted_prompt = formatted_prompt.replace('{model}', selected_model)
            
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
            
            # Save compiled prompt to database
            try:
                with db_manager.get_cursor() as cursor:
                    # Check if post already has a header image
                    cursor.execute("""
                        SELECT header_image_id FROM post WHERE id = %s
                    """, (post_id,))
                    post_result = cursor.fetchone()
                    
                    if post_result and post_result.get('header_image_id'):
                        # Update existing image record with the compiled prompt
                        cursor.execute("""
                            UPDATE images 
                            SET image_prompt = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (compiled_prompt, post_result['header_image_id']))
                        logger.info(f"Updated header image prompt for post {post_id} in image {post_result['header_image_id']}")
                    else:
                        # Create new image record with just the prompt (no actual image yet)
                        cursor.execute("""
                            INSERT INTO images (filename, original_filename, file_path, image_prompt, alt_text, caption)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            'header.jpg',
                            'placeholder.png',
                            f'/static/content/posts/{post_id}/header/header.jpg',
                            compiled_prompt,
                            'Header image prompt',
                            'Generated header image prompt'
                        ))
                        image_id = cursor.fetchone()['id']
                        
                        # Link to post
                        cursor.execute("""
                            UPDATE post 
                            SET header_image_id = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (image_id, post_id))
                        logger.info(f"Created new header image prompt for post {post_id} with image_id {image_id}")
                    
                    cursor.connection.commit()
            except Exception as e:
                logger.error(f"Error saving compiled header prompt to database: {e}")
                # Don't fail the request if save fails, just log it
                import traceback
                logger.error(traceback.format_exc())
            
            return jsonify({
                'success': True,
                'compiled_prompt': compiled_prompt
            })
            
    except Exception as e:
        logger.error(f"Error compiling header prompt for post {post_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/prompt-assembly-data', methods=['GET'])
def api_get_prompt_assembly_data(post_id):
    """Get system/task prompts and section data for Prompt Assembly display"""
    try:
        # Check illustration_method from query parameter or window context
        illustration_method = request.args.get('illustration_method', 'LLM-creation')
        
        with db_manager.get_cursor() as cursor:
            # For Photo-harvesting route, use the new photorealistic prompt
            if illustration_method == 'Photo-harvesting':
                cursor.execute("""
                    SELECT 
                        system_prompt,
                        prompt_text as task_prompt
                    FROM llm_prompt
                    WHERE name = 'Header Image Generation Prompt (Photo-harvesting)'
                """)
                prompt_result = cursor.fetchone()
                
                if not prompt_result:
                    return jsonify({'error': 'Header Image Generation Prompt (Photo-harvesting) not found'}), 404
            else:
                # For LLM-creation route, use workflow step prompts (step 64)
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
            
            # Get year/week from query parameters for week persistence
            year = request.args.get('year', type=int)
            week = request.args.get('week', type=int)
            
            # For header images, use theme name and expanded idea (not sections)
            # BUT: For recipe/profile posts, use recipe/profile data instead
            from utils.taxonomy_helpers import get_post_type
            post_type = get_post_type(post_id)
            
            theme_name = None
            expanded_idea = None
            
            if post_type == 'recipe':
                # For recipe posts, get recipe title and description
                cursor.execute("""
                    SELECT cr.recipe_title, cr.recipe_description, cr.seasonal_context
                    FROM post p
                    LEFT JOIN calendar_recipes cr ON cr.id = p.recipe_id
                    WHERE p.id = %s
                """, (post_id,))
                recipe_data = cursor.fetchone()
                if recipe_data:
                    theme_name = recipe_data.get('recipe_title') or ''
                    expanded_idea = recipe_data.get('recipe_description') or ''
                    if recipe_data.get('seasonal_context'):
                        expanded_idea = f"{expanded_idea}\n\nSeasonal Context: {recipe_data['seasonal_context']}".strip()
            elif post_type == 'profile':
                # For profile posts, get profile data
                cursor.execute("""
                    SELECT title, subtitle
                    FROM post
                    WHERE id = %s
                """, (post_id,))
                profile_data = cursor.fetchone()
                if profile_data:
                    theme_name = profile_data.get('title') or ''
                    expanded_idea = profile_data.get('subtitle') or ''
            elif year and week:
                # For themed posts, get theme and expanded idea from week context
                from utils.week_post_resolver import resolve_post_for_week
                target_post_id = resolve_post_for_week(year, week)
                
                if target_post_id:
                    # Check if calendar_week_selection table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'calendar_week_selection'
                        )
                    """)
                    has_new_table = cursor.fetchone()['exists']
                    
                    if has_new_table:
                        # Get selected theme for this week (new table)
                        cursor.execute("""
                            SELECT ct.theme_title
                            FROM calendar_week_selection cws
                            JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                            WHERE cws.year = %s AND cws.week_number = %s
                        """, (year, week))
                    else:
                        # Fallback to calendar_schedule (legacy table)
                        cursor.execute("""
                            SELECT ct.theme_title
                            FROM calendar_schedule cs
                            JOIN calendar_themes ct ON cs.theme_id = ct.id
                            WHERE cs.year = %s AND cs.week_number = %s
                            LIMIT 1
                        """, (year, week))
                    
                    theme_result = cursor.fetchone()
                    if theme_result:
                        theme_name = theme_result.get('theme_title')
                    
                    # Get expanded idea from post_development
                    cursor.execute("""
                        SELECT expanded_idea
                        FROM post_development
                        WHERE post_id = %s
                    """, (target_post_id,))
                    idea_result = cursor.fetchone()
                    if idea_result:
                        expanded_idea = idea_result.get('expanded_idea')
            else:
                # Fallback: get from post directly (if no week context)
                cursor.execute("""
                    SELECT pd.expanded_idea, ct.theme_title
                    FROM post_development pd
                    LEFT JOIN post p ON pd.post_id = p.id
                    LEFT JOIN calendar_week_selection cws ON p.id = (
                        SELECT cwp.post_id FROM calendar_week_posts cwp 
                        WHERE cwp.post_id = p.id 
                        ORDER BY cwp.created_at DESC LIMIT 1
                    )
                    LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                    WHERE pd.post_id = %s
                """, (post_id,))
                fallback_result = cursor.fetchone()
                if fallback_result:
                    expanded_idea = fallback_result.get('expanded_idea')
                    theme_name = fallback_result.get('theme_title')
            
            return jsonify({
                'success': True,
                'system_prompt': prompt_result.get('system_prompt', ''),
                'task_prompt': prompt_result.get('task_prompt', ''),
                'theme_name': theme_name,
                'expanded_idea': expanded_idea
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
        
        # Get illustration_method from query parameter or post taxonomy
        illustration_method = request.args.get('illustration_method', None)
        if illustration_method is None:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT ti.illustration_method
                    FROM post p
                    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                    WHERE p.id = %s
                """, (post_id,))
                result = cursor.fetchone()
                illustration_method = (result.get('illustration_method') if result else None) or 'LLM-creation'
        
        # Get rendered prompt using the new system
        if use_renderer:
            # For header images, we need to compile a collage prompt from all sections
            rendered_prompt, debug_info = prompt_service.render_header_prompt_for_model(
                post_id, model_name, use_override=True, illustration_method=illustration_method
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
        
        # Set custom dimensions and style for header image
        # For Photo-harvesting route, use photorealistic settings
        if illustration_method == 'Photo-harvesting':
            # Photo-harvesting route: use gpt-image-1 with photorealistic settings
            if model_name == 'gpt-image-1':
                parameters['size'] = '1536x1024'  # Landscape format
                parameters['portrait_size'] = '1024x1536'  # Portrait format
                parameters['quality'] = 'high'  # High quality for photorealistic (gpt-image-1 uses 'high' not 'hd')
            elif model_name == 'dall-e-3':
                parameters['size'] = '1792x1024'
                parameters['quality'] = 'hd'
                parameters['style'] = 'natural'  # Photorealistic
            else:
                # For other models, use photorealistic defaults
                parameters['width'] = 2358
                parameters['height'] = 1048
        elif model_name == 'dall-e-3':
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
        
        # Automatically optimize and watermark the header image after generation
        logger.info(f"Automatically optimizing header image for post {post_id}")
        watermark_result = optimize_image_with_watermark(post_id, 'header', parameters)
        
        if not watermark_result.get('success'):
            logger.error(f"Header image optimization failed: {watermark_result.get('error', 'Unknown error')}")
            # NO FALLBACK - optimization must succeed for image to be shown
            return jsonify({
                'success': False,
                'error': f"Image generation succeeded but optimization failed: {watermark_result.get('error', 'Unknown error')}"
            }), 500
        
        # Create or update image table record
        with db_manager.get_cursor() as cursor:
            # Check if header image already exists
            cursor.execute("""
                SELECT header_image_id FROM post WHERE id = %s
            """, (post_id,))
            
            existing_image_id = cursor.fetchone()
            
            # Get the optimized path - ONLY optimized, no fallback to raw
            new_path = watermark_result.get('optimized_path')
            if not new_path:
                logger.error(f"No optimized path returned from watermark_result for post {post_id}")
                return jsonify({
                    'success': False,
                    'error': 'Image optimization did not return an optimized path'
                }), 500
            # Normalize path: strip leading slash, then ensure it starts with /static/
            # This matches the normalization in api_optimize_header_image for consistency
            if new_path:
                new_path = new_path.lstrip('/')
                if not new_path.startswith('static/'):
                    new_path = 'static/' + new_path.lstrip('/')
                new_path = '/' + new_path  # Add leading slash
            
            # CRITICAL: Write to images table (plural) with file_path column - foreign keys point here
            if existing_image_id and existing_image_id['header_image_id']:
                # Update existing image record
                cursor.execute("""
                    UPDATE images 
                    SET filename = %s, original_filename = %s, file_path = %s, 
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
                    INSERT INTO images (filename, original_filename, file_path, image_prompt, alt_text, caption)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    'header.jpg',
                    'original_header.png', 
                    new_path,
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
            
            # CRITICAL: Create post_images record for publishing system (same as api_optimize_header_image)
            # Delete any existing post_images link for header_optimized
            cursor.execute("""
                DELETE FROM post_images 
                WHERE post_id = %s AND section_id IS NULL AND image_type = 'header_optimized'
            """, (post_id,))
            
            # Create post_images link for header_optimized
            cursor.execute("""
                INSERT INTO post_images (post_id, section_id, image_id, image_type)
                VALUES (%s, NULL, %s, 'header_optimized')
            """, (post_id, image_id))
            
            # Log successful generation event
            prompt_service.log_generation_event(
                post_id=post_id,
                section_id=None,  # Header images don't have section_id
                model_key=model_name,
                params=parameters,
                prompt_text=image_prompt,
                rendered_prompt=image_prompt,
                result_path=new_path,
                success=True,
                generation_time_ms=generation_time_ms
            )
            
            # Include portrait path if available
            portrait_path = result.get('portrait_path')
            
            return jsonify({
                'success': True,
                'image_id': image_id,
                'raw_path': result.get('image_path'),
                'optimized_path': new_path,
                'portrait_path': portrait_path,
                'portrait_generated': result.get('portrait_generated', False),
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
                SELECT i.id, i.filename, i.file_path as path, 
                       i.alt_text, i.caption, i.image_prompt
                FROM post p
                JOIN images i ON p.header_image_id = i.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'No header image found'}), 404
            
            return jsonify({
                'success': True,
                'image_id': result['id'],
                'filename': result['filename'],
                'path': result['path'],
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
                JOIN images i ON p.header_image_id = i.id
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
                UPDATE images 
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
            # Update images table with details
            cursor.execute("""
                UPDATE images 
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
        
        # Optimize the header image (both landscape and portrait)
        result = optimize_image_with_watermark(post_id, 'header', params)
        
        if result['success']:
            # Save optimized image to image table and create post_images link
            with db_manager.get_cursor() as cursor:
                # Get optimized image paths and normalize consistently
                optimized_path = result.get('optimized_path')
                if optimized_path:
                    # Normalize path: strip leading slash, then ensure it starts with /static/
                    # This matches the normalization in api_generate_header_image and load_header_image_from_db
                    optimized_path = optimized_path.lstrip('/')
                    if not optimized_path.startswith('static/'):
                        optimized_path = 'static/' + optimized_path.lstrip('/')
                    optimized_path = '/' + optimized_path  # Add leading slash
                else:
                    optimized_path = None
                
                portrait_optimized_path = result.get('portrait_path', '').lstrip('/') if result.get('portrait_path') else None
                
                # CRITICAL: Write to image table (singular) with path column - foreign keys point here
                # Get the caption from the post's header_image_caption field
                cursor.execute("SELECT header_image_caption, header_image_id FROM post WHERE id = %s", (post_id,))
                post_row = cursor.fetchone()
                caption = post_row['header_image_caption'] if post_row else None
                existing_header_image_id = post_row['header_image_id'] if post_row else None
                
                if existing_header_image_id:
                    # Update existing image record
                    cursor.execute("""
                        UPDATE images 
                        SET filename = %s, file_path = %s, alt_text = %s, caption = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        'header.jpg',
                        optimized_path,
                        'Header image',
                        caption,
                        existing_header_image_id
                    ))
                    image_id = existing_header_image_id
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO images (filename, file_path, alt_text, caption)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        'header.jpg',
                        optimized_path,
                        'Header image',
                        caption
                    ))
                    image_record = cursor.fetchone()
                    image_id = image_record['id']
                
                # Delete any existing post_images link for header_optimized
                cursor.execute("""
                    DELETE FROM post_images 
                    WHERE post_id = %s AND section_id IS NULL AND image_type = 'header_optimized'
                """, (post_id,))
                
                # Create post_images link for header_optimized
                cursor.execute("""
                    INSERT INTO post_images (post_id, section_id, image_id, image_type)
                    VALUES (%s, NULL, %s, 'header_optimized')
                """, (post_id, image_id))
                
                # Update post.header_image_id to point to optimized version
                cursor.execute("""
                    UPDATE post SET header_image_id = %s WHERE id = %s
                """, (image_id, post_id))
            
            response = {
                'success': True,
                'optimized_path': result['optimized_path'],
                'message': 'Image optimized successfully and database records created'
            }
            # Include portrait path if available
            if result.get('portrait_path'):
                response['portrait_optimized_path'] = result['portrait_path']
                response['message'] = 'Landscape and portrait images optimized successfully'
            
            return jsonify(response)
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

#
# Header Photo-harvesting endpoints (week-persistence compliant)
#

@bp.route('/api/llm/prompts/header-image-search', methods=['GET', 'PUT'])
def header_api_image_search_prompt():
    """Get or update Header Image Search prompt (Photo-harvesting).
    
    Supports illustration_method query parameter:
    - 'Photo-harvesting' → 'Header Image Search Prompt (Photo-harvesting)' (for photo search)
    - 'LLM-creation' or default → returns 404 (header uses LLM-creation via different flow)
    No fallbacks: 404 if prompt missing.
    """
    try:
        with db_manager.get_cursor() as cursor:
            illustration_method = request.args.get('illustration_method', 'LLM-creation')
            if illustration_method != 'Photo-harvesting':
                return jsonify({'error': 'Header Image Search prompt only available for Photo-harvesting route'}), 404
            
            prompt_name = 'Header Image Search Prompt (Photo-harvesting)'
            
            if request.method == 'PUT':
                data = request.get_json()
                system_prompt_template = data.get('system_prompt', '')
                prompt_text = data.get('prompt_text', '')
                
                system_prompt_complete = system_prompt_template
                if system_prompt_template and not system_prompt_template.endswith('JSON object'):
                    system_prompt_complete += '\n\nIMPORTANT: Respond ONLY with the final search query text (no quotes, no markdown). No commentary.'
                
                cursor.execute("""
                    UPDATE llm_prompt 
                    SET system_prompt_template = %s, system_prompt = %s, prompt_text = %s
                    WHERE name = %s
                """, (system_prompt_template, system_prompt_complete, prompt_text, prompt_name))
                
                cursor.connection.commit()
                return jsonify({'success': True, 'message': f'Prompt "{prompt_name}" updated successfully'})
            else:
                cursor.execute("""
                    SELECT name, prompt_text, system_prompt, system_prompt_template, updated_at
                    FROM llm_prompt 
                    WHERE name = %s
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (prompt_name,))
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    return jsonify({'error': f'Header Image Search prompt "{prompt_name}" not found'}), 404
                
                system_prompt_for_display = prompt_data['system_prompt_template'] or prompt_data['system_prompt']
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'name': prompt_data['name'],
                        'prompt_text': prompt_data['prompt_text'],
                        'system_prompt': system_prompt_for_display,
                        'updated_at': prompt_data['updated_at'].isoformat() if prompt_data['updated_at'] else None
                    }
                })
                    
    except Exception as e:
        logger.error(f"Error with header image search prompt: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/photo-search/posts/<int:post_id>/header/generate-search-term', methods=['POST'])
def header_api_generate_search_term(post_id: int):
    """Generate header image search term using LLM from theme name and expanded_idea.
    Uses Header Image Search Prompt (Photo-harvesting). No fallbacks.
    """
    try:
        # Get week context from request
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        # Resolve target_post_id (use provided post_id as fallback, but prefer resolved one)
        target_post_id = post_id
        if year and week:
            try:
                from utils.week_post_resolver import resolve_post_for_week
                resolved = resolve_post_for_week(year, week)
                if resolved:
                    target_post_id = resolved
                else:
                    # If no resolved post, use provided post_id (may be from URL)
                    logger.info(f"No resolved post for year={year}, week={week}, using provided post_id={post_id}")
            except Exception as e:
                logger.warning(f"Week resolver failed for header search term: {e}, using provided post_id={post_id}")
        
        with db_manager.get_cursor() as cursor:
            # Get selected theme name and expanded_idea for target_post_id
            theme_name = ''
            expanded_idea = ''
            
            if year and week:
                # Check if new tables exist, fallback to old calendar_schedule if not
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_selection'
                    )
                """)
                has_new_table = cursor.fetchone()['exists']
                
                if has_new_table:
                    # Use new V2 architecture
                    cursor.execute("""
                        SELECT cws.selected_theme_id, ct.theme_title as theme_name
                        FROM calendar_week_selection cws
                        JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                        WHERE cws.year = %s AND cws.week_number = %s
                    """, (year, week))
                else:
                    # Fallback to old calendar_schedule
                    cursor.execute("""
                        SELECT cs.theme_id, ct.theme_title as theme_name
                        FROM calendar_schedule cs
                        LEFT JOIN calendar_themes ct ON cs.theme_id = ct.id
                        WHERE cs.year = %s AND cs.week_number = %s
                        AND cs.theme_id IS NOT NULL
                        ORDER BY cs.updated_at DESC
                        LIMIT 1
                    """, (year, week))
                
                theme_row = cursor.fetchone()
                if theme_row:
                    theme_name = theme_row.get('theme_name', '')
            
            cursor.execute("""
                SELECT expanded_idea FROM post_development WHERE post_id = %s
            """, (target_post_id,))
            dev_row = cursor.fetchone()
            if dev_row:
                expanded_idea = dev_row.get('expanded_idea', '') or ''
            
            # Get prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Header Image Search Prompt (Photo-harvesting)'
                ORDER BY updated_at DESC LIMIT 1
            """)
            prompt_row = cursor.fetchone()
            if not prompt_row:
                return jsonify({'error': 'Header Image Search Prompt (Photo-harvesting) not found'}), 404
            
            prompt_text = prompt_row['prompt_text']
            system_prompt = prompt_row['system_prompt']
            
            # Replace placeholders
            prompt_text = prompt_text.replace('[data:theme_name]', theme_name or '')
            prompt_text = prompt_text.replace('[data:expanded_idea]', expanded_idea or '')
            
            # Call LLM
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt_text}
            ]
            
            llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            if 'error' in llm_response:
                return jsonify({'error': f'LLM generation failed: {llm_response["error"]}'}), 500
            
            search_term = llm_response.get('content', '').strip()
            if not search_term:
                return jsonify({'error': 'Empty search term generated'}), 500
            
            return jsonify({'success': True, 'search_term': search_term})
            
    except Exception as e:
        logger.error(f"Error generating header search term: {e}")
        return jsonify({'error': str(e)}), 500


#
# Header Photo-harvesting endpoints (week-persistence compliant)
#

@bp.route('/api/photo-search/posts/<int:post_id>/header/search', methods=['POST'])
def header_api_photo_search(post_id: int):
    """Search header images via Pexels/Unsplash and persist results to header/raw JSON.
    Does not require week context for storage; relies on resolved post_id.
    """
    try:
        data = request.get_json() or {}
        search_term = (data.get('search_term') or '').strip()
        provider = data.get('provider', 'both')
        per_page = int(data.get('per_page', 20))
        orientation = data.get('orientation')
        if not search_term:
            return jsonify({'success': False, 'error': 'search_term is required'}), 400

        import os
        from utils.photo_apis_adapter import run_photo_search

        pexels_key = os.getenv('PEXELS_API_KEY')
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if provider == 'pexels' and not pexels_key:
            return jsonify({'success': False, 'error': 'PEXELS_API_KEY is not configured'}), 400
        if provider == 'unsplash' and not unsplash_key:
            return jsonify({'success': False, 'error': 'UNSPLASH_ACCESS_KEY is not configured'}), 400
        if provider == 'both' and (not pexels_key and not unsplash_key):
            return jsonify({'success': False, 'error': 'No photo provider API keys configured (PEXELS_API_KEY / UNSPLASH_ACCESS_KEY)'}), 400

        results = run_photo_search(provider, pexels_key, unsplash_key, search_term, per_page, orientation)

        # Persist to header/raw JSON
        import json as _json
        import os as _os
        from datetime import datetime as _dt

        raw_dir = f"static/content/posts/{post_id}/header/raw"
        _os.makedirs(raw_dir, exist_ok=True)
        payload = {
            'timestamp': _dt.now().isoformat(),
            'post_id': post_id,
            'search_term': search_term,
            'provider': provider,
            'orientation': orientation,
            'count': len(results),
            'results': results,
        }
        ts_name = _dt.now().strftime('%Y%m%d_%H%M%S')
        with open(f"{raw_dir}/photo_search_results_{ts_name}.json", 'w') as f:
            _json.dump(payload, f, indent=2)
        with open(f"{raw_dir}/photo_search_results_latest.json", 'w') as f:
            _json.dump(payload, f, indent=2)

        return jsonify({'success': True, 'results': results, 'count': len(results), 'orientation': orientation})
    except Exception as e:
        logger.error(f"Header photo search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/photo-search/posts/<int:post_id>/header/results', methods=['GET'])
def header_api_photo_results(post_id: int):
    """Load persisted header search results from header/raw JSON (latest)."""
    try:
        import json as _json, os as _os
        latest = f"static/content/posts/{post_id}/header/raw/photo_search_results_latest.json"
        if not _os.path.exists(latest):
            return jsonify({'success': True, 'results': [], 'count': 0})
        with open(latest, 'r') as f:
            data = _json.load(f)
        return jsonify({'success': True, 'results': data.get('results', []), 'count': data.get('count', 0)})
    except Exception as e:
        logger.error(f"Header photo results error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/photo-search/posts/<int:post_id>/header/select', methods=['POST'])
def header_api_photo_select(post_id: int):
    """Select a header photo; persist JSON to header/optimized/selected_{orientation}.json and trigger Unsplash download."""
    try:
        import json as _json, os as _os
        data = request.get_json() or {}
        provider = data.get('provider')
        image_id = data.get('image_id')
        orientation = data.get('orientation')  # 'landscape' or 'portrait'
        if not provider or not image_id:
            return jsonify({'success': False, 'error': 'provider and image_id are required'}), 400
        if orientation and orientation not in ('landscape', 'portrait'):
            return jsonify({'success': False, 'error': 'orientation must be "landscape" or "portrait"'}), 400

        # Load latest results
        latest = f"static/content/posts/{post_id}/header/raw/photo_search_results_latest.json"
        if not _os.path.exists(latest):
            return jsonify({'success': False, 'error': 'No search results found'}), 404
        with open(latest, 'r') as f:
            payload = _json.load(f)
        results = payload.get('results', [])

        # Find selected photo
        selected = None
        for p in results:
            if p.get('provider') == provider and str(p.get('image_id')) == str(image_id):
                selected = p
                break
        if not selected:
            return jsonify({'success': False, 'error': 'Photo not found in results'}), 404

        # Determine orientation if not provided
        width, height = selected.get('width', 0), selected.get('height', 0)
        if not orientation:
            orientation = 'landscape' if width >= height else 'portrait'

        # Trigger Unsplash download event if needed
        if selected.get('provider') == 'unsplash':
            try:
                access_key = os.getenv('UNSPLASH_ACCESS_KEY')
                api = selected.get('api_response') or {}
                links = api.get('links') or {}
                download_loc = selected.get('download_location') or links.get('download_location')
                if access_key and download_loc:
                    parsed = urlparse.urlparse(download_loc)
                    qs = urlparse.parse_qs(parsed.query)
                    url = download_loc if 'client_id' in qs else (download_loc + ('&' if parsed.query else '?') + f"client_id={access_key}")
                    try:
                        urlrequest.urlopen(url, timeout=3)
                    except Exception:
                        pass
            except Exception as _e:
                logger.warning(f"Unsplash download trigger failed: {_e}")

        # Persist selection
        optimized_dir = f"static/content/posts/{post_id}/header/optimized"
        _os.makedirs(optimized_dir, exist_ok=True)
        record = {
            'post_id': post_id,
            'orientation': orientation,
            'photo': selected,
        }
        with open(f"{optimized_dir}/selected_{orientation}.json", 'w') as f:
            _json.dump(record, f, indent=2)

        return jsonify({'success': True, 'selected_photo': selected, 'orientation': orientation})
    except Exception as e:
        logger.error(f"Header photo select error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/photo-search/posts/<int:post_id>/header/selected', methods=['GET'])
def header_api_photo_selected(post_id: int):
    """Return selected header photos for both orientations if present."""
    try:
        import json as _json, os as _os
        optimized_dir = f"static/content/posts/{post_id}/header/optimized"
        out = {'landscape': None, 'portrait': None}
        for ori in ('landscape', 'portrait'):
            path = f"{optimized_dir}/selected_{ori}.json"
            if _os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        out[ori] = _json.load(f)
                except Exception:
                    pass
        return jsonify({'success': True, 'selected_landscape': out['landscape'], 'selected_portrait': out['portrait']})
    except Exception as e:
        logger.error(f"Header photo selected error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
