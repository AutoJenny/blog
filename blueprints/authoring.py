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
            
            # Convert to list of dictionaries
            sections_list = []
            for section in sections:
                sections_list.append({
                    'id': section['id'],
                    'order': section['section_order'],
                    'title': section['section_heading'],
                    'description': section['section_description'],
                    'status': section['status'] or 'draft',
                    'draft_content': section['draft'] or '',
                    'polished_content': section['polished'] or '',
                    'ideas_to_include': section['ideas_to_include'] or '',
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
                'description': section['section_description'],
                'status': section['status'] or 'draft',
                'draft_content': section['draft'] or '',
                'polished_content': section['polished'] or '',
                'ideas_to_include': section['ideas_to_include'] or '',
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