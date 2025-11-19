"""Title and summary data get/save API endpoints for header blueprint"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register title/summary data API routes"""
    
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
                    # Use author from database - no recipe-specific logic
                    # Author should come from post.author_id via JOIN in query
                    
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

