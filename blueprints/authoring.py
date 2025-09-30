# Authoring Blueprint - Real workflow integration
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

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

@bp.route('/posts/<int:post_id>/sections')
def authoring_sections(post_id):
    """Sections authoring phase - main entry point"""
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
            
            return render_template('authoring/sections/overview.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Section Authoring",
                                 blueprint_name='authoring')
            
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

@bp.route('/posts/<int:post_id>/sections/author_first_drafts')
def authoring_sections_author_first_drafts(post_id):
    """Author First Drafts step - Step 16"""
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
            
            return render_template('authoring/sections/author_first_drafts.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Author First Drafts",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_author_first_drafts: {e}")
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
    """Get all sections for a post from post_development"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get sections from post_development.sections JSONB field
            cursor.execute("""
                SELECT sections
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result or not result['sections']:
                return jsonify({
                    'success': True,
                    'sections': []
                })
            
            sections = result['sections']
            if isinstance(sections, str):
                import json
                sections = json.loads(sections)
            
            if isinstance(sections, dict) and 'sections' in sections:
                sections = sections['sections']
            
            return jsonify({
                'success': True,
                'sections': sections
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_sections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>')
def api_get_section_detail(post_id, section_id):
    """Get details for a specific section"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get sections from post_development.sections JSONB field
            cursor.execute("""
                SELECT sections
                FROM post_development
                WHERE post_id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result or not result['sections']:
                return jsonify({
                    'success': False,
                    'error': 'No sections found'
                }), 404
            
            sections = result['sections']
            if isinstance(sections, str):
                import json
                sections = json.loads(sections)
            
            if isinstance(sections, dict) and 'sections' in sections:
                sections = sections['sections']
            
            # Find the specific section
            section = None
            for s in sections:
                if s.get('id') == section_id or s.get('order') == int(section_id):
                    section = s
                    break
            
            if not section:
                return jsonify({
                    'success': False,
                    'error': 'Section not found'
                }), 404
            
            return jsonify({
                'success': True,
                'section': section
            })
            
    except Exception as e:
        logger.error(f"Error in api_get_section_detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500