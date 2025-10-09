"""
Planning Data Module

Contains data retrieval functions extracted from planning_original_backup.py
"""

from flask import jsonify
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

def get_post_data(post_id):
    """Get detailed post data for data tab."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id as post_id, p.*, pd.*
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            post_data = cursor.fetchone()
            
            if not post_data:
                return jsonify({'error': 'Post not found'}), 404
            
            # Convert to dict and separate post and development data
            data = dict(post_data)
            
            # Ensure we use the correct post ID
            if 'post_id' in data:
                data['id'] = data['post_id']
            
            # Separate post info from development info
            post_info = {k: v for k, v in data.items() if not k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions', 'section_structure', 'topic_allocation', 'refined_topics'))}
            development_info = {k: v for k, v in data.items() if k.startswith(('basic_idea', 'provisional_title', 'idea_scope', 'topics_to_cover', 'interesting_facts', 'section_headings', 'section_order', 'main_title', 'intro_blurb', 'seo_optimization', 'summary', 'idea_seed', 'provisional_title_primary', 'concepts', 'facts', 'outline', 'allocated_facts', 'sections', 'title_order', 'expanded_idea', 'image_montage_concept', 'image_montage_prompt', 'image_captions', 'section_structure', 'topic_allocation', 'refined_topics'))}
            
            # Get calendar schedule data for this post
            cursor.execute("""
                SELECT cs.*
                FROM calendar_schedule cs
                WHERE cs.post_id = %s
            """, (post_id,))
            calendar_schedule_data = cursor.fetchall()
            
            # Debug logging
            logger.info(f"Calendar schedule query for post_id={post_id} returned {len(calendar_schedule_data)} results")
            
            # Convert calendar schedule data to list of dicts
            calendar_schedule_list = []
            for row in calendar_schedule_data:
                schedule_dict = dict(row)
                calendar_schedule_list.append(schedule_dict)
                logger.info(f"Calendar schedule entry: {schedule_dict}")
            
            # Get post sections data
            cursor.execute("""
                SELECT ps.*
                FROM post_section ps
                WHERE ps.post_id = %s
                ORDER BY ps.section_order
            """, (post_id,))
            post_sections_data = cursor.fetchall()
            
            # Debug logging
            logger.info(f"Post sections query for post_id={post_id} returned {len(post_sections_data)} results")
            
            # Convert post sections data to list of dicts
            post_sections_list = []
            for row in post_sections_data:
                section_dict = dict(row)
                post_sections_list.append(section_dict)
                logger.info(f"Post section entry: {section_dict}")
            
            return jsonify({
                **post_info,
                'development': development_info,
                'calendar_schedule': calendar_schedule_list,
                'post_sections': post_sections_list
            })
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500
