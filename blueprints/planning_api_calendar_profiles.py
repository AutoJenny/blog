"""
Planning Calendar API - Profiles

Calendar profiles endpoints for Product & Category Profiles

UPDATED: Now uses unified resolver (resolve_item_for_week) as single source of truth.
This ensures consistency with scheduling view and all other calendar views.
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
from utils.calendar_resolver import resolve_item_for_week
import logging
from datetime import date

logger = logging.getLogger(__name__)

def api_calendar_profiles(year, week_number):
    """
    Get profiles scheduled for a specific year and week.
    
    NOW USES: Unified resolver (resolve_item_for_week) as single source of truth.
    This ensures consistency with scheduling view and all other calendar views.
    
    Returns profiles based on cyclic schedule + overrides, matching the scheduling view.
    """
    try:
        profiles = []
        
        # Use unified resolver for both profile types
        # This ensures we get the same data as the scheduling view
        profile_product = resolve_item_for_week("profile_product", year, week_number)
        profile_surname = resolve_item_for_week("profile_surname", year, week_number)
        
        # Fetch post details for resolved profiles
        profile_ids = []
        if profile_product and profile_product.get('post_id'):
            profile_ids.append(('product', profile_product.get('post_id')))
        if profile_surname and profile_surname.get('post_id'):
            profile_ids.append(('surname', profile_surname.get('post_id')))
        
        if profile_ids:
            # Fetch post details from database
            post_ids = [pid for _, pid in profile_ids]
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.id,
                        p.title,
                        p.profile_type,
                        p.profile_producer_name,
                        p.profile_standfirst,
                        p.slug,
                        p.created_at,
                        p.updated_at
                    FROM post p
                    WHERE p.id = ANY(%s)
                """, (post_ids,))
                
                rows = cursor.fetchall()
                post_map = {}
                for row in rows:
                    if isinstance(row, dict):
                        post_map[row['id']] = row
                    else:
                        post_map[row[0]] = {
                            'id': row[0],
                            'title': row[1],
                            'profile_type': row[2],
                            'profile_producer_name': row[3] if len(row) > 3 else None,
                            'profile_standfirst': row[4] if len(row) > 4 else None,
                            'slug': row[5] if len(row) > 5 else None,
                            'created_at': row[6] if len(row) > 6 else None,
                            'updated_at': row[7] if len(row) > 7 else None
                        }
                
                # Build response in order: product first, then surname
                for profile_type, post_id in profile_ids:
                    if post_id in post_map:
                        post_data = post_map[post_id]
                        profile = {
                            'id': post_data['id'],
                            'title': post_data['title'],
                            'profile_type': profile_type,
                            'profile_producer_name': post_data.get('profile_producer_name'),
                            'profile_standfirst': post_data.get('profile_standfirst'),
                            'slug': post_data.get('slug'),
                            'scheduled_date': None,  # Not stored in cyclic system
                            'weekday': None,  # Not stored in cyclic system
                            'day': None,  # Alias for compatibility
                            'created_at': post_data['created_at'].isoformat() if post_data.get('created_at') else None,
                            'updated_at': post_data['updated_at'].isoformat() if post_data.get('updated_at') else None,
                            '_from_cyclic_system': True  # Flag to indicate unified resolver
                        }
                        profiles.append(profile)
        
        return jsonify(profiles)
            
    except Exception as e:
        logger.error(f"Error fetching profiles for week {year}/{week_number}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500





