# Header Blueprint - Blog post header and metadata generation
from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
import logging
import json
import re

logger = logging.getLogger(__name__)

bp = Blueprint('header', __name__, url_prefix='/header')

# Main routes
@bp.route('/posts/<int:post_id>/title-summary')
def header_title_summary(post_id):
    """Title & Summary substage - Generate post title, subtitle, slug, and summary"""
    return render_template('header/title_summary.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/header-image')
def header_header_image(post_id):
    """Header Image substage - Create header image with caption and alt text"""
    return render_template('header/header_image.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/seo-meta')
def header_seo_meta(post_id):
    """SEO & Meta substage - Generate SEO metadata including meta title, description, and tags"""
    return render_template('header/seo_meta.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/publishing-details')
def header_publishing_details(post_id):
    """Publishing Details substage - Set author, word count, publish date, and status"""
    return render_template('header/publishing_details.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/final-review')
def header_final_review(post_id):
    """Final Review substage - Review and finalize all header elements before publishing"""
    return render_template('header/final_review.html', post_id=post_id)

# API endpoints
@bp.route('/api/posts/<int:post_id>/generate-title-summary', methods=['POST'])
def api_generate_title_summary(post_id):
    """Generate multiple title options, subtitle, slug, summary"""
    try:
        data = request.get_json()
        
        # Get post data for context
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, summary, expanded_idea, idea_seed
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # TODO: Implement LLM generation for titles and summary
            # For now, return empty data that will be populated by actual generation
            title_options = []
            subtitle = ""
            slug = ""
            summary = ""
            
            return jsonify({
                'success': True,
                'title_options': title_options,
                'subtitle': subtitle,
                'slug': slug,
                'summary': summary
            })
            
    except Exception as e:
        logger.error(f"Error generating title and summary: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-header-image', methods=['POST'])
def api_generate_header_image(post_id):
    """Generate header image with caption and alt text"""
    try:
        data = request.get_json()
        
        # TODO: Implement header image generation
        # For now, return empty data that will be populated by actual generation
        return jsonify({
            'success': True,
            'image_path': '',
            'caption': '',
            'alt_text': '',
            'title': ''
        })
        
    except Exception as e:
        logger.error(f"Error generating header image: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>/generate-seo-meta', methods=['POST'])
def api_generate_seo_meta(post_id):
    """Generate meta title, description, tags"""
    try:
        data = request.get_json()
        
        # Get post data for context
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT title, summary, idea_seed
                FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            post_data = cursor.fetchone()
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # TODO: Implement LLM generation for SEO meta
            # For now, return empty data that will be populated by actual generation
            meta_title = ""
            meta_description = ""
            meta_tags = ""
            
            return jsonify({
                'success': True,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'meta_tags': meta_tags
            })
            
    except Exception as e:
        logger.error(f"Error generating SEO meta: {e}")
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
