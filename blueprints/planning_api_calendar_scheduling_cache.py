"""
Planning Calendar API - Scheduling Cache

Provides cached scheduling data for all weeks to avoid multiple DB calls
"""

from flask import jsonify
from config.database import db_manager
from datetime import datetime, date
import json
import os
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = 'data/calendar_scheduling_cache.json'
CACHE_MAX_AGE_SECONDS = 300  # 5 minutes

def get_scheduling_cache_path():
    """Get the full path to the cache file"""
    # Get project root (blueprints/ -> project root)
    project_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root, CACHE_FILE)

def load_scheduling_cache():
    """Load scheduling data from cache file if it exists and is fresh"""
    cache_path = get_scheduling_cache_path()
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        # Check file age
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        if file_age > CACHE_MAX_AGE_SECONDS:
            logger.info(f"Cache file is stale ({file_age:.0f}s old), will regenerate")
            return None
        
        with open(cache_path, 'r') as f:
            data = json.load(f)
            logger.info(f"Loaded scheduling cache from file ({len(data.get('weeks', []))} weeks)")
            return data
    except Exception as e:
        logger.warning(f"Error loading cache file: {e}")
        return None

def save_scheduling_cache(data):
    """Save scheduling data to cache file"""
    cache_path = get_scheduling_cache_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved scheduling cache to {cache_path}")
    except Exception as e:
        logger.error(f"Error saving cache file: {e}")

def generate_scheduling_data(current_year, current_week):
    """Generate scheduling data for 52 weeks starting from current week"""
    weeks_data = []
    year = current_year
    week = current_week
    
    try:
        with db_manager.get_cursor() as cursor:
            # Check if unified calendar_week_items table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_items'
                ) as has_week_items
            """)
            has_week_items = cursor.fetchone()['has_week_items']
            
            # Generate 52 weeks
            for i in range(52):
                schedule = []
                
                if has_week_items:
                    # Get selected theme - first try calendar_week_items
                    cursor.execute("""
                        SELECT cwi.item_id as selected_theme_id, cwi.updated_at,
                               ct.theme_title, ct.theme_description
                        FROM calendar_week_items cwi
                        LEFT JOIN calendar_themes ct ON cwi.item_id = ct.id
                        WHERE cwi.year = %s AND cwi.week_number = %s
                          AND cwi.item_type = 'theme' AND cwi.is_selected = TRUE
                          AND cwi.is_active = TRUE
                        LIMIT 1
                    """, (year, week))
                    theme_selection = cursor.fetchone()
                    
                    # Fallback: Check calendar_week_selection if no theme in calendar_week_items
                    if not theme_selection:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = 'calendar_week_selection'
                            )
                        """)
                        has_selection = cursor.fetchone()['exists']
                        
                        if has_selection:
                            cursor.execute("""
                                SELECT cws.selected_theme_id, cws.updated_at,
                                       ct.theme_title, ct.theme_description
                                FROM calendar_week_selection cws
                                LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
                                WHERE cws.year = %s AND cws.week_number = %s
                                LIMIT 1
                            """, (year, week))
                            theme_selection = cursor.fetchone()
                    
                    # Final fallback: Get themes from calendar_themes by week_number
                    # This gets all themes for the week, we'll use the first one as selected
                    if not theme_selection:
                        cursor.execute("""
                            SELECT ct.id as selected_theme_id, ct.updated_at,
                                   ct.theme_title, ct.theme_description
                            FROM calendar_themes ct
                            WHERE ct.week_number = %s
                            ORDER BY ct.id
                            LIMIT 1
                        """, (week,))
                        theme_selection = cursor.fetchone()
                    
                    if theme_selection:
                        schedule.append({
                            'type': 'theme_selection',
                            'selected_theme_id': theme_selection['selected_theme_id'],
                            'theme_title': theme_selection['theme_title'],
                            'theme_description': theme_selection['theme_description'],
                            'updated_at': theme_selection['updated_at'].isoformat() if theme_selection['updated_at'] else None
                        })
                    
                    # Get recipes for this week (using same logic as recipes endpoint)
                    # Calculate recipe week number based on current week
                    from datetime import date
                    current_iso = date.today().isocalendar()
                    current_year = current_iso[0]
                    current_week = current_iso[1]
                    weeks_from_current = (week - current_week) % 52
                    if weeks_from_current < 0:
                        weeks_from_current += 52
                    recipe_week_number = weeks_from_current + 1
                    if recipe_week_number > 52:
                        recipe_week_number = 1
                    elif recipe_week_number < 1:
                        recipe_week_number = 52
                    
                    # Check for scheduled recipe post in calendar_week_items
                    cursor.execute("""
                        SELECT DISTINCT
                            p.id as post_id,
                            p.title as post_title,
                            p.status as post_status,
                            p.recipe_week_number,
                            cwi.scheduled_date,
                            cwi.weekday,
                            cwi.created_at,
                            cwi.updated_at
                        FROM post p
                        INNER JOIN calendar_week_items cwi ON p.id = cwi.item_id
                        WHERE cwi.item_type = 'recipe'
                          AND cwi.year = %s
                          AND cwi.week_number = %s
                          AND cwi.is_active = TRUE
                        LIMIT 1
                    """, (year, week))
                    recipe_post = cursor.fetchone()
                    
                    # If no scheduled post, check calendar_recipes for definition
                    if not recipe_post:
                        cursor.execute("""
                            SELECT 
                                cr.id,
                                cr.recipe_title,
                                cr.recipe_description
                            FROM calendar_recipes cr
                            WHERE cr.week_number = %s
                            LIMIT 1
                        """, (recipe_week_number,))
                        recipe_def = cursor.fetchone()
                        if recipe_def:
                            schedule.append({
                                'type': 'post',
                                'post_id': None,
                                'post_title': recipe_def['recipe_title'],
                                'post_status': 'draft',
                                'item_type': 'recipe',
                                'recipe_week_number': recipe_week_number,
                                'scheduled_date': None,
                                'weekday': 1,
                                '_definition': True
                            })
                    else:
                        schedule.append({
                            'type': 'post',
                            'post_id': recipe_post['post_id'],
                            'post_title': recipe_post['post_title'],
                            'post_status': recipe_post['post_status'],
                            'item_type': 'recipe',
                            'recipe_week_number': recipe_post['recipe_week_number'],
                            'scheduled_date': recipe_post['scheduled_date'].isoformat() if recipe_post['scheduled_date'] else None,
                            'weekday': recipe_post['weekday'],
                            'created_at': recipe_post['created_at'].isoformat() if recipe_post['created_at'] else None,
                            'updated_at': recipe_post['updated_at'].isoformat() if recipe_post['updated_at'] else None,
                            '_scheduled': True
                        })
                    
                    # Get profiles for this week (using same logic as profiles endpoint)
                    cursor.execute("""
                        SELECT DISTINCT
                            p.id as post_id,
                            p.title as post_title,
                            p.status as post_status,
                            p.profile_type,
                            cwi.scheduled_date,
                            cwi.weekday,
                            cwi.created_at,
                            cwi.updated_at
                        FROM post p
                        INNER JOIN calendar_week_items cwi ON p.id = cwi.item_id
                        WHERE cwi.item_type = 'profile'
                          AND cwi.year = %s
                          AND cwi.week_number = %s
                          AND cwi.is_active = TRUE
                        ORDER BY cwi.weekday NULLS LAST, p.title
                    """, (year, week))
                    profile_posts = cursor.fetchall()
                    
                    for profile in profile_posts:
                        schedule.append({
                            'type': 'post',
                            'post_id': profile['post_id'],
                            'post_title': profile['post_title'],
                            'post_status': profile['post_status'],
                            'item_type': 'profile',
                            'profile_type': profile['profile_type'],
                            'scheduled_date': profile['scheduled_date'].isoformat() if profile['scheduled_date'] else None,
                            'weekday': profile['weekday'],
                            'created_at': profile['created_at'].isoformat() if profile['created_at'] else None,
                            'updated_at': profile['updated_at'].isoformat() if profile['updated_at'] else None
                        })
                
                weeks_data.append({
                    'year': year,
                    'week': week,
                    'schedule': schedule
                })
                
                # Move to next week
                week += 1
                if week > 52:
                    week = 1
                    year += 1
            
            return {
                'current_year': current_year,
                'current_week': current_week,
                'generated_at': datetime.now().isoformat(),
                'weeks': weeks_data
            }
    except Exception as e:
        logger.error(f"Error generating scheduling data: {e}")
        raise

def api_calendar_scheduling_all():
    """Get all scheduling data for 52 weeks (cached)"""
    try:
        # Get current week
        now = datetime.now()
        current_year = now.year
        current_week = now.isocalendar()[1]
        
        # Try to load from cache
        cache_data = load_scheduling_cache()
        
        if cache_data and cache_data.get('current_year') == current_year and cache_data.get('current_week') == current_week:
            return jsonify({
                'success': True,
                'cached': True,
                'data': cache_data
            })
        
        # Generate fresh data
        logger.info("Generating fresh scheduling data...")
        data = generate_scheduling_data(current_year, current_week)
        
        # Save to cache
        save_scheduling_cache(data)
        
        return jsonify({
            'success': True,
            'cached': False,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error in api_calendar_scheduling_all: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

