# Authoring Blueprint - Core functionality only
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)
bp = Blueprint('authoring', __name__)

# Import micro-modules
from blueprints.authoring_api_sections import api_get_sections as sections_api_func, api_get_section as section_api_func

# Helper functions
def _get_post_extra_settings(cursor, post_id):
    """Helper function to get post extra_settings"""
    cursor.execute("SELECT extra_settings FROM post WHERE id = %s", (post_id,))
    row = cursor.fetchone()
    return row['extra_settings'] if row and row['extra_settings'] else {}

def _set_post_extra_settings(cursor, post_id, extra_settings):
    """Helper function to set post extra_settings"""
    cursor.execute("UPDATE post SET extra_settings = %s WHERE id = %s", (json.dumps(extra_settings), post_id))

# Main authoring routes
@bp.route('/posts/<int:post_id>')
def authoring_post_overview(post_id):
    """Authoring post overview page"""
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
    """Drafting step - Step 50"""
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
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_drafting: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/author-first-drafts')
def authoring_sections_author_first_drafts(post_id):
    """Author first drafts step - Step 51"""
    return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))

@bp.route('/posts/<int:post_id>/sections')
def authoring_sections_overview(post_id):
    """Sections overview page"""
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
                                 page_title="Sections Overview",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_overview: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections/ideas_to_include')
def authoring_sections_ideas_to_include(post_id):
    """Ideas to include step - Step 49"""
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
    """Fix language step - Step 52"""
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

# Image concepts route moved to authoring_api_imaging.py

# Image prompts route moved to authoring_api_imaging.py

# Image captions route moved to authoring_api_imaging.py

# DEPRECATED: Image generation route moved to imaging stage
@bp.route('/posts/<int:post_id>/sections/image_generation')
def authoring_sections_image_generation(post_id):
    """DEPRECATED: Image generation step - moved to imaging stage"""
    return redirect(url_for('imaging.sections_image_generation', post_id=post_id))

# Styles API functions moved to authoring_api_imaging.py

# Image-related API functions moved to authoring_api_imaging.py

# Test route
@bp.route('/test-sections')
def test_sections():
    """Test route for sections functionality"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM post_section")
            result = cursor.fetchone()
            return jsonify({'sections_count': result['count']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API routes delegated to micro-modules
@bp.route('/api/posts/<int:post_id>/sections')
def api_get_sections(post_id):
    """Get all sections for a post - delegated to micro-module"""
    return sections_api_func(post_id)

@bp.route('/api/posts/<int:post_id>/sections/<section_id>')
def api_get_section_detail(post_id, section_id):
    """Get detailed information for a specific section - delegated to micro-module"""
    return section_api_func(post_id, section_id)

@bp.route('/api/posts/<int:post_id>/sections/<int:section_id>', methods=['PUT'])
def api_save_section_content(post_id, section_id):
    """Save section content (draft, polished, etc.) - delegated to micro-module"""
    try:
        data = request.get_json()
        
        # Extract content fields
        draft = data.get('draft', '')
        polished = data.get('polished', '')
        ideas_to_include = data.get('ideas_to_include', '')
        facts_to_include = data.get('facts_to_include', '')
        highlighting = data.get('highlighting', '')
        status = data.get('status', 'draft')
        
        with db_manager.get_cursor() as cursor:
            # Update the section
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, polished = %s, ideas_to_include = %s, 
                    facts_to_include = %s, highlighting = %s, status = %s,
                    updated_at = NOW()
                WHERE post_id = %s AND id = %s
            """, (draft, polished, ideas_to_include, facts_to_include, 
                  highlighting, status, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section content saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving section content: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate', methods=['POST'])
def api_generate_section_draft(post_id, section_id):
    """Generate section draft using LLM - delegated to micro-module"""
    try:
        data = request.get_json()
        
        # Get section data
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT section_heading, section_description, ideas_to_include, 
                       facts_to_include, highlighting
                FROM post_section 
                WHERE post_id = %s AND id = %s
            """, (post_id, section_id))
            section = cursor.fetchone()
            
            if not section:
                return jsonify({'error': 'Section not found'}), 404
            
            # Get post context
            cursor.execute("""
                SELECT title, status FROM post WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get LLM prompt template
            cursor.execute("""
                SELECT prompt_text, system_prompt
                FROM llm_prompt 
                WHERE name = 'Section Drafting'
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            prompt_data = cursor.fetchone()
            
            if not prompt_data:
                return jsonify({'error': 'Section Drafting prompt not found'}), 404
            
            # Build the prompt
            prompt_text = prompt_data['prompt_text']
            system_prompt = prompt_data['system_prompt']
            
            # Replace placeholders
            prompt_text = prompt_text.replace('[data:post_title]', post['title'] or '')
            prompt_text = prompt_text.replace('[data:section_heading]', section['section_heading'] or '')
            prompt_text = prompt_text.replace('[data:section_description]', section['section_description'] or '')
            prompt_text = prompt_text.replace('[data:ideas_to_include]', section['ideas_to_include'] or '')
            prompt_text = prompt_text.replace('[data:facts_to_include]', section['facts_to_include'] or '')
            prompt_text = prompt_text.replace('[data:highlighting]', section['highlighting'] or '')
            
            # Prepare messages for LLM
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Execute LLM request
            from modules.llm_service import llm_service
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                return jsonify({'error': f'LLM generation failed: {result["error"]}'}), 500
            
            generated_content = result['content'].strip()
            
            # Save the generated content
            cursor.execute("""
                UPDATE post_section 
                SET draft = %s, status = 'draft', updated_at = NOW()
                WHERE post_id = %s AND id = %s
            """, (generated_content, post_id, section_id))
            
            cursor.connection.commit()
            
            return jsonify({
                'success': True,
                'draft': generated_content,
                'message': 'Section draft generated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error generating section draft: {e}")
        return jsonify({'error': str(e)}), 500
