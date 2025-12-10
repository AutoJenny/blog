"""
Planning Posts API Module

Micro-file for post-specific API endpoints
"""

from flask import request, jsonify
from config.database import db_manager
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def api_posts(post_id):
    """Get post data for planning"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       p.profile_product_id, p.profile_category_id, p.profile_type,
                       pd.idea_scope, pd.section_structure, pd.topic_allocation,
                       pd.refined_topics, pd.expanded_idea, pd.idea_seed, pd.sections
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Post not found'}), 404
            
            # Get calendar schedule with selected theme
            # Check for calendar_week_posts_v2 table (current table)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts_v2'
                ) as has_v2_posts
            """)
            table_check = cursor.fetchone()
            has_v2_table = table_check['has_v2_posts'] if table_check else False
            
            schedule = None
            if has_v2_table:
                # Use V2 architecture - get schedule from calendar_week_items_deprecated (the actual table)
                # calendar_week_posts_v2 is a view that only shows recipe/profile, so query calendar_week_items_deprecated directly
                cursor.execute("""
                    SELECT cwi.year, cwi.week_number, cwi.scheduled_date, cwi.created_at, cwi.updated_at,
                           cws.selected_theme_id,
                           ct.theme_title as selected_theme_title
                    FROM calendar_week_items_deprecated cwi
                    LEFT JOIN calendar_week_selection_v2 cws ON cwi.year = cws.year AND cwi.week_number = cws.week_number
                    LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                    WHERE cwi.item_id = %s
                      AND cwi.is_active = TRUE
                    ORDER BY cwi.created_at DESC
                    LIMIT 1
                """, (post_id,))
                schedule = cursor.fetchone()
            else:
                # Check for legacy calendar_week_posts table
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_posts'
                    ) as has_posts
                """)
                legacy_check = cursor.fetchone()
                has_legacy_table = legacy_check['has_posts'] if legacy_check else False
                
                if has_legacy_table:
                    cursor.execute("""
                        SELECT cwp.year, cwp.week_number, cwp.scheduled_date, cwp.created_at, cwp.updated_at,
                               cws.selected_theme_id,
                               ct.theme_title as selected_theme_title
                        FROM calendar_week_posts cwp
                        LEFT JOIN calendar_week_selection cws ON cwp.year = cws.year AND cwp.week_number = cws.week_number
                        LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                        WHERE cwp.post_id = %s
                        ORDER BY cwp.created_at DESC
                        LIMIT 1
                    """, (post_id,))
                    schedule = cursor.fetchone()
            
            # Get post sections from post_section table
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
            
            # If no sections found in post_section table, check post_development.sections
            if not sections and result.get('sections'):
                import json
                try:
                    sections_data = json.loads(result['sections'])
                    if isinstance(sections_data, dict) and 'sections' in sections_data:
                        sections = sections_data['sections']
                    elif isinstance(sections_data, list):
                        sections = sections_data
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse sections from post_development: {e}")
                    sections = []
            
            return jsonify({
                'success': True,
                'post': result,
                'schedule': schedule,
                'sections': sections
            })
            
    except Exception as e:
        logger.error(f"Error fetching post data: {e}")
        return jsonify({'error': str(e)}), 500


def confirm_calendar_idea():
    """Consolidated endpoint to confirm a calendar idea and produce a post.

    Input JSON: { "topic": str, "week_number": int, "year"?: int, "force_new"?: bool }
    Behavior:
      1) Check if topic exists this year (reuses unless force_new=True)
      2) Create post if needed (status=draft)
      3) Upsert calendar_schedule (post_id, year, week_number)
      4) Upsert post_development.idea_seed = f"{topic}: {optional description}" (here: topic only)
    Returns: { success: true, post_id }
    """
    try:
        data = request.get_json(force=True) or {}
        topic = (data.get('topic') or '').strip()
        week_number = data.get('week_number')
        year = data.get('year') or datetime.now().year
        force_new = bool(data.get('force_new', False))
        if not topic or not isinstance(week_number, int):
            return jsonify({ 'error': 'topic and week_number are required' }), 400

        with db_manager.get_cursor() as cursor:
            post_id = None
            if not force_new:
                # Check existing topic (same year)
                # CRITICAL: Only reuse posts that are NOT deleted
                # If a deleted post exists, create a new one instead
                cursor.execute("""
                    SELECT p.id
                    FROM post p
                    LEFT JOIN post_development pd ON pd.post_id = p.id
                    WHERE (p.title = %s OR pd.idea_seed ILIKE %s)
                      AND p.status != 'deleted'
                    ORDER BY p.updated_at DESC
                    LIMIT 1
                """, (topic, f"%{topic}%"))
                row = cursor.fetchone()
                if row:
                    post_id = row['id']

            # Create post if needed
            if not post_id:
                # Generate slug from topic
                base = re.sub(r"[^a-z0-9\-]+", '-', (topic or '').lower().strip().replace(' ', '-'))
                base = re.sub(r"-+", '-', base).strip('-') or 'post'
                slug = base
                # Ensure slug uniqueness (best-effort: append suffix if clash)
                suffix = 1
                while True:
                    cursor.execute("SELECT 1 FROM post WHERE slug = %s LIMIT 1", (slug,))
                    if not cursor.fetchone():
                        break
                    suffix += 1
                    slug = f"{base}-{suffix}"
                cursor.execute("""
                    INSERT INTO post (title, slug, status, created_at, updated_at)
                    VALUES (%s, %s, 'draft', NOW(), NOW())
                    RETURNING id
                """, (topic, slug))
                post_id = cursor.fetchone()['id']

            # Check if selected theme exists for this week (required)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_selection'
                )
            """)
            has_new_table = cursor.fetchone()['exists']
            
            if has_new_table:
                # Check if selected theme exists (REQUIRED)
                cursor.execute("""
                    SELECT selected_theme_id
                    FROM calendar_week_selection
                    WHERE year = %s AND week_number = %s
                """, (year, week_number))
                theme_selection = cursor.fetchone()
                
                if not theme_selection:
                    return jsonify({
                        'success': False,
                        'error': f'No theme selected for week {year}/{week_number}. Please select a theme first.'
                    }), 400
                
                # Get default publication day for themed posts
                from blueprints.post_type_config import get_publication_day_for_post_type
                themed_config = get_publication_day_for_post_type('themed', cursor)
                default_weekday = themed_config['day'] if themed_config else 3  # Fallback to Wednesday
                
                # Assign post to week using calendar_week_posts with default weekday
                cursor.execute("""
                    INSERT INTO calendar_week_posts (year, week_number, post_id, weekday, scheduled_date, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NULL, NOW(), NOW())
                    ON CONFLICT (year, week_number, post_id) DO UPDATE SET
                        weekday = EXCLUDED.weekday,
                        updated_at = NOW()
                """, (year, week_number, post_id, default_weekday))
                
                # DUAL-WRITE: Also write to calendar_week_items (new unified table)
                # Determine item_type based on post type
                cursor.execute("""
                    SELECT post_type, profile_type, recipe_id, recipe_week_number
                    FROM post
                    WHERE id = %s
                """, (post_id,))
                post_info = cursor.fetchone()
                
                if post_info:
                    # Check if calendar_week_items table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'calendar_week_items'
                        )
                    """)
                    has_week_items = cursor.fetchone()['exists']
                    
                    if has_week_items:
                        item_type = None
                        metadata = {}
                        
                        if post_info.get('post_type') == 'recipe':
                            item_type = 'recipe'
                            if post_info.get('recipe_id'):
                                metadata['recipe_definition_id'] = post_info['recipe_id']
                            if post_info.get('recipe_week_number'):
                                metadata['recipe_week_number'] = post_info['recipe_week_number']
                        elif post_info.get('profile_type'):
                            item_type = 'profile'
                            metadata['profile_type'] = post_info['profile_type']
                            # Add profile-specific IDs if available
                            cursor.execute("""
                                SELECT profile_product_id, profile_category_id
                                FROM post
                                WHERE id = %s
                            """, (post_id,))
                            profile_info = cursor.fetchone()
                            if profile_info:
                                if profile_info.get('profile_product_id'):
                                    metadata['profile_product_id'] = profile_info['profile_product_id']
                                if profile_info.get('profile_category_id'):
                                    metadata['profile_category_id'] = profile_info['profile_category_id']
                        
                        # Only write if we determined an item_type
                        if item_type:
                            cursor.execute("""
                                INSERT INTO calendar_week_items (
                                    item_type, item_id, year, week_number, weekday, 
                                    is_active, metadata, created_at, updated_at
                                ) VALUES (
                                    %s, %s, %s, %s, %s, TRUE, %s, NOW(), NOW()
                                )
                                ON CONFLICT (year, week_number, item_type, item_id)
                                DO UPDATE SET
                                    weekday = EXCLUDED.weekday,
                                    metadata = EXCLUDED.metadata,
                                    updated_at = NOW()
                            """, (item_type, post_id, year, week_number, default_weekday, metadata))
            else:
                # Fallback to old calendar_schedule table during migration
                cursor.execute("""
                    INSERT INTO calendar_schedule (post_id, year, week_number, scheduled_date, created_at, updated_at)
                    VALUES (%s, %s, %s, NULL, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """, (post_id, year, week_number))

                # Ensure only one schedule row per post/year/week: cleanup duplicates if schema allows multiples
                cursor.execute("""
                    DELETE FROM calendar_schedule cs
                    USING calendar_schedule cs2
                    WHERE cs.id > cs2.id
                      AND cs.post_id = cs2.post_id
                      AND cs.year = cs2.year
                      AND cs.week_number = cs2.week_number
                """)

            # Upsert post_development.idea_seed
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (post_id)
                DO UPDATE SET idea_seed = EXCLUDED.idea_seed, updated_at = NOW()
            """, (post_id, topic))

            # Bump post.updated_at so it reflects this action in listings
            cursor.execute("""
                UPDATE post
                SET updated_at = NOW()
                WHERE id = %s
            """, (post_id,))

        return jsonify({ 'success': True, 'post_id': post_id })
    except Exception as e:
        logger.error(f"Error in confirm_calendar_idea: {e}")
        return jsonify({ 'error': str(e) }), 500
