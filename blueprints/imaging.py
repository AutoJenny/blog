# Imaging Blueprint - Standalone image generation workflow
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('imaging', __name__, url_prefix='/imaging')

@bp.route('/posts/<int:post_id>/sections/image-generation')
def imaging_sections_image_generation(post_id):
    """Image Generation page - standalone imaging workflow"""
    try:
        return render_template('imaging/sections/image_generation.html', 
                             post_id=post_id)
    except Exception as e:
        logger.error(f"Error rendering image generation page: {str(e)}")
        return f"Error: {str(e)}", 500

@bp.route('/api/posts/<int:post_id>')
def api_get_post(post_id):
    """Get post data for imaging workflow"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get basic post data
            cursor.execute("""
                SELECT id, title, summary, status, created_at, updated_at
                FROM post
                WHERE id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get development data
            cursor.execute("""
                SELECT idea_seed, expanded_idea, basic_idea, provisional_title
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            
            development = cursor.fetchone()
            
            # Combine post and development data
            post_data = dict(post)
            if development:
                post_data.update(dict(development))
            
            return jsonify({
                'success': True,
                'post': post_data
            })
    except Exception as e:
        logger.error(f"Error getting post data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get sections data for imaging workflow"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description,
                       image_prompts, image_captions, selected_image_concept
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'sections': [dict(section) for section in sections]
            })
    except Exception as e:
        logger.error(f"Error getting sections data: {str(e)}")
        return jsonify({'error': str(e)}), 500
