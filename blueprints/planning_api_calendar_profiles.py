"""
Planning Calendar API - Profiles

Calendar profiles endpoints for Product & Category Profiles
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging
from datetime import date

logger = logging.getLogger(__name__)

def api_calendar_profiles(year, week_number):
    """
    Get profiles scheduled for a specific year and week.
    
    Profiles are posts with profile_type IS NOT NULL, scheduled via calendar_week_posts.
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Check if calendar_week_items table exists (new unified table)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_items'
                )
            """)
            has_week_items = cursor.fetchone()['exists']
            
            if has_week_items:
                # Query profiles scheduled for this week using calendar_week_items
                cursor.execute("""
                    SELECT DISTINCT
                        p.id,
                        p.title,
                        p.profile_type,
                        p.profile_producer_name,
                        p.profile_standfirst,
                        p.slug,
                        cwi.scheduled_date,
                        cwi.weekday,
                        p.created_at,
                        p.updated_at
                    FROM post p
                    INNER JOIN calendar_week_items cwi ON p.id = cwi.item_id
                    WHERE cwi.item_type = 'profile'
                      AND cwi.year = %s
                      AND cwi.week_number = %s
                      AND cwi.is_active = TRUE
                    ORDER BY cwi.weekday NULLS LAST, p.title
                """, (year, week_number))
            else:
                # Fallback: Check if calendar_week_posts table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_posts'
                    )
                """)
                has_week_posts = cursor.fetchone()['exists']
                
                if has_week_posts:
                    # Query profiles scheduled for this week using calendar_week_posts
                    cursor.execute("""
                        SELECT DISTINCT
                            p.id,
                            p.title,
                            p.profile_type,
                            p.profile_producer_name,
                            p.profile_standfirst,
                            p.slug,
                            cwp.scheduled_date,
                            cwp.weekday,
                            p.created_at,
                            p.updated_at
                        FROM post p
                        INNER JOIN calendar_week_posts cwp ON p.id = cwp.post_id
                        WHERE p.profile_type IS NOT NULL
                          AND cwp.year = %s
                          AND cwp.week_number = %s
                        ORDER BY cwp.weekday NULLS LAST, p.title
                    """, (year, week_number))
                else:
                    # Fallback to calendar_schedule table
                    cursor.execute("""
                        SELECT DISTINCT
                            p.id,
                            p.title,
                            p.profile_type,
                            p.profile_producer_name,
                            p.profile_standfirst,
                            p.slug,
                            cs.scheduled_date,
                            NULL::integer as weekday,
                            p.created_at,
                            p.updated_at
                        FROM post p
                        INNER JOIN calendar_schedule cs ON p.id = cs.post_id
                        WHERE p.profile_type IS NOT NULL
                          AND EXTRACT(YEAR FROM cs.scheduled_date) = %s
                          AND EXTRACT(WEEK FROM cs.scheduled_date) = %s
                        ORDER BY cs.scheduled_date NULLS LAST, p.title
                    """, (year, week_number))
            
            profiles = []
            rows = cursor.fetchall()
            
            for row in rows:
                if isinstance(row, dict):
                    profile = {
                        'id': row['id'],
                        'title': row['title'],
                        'profile_type': row['profile_type'],
                        'profile_producer_name': row.get('profile_producer_name'),
                        'profile_standfirst': row.get('profile_standfirst'),
                        'slug': row.get('slug'),
                        'scheduled_date': row['scheduled_date'].isoformat() if row.get('scheduled_date') else None,
                        'weekday': row.get('weekday'),
                        'day': row.get('weekday'),  # Alias for compatibility
                        'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                        'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
                    }
                else:
                    # Handle tuple results
                    profile = {
                        'id': row[0],
                        'title': row[1],
                        'profile_type': row[2],
                        'profile_producer_name': row[3] if len(row) > 3 else None,
                        'profile_standfirst': row[4] if len(row) > 4 else None,
                        'slug': row[5] if len(row) > 5 else None,
                        'scheduled_date': row[6].isoformat() if len(row) > 6 and row[6] else None,
                        'weekday': row[7] if len(row) > 7 else None,
                        'day': row[7] if len(row) > 7 else None,
                        'created_at': row[8].isoformat() if len(row) > 8 and row[8] else None,
                        'updated_at': row[9].isoformat() if len(row) > 9 and row[9] else None
                    }
                
                profiles.append(profile)
            
            return jsonify(profiles)
            
    except Exception as e:
        logger.error(f"Error fetching profiles for week {year}/{week_number}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500




