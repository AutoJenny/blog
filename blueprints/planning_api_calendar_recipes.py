"""
Planning Calendar API - Recipes

Calendar recipes endpoints for Scottish Recipe Series
"""

from flask import request, jsonify
from config.database import db_manager
from blueprints.planning_api_calendar_utils import _safe_parse_json_request, _current_iso_week
import logging
from datetime import date

logger = logging.getLogger(__name__)

def api_calendar_recipes(year, week_number):
    """
    Get recipes for a specific year and week.
    
    Returns:
    1. Recipe definitions from calendar_recipes table (perpetual, based on week_number)
    2. Recipe posts scheduled for this specific year/week (if any exist)
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Calculate week start date (Monday)
            week_start_date = date.fromisocalendar(year, week_number, 1)
            
            recipes = []
            
            # First: Get recipe definition from calendar_recipes for this perpetual week_number
            cursor.execute("""
                SELECT 
                    cr.id,
                    cr.week_number,
                    cr.recipe_title,
                    cr.recipe_description,
                    cr.seasonal_context,
                    cr.priority,
                    cr.tags,
                    cr.created_at,
                    cr.updated_at
                FROM calendar_recipes cr
                WHERE cr.week_number = %s
                LIMIT 1
            """, (week_number,))
            
            recipe_def = cursor.fetchone()
            
            if recipe_def:
                if isinstance(recipe_def, dict):
                    recipe_def_dict = {
                        'id': recipe_def['id'],
                        'title': recipe_def['recipe_title'],
                        'recipe_week_number': recipe_def['week_number'],
                        'description': recipe_def.get('recipe_description'),
                        'seasonal_context': recipe_def.get('seasonal_context'),
                        'priority': recipe_def.get('priority'),
                        'tags': recipe_def.get('tags'),
                        'created_at': recipe_def['created_at'].isoformat() if recipe_def.get('created_at') else None,
                        'updated_at': recipe_def['updated_at'].isoformat() if recipe_def.get('updated_at') else None,
                        '_recipe': True,
                        '_definition': True  # Mark as definition, not a post
                    }
                else:
                    recipe_def_dict = {
                        'id': recipe_def[0],
                        'title': recipe_def[2],
                        'recipe_week_number': recipe_def[1],
                        'description': recipe_def[3] if len(recipe_def) > 3 else None,
                        'seasonal_context': recipe_def[4] if len(recipe_def) > 4 else None,
                        'priority': recipe_def[5] if len(recipe_def) > 5 else None,
                        'tags': recipe_def[6] if len(recipe_def) > 6 else None,
                        'created_at': recipe_def[7].isoformat() if len(recipe_def) > 7 and recipe_def[7] else None,
                        'updated_at': recipe_def[8].isoformat() if len(recipe_def) > 8 and recipe_def[8] else None,
                        '_recipe': True,
                        '_definition': True
                    }
                
                # Check if there's a scheduled post for this recipe
                # Try to query calendar_week_posts - if it doesn't exist, just skip
                scheduled_post = None
                try:
                    # Check if calendar_week_posts exists and query it
                    cursor.execute("""
                        SELECT DISTINCT
                            p.id,
                            p.title,
                            p.recipe_week_number,
                            p.subtitle,
                            p.slug,
                            cwp.scheduled_date,
                            p.created_at,
                            p.updated_at,
                            CASE 
                                WHEN cwp.scheduled_date IS NOT NULL 
                                THEN EXTRACT(DOW FROM cwp.scheduled_date) + 1
                                ELSE NULL
                            END as weekday
                        FROM post p
                        INNER JOIN calendar_week_posts cwp ON p.id = cwp.post_id
                        WHERE p.recipe_week_number = %s
                          AND cwp.year = %s
                          AND cwp.week_number = %s
                        LIMIT 1
                    """, (week_number, year, week_number))
                    
                    scheduled_post = cursor.fetchone()
                except Exception as table_error:
                    # Table doesn't exist or other error - that's fine, just use definition
                    logger.debug(f"calendar_week_posts table not available or error querying: {table_error}")
                    scheduled_post = None
                
                if scheduled_post:
                    # Use the scheduled post data instead of definition
                    if isinstance(scheduled_post, dict):
                        recipe = {
                            'id': scheduled_post['id'],
                            'title': scheduled_post['title'],
                            'recipe_week_number': scheduled_post['recipe_week_number'],
                            'subtitle': scheduled_post.get('subtitle'),
                            'slug': scheduled_post.get('slug'),
                            'scheduled_date': scheduled_post['scheduled_date'].isoformat() if scheduled_post.get('scheduled_date') else None,
                            'weekday': int(scheduled_post['weekday']) if scheduled_post.get('weekday') is not None else None,
                            'day': int(scheduled_post['weekday']) if scheduled_post.get('weekday') is not None else None,
                            'created_at': scheduled_post['created_at'].isoformat() if scheduled_post.get('created_at') else None,
                            'updated_at': scheduled_post['updated_at'].isoformat() if scheduled_post.get('updated_at') else None,
                            '_recipe': True,
                            '_scheduled': True  # Mark as scheduled post
                        }
                    else:
                        recipe = {
                            'id': scheduled_post[0],
                            'title': scheduled_post[1],
                            'recipe_week_number': scheduled_post[2],
                            'subtitle': scheduled_post[3] if len(scheduled_post) > 3 else None,
                            'slug': scheduled_post[4] if len(scheduled_post) > 4 else None,
                            'scheduled_date': scheduled_post[5].isoformat() if len(scheduled_post) > 5 and scheduled_post[5] else None,
                            'weekday': int(scheduled_post[8]) if len(scheduled_post) > 8 and scheduled_post[8] is not None else None,
                            'day': int(scheduled_post[8]) if len(scheduled_post) > 8 and scheduled_post[8] is not None else None,
                            'created_at': scheduled_post[6].isoformat() if len(scheduled_post) > 6 and scheduled_post[6] else None,
                            'updated_at': scheduled_post[7].isoformat() if len(scheduled_post) > 7 and scheduled_post[7] else None,
                            '_recipe': True,
                            '_scheduled': True
                        }
                    recipes.append(recipe)
                else:
                    # No scheduled post yet, use definition
                    # Default to Monday (weekday 1) for display purposes
                    recipe_def_dict['weekday'] = 1
                    recipe_def_dict['day'] = 1
                    recipes.append(recipe_def_dict)
            
            if not recipes:
                # No recipe definition found for this week
                return jsonify([])
            
            return jsonify(recipes)
            
    except Exception as e:
        logger.error(f"Error fetching recipes for week {year}/{week_number}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

