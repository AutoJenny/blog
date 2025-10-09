"""
Planning Posts API Module

Micro-file for post-specific API endpoints
"""

from flask import request, jsonify
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

def api_posts(post_id):
    """Get post data for planning"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.idea_scope, pd.section_structure, pd.topic_allocation,
                       pd.refined_topics, pd.expanded_idea, pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get calendar schedule
            cursor.execute("""
                SELECT id, year, week_number, scheduled_date, created_at, updated_at
                FROM calendar_schedule 
                WHERE post_id = %s
            """, (post_id,))
            
            schedule = cursor.fetchone()
            
            # Get post sections
            cursor.execute("""
                SELECT id, post_id, section_order, section_heading, section_description, 
                       ideas_to_include, facts_to_include, highlighting, image_concepts,
                       image_prompts, image_alt_text, image_captions, status, polished, draft,
                       image_filename, image_generated_at, image_title, image_width, image_height,
                       selected_image_concept
                FROM post_section 
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            
            sections = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'post': result,
                'schedule': schedule,
                'sections': sections
            })
            
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500
