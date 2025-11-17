"""
Image Data API Endpoints
API routes for retrieving post/section data and images
"""

from flask import Blueprint, jsonify, request
from config.database import db_manager
from blueprints.authoring_api_sections import api_get_sections as sections_api_func
import logging
import os
import re
import json

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register data API routes with the blueprint"""
    
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
        """Get sections data for imaging workflow - use same logic as authoring"""
        return sections_api_func(post_id)

    @bp.route('/api/posts/<int:post_id>/sections/<section_id>/raw-image')
    def imaging_get_raw_image(post_id, section_id):
        """Get raw image path(s) for a section, accepting both numeric and string section IDs.
        Returns both landscape and portrait images if available."""
        try:
            # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
            resolved_section_id = None
            if section_id.isdigit():
                resolved_section_id = int(section_id)
            else:
                # Try to parse trailing number from patterns like section_1
                m = re.search(r'(\d+)$', section_id)
                if m:
                    section_order = int(m.group(1))
                    with db_manager.get_cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT id FROM post_section
                            WHERE post_id = %s AND section_order = %s
                            """,
                            (post_id, section_order),
                        )
                        row = cursor.fetchone()
                        if row:
                            resolved_section_id = row['id']

            if resolved_section_id is None:
                return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

            # Check for landscape image (new structure)
            landscape_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/landscape/raw/{resolved_section_id}.png"
            portrait_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/portrait/raw/{resolved_section_id}_portrait.png"
            
            # Also check old structure for backward compatibility
            old_raw_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/raw/{resolved_section_id}.png"
            
            result = {
                'success': True,
                'landscape_path': None,
                'portrait_path': None,
                'path': None,  # For backward compatibility
                'type': 'raw'
            }
            
            if os.path.exists(landscape_path):
                result['landscape_path'] = f"/static/content/posts/{post_id}/sections/{resolved_section_id}/landscape/raw/{resolved_section_id}.png"
                result['path'] = result['landscape_path']  # Default to landscape for backward compatibility
            
            if os.path.exists(portrait_path):
                result['portrait_path'] = f"/static/content/posts/{post_id}/sections/{resolved_section_id}/portrait/raw/{resolved_section_id}_portrait.png"
            
            # Fallback to old structure if new structure doesn't exist
            if not result['landscape_path'] and os.path.exists(old_raw_path):
                result['path'] = f"/static/content/posts/{post_id}/sections/{resolved_section_id}/raw/{resolved_section_id}.png"
                result['landscape_path'] = result['path']
            
            if result['landscape_path'] or result['portrait_path']:
                return jsonify(result)
            else:
                return jsonify({'success': False, 'message': 'No raw image found for this section'})

        except Exception as e:
            logger.error(f"Error getting raw image: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

    @bp.route('/api/posts/<int:post_id>/sections/<section_id>/image')
    def imaging_get_section_image(post_id, section_id):
        """Get persisted image path for a section, accepting both numeric and string section IDs"""
        try:
            # Resolve section_id: if numeric, use directly; if like section_1, map to section_order = 1
            resolved_section_id = None
            if section_id.isdigit():
                resolved_section_id = int(section_id)
            else:
                # Try to parse trailing number from patterns like section_1
                m = re.search(r'(\d+)$', section_id)
                if m:
                    section_order = int(m.group(1))
                    with db_manager.get_cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT id FROM post_section
                            WHERE post_id = %s AND section_order = %s
                            """,
                            (post_id, section_order),
                        )
                        row = cursor.fetchone()
                        if row:
                            resolved_section_id = row['id']

            if resolved_section_id is None:
                return jsonify({'success': False, 'error': f'Unable to resolve section id: {section_id}'}), 400

            # Optimise page must not fall back to raw; only return optimized if it exists
            optimized_path = f"static/content/posts/{post_id}/sections/{resolved_section_id}/optimized/{resolved_section_id}.jpg"
            if os.path.exists(optimized_path):
                return jsonify({
                    'success': True,
                    'path': f"/static/content/posts/{post_id}/sections/{resolved_section_id}/optimized/{resolved_section_id}.jpg",
                    'type': 'optimized'
                })
            # No optimized image available
            return jsonify({'success': False, 'message': 'No optimized image found for this section'})

        except Exception as e:
            logger.error(f"Error getting section image: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

    @bp.route('/api/generation-events', methods=['GET'])
    def imaging_get_generation_events():
        """Get generation events for audit/debugging"""
        try:
            post_id = request.args.get('post_id', type=int)
            section_id = request.args.get('section_id', type=int)
            limit = request.args.get('limit', type=int, default=50)
            
            with db_manager.get_cursor() as cursor:
                query = """
                    SELECT id, post_id, section_id, model_key, params, prompt_text, 
                           rendered_prompt, result_path, success, error_message, 
                           generation_time_ms, created_at
                    FROM image_generation_events
                    WHERE 1=1
                """
                params = []
                
                if post_id:
                    query += " AND post_id = %s"
                    params.append(post_id)
                
                if section_id:
                    query += " AND section_id = %s"
                    params.append(section_id)
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                events = cursor.fetchall()
                
                return jsonify({
                    'success': True,
                    'events': [dict(event) for event in events],
                    'count': len(events)
                })
        except Exception as e:
            logger.error(f"Error getting generation events: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

