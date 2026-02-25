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
    """Get or replace required ideas (stored in post_required_idea). W2: single source of truth."""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, post_id, text, sort_order
                    FROM post_required_idea
                    WHERE post_id = %s
                    ORDER BY sort_order ASC, id ASC
                """, (post_id,))
                rows = cursor.fetchall()
                required_ideas = [
                    {'id': r.get('id'), 'text': r.get('text') or '', 'sort_order': r.get('sort_order', 0)}
                    for r in rows
                ]
                return jsonify({'success': True, 'required_ideas': required_ideas})

        elif request.method == 'POST':
            data = request.get_json() or {}
            required_ideas = data.get('required_ideas', [])
            if not isinstance(required_ideas, list):
                return jsonify({'success': False, 'error': 'required_ideas must be an array'}), 400
            # Normalize: allow [{ text, sort_order }] or ["text", ...]
            normalized = []
            for i, item in enumerate(required_ideas):
                if isinstance(item, str):
                    normalized.append((item.strip(), i))
                elif isinstance(item, dict):
                    text = (item.get('text') or item.get('idea') or '').strip()
                    sort_order = item.get('sort_order', i)
                    normalized.append((text, sort_order))
                else:
                    normalized.append((str(item).strip(), i))
            with db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM post_required_idea WHERE post_id = %s", (post_id,))
                for sort_order, (text, _) in enumerate(normalized):
                    if text:
                        cursor.execute(
                            "INSERT INTO post_required_idea (post_id, text, sort_order) VALUES (%s, %s, %s)",
                            (post_id, text, sort_order),
                        )
                cursor.connection.commit()
                cursor.execute("""
                    SELECT id, post_id, text, sort_order FROM post_required_idea
                    WHERE post_id = %s ORDER BY sort_order ASC, id ASC
                """, (post_id,))
                rows = cursor.fetchall()
                out = [{'id': r.get('id'), 'text': r.get('text') or '', 'sort_order': r.get('sort_order', 0)} for r in rows]
            return jsonify({'success': True, 'required_ideas': out})
    except Exception as e:
        logger.error(f"Error handling required ideas for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:post_id>/required-ideas/items', methods=['POST'])
def api_post_required_idea_add(post_id):
    """Add one required idea (post_required_idea). Body: { text, sort_order? }."""
    try:
        data = request.get_json() or {}
        text = (data.get('text') or data.get('idea') or '').strip()
        if not text:
            return jsonify({'success': False, 'error': 'text is required'}), 400
        sort_order = data.get('sort_order')
        with db_manager.get_cursor() as cursor:
            if sort_order is None:
                cursor.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM post_required_idea WHERE post_id = %s",
                    (post_id,)
                )
                row = cursor.fetchone()
                sort_order = (row.get('coalesce') if isinstance(row, dict) else row[0]) or 0
            cursor.execute(
                "INSERT INTO post_required_idea (post_id, text, sort_order) VALUES (%s, %s, %s) RETURNING id, text, sort_order",
                (post_id, text, sort_order)
            )
            row = cursor.fetchone()
            cursor.connection.commit()
        out = {'id': row.get('id'), 'text': row.get('text') or '', 'sort_order': row.get('sort_order', 0)}
        return jsonify({'success': True, 'required_idea': out}), 201
    except Exception as e:
        logger.error(f"Error adding required idea for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:post_id>/required-ideas/items/<int:item_id>', methods=['PATCH', 'DELETE'])
def api_post_required_idea_item(post_id, item_id):
    """Update or delete one required idea (post_required_idea)."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, text, sort_order FROM post_required_idea WHERE post_id = %s AND id = %s",
                (post_id, item_id)
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Not found'}), 404
            if request.method == 'DELETE':
                cursor.execute("DELETE FROM post_required_idea WHERE post_id = %s AND id = %s", (post_id, item_id))
                cursor.connection.commit()
                return jsonify({'success': True, 'deleted': item_id}), 200
            # PATCH
            data = request.get_json() or {}
            text = data.get('text')
            sort_order = data.get('sort_order')
            if text is not None:
                cursor.execute(
                    "UPDATE post_required_idea SET text = %s, sort_order = COALESCE(%s, sort_order) WHERE post_id = %s AND id = %s",
                    (text.strip(), sort_order, post_id, item_id)
                )
            elif sort_order is not None:
                cursor.execute(
                    "UPDATE post_required_idea SET sort_order = %s WHERE post_id = %s AND id = %s",
                    (sort_order, post_id, item_id)
                )
            else:
                return jsonify({'success': False, 'error': 'text or sort_order required'}), 400
            cursor.connection.commit()
            cursor.execute(
                "SELECT id, text, sort_order FROM post_required_idea WHERE post_id = %s AND id = %s",
                (post_id, item_id)
            )
            row = cursor.fetchone()
        out = {'id': row.get('id'), 'text': row.get('text') or '', 'sort_order': row.get('sort_order', 0)}
        return jsonify({'success': True, 'required_idea': out}), 200
    except Exception as e:
        logger.error(f"Error updating required idea for post {post_id}: {e}")
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
