"""

# Auto-generated from blueprints/planning.py
# Module: repositories/posts.py

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


def save_section_structure(post_id, structure_data):
    """Save section structure design to database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET section_structure = %s, structure_design_at = NOW()
                WHERE post_id = %s
            """, (json.dumps(structure_data), post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, section_structure, structure_design_at, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW(), NOW())
                """, (post_id, json.dumps(structure_data)))
            
            cursor.connection.commit()
    except Exception as e:
        logger.error(f"Error saving section structure: {e}")
        raise


def save_topic_allocation(post_id, allocation_data, raw_response=None):
    """Save topic allocation to database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post_development 
                SET topic_allocation = %s, allocation_completed_at = NOW()
                WHERE post_id = %s
            """, (json.dumps(allocation_data), post_id))
            
            if cursor.rowcount == 0:
                # Create new record if it doesn't exist
                cursor.execute("""
                    INSERT INTO post_development (post_id, topic_allocation, allocation_completed_at, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW(), NOW())
                """, (post_id, json.dumps(allocation_data)))
            
            cursor.connection.commit()
    except Exception as e:
        logger.error(f"Error saving topic allocation: {e}")


def load_topic_allocation(post_id):
    """Load existing topic allocation from database"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic_allocation FROM post_development 
                WHERE post_id = %s AND topic_allocation IS NOT NULL
            """, (post_id,))
            
            result = cursor.fetchone()
            if result and result['topic_allocation']:
                return json.loads(result['topic_allocation'])
            return None
    except Exception as e:
        logger.error(f"Error loading topic allocation: {e}")
        return None
        raise


