"""
Planning Post Metadata API
Endpoints for managing post metadata (subtitle, required ideas, etc.)
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from blueprints.header.llm_service import LLMService
import json
import logging
import re

# Initialize LLM service
llm_service = LLMService()

logger = logging.getLogger(__name__)

bp = Blueprint('planning_api_post_metadata', __name__, url_prefix='/planning/api/posts')

@bp.route('/<int:post_id>/subtitle', methods=['GET', 'POST'])
def api_post_subtitle(post_id):
    """Get or update post subtitle"""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT subtitle
                    FROM post
                    WHERE id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Post not found'}), 404
                
                return jsonify({
                    'success': True,
                    'subtitle': result.get('subtitle') or ''
                })
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            subtitle = data.get('subtitle', '').strip()
            
            with db_manager.get_cursor() as cursor:
                # Truncate to 300 characters to match database column size
                subtitle_trimmed = subtitle[:300] if subtitle else None
                cursor.execute("""
                    UPDATE post
                    SET subtitle = %s, updated_at = NOW()
                    WHERE id = %s
                """, (subtitle_trimmed, post_id))
                
                if cursor.rowcount == 0:
                    return jsonify({'success': False, 'error': 'Post not found'}), 404
            
            return jsonify({
                'success': True,
                'subtitle': subtitle
            })
            
    except Exception as e:
        logger.error(f"Error handling subtitle for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:post_id>/required-ideas', methods=['GET', 'POST'])
def api_post_required_ideas(post_id):
    """Get or update required ideas to include (stored in embedding_overrides)"""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT embedding_overrides
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({
                        'success': True,
                        'required_ideas': []
                    })
                
                overrides = result.get('embedding_overrides') or {}
                if isinstance(overrides, str):
                    try:
                        overrides = json.loads(overrides)
                    except:
                        overrides = {}
                
                required_ideas = overrides.get('required_ideas', [])
                if not isinstance(required_ideas, list):
                    required_ideas = []
                
                return jsonify({
                    'success': True,
                    'required_ideas': required_ideas
                })
        
        elif request.method == 'POST':
            data = request.get_json() or {}
            required_ideas = data.get('required_ideas', [])
            
            if not isinstance(required_ideas, list):
                return jsonify({'success': False, 'error': 'required_ideas must be an array'}), 400
            
            with db_manager.get_cursor() as cursor:
                # Get existing embedding_overrides
                cursor.execute("""
                    SELECT embedding_overrides
                    FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                result = cursor.fetchone()
                
                # Parse existing overrides
                overrides = {}
                if result and result.get('embedding_overrides'):
                    existing = result.get('embedding_overrides')
                    if isinstance(existing, str):
                        try:
                            overrides = json.loads(existing)
                        except:
                            overrides = {}
                    elif isinstance(existing, dict):
                        overrides = existing
                
                # Update required_ideas
                overrides['required_ideas'] = required_ideas
                
                # Ensure post_development record exists
                cursor.execute("""
                    SELECT id FROM post_development WHERE post_id = %s
                """, (post_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO post_development (post_id, embedding_overrides, updated_at)
                        VALUES (%s, %s, NOW())
                    """, (post_id, json.dumps(overrides)))
                else:
                    cursor.execute("""
                        UPDATE post_development
                        SET embedding_overrides = %s, updated_at = NOW()
                        WHERE post_id = %s
                    """, (json.dumps(overrides), post_id))
            
            return jsonify({
                'success': True,
                'required_ideas': required_ideas
            })
            
    except Exception as e:
        logger.error(f"Error handling required ideas for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:post_id>/generate-subtitle-from-theme', methods=['POST'])
def api_generate_subtitle_from_theme(post_id):
    """Generate subtitle from theme using LLM"""
    try:
        data = request.get_json() or {}
        theme_title = data.get('theme_title', '').strip()
        theme_description = data.get('theme_description', '').strip()
        
        if not theme_title:
            return jsonify({'success': False, 'error': 'theme_title is required'}), 400
        
        # Create prompt for subtitle generation
        system_prompt = """You are a content writer for clan.com, a blog about Scottish culture and heritage.
Generate expanded descriptive subtitles (a few sentences) that explain what the article will cover.
Subtitles should be informative and help readers understand the article's scope, topics, and focus."""
        
        task_prompt = f"""Generate an expanded subtitle (description) for a blog post about: {theme_title}
{f'Theme description: {theme_description}' if theme_description else ''}

This subtitle should be a few sentences describing what the article will cover, not a marketing tagline.

Requirements:
- Should be 2-4 sentences (approximately 150-300 characters)
- Should describe what topics, aspects, or content the article will explore
- Should explain the scope and focus of the article
- Should fit the clan.com blog's focus on Scottish culture and heritage
- Should help readers understand what they'll learn from the article
- Use clear, descriptive language (not marketing copy)
- Focus on content coverage and educational value, not selling or enticing
- Write as a brief expanded idea of what the article will cover

Example format: "This article explores [key aspects] of [topic], examining [specific elements]. We'll delve into [related topics] and their significance in Scottish [culture/heritage/history]. The piece will cover [additional content areas] to provide a comprehensive understanding of [main theme]."

CRITICAL: Return ONLY the subtitle text, no explanation, no quotes, no JSON."""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': task_prompt}
        ]
        
        # Execute LLM request
        logger.info(f"Generating subtitle from theme: {theme_title}")
        llm_response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in llm_response:
            logger.error(f"LLM generation failed: {llm_response['error']}")
            return jsonify({'success': False, 'error': f'LLM generation failed: {llm_response["error"]}'}), 500
        
        generated_content = llm_response.get('content', '').strip()
        
        # Clean up the response (remove quotes, extra whitespace)
        generated_content = re.sub(r'^["\']|["\']$', '', generated_content)
        generated_content = generated_content.strip()
        
        # Limit to 300 characters (allowing for a few sentences)
        if len(generated_content) > 300:
            # Try to cut at sentence boundary
            sentences = generated_content[:297].rsplit('.', 1)
            if len(sentences) > 1:
                generated_content = sentences[0] + '.'
            else:
                generated_content = generated_content[:297] + '...'
        
        return jsonify({
            'success': True,
            'subtitle': generated_content
        })
        
    except Exception as e:
        logger.error(f"Error generating subtitle from theme for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
