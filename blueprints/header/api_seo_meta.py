"""SEO meta API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from .helpers import resolve_target_post_id
import logging
import json
import re

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register SEO meta API routes"""
    
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

