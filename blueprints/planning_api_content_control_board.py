"""
Content Control Board API

Provides read-only data for the Content Control Board UI.
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import date, datetime, timedelta
from config.database import db_manager
from config.content_roles_schedule_rails import get_rails_for_platform
import json

bp = Blueprint('planning_api_content_control_board', __name__, url_prefix='/api/planning/content-control-board')
logger = logging.getLogger(__name__)


@bp.route('/week-data')
def get_week_data():
    """
    Get all post data for a given week.
    
    Query params:
        year: ISO year
        week: ISO week number
    
    Returns:
        JSON with:
        - active_topic: Weekly topic from rota (if any)
        - schedule_rails: All rails for the week
        - posts: Posts matching the rails
        - legacy_posts: Posts without roles (for visibility)
    """
    try:
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        if not year or not week:
            # Get current week
            today = date.today()
            year, week, _ = today.isocalendar()
        
        # Calculate week start (Monday)
        jan4 = date(year, 1, 4)
        week_start = jan4 - timedelta(days=jan4.weekday())
        week_start = week_start + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)
        
        # Get active topic for this week
        active_topic = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.id as rota_id,
                    r.topic_id,
                    r.scheduled_year,
                    r.scheduled_week,
                    t.topic_name,
                    t.topic_description,
                    t.topic_type,
                    t.article_ids
                FROM kb_topic_rota r
                LEFT JOIN kb_topics t ON r.topic_id = t.id
                WHERE r.scheduled_year = %s AND r.scheduled_week = %s
                LIMIT 1
            """, (year, week))
            
            rota_entry = cursor.fetchone()
            if rota_entry:
                active_topic = {
                    'rota_id': rota_entry['rota_id'],
                    'topic_id': rota_entry['topic_id'],
                    'topic_name': rota_entry['topic_name'],
                    'topic_description': rota_entry['topic_description'],
                    'topic_type': rota_entry['topic_type'],
                    'source_type': 'kb_cluster',
                    'article_count': len(rota_entry['article_ids']) if rota_entry['article_ids'] else 0
                }
        
        # Get schedule rails for Facebook
        rails = get_rails_for_platform('facebook', is_active=True)
        
        # Build schedule map: (day, time) -> rail
        # Rails use ISO 8601: 1=Monday, 7=Sunday
        # Internal matching uses 0-indexed: 0=Monday, 6=Sunday
        schedule_map = {}
        for rail in rails:
            day_iso = rail['day']  # ISO: 1=Monday, 7=Sunday
            day_zero_indexed = day_iso - 1  # Convert to 0-6 for internal matching
            time = rail['time']
            schedule_map[(day_zero_indexed, time)] = rail
        
        # Get posts for this week from posting_queue
        posts_by_slot = {}
        legacy_posts = []
        
        with db_manager.get_cursor() as cursor:
            # Get framework posts (with roles)
            cursor.execute("""
                SELECT 
                    pq.id,
                    pq.role,
                    pq.platform,
                    pq.channel_type,
                    pq.content_type,
                    pq.generated_content,
                    pq.generated_caption,
                    pq.status,
                    pq.scheduled_date,
                    pq.scheduled_time,
                    pq.scheduled_timestamp,
                    pq.topic_id,
                    pq.source_page_id,
                    pq.rota_year,
                    pq.rota_week,
                    pq.validation_report_json,
                    pq.approved_at,
                    pq.approved_by,
                    pq.created_at,
                    pq.updated_at,
                    -- Topic info
                    t.topic_name,
                    -- Source article info
                    kb.name as source_article_name
                FROM posting_queue pq
                LEFT JOIN kb_topics t ON pq.topic_id = t.id
                LEFT JOIN clan_kb_articles kb ON pq.source_page_id = kb.id
                WHERE pq.scheduled_date >= %s
                AND pq.scheduled_date <= %s
                AND pq.platform = 'facebook'
                AND pq.role IS NOT NULL
                ORDER BY pq.scheduled_date, pq.scheduled_time
            """, (week_start, week_end))
            
            framework_posts = cursor.fetchall()
            
            # Get legacy posts (without roles)
            cursor.execute("""
                SELECT 
                    pq.id,
                    pq.platform,
                    pq.channel_type,
                    pq.content_type,
                    pq.generated_content,
                    pq.generated_caption,
                    pq.status,
                    pq.scheduled_date,
                    pq.scheduled_time,
                    pq.scheduled_timestamp,
                    pq.created_at,
                    pq.updated_at,
                    -- Product info
                    cp.name as product_name,
                    -- Idea info
                    ci.idea_title
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                LEFT JOIN calendar_ideas ci ON pq.idea_id = ci.id
                WHERE pq.scheduled_date >= %s
                AND pq.scheduled_date <= %s
                AND pq.platform = 'facebook'
                AND pq.role IS NULL
                ORDER BY pq.scheduled_date, pq.scheduled_time
            """, (week_start, week_end))
            
            legacy_posts_raw = cursor.fetchall()
        
        # Process framework posts
        for post in framework_posts:
            post_dict = dict(post)
            scheduled_date = post_dict['scheduled_date']
            
            if not scheduled_date:
                continue
            
            # Get weekday (0=Monday, 6=Sunday)
            weekday = scheduled_date.isoweekday() - 1  # Convert 1-7 to 0-6
            scheduled_time = post_dict['scheduled_time']
            
            if scheduled_time:
                if isinstance(scheduled_time, str):
                    time_str = scheduled_time[:5]  # HH:MM
                else:
                    time_str = str(scheduled_time)[:5]
            else:
                time_str = None
            
            # Find matching rail
            rail = schedule_map.get((weekday, time_str))
            
            if rail:
                slot_key = (weekday, rail['role'])
                if slot_key not in posts_by_slot:
                    posts_by_slot[slot_key] = []
                
                # Format post data
                post_data = {
                    'id': post_dict['id'],
                    'role': post_dict['role'],
                    'platform': post_dict['platform'],
                    'status': post_dict['status'],
                    'scheduled_date': scheduled_date.isoformat() if hasattr(scheduled_date, 'isoformat') else str(scheduled_date),
                    'scheduled_time': time_str,
                    'content': post_dict['generated_content'] or post_dict['generated_caption'] or '',
                    'preview': _get_preview(post_dict['generated_content'] or post_dict['generated_caption'] or ''),
                    'topic_id': post_dict['topic_id'],
                    'topic_name': post_dict['topic_name'],
                    'source_page_id': post_dict['source_page_id'],
                    'source_article_name': post_dict['source_article_name'],
                    'validation_report': post_dict['validation_report_json'],
                    'approved_at': post_dict['approved_at'].isoformat() if post_dict['approved_at'] else None,
                    'approved_by': post_dict['approved_by'],
                    'is_framework': True
                }
                
                posts_by_slot[slot_key].append(post_data)
        
        # Process legacy posts and detect conflicts
        for post in legacy_posts_raw:
            post_dict = dict(post)
            scheduled_date = post_dict['scheduled_date']
            
            if not scheduled_date:
                continue
            
            # Check for conflicts: legacy posts scheduled for Sunday 15:00 (reserved for DEPTH_LONG)
            is_conflict = False
            conflict_reason = None
            weekday_iso = scheduled_date.isoweekday()  # ISO: 1=Monday, 7=Sunday
            scheduled_time = post_dict['scheduled_time']
            
            if weekday_iso == 7:  # Sunday
                # Check if time is 15:00 (or close to it)
                if scheduled_time:
                    time_str = str(scheduled_time)[:5] if isinstance(scheduled_time, str) else str(scheduled_time)[:5]
                    if time_str == '15:00' or time_str.startswith('15:'):
                        # Check if DEPTH_LONG rail exists for Sunday 15:00
                        sunday_rail = schedule_map.get((6, '15:00'))  # 6 = Sunday in 0-indexed
                        if sunday_rail and sunday_rail.get('role') == 'DEPTH_LONG':
                            is_conflict = True
                            conflict_reason = f"Sunday 15:00 is reserved for DEPTH_LONG (Deep Dive) posts. This {post_dict['content_type']} post conflicts with the Content Roles Framework."
            
            legacy_posts.append({
                'id': post_dict['id'],
                'content_type': post_dict['content_type'],
                'platform': post_dict['platform'],
                'status': post_dict['status'],
                'scheduled_date': scheduled_date.isoformat() if hasattr(scheduled_date, 'isoformat') else str(scheduled_date),
                'scheduled_time': str(post_dict['scheduled_time']) if post_dict['scheduled_time'] else None,
                'content': post_dict['generated_content'] or post_dict['generated_caption'] or '',
                'preview': _get_preview(post_dict['generated_content'] or post_dict['generated_caption'] or ''),
                'product_name': post_dict['product_name'],
                'idea_title': post_dict['idea_title'],
                'is_framework': False,
                'is_legacy': True,
                'is_conflict': is_conflict,
                'conflict_reason': conflict_reason
            })
        
        # Build response with schedule rails and posts
        # Include ALL rails, even if no posts exist
        schedule_data = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_num in range(7):
            day_name = days[day_num]
            # Rails use ISO (1-7), convert to 0-indexed (0-6) for matching
            day_iso = day_num + 1
            day_rails = [r for r in rails if r['day'] == day_iso]
            
            for rail in day_rails:
                slot_key = (day_num, rail['role'])
                posts = posts_by_slot.get(slot_key, [])
                
                # Also check for posts by time match (in case time format differs slightly)
                if len(posts) == 0:
                    # Try to find posts for this day/time/role combination
                    for post_list in posts_by_slot.values():
                        for post in post_list:
                            # Check if this post matches this rail
                            post_date = datetime.fromisoformat(post['scheduled_date'].replace('Z', '+00:00')) if 'T' in post['scheduled_date'] else datetime.strptime(post['scheduled_date'], '%Y-%m-%d')
                            post_weekday = post_date.weekday()  # 0=Monday, 6=Sunday
                            
                            if post_weekday == day_num and post['role'] == rail['role']:
                                if slot_key not in posts_by_slot:
                                    posts_by_slot[slot_key] = []
                                if post not in posts_by_slot[slot_key]:
                                    posts_by_slot[slot_key].append(post)
                                    posts = posts_by_slot[slot_key]
                
                schedule_data.append({
                    'day': day_num,
                    'day_name': day_name,
                    'time': rail['time'],
                    'role': rail['role'],
                    'platform': rail['platform'],
                    'posts': posts,
                    'is_empty': len(posts) == 0
                })
        
        return jsonify({
            'success': True,
            'year': year,
            'week': week,
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'active_topic': active_topic,
            'schedule': schedule_data,
            'legacy_posts': legacy_posts
        })
    
    except Exception as e:
        logger.error(f"Error getting week data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/post/<int:post_id>')
def get_post_details(post_id):
    """
    Get detailed information for a specific post (for drill-down panel).
    
    Returns:
        Full post details including validation report, timestamps, etc.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pq.*,
                    t.topic_name,
                    t.topic_description,
                    kb.name as source_article_name,
                    kb.text as source_article_text,
                    cr.role_name,
                    cr.description as role_description,
                    cr.characteristics as role_characteristics
                FROM posting_queue pq
                LEFT JOIN kb_topics t ON pq.topic_id = t.id
                LEFT JOIN clan_kb_articles kb ON pq.source_page_id = kb.id
                LEFT JOIN content_roles cr ON pq.role = cr.role_code
                WHERE pq.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
        
        if not post:
            return jsonify({
                'success': False,
                'error': f'Post {post_id} not found'
            }), 404
        
        post_dict = dict(post)
        
        # Format dates
        for key in ['created_at', 'updated_at', 'scheduled_date', 'scheduled_timestamp', 'approved_at']:
            if post_dict.get(key) and hasattr(post_dict[key], 'isoformat'):
                post_dict[key] = post_dict[key].isoformat()
        
        # Parse validation report if JSON string
        if post_dict.get('validation_report_json'):
            if isinstance(post_dict['validation_report_json'], str):
                try:
                    post_dict['validation_report_json'] = json.loads(post_dict['validation_report_json'])
                except:
                    pass
        
        return jsonify({
            'success': True,
            'post': post_dict
        })
    
    except Exception as e:
        logger.error(f"Error getting post details: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_preview(text: str, max_length: int = 80) -> str:
    """Get preview text (first ~80 chars)."""
    if not text:
        return ''
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:  # If we found a space reasonably close
        return truncated[:last_space] + '...'
    
    return truncated + '...'
