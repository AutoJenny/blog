"""
Planning Calendar API - Content Generator

Calendar endpoints for AI-generated posts from products/categories
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging
from datetime import date

logger = logging.getLogger(__name__)

def api_calendar_content_generator(year, week_number):
    """
    Get generated posts scheduled for a specific year and week.
    
    Generated posts are identified by having idea_seed starting with "Generated from"
    and are scheduled via calendar_week_posts.
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Query generated posts scheduled for this week
            # Generated posts have idea_seed like "Generated from product/category: ..."
            # Check if calendar_week_posts table exists, otherwise use calendar_schedule
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'calendar_week_posts'
            """)
            has_week_posts = cursor.fetchone() is not None
            
            if has_week_posts:
                cursor.execute("""
                    SELECT DISTINCT
                        p.id,
                        p.title,
                        p.summary,
                        p.slug,
                        pd.idea_seed,
                        cwp.scheduled_date,
                        cwp.weekday,
                        p.created_at,
                        p.updated_at
                    FROM post p
                    INNER JOIN post_development pd ON p.id = pd.post_id
                    INNER JOIN calendar_week_posts cwp ON p.id = cwp.post_id
                    WHERE pd.idea_seed LIKE 'Generated from %%'
                      AND cwp.year = %s
                      AND cwp.week_number = %s
                    ORDER BY cwp.weekday NULLS LAST, p.created_at DESC
                """, (year, week_number))
            else:
                # Fallback to calendar_schedule table
                cursor.execute("""
                    SELECT DISTINCT
                        p.id,
                        p.title,
                        p.summary,
                        p.slug,
                        pd.idea_seed,
                        cs.scheduled_date,
                        NULL::integer as weekday,
                        p.created_at,
                        p.updated_at
                    FROM post p
                    INNER JOIN post_development pd ON p.id = pd.post_id
                    INNER JOIN calendar_schedule cs ON p.id = cs.post_id
                    WHERE pd.idea_seed LIKE 'Generated from %%'
                      AND EXTRACT(YEAR FROM cs.scheduled_date) = %s
                      AND EXTRACT(WEEK FROM cs.scheduled_date) = %s
                    ORDER BY cs.scheduled_date NULLS LAST, p.created_at DESC
                """, (year, week_number))
            
            generated_posts = []
            rows = cursor.fetchall()
            
            for row in rows:
                # Extract source type from idea_seed
                idea_seed = row.get('idea_seed', '')
                source_type = 'unknown'
                if 'product' in idea_seed.lower():
                    source_type = 'product'
                elif 'category' in idea_seed.lower():
                    source_type = 'category'
                
                generated_posts.append({
                    'id': row['id'],
                    'post_id': row['id'],
                    'title': row.get('title', 'Untitled'),
                    'summary': row.get('summary', ''),
                    'slug': row.get('slug', ''),
                    'source_type': source_type,
                    'idea_seed': idea_seed,
                    'scheduled_date': row.get('scheduled_date'),
                    'weekday': row.get('weekday'),
                    'created_at': row.get('created_at').isoformat() if row.get('created_at') else None,
                    'updated_at': row.get('updated_at').isoformat() if row.get('updated_at') else None
                })
            
            return jsonify({
                'success': True,
                'year': year,
                'week_number': week_number,
                'generated_posts': generated_posts
            })
            
    except Exception as e:
        logger.error(f"Error fetching generated posts for week {year}/{week_number}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

