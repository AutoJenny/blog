# Authoring Imaging API Blueprint
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
from config.authoring_panel_configs import get_panel_config
import logging
import json
import os
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
bp = Blueprint('authoring_imaging', __name__)

# Import micro-modules
from blueprints.authoring_api_sections import api_get_sections as sections_api_func, api_get_section as section_api_func

# Import LLM service
try:
    from modules.llm_service import llm_service
except ImportError:
    # Fallback for when llm_service is not available
    llm_service = None

@bp.route('/posts/<int:post_id>/sections/image_concepts')
def authoring_sections_image_concepts(post_id):
    """Image concepts step - Step 53"""
    try:
        # CRITICAL: Check for week context in URL params to determine correct post
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        
        with db_manager.get_cursor() as cursor:
            # Get post details with taxonomy illustration_method using the correct post_id
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id, content_type.illustration_method
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get illustration_method from taxonomy (default to 'LLM-creation' if null/not found)
            illustration_method = post.get('illustration_method') or 'LLM-creation'
            
            # Get panel configuration for this illustration method
            panel_config = get_panel_config(illustration_method)
            
            # Log which post and illustration method are being used
            if target_post_id != post_id:
                logger.info(f"Illustration method determined from post {target_post_id}: {illustration_method} (URL had post_id {post_id})")
            
            return render_template('authoring/sections/image_concepts.html', 
                                 post_id=post_id,  # Keep original post_id for URL consistency
                                 post=post,
                                 page_title="Image Concepts",
                                 blueprint_name='authoring',
                                 illustration_method=illustration_method,
                                 panel_config=panel_config)
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_concepts: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/image_prompts')
def authoring_sections_image_prompts(post_id):
    """Image prompts step - Step 54"""
    try:
        # CRITICAL: Check for week context in URL params to determine correct post
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        logger.info(f"[IMAGE_PROMPTS] Week context from URL: year={url_year}, week={url_week}")
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"[IMAGE_PROMPTS] Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"[IMAGE_PROMPTS] Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        else:
            logger.warning(f"[IMAGE_PROMPTS] No week context provided - using URL post_id {post_id}")
        
        logger.info(f"[IMAGE_PROMPTS] Using target_post_id={target_post_id} for taxonomy lookup")
        
        with db_manager.get_cursor() as cursor:
            # Get post details with taxonomy illustration_method using the correct post_id
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.content_type_id, content_type.illustration_method
                FROM post p
                LEFT JOIN taxonomy_item content_type ON p.content_type_id = content_type.id
                WHERE p.id = %s
            """, (target_post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get illustration_method from taxonomy (default to 'LLM-creation' if null/not found)
            illustration_method = post.get('illustration_method') or 'LLM-creation'
            
            # Log which post and illustration method are being used
            if target_post_id != post_id:
                logger.info(f"Illustration method determined from post {target_post_id}: {illustration_method} (URL had post_id {post_id})")
            
            return render_template('authoring/sections/image_prompts.html', 
                                 post_id=post_id,  # Keep original post_id for URL consistency
                                 post=post,
                                 page_title="Image Prompts",
                                 blueprint_name='authoring',
                                 illustration_method=illustration_method)
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_prompts: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/image_captions')
def authoring_sections_image_captions(post_id):
    """Image captions step - Step 55"""
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

def _get_post_extra_settings(cursor, post_id):
    """Helper function to get post extra_settings"""
    cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
    row = cursor.fetchone()
    return row['extra_settings'] if row and row['extra_settings'] else {}

def _set_post_extra_settings(cursor, post_id, extra_settings):
    """Helper function to set post extra_settings"""
    cursor.execute("UPDATE post SET extra_settings = %s WHERE id = %s", (json.dumps(extra_settings), post_id))

@bp.route('/api/posts/<int:post_id>/styles', methods=['GET'])
def api_list_post_styles(post_id):
    """List all styles for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            active_index = imaging.get('activeIndex', 0)
            # Fallback to permanent system default if none exist (do NOT persist)
            if not styles:
                # Try to get default style from taxonomy first
                from utils.taxonomy_helpers import get_default_image_style
                taxonomy_style = get_default_image_style(post_id)
                
                if taxonomy_style:
                    styles = [taxonomy_style]
                    logger.info(f"Using taxonomy default image style: {taxonomy_style.get('name', 'Unknown')}")
                else:
                    # Fallback to permanent system default (Watercolour and Pen & Ink)
                    styles = [{
                        'name': 'Watercolour and Pen & Ink',
                        'style_json': {
                            'medium': 'watercolour and pen and ink',
                            'technique': 'brushstrokes fading out by ending towards the edges of the image',
                            'palette': ['ochres', 'siennas', 'umbers', 'celestial blues', 'golds'],
                            'composition': 'rule-of-thirds with negative space',
                            'lighting': 'soft, ethereal, golden hour',
                            'constraints': ['no text', 'no watermark in frame', 'edges fade to white'],
                            'negatives': ['hyperrealism', 'sharp edges', 'solid borders']
                        }
                    }]
                    logger.info("Using system default image style (no taxonomy default found)")
                active_index = 0
            
            return jsonify({
                'success': True,
                'styles': styles,
                'activeIndex': active_index,
                'count': len(styles)
            })
    except Exception as e:
        logger.error(f"Error listing styles: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/styles/active', methods=['GET'])
def api_get_active_style(post_id):
    """Get the currently active style for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            active_index = imaging.get('activeIndex', 0)
            
            active_style = styles[active_index] if styles and 0 <= active_index < len(styles) else None
            
            # If no saved styles, check taxonomy default
            if not active_style:
                from utils.taxonomy_helpers import get_default_image_style
                taxonomy_style = get_default_image_style(post_id)
                if taxonomy_style:
                    active_style = taxonomy_style
                    logger.info(f"Using taxonomy default image style for active: {taxonomy_style.get('name', 'Unknown')}")
            
            return jsonify({
                'active_style': active_style,
                'active_index': active_index if active_style else -1,
                'has_styles': len(styles) > 0
            })
    except Exception as e:
        logger.error(f"Error getting active style: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/styles', methods=['POST'])
def api_create_style(post_id):
    """Create a new style for a post"""
    try:
        data = request.get_json()
        style_name = data.get('name')
        style_json = data.get('style_json', {})
        
        if not style_name:
            return jsonify({'error': 'Style name is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            
            # Initialize imaging structure if it doesn't exist
            if 'imaging' not in extra_settings:
                extra_settings['imaging'] = {}
            if 'styles' not in extra_settings['imaging']:
                extra_settings['imaging']['styles'] = []
            
            # Create new style
            new_style = {
                'name': style_name,
                'style_json': style_json,
                'created_at': json.dumps({'timestamp': 'now'})  # Simple timestamp
            }
            
            # Add to styles array
            extra_settings['imaging']['styles'].append(new_style)
            
            # Set as active if it's the first style
            if len(extra_settings['imaging']['styles']) == 1:
                extra_settings['imaging']['activeIndex'] = 0
            
            # Save back to database
            _set_post_extra_settings(cursor, post_id, extra_settings)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'style': new_style,
                'active_index': extra_settings['imaging']['activeIndex']
            })
            
    except Exception as e:
        logger.error(f"Error creating style: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/styles/<int:style_index>/activate', methods=['POST'])
def api_activate_style(post_id, style_index):
    """Activate a specific style by index"""
    try:
        with db_manager.get_cursor() as cursor:
            extra_settings = _get_post_extra_settings(cursor, post_id)
            imaging = extra_settings.get('imaging', {})
            styles = imaging.get('styles', [])
            
            if not styles or style_index < 0 or style_index >= len(styles):
                return jsonify({'error': 'Invalid style index'}), 400
            
            # Update active index
            extra_settings['imaging']['activeIndex'] = style_index
            
            # Save back to database
            _set_post_extra_settings(cursor, post_id, extra_settings)
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'active_style': styles[style_index],
                'active_index': style_index
            })
            
    except Exception as e:
        logger.error(f"Error activating style: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>/save-image-prompt', methods=['POST'])
def api_save_image_prompt(post_id, section_id):
    """Save image prompt for a section"""
    try:
        data = request.get_json()
        image_prompt = data.get('image_prompt')
        
        if not image_prompt:
            return jsonify({'error': 'Image prompt is required'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Create a JSON structure similar to the existing image_prompts format
            image_prompt_json = {
                "image_prompt": image_prompt,
                "dimensions": "1792x1024",  # Default dimensions
                "style": "inkwash and watercolour",
                "base_concept": image_prompt
            }
            
            # Update post_section table
            cursor.execute("""
                UPDATE post_section 
                SET image_prompts = %s
                WHERE post_id = %s AND id = %s
            """, (json.dumps(image_prompt_json), post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image prompt saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving image prompt: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/render-prompt-preview', methods=['POST'])
def api_render_prompt_preview():
    """Preview rendered prompt for a specific model"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        model_key = data.get('model_key', 'gpt-image-1')
        
        if not post_id or not section_id:
            return jsonify({'error': 'post_id and section_id are required'}), 400
        
        # Import here to avoid circular imports
        from modules.prompt_service import prompt_service
        
        rendered_prompt, metadata = prompt_service.render_prompt_for_model(
            post_id, section_id, model_key, use_override=True
        )
        
        return jsonify({
            'success': True,
            'rendered_prompt': rendered_prompt,
            'metadata': metadata,
            'model_key': model_key
        })
        
    except Exception as e:
        logger.error(f"Error rendering prompt preview: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/preview-rendered-prompt', methods=['POST'])
def api_preview_rendered_prompt(post_id, section_id):
    """Preview rendered prompt for a specific section"""
    try:
        data = request.get_json()
        model_key = data.get('model_key', 'gpt-image-1')
        
        # Import here to avoid circular imports
        from modules.prompt_service import prompt_service
        
        rendered_prompt, metadata = prompt_service.render_prompt_for_model(
            post_id, section_id, model_key, use_override=True
        )
        
        return jsonify({
            'success': True,
            'rendered_prompt': rendered_prompt,
            'metadata': metadata,
            'model_key': model_key,
            'length': len(rendered_prompt)
        })
        
    except Exception as e:
        logger.error(f"Error previewing rendered prompt: {e}")
        return jsonify({'error': str(e)}), 500

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

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/save-image-prompt', methods=['POST'])
def api_save_image_prompt_legacy(post_id, section_id):
    """Save the generated image prompt for a specific section"""
    try:
        data = request.get_json()
        image_prompt = data.get('image_prompt', '')
        
        if not image_prompt:
            return jsonify({'error': 'Missing image_prompt'}), 400
        
        with db_manager.get_cursor() as cursor:
            # Create a JSON structure similar to the existing image_prompts format
            image_prompt_json = {
                "image_prompt": image_prompt,
                "dimensions": "1792x1024",  # Default dimensions
                "style": "inkwash and watercolour",
                "base_concept": image_prompt
            }
            
            # Handle both string and integer section IDs
            if str(section_id).isdigit():
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
                        
                        # Find the section by ID
                        for section in sections_list:
                            if section.get('id') == section_id:
                                section['image_prompts'] = image_prompt_json
                                break
                        
                        # Update the sections data
                        cursor.execute("""
                            UPDATE post_development 
                            SET sections = %s, updated_at = NOW()
                            WHERE post_id = %s
                        """, (json.dumps(sections_data), post_id))
                        
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Error parsing sections JSON: {e}")
                        return jsonify({'error': 'Failed to update section data'}), 500
                else:
                    return jsonify({'error': 'Section data not found'}), 404
            
        return jsonify({
            'success': True,
            'message': 'Image prompt saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving image prompt: {e}")
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
        logger.info(f"[IMAGE_CONCEPTS] Starting generation for post_id={post_id}, section_id={section_id}")
        
        # CRITICAL: Check for week context in URL params to determine correct post
        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        logger.info(f"[IMAGE_CONCEPTS] Week context from URL: year={url_year}, week={url_week}")
        
        # SINGLE SOURCE OF TRUTH: Use approved utility for week/post resolution
        target_post_id = post_id
        if url_year and url_week:
            from utils.week_post_resolver import resolve_post_for_week
            resolved_post_id = resolve_post_for_week(url_year, url_week)
            if resolved_post_id:
                target_post_id = resolved_post_id
                logger.info(f"[IMAGE_CONCEPTS] Week {url_year}/{url_week} resolved to post_id {target_post_id} (instead of URL post_id {post_id})")
            else:
                logger.warning(f"[IMAGE_CONCEPTS] Week {url_year}/{url_week} has no scheduled post - using URL post_id {post_id}")
        else:
            logger.warning(f"[IMAGE_CONCEPTS] No week context provided - using URL post_id {post_id}")
        
        logger.info(f"[IMAGE_CONCEPTS] Using target_post_id={target_post_id} for section lookup")
        
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
                """, (target_post_id, int(section_id)))
                section = cursor.fetchone()
            
            # If not found in post_section or section_id is not numeric, try post_development
            if not section:
                cursor.execute("""
                    SELECT sections FROM post_development 
                    WHERE post_id = %s AND sections IS NOT NULL
                """, (target_post_id,))
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
                            
                            # Handle both numeric IDs (1,2,3) and string IDs (section_1, section_2, etc.)
                            section_matches = False
                            if section_id_from_data == section_id:
                                section_matches = True
                            elif section_id.startswith('section_') and str(section_id_from_data) == section_id.replace('section_', ''):
                                section_matches = True
                            elif section_id.isdigit() and str(section_id_from_data) == section_id:
                                section_matches = True
                            
                            if section_matches:
                                section_order = section_data.get('order', i+1)
                                
                                # Get section content from post_section table (including section_heading which has titles from titling step)
                                cursor.execute("""
                                    SELECT draft, polished, status, section_heading, section_description
                                    FROM post_section
                                    WHERE post_id = %s AND section_order = %s
                                """, (target_post_id, section_order))
                                post_section_data = cursor.fetchone()
                                
                                # Prioritize section_heading from post_section (synced from titling) over title from JSON
                                section_heading = None
                                if post_section_data and post_section_data.get('section_heading'):
                                    section_heading = post_section_data['section_heading']
                                else:
                                    section_heading = section_data.get('title', f'Section {i+1}')
                                
                                # Prioritize section_description from post_section over original from JSON
                                section_description = None
                                if post_section_data and post_section_data.get('section_description'):
                                    section_description = post_section_data['section_description']
                                else:
                                    section_description = section_data.get('original', '')
                                
                                section = {
                                    'id': section_id_from_data,
                                    'section_order': section_order,
                                    'section_heading': section_heading,
                                    'section_description': section_description,
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
                logger.error(f"[IMAGE_CONCEPTS] Section not found: post_id={target_post_id}, section_id={section_id}")
                return jsonify({'error': f'Section {section_id} not found for post {target_post_id}'}), 404
            
            logger.info(f"[IMAGE_CONCEPTS] Found section: id={section.get('id')}, order={section.get('section_order')}, heading={section.get('section_heading', '')[:50]}")
            
            # Get post data for context
            cursor.execute("""
                SELECT p.id, pd.idea_seed, pd.expanded_idea
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (target_post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get topic allocation for this section (use target_post_id, not URL post_id)
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (target_post_id,))
            topic_result = cursor.fetchone()
            
            topics = []
            if topic_result and topic_result['topic_allocation']:
                try:
                    if isinstance(topic_result['topic_allocation'], dict):
                        topic_allocation = topic_result['topic_allocation']
                    else:
                        topic_allocation = json.loads(topic_result['topic_allocation'])
                    
                    # Get topics for this section
                    allocations = topic_allocation.get('allocations', [])
                    section_order_for_matching = section.get('section_order') if section else None
                    
                    for allocation in allocations:
                        # Try multiple matching strategies since section_id format varies
                        allocation_section_id = allocation.get('section_id')
                        if (allocation_section_id == section_id or 
                            str(allocation_section_id) == str(section_id) or
                            (section_order_for_matching and allocation_section_id == section_order_for_matching) or
                            (section_order_for_matching and str(allocation_section_id) == str(section_order_for_matching))):
                            topics = allocation.get('topics', [])
                            logger.info(f"Found topics for section {section_id}: {len(topics)} topics")
                            break
                except Exception as e:
                    logger.error(f"Error parsing topic_allocation: {e}")
            
            # Determine prompt by illustration_method (no fallbacks)
            concepts_prompt_name = 'Image Concepts Generation (Photo-harvesting)' if (post_data.get('illustration_method') == 'Photo-harvesting') else 'Image Concepts Generation'
            # Get the image concepts prompt
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (concepts_prompt_name,))
            
            prompt_data = cursor.fetchone()
            if not prompt_data:
                return jsonify({'error': 'Image Concepts prompt not found'}), 404
            
            # Build the prompt with actual data
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            logger.info(f"[DEBUG] System prompt length: {len(system_prompt) if system_prompt else 0}")
            logger.info(f"[DEBUG] System prompt preview: {system_prompt[:100] if system_prompt else 'None'}")
            logger.info(f"[DEBUG] *** SYSTEM PROMPT DEBUG ***")
            
            # Replace placeholders with actual data
            if post_data.get('illustration_method') == 'Photo-harvesting':
                # STRICT: Use only section_description; zero out all other inputs
                only_desc = section['section_description'] or ''
                prompt_text = prompt_text.replace('[data:idea_seed]', '')
                prompt_text = prompt_text.replace('[data:expanded_idea]', '')
                prompt_text = prompt_text.replace('[data:title]', '')
                prompt_text = prompt_text.replace('[data:subtitle]', only_desc)
                prompt_text = prompt_text.replace('[data:section_text]', '')
                prompt_text = prompt_text.replace('[data:selected_concept]', '')
                prompt_text = prompt_text.replace('[data:topics]', '')
            else:
                prompt_text = prompt_text.replace('[data:idea_seed]', post_data['idea_seed'] or '')
                prompt_text = prompt_text.replace('[data:expanded_idea]', post_data['expanded_idea'] or '')
                prompt_text = prompt_text.replace('[data:title]', section['section_heading'] or '')
                prompt_text = prompt_text.replace('[data:subtitle]', section['section_description'] or '')
                prompt_text = prompt_text.replace('[data:section_text]', section['polished'] or section['draft'] or '')
                prompt_text = prompt_text.replace('[data:selected_concept]', '')
                topics_text = '\n'.join([f'- {topic}' for topic in topics])
                prompt_text = prompt_text.replace('[data:topics]', topics_text)
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            logger.info(f"[DEBUG] Messages prepared: {len(messages)} messages")
            logger.info(f"[DEBUG] System message included: {any(m['role'] == 'system' for m in messages)}")
            
            # Check if LLM service is available
            if not llm_service:
                logger.error("[IMAGE_CONCEPTS] LLM service not available")
                return jsonify({'error': 'LLM service not available'}), 500
            
            # Execute LLM request with retry logic for valid JSON
            max_retries = 3
            image_concepts = None
            
            logger.info(f"[IMAGE_CONCEPTS] Starting LLM generation with {max_retries} retries")
            
            for attempt in range(max_retries):
                # Add intercept context for message capture (use target_post_id, not URL post_id)
                intercept_context = {
                    'post_id': target_post_id,
                    'section_id': section_id
                }
                logger.info(f"[IMAGE_CONCEPTS] Attempt {attempt + 1}/{max_retries}: Calling LLM service")
                result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, intercept_context=intercept_context)
                
                logger.info(f"[IMAGE_CONCEPTS] LLM response received: has_content={bool(result.get('content'))}, has_error={bool(result.get('error'))}")
                
                if 'error' in result:
                    logger.error(f"[IMAGE_CONCEPTS] LLM error on attempt {attempt + 1}: {result['error']}")
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
            
            # Parse concepts to get first concept ID for auto-selection
            selected_concept_id = None
            try:
                concepts_data = json.loads(image_concepts)
                if concepts_data.get('concepts') and len(concepts_data['concepts']) > 0:
                    selected_concept_id = concepts_data['concepts'][0]['concept_id']
                    logger.info(f"Auto-selected concept {selected_concept_id} for section {section_id}")
            except Exception as e:
                logger.warning(f"Could not parse concepts for auto-selection: {e}")
            
            # PRIMARY: Always save to post_section.image_concepts table if section_id is numeric
            # This is the main database table storage - JSON is secondary
            section_saved_to_table = False
            if section_id.isdigit():
                try:
                    if selected_concept_id:
                        cursor.execute("""
                            UPDATE post_section 
                            SET image_concepts = %s, selected_image_concept = %s
                            WHERE post_id = %s AND id = %s
                        """, (image_concepts, selected_concept_id, target_post_id, int(section_id)))
                        logger.info(f"[DEBUG] Saved image_concepts and selected_image_concept to post_section table for section {section_id} (post_id {target_post_id})")
                    else:
                        cursor.execute("""
                            UPDATE post_section 
                            SET image_concepts = %s
                            WHERE post_id = %s AND id = %s
                        """, (image_concepts, target_post_id, int(section_id)))
                        logger.info(f"[DEBUG] Saved image_concepts to post_section table for section {section_id} (post_id {target_post_id})")
                    section_saved_to_table = True
                except Exception as e:
                    logger.error(f"Error saving to post_section table for section {section_id}: {e}")
                    return jsonify({'error': f'Failed to save to post_section table (primary storage): {str(e)}'}), 500
            
            # SECONDARY: Also update post_development.sections JSON for backwards compatibility
            # This is maintained as a secondary storage, but post_section table is primary
            cursor.execute("""
                SELECT sections FROM post_development 
                WHERE post_id = %s AND sections IS NOT NULL
            """, (target_post_id,))
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
                    
                    # Find and update the section in JSON
                    section_found_in_json = False
                    for i, section_data in enumerate(sections_list):
                        section_id_from_data = section_data.get('id', f'section_{i+1}')
                        
                        # Handle both numeric IDs (1,2,3) and string IDs (section_1, section_2, etc.)
                        section_matches = False
                        if str(section_id_from_data) == str(section_id):
                            section_matches = True
                        elif section_id.startswith('section_') and str(section_id_from_data) == section_id.replace('section_', ''):
                            section_matches = True
                        elif section_id.isdigit() and str(section_id_from_data) == section_id:
                            section_matches = True
                        
                        if section_matches:
                            section_data['image_concepts'] = image_concepts
                            
                            # Auto-select the first concept if no selection exists
                            if not section_data.get('selected_image_concept') and selected_concept_id:
                                section_data['selected_image_concept'] = selected_concept_id
                            
                            section_found_in_json = True
                            break
                    
                    # Update the JSON in database
                    if section_found_in_json:
                        cursor.execute("""
                            UPDATE post_development 
                            SET sections = %s
                            WHERE post_id = %s
                        """, (json.dumps(sections_data), target_post_id))
                        logger.info(f"[DEBUG] Also updated image_concepts in post_development.sections JSON for section {section_id}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Error updating sections JSON (non-critical): {e}")
            
            # Commit all changes
            cursor.connection.commit()
            
            # Verify primary storage succeeded
            if section_id.isdigit() and not section_saved_to_table:
                return jsonify({'error': 'Failed to save to post_section table (primary storage)'}), 500
            
            return jsonify({
                'success': True,
                'image_concepts': image_concepts,
                'message': 'Image concepts generated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error generating image concepts: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/generate-image-prompt-from-builder', methods=['POST'])
def api_generate_image_prompt_from_builder():
    """Generate image prompt using the compiled prompt from Prompt Builder"""
    try:
        data = request.get_json()
        compiled_prompt = data.get('compiled_prompt')
        post_id = data.get('post_id')
        section_id = data.get('section_id')
        
        # NEW: Get user preferences for compression/expansion
        enable_compression = data.get('enable_compression', True)
        enable_expansion = data.get('enable_expansion', False)  # DEFAULT TO FALSE
        
        llm_provider = data.get('llm_provider', 'Ollama')
        llm_model = data.get('llm_model', 'llama3.2:latest')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
        
        # NEW: Track all LLM calls for transparency
        pipeline_steps = []
        
        logger.info(f"[DEBUG] API received: post_id={post_id}, section_id={section_id}")
        logger.info(f"[DEBUG] Compiled prompt: {compiled_prompt[:100]}...")
        
        if not compiled_prompt:
            return jsonify({'error': 'Missing compiled_prompt'}), 400
        
        if not post_id or not section_id:
            return jsonify({'error': 'Missing post_id or section_id'}), 400
        
        # Step 1: Initial generation
        messages = [{'role': 'user', 'content': compiled_prompt}]
        # Add intercept context for message capture
        intercept_context = {
            'post_id': post_id,
            'section_id': section_id
        }
        result = llm_service.execute_llm_request(llm_provider.lower(), llm_model, messages, intercept_context=intercept_context)
        
        if 'error' in result:
            return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
        
        generated_prompt = result['content'].strip()
        
        # NEW: Log first step
        pipeline_steps.append({
            'step': 'initial_generation',
            'input': compiled_prompt,
            'output': generated_prompt,
            'llm_call': {'provider': llm_provider, 'model': llm_model, 'messages': messages}
        })
        
        # Parse JSON response
        try:
            response_data = json.loads(generated_prompt)
            if 'image_prompt' in response_data:
                generated_prompt = response_data['image_prompt']
        except json.JSONDecodeError:
            logger.warning("LLM response is not valid JSON, using full response")
        
        # Get imaging model and limits
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT imaging_model_selection FROM post_development WHERE post_id = %s", (post_id,))
            row = cursor.fetchone()
            selected_model = (row.get('imaging_model_selection') if row else None) or 'sdxl-lora'
        
        model_limits = {
            'dall-e-3': 4000,
            'dall-e-2': 1000,
            'sdxl-lora': 400,
            'gpt-image-1': 2000,
        }
        imaging_limit = model_limits.get(selected_model, 400)
        
        # Step 2: Compression (if enabled and needed)
        if enable_compression and len(generated_prompt) > imaging_limit:
            target_min = max(0, imaging_limit - 40)
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
            compact = llm_service.execute_llm_request(llm_provider.lower(), llm_model, compact_messages, intercept_context=intercept_context)
            
            if 'content' in compact:
                compact_text = compact['content'].strip()
                try:
                    compact_json = json.loads(compact_text)
                    compact_prompt = compact_json.get('image_prompt') or compact_text
                except Exception:
                    compact_prompt = compact_text
                
                if len(compact_prompt) <= imaging_limit:
                    # NEW: Log compression step
                    pipeline_steps.append({
                        'step': 'compression',
                        'input': generated_prompt,
                        'output': compact_prompt,
                        'llm_call': {'system_prompt': compact_system, 'messages': compact_messages}
                    })
                    generated_prompt = compact_prompt
        
        # Step 3: Expansion (if enabled and under budget)
        if enable_expansion and len(generated_prompt) < int(imaging_limit * 0.8):
            target_min = max(0, imaging_limit - 40)
            
            # NEW: Get active style guidelines to inject into expansion prompt
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
                post_row = cursor.fetchone()
                active_style_json = None
                
                if post_row and post_row.get('extra_settings'):
                    imaging = post_row['extra_settings'].get('imaging', {})
                    styles = imaging.get('styles', [])
                    active_index = imaging.get('activeIndex', 0)
                    
                    if styles and 0 <= active_index < len(styles):
                        active_style = styles[active_index]
                        active_style_json = active_style.get('style_json', {})
            
            # NEW: Use active style guidelines in expansion
            style_guidelines_text = ""
            if active_style_json:
                style_guidelines_text = f"\n\nIMPORTANT: You MUST incorporate these exact style guidelines:\n{json.dumps(active_style_json, indent=2)}"
            
            expand_system = (
                "You are an expert at expanding image prompts while keeping them within a strict limit. "
                f"Expand the user's prompt to approach {target_min}-{imaging_limit} characters (do not exceed {imaging_limit}). "
                "Add concrete detail (subject, setting, composition, lighting, palette) based ONLY on the existing prompt content. "
                "DO NOT add new style instructions that conflict with the provided Style Guidelines. "
                f"{style_guidelines_text}"
                "Respond ONLY as JSON in the exact format: {\"image_prompt\": \"...\"}. No commentary."
            )
            expand_messages = [
                { 'role': 'system', 'content': expand_system },
                { 'role': 'user', 'content': generated_prompt }
            ]
            expand = llm_service.execute_llm_request(llm_provider.lower(), llm_model, expand_messages, intercept_context=intercept_context)
            
            if 'content' in expand:
                expand_text = expand['content'].strip()
                try:
                    expand_json = json.loads(expand_text)
                    expanded_prompt = expand_json.get('image_prompt') or expand_text
                except Exception:
                    expanded_prompt = expand_text
                
                if len(expanded_prompt) <= imaging_limit:
                    # NEW: Log expansion step
                    pipeline_steps.append({
                        'step': 'expansion',
                        'input': generated_prompt,
                        'output': expanded_prompt,
                        'llm_call': {'system_prompt': expand_system, 'messages': expand_messages}
                    })
                    generated_prompt = expanded_prompt
        
        # NEW: Get active style for saving (not hardcoded)
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
            post_row = cursor.fetchone()
            active_style_name = "inkwash and watercolour"  # fallback
            
            if post_row and post_row.get('extra_settings'):
                imaging = post_row['extra_settings'].get('imaging', {})
                styles = imaging.get('styles', [])
                active_index = imaging.get('activeIndex', 0)
                
                if styles and 0 <= active_index < len(styles):
                    active_style = styles[active_index]
                    active_style_name = active_style.get('name', active_style_name)
        
        # NEW: Get dimensions from model selection (not hardcoded)
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT param_key, default_value 
                FROM model_param_default 
                WHERE model_key = %s AND param_key = 'size'
            """, (selected_model,))
            size_row = cursor.fetchone()
            default_dimensions = size_row['default_value'] if size_row else "1792x1024"
        
        # Save to database with correct values
        with db_manager.get_cursor() as cursor:
            image_prompt_json = {
                "image_prompt": generated_prompt,
                "dimensions": default_dimensions,  # FROM MODEL SELECTION
                "style": active_style_name,  # FROM ACTIVE STYLE
                "base_concept": generated_prompt
            }
            
            # Handle both numeric and legacy string section IDs robustly
            section_id_str = str(section_id)
            is_numeric_id = section_id_str.isdigit()
            if is_numeric_id:
                # Numeric section ID (int or numeric string) - update post_section table
                cursor.execute("""
                    UPDATE post_section 
                    SET image_prompts = %s
                    WHERE post_id = %s AND id = %s
                """, (json.dumps(image_prompt_json), post_id, int(section_id_str)))
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
            
            logger.info(f"[DEBUG] Generated prompt: {generated_prompt[:100]}...")
            logger.info(f"[DEBUG] Saved to database for post {post_id}, section {section_id}")
            
            # NEW: Return detailed pipeline information
            return jsonify({
                'success': True,
                'image_prompt': generated_prompt,
                'message': 'Image prompt generated and saved successfully',
                'pipeline_steps': pipeline_steps,  # NEW: Full transparency
                'final_length': len(generated_prompt),
                'character_limit': imaging_limit,
                'compression_used': any(step['step'] == 'compression' for step in pipeline_steps),
                'expansion_used': any(step['step'] == 'expansion' for step in pipeline_steps)
            })
            
    except Exception as e:
        logger.error(f"Error generating image prompt: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ui/preferences', methods=['GET', 'POST'])
def api_ui_preferences():
    """Get or save UI preferences for accordion states"""
    try:
        if request.method == 'GET':
            # Get preferences from database
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT preference_key, preference_value FROM ui_user_preferences 
                    WHERE user_id = 1 AND category = 'image_prompts'
                """)
                rows = cursor.fetchall()
                
                preferences = {}
                for row in rows:
                    try:
                        preferences[row['preference_key']] = json.loads(row['preference_value'])
                    except (json.JSONDecodeError, TypeError):
                        preferences[row['preference_key']] = row['preference_value']
                
                return jsonify({
                    'success': True,
                    'preferences': preferences
                })
        
        elif request.method == 'POST':
            data = request.get_json()
            preferences = data.get('preferences', {})
            
            # Save preferences to database
            with db_manager.get_cursor() as cursor:
                for key, value in preferences.items():
                    cursor.execute("""
                        INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category)
                        VALUES (1, %s, %s, 'json', 'image_prompts')
                        ON CONFLICT (user_id, preference_key) 
                        DO UPDATE SET preference_value = %s, updated_at = CURRENT_TIMESTAMP
                    """, (key, json.dumps(value), json.dumps(value)))
                
                return jsonify({
                    'success': True,
                    'message': 'Preferences saved successfully'
                })
                
    except Exception as e:
        logger.error(f"Error handling UI preferences: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
