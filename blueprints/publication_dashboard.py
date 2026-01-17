"""
Publication Dashboard Blueprint
Unified publication management dashboard
"""

from flask import Blueprint, render_template, jsonify, request
from config.database import db_manager
from utils.calendar_json_loader import load_category_year
from utils.channel_assignment import get_channels_for_post_type
from config.calendar_settings import CATEGORIES
from datetime import date
import logging
from utils.publication_status_resolver import (
    resolve_post_for_calendar_item,
    normalize_queue_status,
)

logger = logging.getLogger(__name__)

bp = Blueprint('publication_dashboard', __name__, url_prefix='/publication')

@bp.route('/dashboard')
def dashboard():
    """Main publication dashboard."""
    from flask import request
    tab = request.args.get('tab', 'schedule')
    return render_template('publication/dashboard.html', active_tab=tab)

@bp.route('/dashboard/deprecated')
def dashboard_deprecated():
    """Deprecated dashboard version."""
    return render_template('publication/dashboard_deprecated.html')

@bp.route('/dashboard/mockup')
def dashboard_mockup():
    """Legacy mockup route - redirects to deprecated dashboard."""
    from flask import redirect
    return redirect('/publication/dashboard/deprecated')

@bp.route('/api/publication-days')
def api_publication_days():
    """
    Get all publication day assignments.
    
    Returns all (post_type, channel, content_format) combinations with their day assignments.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    post_type,
                    channel,
                    content_format,
                    publication_day,
                    is_primary,
                    is_required,
                    is_active
                FROM post_type_channel_config
                ORDER BY post_type, channel, content_format
            """)
            
            results = cursor.fetchall()
            assignments = []
            day_names = {
                1: "Monday",
                2: "Tuesday",
                3: "Wednesday",
                4: "Thursday",
                5: "Friday",
                6: "Saturday",
                7: "Sunday"
            }
            
            for row in results:
                assignment = {
                    'id': row['id'],
                    'post_type': row['post_type'],
                    'channel': row['channel'],
                    'content_format': row['content_format'],
                    'publication_day': row['publication_day'],
                    'day_name': day_names.get(row['publication_day']) if row['publication_day'] else None,
                    'is_primary': row['is_primary'],
                    'is_required': row['is_required'],
                    'is_active': row['is_active']
                }
                assignments.append(assignment)
            
            # Get unique post types and channels for UI
            post_types = sorted(set(a['post_type'] for a in assignments))
            channels = sorted(set(a['channel'] for a in assignments))
            
            return jsonify({
                'success': True,
                'assignments': assignments,
                'post_types': post_types,
                'channels': channels,
                'day_names': day_names
            })
            
    except Exception as e:
        logger.error(f"Error getting publication days: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/publication-days/<int:assignment_id>', methods=['PUT'])
def api_update_publication_day(assignment_id):
    """Update publication day for a specific assignment."""
    try:
        data = request.get_json()
        publication_day = data.get('publication_day')  # Can be 1-7 or null
        
        # Validate day if provided
        if publication_day is not None:
            if not isinstance(publication_day, int) or publication_day < 1 or publication_day > 7:
                return jsonify({
                    'success': False,
                    'error': 'publication_day must be between 1 and 7, or null'
                }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE post_type_channel_config
                    SET publication_day = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, post_type, channel, content_format, publication_day
                """, (publication_day, assignment_id))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({
                        'success': False,
                        'error': 'Assignment not found'
                    }), 404
                
                conn.commit()
                
                day_names = {
                    1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
                    5: "Friday", 6: "Saturday", 7: "Sunday"
                }
                
                return jsonify({
                    'success': True,
                    'message': 'Publication day updated',
                    'assignment': {
                        'id': result['id'],
                        'post_type': result['post_type'],
                        'channel': result['channel'],
                        'content_format': result['content_format'],
                        'publication_day': result['publication_day'],
                        'day_name': day_names.get(result['publication_day']) if result['publication_day'] else None
                    }
                })
                
    except Exception as e:
        logger.error(f"Error updating publication day: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/publication-days/bulk', methods=['PUT'])
def api_bulk_update_publication_days():
    """Bulk update publication days."""
    try:
        data = request.get_json()
        updates = data.get('updates', [])
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No updates provided'
            }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                updated_count = 0
                for update in updates:
                    assignment_id = update.get('id')
                    publication_day = update.get('publication_day')
                    
                    if assignment_id is None:
                        continue
                    
                    # Validate day if provided
                    if publication_day is not None:
                        if not isinstance(publication_day, int) or publication_day < 1 or publication_day > 7:
                            continue
                    
                    cursor.execute("""
                        UPDATE post_type_channel_config
                        SET publication_day = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (publication_day, assignment_id))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Updated {updated_count} assignment(s)'
                })
                
    except Exception as e:
        logger.error(f"Error bulk updating publication days: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/dashboard/schedule')
def api_dashboard_schedule():
    """
    Get schedule data for the publication dashboard.
    
    Returns items organized by channel and day of week for the current week.
    Uses the calendar scheduling JSON files and filters by channel assignments.
    """
    try:
        # Get current ISO week
        today = date.today()
        year, week, weekday = today.isocalendar()
        
        # Get optional year/week from query params
        year = request.args.get('year', type=int) or year
        week = request.args.get('week', type=int) or week
        
        # Map category to post_type (must match database post_type values)
        category_to_post_type = {
            'theme': 'themed',
            'recipe': 'recipe',
            'profile_product': 'profile_product',  # Database uses profile_product, not profile
            'profile_surname': 'profile_surname',  # Database uses profile_surname, not profile
            'weekly_word': 'weekly_word',
            'weekly_phrase': 'weekly_phrase',
            'weekly_insult': 'weekly_insult'
        }
        
        # Organize items by channel
        channels = {
            'blog': [],
            'facebook': [],
            'instagram': [],
            'twitter': [],
            'newsletter': []
        }
        
        # Process each category
        for category in CATEGORIES:
            # Load schedule for this category and year
            from utils.calendar_json_loader import load_category_year
            from utils.calendar_resolver import resolve_item_for_week
            
            schedule = load_category_year(category, year)
            item = None
            
            # Try to get item from JSON schedule
            if schedule and week in schedule:
                item = schedule[week]
            
            # If JSON doesn't have the item or has null values, try resolver as fallback
            if not item or (not item.get('item_id') and not item.get('id') and not item.get('title')):
                resolved = resolve_item_for_week(category, year, week)
                if resolved:
                    # Convert resolved item to schedule format
                    item = {
                        'item_id': resolved.get('id'),
                        'id': resolved.get('id'),
                        'title': resolved.get('recipe_title') or resolved.get('theme_title') or resolved.get('idea_title'),
                        'description': resolved.get('recipe_description') or resolved.get('theme_description') or resolved.get('idea_description'),
                        'post_id': resolved.get('post_id')
                    }
            
            if not item:
                continue
            
            # Extract basic item data
            item_id = item.get('item_id') or item.get('id')
            title = item.get('title') or item.get('theme_title') or item.get('idea_title') or item.get('recipe_title')
            post_id = item.get('post_id')
            
            # Only skip if we have absolutely no identifying data
            # (For recipes, we might have item_id but no title yet - that's OK, we'll fetch it)
            if not item_id and not title and not post_id:
                continue
            
            # Get post type
            post_type = category_to_post_type.get(category)
            if not post_type:
                continue
            
            # Get channels for this post type
            channel_configs = get_channels_for_post_type(post_type)
            
            # Add item to each assigned channel
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for channel_config in channel_configs:
                        channel = channel_config['channel']
                        content_format = channel_config['content_format']
                        
                        # Get publication day from database
                        cursor.execute("""
                            SELECT publication_day
                            FROM post_type_channel_config
                            WHERE post_type = %s 
                            AND channel = %s 
                            AND content_format = %s
                            AND is_active = TRUE
                        """, (post_type, channel, content_format))
                        
                        result = cursor.fetchone()
                        publication_day = result['publication_day'] if result and result.get('publication_day') else None
                        
                        # Only add items that have a publication day assigned
                        if publication_day is None:
                            continue
                        
                        # Build item data (item_id, title, post_id already extracted above)
                        description = item.get('description') or item.get('theme_description') or item.get('idea_description')
                        
                        # For recipes, if we have item_id but no title, fetch from database
                        if category == 'recipe':
                            if item_id and not title:
                                cursor.execute("""
                                    SELECT recipe_title, recipe_description
                                    FROM calendar_recipes
                                    WHERE id = %s
                                """, (item_id,))
                                recipe_row = cursor.fetchone()
                                if recipe_row:
                                    title = recipe_row.get('recipe_title') or title
                                    description = recipe_row.get('recipe_description') or description
                        
                        # For profiles, fetch title from post if missing
                        if category in ('profile_product', 'profile_surname') and not title:
                            profile_post_id = post_id or item_id
                            if profile_post_id:
                                cursor.execute("""
                                    SELECT title
                                    FROM post
                                    WHERE id = %s
                                """, (profile_post_id,))
                                post_row = cursor.fetchone()
                                if post_row:
                                    title = post_row.get('title') or title

                        # Resolve post status using the central resolver (ID-only matching).
                        if category in ('theme', 'recipe', 'profile_product', 'profile_surname') and item_id:
                            status_info = resolve_post_for_calendar_item(
                                category, item_id, year=year, week=week
                            )
                            post_id = status_info.get('post_id')
                            post_exists = bool(status_info.get('exists'))
                            post_status = status_info.get('status')
                        else:
                            post_id = None
                            post_exists = False
                            post_status = None
                        
                        # Determine display type name
                        type_names = {
                            'theme': 'Theme',
                            'recipe': 'Recipe',
                            'profile_product': 'Product Profile',
                            'profile_surname': 'Surname Profile',
                            'weekly_word': 'Word of the Week',
                            'weekly_phrase': 'Phrase of the Week',
                            'weekly_insult': 'Insult of the Week'
                        }
                        type_name = type_names.get(category, category.title())
                        
                        item_data = {
                            'category': category,
                            'item_id': item_id,
                            'title': title,
                            'post_id': post_id,
                            'post_exists': post_exists,
                            'post_status': post_status,  # 'draft', 'published', 'deleted', or None
                            'year': year,
                            'week': week,
                            'channel': channel,
                            'content_format': content_format,
                            'is_primary': channel_config.get('is_primary', False),
                            'description': description,
                            'day': publication_day,
                            'type_name': type_name
                        }
                        
                        channels[channel].append(item_data)
        
        # Add social outputs (products + weekly word/phrase/insult) from posting_queue
        # Use unified SocialOutputView helper for consistent status and Content Item linkage
        from utils.social_output_view import get_social_outputs_for_week
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get all social outputs for this week (products and weekly items)
                social_outputs = get_social_outputs_for_week(year, week, cursor=cursor)
                
                for output in social_outputs:
                    channel = output['channel']
                    
                    # Only add to channels that exist in our channels dict
                    if channel not in channels:
                        continue
                    
                    # Skip if no scheduled date (shouldn't happen, but be safe)
                    if not output.get('scheduled_date'):
                        continue
                    
                    # Build item data in same format as calendar items
                    item_data = {
                        'category': output.get('content_type', 'product'),  # 'product', 'weekly_word', etc.
                        'item_id': output.get('content_item_id'),
                        'queue_id': output['output_id'],
                        'title': '',  # Will be filled from product/idea lookup if needed
                        'description': '',
                        'post_id': None,  # Social posts don't have post_id
                        'post_exists': False,
                        'post_status': output['status'],  # Already normalized
                        'year': year,
                        'week': week,
                        'channel': channel,
                        'content_format': output['content_format'],
                        'is_primary': False,
                        'day': output.get('day'),
                        'type_name': 'Product' if output.get('content_type') == 'product' else output.get('content_type', 'Social').title(),
                        'scheduled_time': output.get('scheduled_time', ''),
                        'platform': channel
                    }
                    
                    # For products, fetch product name
                    if output.get('content_type') == 'product' and output.get('content_item_id'):
                        cursor.execute("""
                            SELECT name FROM clan_products WHERE id = %s
                        """, (output['content_item_id'],))
                        product_row = cursor.fetchone()
                        if product_row:
                            item_data['title'] = product_row.get('name') or f"Product {output['content_item_id']}"
                    
                    # For weekly items, fetch idea title from calendar_ideas
                    elif output.get('content_type') in ('weekly_word', 'weekly_phrase', 'weekly_insult') and output.get('content_item_id'):
                        cursor.execute("""
                            SELECT idea_title FROM calendar_ideas WHERE id = %s
                        """, (output['content_item_id'],))
                        idea_row = cursor.fetchone()
                        if idea_row:
                            item_data['title'] = idea_row.get('idea_title') or f"Weekly {output['content_type']}"
                    
                    channels[channel].append(item_data)
        
        # Sort items by day within each channel
        for channel in channels:
            channels[channel].sort(key=lambda x: x.get('day', 1))
        
        return jsonify({
            'success': True,
            'year': year,
            'week': week,
            'channels': channels
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard schedule: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
