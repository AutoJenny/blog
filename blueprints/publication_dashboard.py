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
    BASED ON post_type_channel_config (types only), not actual posts.
    This provides a reliable basis for showing and shuffling post types.
    """
    try:
        # Get current ISO week
        today = date.today()
        year, week, weekday = today.isocalendar()
        
        # Get optional year/week from query params
        year = request.args.get('year', type=int) or year
        week = request.args.get('week', type=int) or week
        
        # Organize items by channel
        channels = {
            'blog': [],
            'facebook': [],
            'instagram': [],
            'twitter': [],
            'newsletter': []
        }
        
        # Map post_type to display name
        type_name_map = {
            'themed': 'Theme',
            'recipe': 'Recipe',
            'profile_product': 'Product Profile',
            'profile_surname': 'Surname Profile',
            'weekly_word': 'Word',
            'weekly_phrase': 'Phrase',
            'weekly_insult': 'Insult',
            'product': 'Product',
            'message': 'Message'
        }
        
        # Get all active post type configurations
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Query post_type_channel_config for all active configurations with publication_day
                cursor.execute("""
                    SELECT 
                        post_type,
                        channel,
                        content_format,
                        publication_day,
                        publication_time,
                        is_primary
                    FROM post_type_channel_config
                    WHERE is_active = TRUE
                    AND publication_day IS NOT NULL
                    ORDER BY channel, publication_day, publication_time NULLS LAST
                """)
                configs = cursor.fetchall()
                
                for config in configs:
                    post_type = config['post_type']
                    channel = config['channel']
                    content_format = config['content_format']
                    publication_day = config['publication_day']
                    publication_time = config['publication_time']
                    is_primary = config.get('is_primary', False)
                    
                    # Only add to channels that exist in our channels dict
                    if channel not in channels:
                        continue
                    
                    # Get display type name
                    type_name = type_name_map.get(post_type, post_type.title())
                    
                    # Format time as HH:MM string
                    time_str = None
                    if publication_time:
                        if isinstance(publication_time, str):
                            time_str = publication_time[:5]  # HH:MM
                        else:
                            time_str = publication_time.strftime('%H:%M')
                    
                    # Determine if this post type is automated
                    # Automated: weekly content (word/phrase/insult), product posts, and message posts
                    # Manual/Development: blog posts (theme, recipe, profiles)
                    is_automated = post_type in ('weekly_word', 'weekly_phrase', 'weekly_insult', 'product', 'message')
                    
                    # Build item data - TYPE ONLY, no details
                    item_data = {
                        'post_type': post_type,
                        'type_name': type_name,
                        'title': type_name,  # Show type, not specific content
                        'channel': channel,
                        'content_format': content_format,
                        'day': publication_day,
                        'scheduled_time': time_str,
                        'is_primary': is_primary,
                        'is_automated': is_automated,
                        'year': year,
                        'week': week
                    }
                    
                    channels[channel].append(item_data)
        
        # For product posts, we need to check daily_posts_schedule for recurring schedules
        # These don't have a single publication_day, but have weekday patterns
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        name,
                        days,
                        time,
                        platform
                    FROM daily_posts_schedule
                    WHERE is_active = TRUE
                    AND content_type = 'product'
                """)
                product_schedules = cursor.fetchall()
                
                for schedule in product_schedules:
                    days = schedule['days']  # JSONB array of weekday numbers
                    scheduled_time = schedule['time']
                    platform = schedule['platform']
                    
                    # Map platform to channel
                    platform_to_channel = {
                        'facebook': 'facebook',
                        'instagram': 'instagram',
                        'twitter': 'twitter'
                    }
                    channel = platform_to_channel.get(platform.lower())
                    
                    if not channel or channel not in channels:
                        continue
                    
                    # Format time
                    time_str = None
                    if scheduled_time:
                        if isinstance(scheduled_time, str):
                            time_str = scheduled_time[:5]
                        else:
                            time_str = scheduled_time.strftime('%H:%M')
                    
                    # Parse days JSONB array
                    weekdays = []
                    if days:
                        if isinstance(days, list):
                            weekdays = days
                        elif isinstance(days, str):
                            import json
                            weekdays = json.loads(days)
                    
                    # Add one Product entry for each weekday in the schedule
                    # EXCLUDE Saturday (day 6) - Messages replace Saturday product posts
                    for weekday in weekdays:
                        if 1 <= weekday <= 7 and weekday != 6:  # Skip Saturday
                            item_data = {
                                'post_type': 'product',
                                'type_name': 'Product',
                                'title': 'Product',
                                'channel': channel,
                                'content_format': 'product_post',
                                'day': weekday,
                                'scheduled_time': time_str,
                                'is_primary': False,
                                'is_automated': True,  # Product posts are automated
                                'year': year,
                                'week': week,
                                'schedule_name': schedule['name']
                            }
                            channels[channel].append(item_data)
        
        # For Facebook automated items, get actual scheduled_time from posting_queue
        # This shows the real time from the queue, not just the config
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Calculate week start/end dates
                from datetime import timedelta
                jan4 = date(year, 1, 4)
                jan4_day = (jan4.isoweekday() + 6) % 7
                week_start = date(year, 1, 4) + timedelta(days=(week - 1) * 7 - jan4_day)
                week_end = week_start + timedelta(days=6)
                
                # Get scheduled times from posting_queue for Facebook automated items
                # Include ALL posts (including published) to get the actual scheduled times
                # We'll prefer non-published posts if multiple exist for the same type/day
                cursor.execute("""
                    SELECT 
                        pq.content_type,
                        pq.scheduled_date,
                        pq.scheduled_time,
                        pq.status,
                        EXTRACT(DOW FROM pq.scheduled_date) + 1 as weekday,
                        CASE 
                            WHEN pq.status = 'published' THEN 2
                            WHEN pq.status = 'failed' THEN 3
                            ELSE 1
                        END as priority
                    FROM posting_queue pq
                    WHERE pq.platform = 'facebook'
                    AND pq.content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult', 'product', 'message')
                    AND pq.scheduled_date >= %s
                    AND pq.scheduled_date <= %s
                    AND pq.status != 'failed'
                    AND pq.scheduled_time IS NOT NULL
                    ORDER BY pq.content_type, weekday, priority, pq.scheduled_date DESC
                """, (week_start, week_end))
                
                queue_times = cursor.fetchall()
                
                # Create a lookup: (content_type, weekday) -> scheduled_time
                # Prefer non-published posts, and prefer "normal" times (09:00, 11:00, etc.) over weird times (00:04)
                time_lookup = {}
                seen_keys = set()
                for row in queue_times:
                    content_type = row['content_type']
                    weekday = int(row['weekday'])
                    scheduled_time = row['scheduled_time']
                    status = row['status']
                    key = (content_type, weekday)
                    
                    # Format time
                    if scheduled_time:
                        if isinstance(scheduled_time, str):
                            time_str = scheduled_time[:5]  # HH:MM
                        else:
                            time_str = scheduled_time.strftime('%H:%M')
                        
                        # Check if this is a "normal" time (hour >= 8, not midnight-ish)
                        hour = int(time_str.split(':')[0]) if ':' in time_str else 0
                        is_normal_time = hour >= 8
                        
                        # If we already have an entry for this key
                        if key in seen_keys:
                            existing_time = time_lookup[key]
                            existing_hour = int(existing_time.split(':')[0]) if ':' in existing_time else 0
                            existing_is_normal = existing_hour >= 8
                            
                            # Prefer normal times over weird times
                            if is_normal_time and not existing_is_normal:
                                time_lookup[key] = time_str
                            # Prefer non-published over published if times are similar
                            elif status != 'published' and existing_time == time_str:
                                time_lookup[key] = time_str
                            # Otherwise keep existing
                            continue
                        
                        time_lookup[key] = time_str
                        seen_keys.add(key)
                
                # Update Facebook channel items with actual queue times
                for item in channels.get('facebook', []):
                    post_type = item.get('post_type')
                    day = item.get('day')
                    
                    # Map post_type to content_type
                    content_type_map = {
                        'weekly_word': 'weekly_word',
                        'weekly_phrase': 'weekly_phrase',
                        'weekly_insult': 'weekly_insult',
                        'product': 'product',
                        'message': 'message'
                    }
                    content_type = content_type_map.get(post_type)
                    
                    # If we have a time from the queue, use it (overrides config time)
                    # But ignore "weird" times (like 00:04) and use default instead
                    # Otherwise, use config time, or default to 09:00 for weekly content if config is None
                    if content_type and day:
                        queue_time = time_lookup.get((content_type, day))
                        if queue_time:
                            # Check if this is a "normal" time (hour >= 8, not midnight-ish)
                            hour = int(queue_time.split(':')[0]) if ':' in queue_time else 0
                            is_normal_time = hour >= 8
                            
                            if is_normal_time:
                                item['scheduled_time'] = queue_time
                                item['queue_time_source'] = 'queue'  # Mark as from queue
                            elif post_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                                # Queue has a weird time, use default instead
                                item['scheduled_time'] = '09:00'
                                item['queue_time_source'] = 'default'
                            else:
                                # For products, use the queue time even if weird
                                item['scheduled_time'] = queue_time
                                item['queue_time_source'] = 'queue'
                        elif not item.get('scheduled_time') and post_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                            # Default to 09:00 for weekly content if no config time is set
                            item['scheduled_time'] = '09:00'
                            item['queue_time_source'] = 'default'
                        # If no queue time and config time exists, item['scheduled_time'] already has it from line 313
        
        # Sort items by day and time within each channel
        for channel in channels:
            channels[channel].sort(key=lambda x: (
                x.get('day', 99),
                x.get('scheduled_time') or '99:99'  # NULL times go last
            ))
        
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


@bp.route('/api/dashboard/schedule/update', methods=['POST'])
def api_update_schedule():
    """
    Update publication day and/or time for a post type.
    """
    try:
        data = request.get_json()
        post_type = data.get('post_type')
        channel = data.get('channel', 'facebook')
        day = data.get('day')
        time = data.get('time')
        year = data.get('year')
        week = data.get('week')
        
        if not post_type:
            return jsonify({
                'success': False,
                'error': 'post_type is required'
            }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Update post_type_channel_config
                if day is not None:
                    cursor.execute("""
                        UPDATE post_type_channel_config
                        SET publication_day = %s,
                            updated_at = NOW()
                        WHERE post_type = %s
                        AND channel = %s
                        AND is_active = TRUE
                    """, (day, post_type, channel))
                
                if time is not None:
                    cursor.execute("""
                        UPDATE post_type_channel_config
                        SET publication_time = %s,
                            updated_at = NOW()
                        WHERE post_type = %s
                        AND channel = %s
                        AND is_active = TRUE
                    """, (time, post_type, channel))
                
                # For automated items, also update posting_queue entries for this week
                if year and week and post_type in ('weekly_word', 'weekly_phrase', 'weekly_insult', 'product', 'message'):
                    # Calculate week dates
                    from datetime import timedelta
                    jan4 = date(year, 1, 4)
                    jan4_day = (jan4.isoweekday() + 6) % 7
                    week_start = date(year, 1, 4) + timedelta(days=(week - 1) * 7 - jan4_day)
                    week_end = week_start + timedelta(days=6)
                    
                    # Update posting_queue entries
                    if day is not None:
                        # Calculate new scheduled_date based on day
                        days_to_add = day - 1  # Monday = 0, Sunday = 6
                        new_scheduled_date = week_start + timedelta(days=days_to_add)
                        
                        if time is not None:
                            # Update both date and time
                            cursor.execute("""
                                UPDATE posting_queue
                                SET scheduled_date = %s,
                                    scheduled_time = %s,
                                    scheduled_timestamp = (%s::date + %s::time)::timestamp,
                                    updated_at = NOW()
                                WHERE platform = %s
                                AND content_type = %s
                                AND scheduled_date >= %s
                                AND scheduled_date <= %s
                                AND status != 'published'
                                AND status != 'failed'
                            """, (new_scheduled_date, time, new_scheduled_date, time, channel, post_type, week_start, week_end))
                        else:
                            # Update only date
                            cursor.execute("""
                                UPDATE posting_queue
                                SET scheduled_date = %s,
                                    scheduled_timestamp = (%s::date + COALESCE(scheduled_time, '09:00'::time))::timestamp,
                                    updated_at = NOW()
                                WHERE platform = %s
                                AND content_type = %s
                                AND scheduled_date >= %s
                                AND scheduled_date <= %s
                                AND status != 'published'
                                AND status != 'failed'
                            """, (new_scheduled_date, new_scheduled_date, channel, post_type, week_start, week_end))
                    elif time is not None:
                        # Update only time (keep existing dates)
                        cursor.execute("""
                            UPDATE posting_queue
                            SET scheduled_time = %s,
                                scheduled_timestamp = (scheduled_date + %s::time)::timestamp,
                                updated_at = NOW()
                            WHERE platform = %s
                            AND content_type = %s
                            AND scheduled_date >= %s
                            AND scheduled_date <= %s
                            AND status != 'published'
                            AND status != 'failed'
                        """, (time, time, channel, post_type, week_start, week_end))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Schedule updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating schedule: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
