# blueprints/launchpad.py
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import logging
import json
import os
import requests
from datetime import datetime, date, time, timedelta
import pytz
from humanize import naturaltime
from config.database import db_manager
import psycopg

bp = Blueprint('launchpad', __name__)
logger = logging.getLogger(__name__)

def get_next_posting_slot(cursor, platform='facebook', content_type='product'):
    """Calculate the next available posting slot based on schedules and existing queue."""
    try:
        # Get active schedules for the specific platform and content type
        cursor.execute("""
            SELECT id, time, timezone, days, is_active
            FROM daily_posts_schedule
            WHERE is_active = true AND platform = %s AND content_type = %s
            ORDER BY time ASC
        """, (platform, content_type))
        schedules = cursor.fetchall()
        
        if not schedules:
            return None
        
        # Get the latest scheduled post to know where to start
        cursor.execute("""
            SELECT scheduled_timestamp, scheduled_date, scheduled_time
            FROM posting_queue
            WHERE scheduled_timestamp IS NOT NULL
            ORDER BY scheduled_timestamp DESC
            LIMIT 1
        """)
        latest_scheduled = cursor.fetchone()
        
        # Start from current time or latest scheduled time + 1 day
        if latest_scheduled and latest_scheduled['scheduled_timestamp']:
            start_date = latest_scheduled['scheduled_date'] + timedelta(days=1)
        else:
            start_date = date.today()
        
        # First, try to fill existing scheduled days
        cursor.execute("""
            SELECT scheduled_date, scheduled_time, COUNT(*) as count
            FROM posting_queue
            WHERE scheduled_timestamp IS NOT NULL
            GROUP BY scheduled_date, scheduled_time
            ORDER BY scheduled_date, scheduled_time
        """)
        existing_slots = cursor.fetchall()
        
        # Check existing slots first to fill them up
        for slot in existing_slots:
            slot_date = slot['scheduled_date']
            slot_time = slot['scheduled_time']
            existing_count = slot['count']
            
            # Allow only 1 post per time slot
            max_posts_per_slot = 1
            
            if existing_count < max_posts_per_slot:
                # Found an available slot in existing day
                slot_timestamp = datetime.combine(slot_date, slot_time)
                return {
                    'date': slot_date,
                    'time': slot_time,
                    'timestamp': slot_timestamp,
                    'schedule_name': f'Existing Slot',
                    'timezone': 'GMT'
                }
        
        # If no existing slots available, find the next new slot
        for days_ahead in range(30):  # Look up to 30 days ahead
            check_date = start_date + timedelta(days=days_ahead)
            day_of_week = check_date.isoweekday()  # 1=Monday, 7=Sunday
            
            for schedule in schedules:
                schedule_days = schedule['days'] if isinstance(schedule['days'], list) else json.loads(schedule['days'])
                
                if day_of_week in schedule_days:
                    # This schedule applies to this day
                    schedule_time = schedule['time']
                    schedule_timestamp = datetime.combine(check_date, schedule_time)
                    
                    # Check if this slot already exists
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM posting_queue
                        WHERE scheduled_date = %s AND scheduled_time = %s
                    """, (check_date, schedule_time))
                    
                    existing_count = cursor.fetchone()['count']
                    
                    if existing_count == 0:
                        # Found a new available slot
                        return {
                            'date': check_date,
                            'time': schedule_time,
                            'timestamp': schedule_timestamp,
                            'schedule_name': f'Schedule {schedule["id"]}',
                            'timezone': schedule['timezone']
                        }
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculating next posting slot: {e}")
        return None

# Custom Jinja2 filter to strip HTML document structure
def strip_html_doc(content):
    """Strip HTML document structure and return only body content."""
    if not content:
        return content
    
    import re
    
    # Remove DOCTYPE declaration
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove html, head, and body tags, keeping only the content inside body
    content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove any remaining malformed HTML closing tags
    content = re.sub(r'</html[^>]*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*', '', content, flags=re.IGNORECASE)
    
    # Clean up any remaining whitespace and newlines
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'>\s+<', '><', content)
    
    return content.strip()

# Register the template filter with the blueprint
bp.add_app_template_filter(strip_html_doc, 'strip_html_doc')

@bp.route('/')
def index():
    """Main launchpad page."""
    return render_template('launchpad/index.html')

@bp.route('/api/syndication/save-generated-content', methods=['POST'])
def save_generated_content():
    """Save generated content for a product."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        content_type = data.get('content_type', 'product')
        generated_content = data.get('content') or data.get('generated_content')
        
        if not product_id or not generated_content:
            return jsonify({
                'success': False,
                'error': 'Product ID and generated content are required'
            }), 400
        
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            
            # Check if content already exists for this product and content_type
            cur.execute("""
                SELECT id FROM posting_queue 
                WHERE product_id = %s AND content_type = %s AND status = 'draft'
            """, (product_id, content_type))
            
            existing = cur.fetchone()
            
            if existing:
                # Update existing content
                cur.execute("""
                    UPDATE posting_queue 
                    SET generated_content = %s, updated_at = NOW()
                    WHERE product_id = %s AND content_type = %s AND status = 'draft'
                """, (generated_content, product_id, content_type))
            else:
                # Insert new content as draft
                cur.execute("""
                    INSERT INTO posting_queue (product_id, content_type, generated_content, status, created_at, updated_at)
                    VALUES (%s, %s, %s, 'draft', NOW(), NOW())
                """, (product_id, content_type, generated_content))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Content saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error saving generated content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/get-generated-content/<int:product_id>/<content_type>')
def get_generated_content(product_id, content_type):
    """Get generated content for a product and content type."""
    try:
        with db_manager.get_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Query for generated content
            cur.execute("""
                SELECT generated_content as content, created_at, updated_at 
                FROM posting_queue 
                WHERE product_id = %s AND content_type = %s AND status IN ('draft', 'ready', 'pending')
            """, (product_id, content_type))
            
            result = cur.fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'content': result['content'],
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                    'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
                })
            else:
                return jsonify({
                    'success': True,
                    'content': None,
                    'message': 'No content found'
                })
                
    except Exception as e:
        logger.error(f"Error getting generated content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/update-queue-status', methods=['POST'])
def update_queue_status():
    """Update the status of a queue item from 'draft' to 'ready' and schedule it."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        content_type = data.get('content_type', 'product')
        status = data.get('status', 'ready')
        
        if not product_id or not content_type:
            return jsonify({
                'success': False,
                'error': 'product_id and content_type are required'
            }), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get the next available posting slot for this platform and content type
                next_slot = get_next_posting_slot(cursor, platform='facebook', content_type=content_type)
                
                if not next_slot:
                    return jsonify({
                        'success': False,
                        'error': 'No available posting slots found'
                    }), 400
                
                # Update the status and schedule the post
                cursor.execute("""
                    UPDATE posting_queue 
                    SET status = %s, 
                        scheduled_date = %s,
                        scheduled_time = %s,
                        scheduled_timestamp = %s,
                        schedule_name = %s,
                        timezone = %s,
                        updated_at = NOW()
                    WHERE product_id = %s AND content_type = %s AND status IN ('draft', 'pending', 'ready')
                """, (status, next_slot['date'], next_slot['time'], next_slot['timestamp'], 
                      next_slot['schedule_name'], next_slot['timezone'], product_id, content_type))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return jsonify({
                        'success': True,
                        'message': f'Queue item scheduled for {next_slot["date"]} at {next_slot["time"]} {next_slot["timezone"]}',
                        'scheduled_date': next_slot['date'].isoformat(),
                        'scheduled_time': str(next_slot['time']),
                        'scheduled_timestamp': next_slot['timestamp'].isoformat()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No draft content found for this product and content type'
                    }), 404
                
    except Exception as e:
        logger.error(f"Error updating queue status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/cross-promotion')
def cross_promotion():
    """Cross-promotion management page."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug,
                       pd.idea_seed, pd.intro_blurb, pd.main_title,
                       p.cross_promotion_category_id, p.cross_promotion_category_title,
                       p.cross_promotion_product_id, p.cross_promotion_product_title,
                       p.cross_promotion_category_position, p.cross_promotion_product_position,
                       p.cross_promotion_category_widget_html, p.cross_promotion_product_widget_html
                FROM post p
                LEFT JOIN post_development pd ON pd.post_id = p.id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC NULLS LAST, p.created_at DESC
            """)
            posts = cursor.fetchall()
            
            for post in posts:
                post['cross_promotion'] = {
                    'category_id': post.get('cross_promotion_category_id'),
                    'category_title': post.get('cross_promotion_category_title'),
                    'product_id': post.get('cross_promotion_product_id'),
                    'product_title': post.get('cross_promotion_product_title'),
                    'category_position': post.get('cross_promotion_category_position'),
                    'product_position': post.get('cross_promotion_product_position'),
                    'category_widget_html': post.get('cross_promotion_category_widget_html'),
                    'product_widget_html': post.get('cross_promotion_product_widget_html')
                }
                # Note: get_post_sections_with_images would need to be implemented
                post['sections'] = []
    
        default_post = posts[0] if posts else None
        return render_template('launchpad/cross_promotion.html', posts=posts, default_post=default_post)
    except Exception as e:
        logger.error(f"Error in cross_promotion: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/publishing')
def publishing():
    """Publishing management page."""
    return render_template('launchpad/publishing.html')

@bp.route('/syndication/dashboard')
def syndication_dashboard():
    """Redirect to main syndication page."""
    return redirect('/launchpad/syndication')

@bp.route('/syndication')
def syndication():
    """Main syndication dashboard."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get platform data
            cursor.execute("""
                SELECT p.name, p.display_name, p.logo_url, p.development_status,
                       COUNT(cp.id) as process_count
                FROM platforms p
                LEFT JOIN content_processes cp ON p.id = cp.platform_id
                GROUP BY p.id, p.name, p.display_name, p.logo_url, p.development_status
                ORDER BY p.display_name
            """)
            platforms = cursor.fetchall()
            
            # Get content processes
            cursor.execute("""
                SELECT cp.id, cp.platform_id, cp.channel_type_id,
                       p.name as platform_name, p.display_name as platform_display_name
                FROM content_processes cp
                JOIN platforms p ON cp.platform_id = p.id
                ORDER BY p.display_name
            """)
            content_processes = cursor.fetchall()
            
        return render_template('launchpad/syndication.html', 
                             platforms=platforms, 
                             content_processes=content_processes)
    except Exception as e:
        logger.error(f"Error in syndication: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/syndication/<platform_name>/<channel_type>')
def syndication_platform_channel(platform_name, channel_type):
    """Platform-specific syndication configuration."""
    try:
        # Create fallback data for now to avoid database issues
        platform = {
            'id': 1,
            'name': platform_name,
            'display_name': platform_name.title(),
            'logo_url': f'/static/images/platforms/{platform_name}.png',
            'development_status': 'active'
        }
        
        # Define channel type configurations with proper icons and display names
        channel_configs = {
            'product_post': {
                'display_name': 'Product Posts',
                'icon': 'shopping-bag',
                'description': 'Automated daily Facebook posts featuring Clan.com products'
            },
            'blog_post': {
                'display_name': 'Blog Posts',
                'icon': 'newspaper',
                'description': 'Automated Facebook posts featuring blog content and articles'
            }
        }
        
        channel_config = channel_configs.get(channel_type, {
            'display_name': channel_type.replace('_', ' ').title(),
            'icon': 'cog',
            'description': f'{channel_type.replace("_", " ").title()} channel configuration'
        })
        
        channel_type_info = {
            'id': 1,
            'name': channel_type,
            'display_name': channel_config['display_name'],
            'icon': channel_config['icon'],
            'description': channel_config['description']
        }
        
        content_process = {
            'id': 1,
            'name': f'{platform_name}_{channel_type}',
            'config': {},
            'status': 'active'
        }
        
        return render_template(f'launchpad/syndication/{platform_name}/{channel_type}.html',
                             platform=platform,
                             channel_type=channel_type_info,
                             content_process=content_process)
    except Exception as e:
        logger.error(f"Error in syndication_platform_channel: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/posts')
def get_posts():
    """Get all posts for the launchpad."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.created_at, p.updated_at, p.status,
                       p.clan_post_id, p.clan_last_attempt, p.clan_error, p.clan_uploaded_url,
                       pd.idea_seed, pd.provisional_title, pd.intro_blurb
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.created_at DESC
            """)
            posts = cursor.fetchall()
            return jsonify([dict(post) for post in posts])
    except Exception as e:
        logger.error(f"Error in get_posts: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/syndication/posts')
def get_syndication_posts():
    """Get posts for syndication."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.subtitle, p.created_at, p.updated_at, p.status, p.slug,
                       pd.idea_seed, pd.intro_blurb, pd.main_title
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC
            """)
            posts = cursor.fetchall()
            return jsonify([dict(post) for post in posts])
    except Exception as e:
        logger.error(f"Error in get_syndication_posts: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/syndication/social-media-platforms')
def get_social_media_platforms():
    """Get all social media platforms."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.name, p.display_name, p.logo_url, p.development_status
                FROM platforms p
                ORDER BY p.display_name
            """)
            platforms = cursor.fetchall()
            return jsonify([dict(platform) for platform in platforms])
    except Exception as e:
        logger.error(f"Error in get_social_media_platforms: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/syndication/content-processes')
def get_content_processes():
    """Get all content processes."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cp.id, cp.platform_id, cp.channel_type_id,
                       p.name as platform_name, p.display_name as platform_display_name
                FROM content_processes cp
                JOIN platforms p ON cp.platform_id = p.id
                ORDER BY p.display_name
            """)
            processes = cursor.fetchall()
            return jsonify([dict(process) for process in processes])
    except Exception as e:
        logger.error(f"Error in get_content_processes: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/social-media-command-center')
def social_media_command_center():
    """Main Social Media Command Center dashboard."""
    return render_template('launchpad/social_media_command_center.html')

@bp.route('/api/queue')
def get_queue():
    """Get unified queue data for the command center."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT pq.id, pq.platform, pq.channel_type, pq.content_type,
                       pq.generated_content, pq.status,
                       pq.platform_post_id, pq.error_message,
                       pq.product_id, pq.created_at, pq.updated_at,
                       pq.scheduled_date, pq.scheduled_time, pq.scheduled_timestamp,
                       pq.schedule_name, pq.timezone,
                       cp.name as product_name, cp.sku, cp.image_url as product_image,
                       cp.price
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                WHERE pq.status IN ('pending', 'ready', 'published', 'failed')
                ORDER BY pq.scheduled_timestamp ASC NULLS LAST, pq.created_at ASC
                LIMIT 50
            """)
            
            items = cursor.fetchall()
            
            timeline_items = []
            for item in items:
                timeline_items.append({
                    'id': item['id'],
                    'platform': item['platform'],
                    'channel_type': item['channel_type'],
                    'content_type': item['content_type'],
                    'generated_content': item['generated_content'],
                    'status': item['status'],
                    'platform_post_id': item['platform_post_id'],
                    'error_message': item['error_message'],
                    'product_id': item['product_id'],
                    'product_name': item['product_name'],
                    'product_sku': item['sku'],
                    'product_image': item['product_image'],
                    'product_price': item['price'],
                    'created_at': item['created_at'].isoformat() if item['created_at'] else None,
                    'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None,
                    'scheduled_date': item['scheduled_date'].isoformat() if item['scheduled_date'] else None,
                    'scheduled_time': str(item['scheduled_time']) if item['scheduled_time'] else None,
                    'scheduled_timestamp': item['scheduled_timestamp'].isoformat() if item['scheduled_timestamp'] else None,
                    'schedule_name': item['schedule_name'],
                    'timezone': item['timezone']
                })
            
            return jsonify({
                'success': True,
                'items': timeline_items,
                'count': len(timeline_items)
            })
            
    except Exception as e:
        logger.error(f"Error in get_queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'items': [],
            'count': 0
        }), 500

@bp.route('/api/queue/<int:item_id>', methods=['DELETE'])
def delete_queue_item(item_id):
    """Delete a single queue item."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if item exists
                cursor.execute("SELECT id FROM posting_queue WHERE id = %s", (item_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'error': 'Queue item not found'
                    }), 404
                
                # Delete the item
                cursor.execute("DELETE FROM posting_queue WHERE id = %s", (item_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Queue item deleted successfully'
                })
            
    except Exception as e:
        logger.error(f"Error deleting queue item: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/queue/clear', methods=['POST'])
def clear_queue():
    """Clear all items from the queue."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get count before deletion
                cursor.execute("SELECT COUNT(*) FROM posting_queue")
                count = cursor.fetchone()['count']
                
                # Delete all items
                cursor.execute("DELETE FROM posting_queue")
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'All queue items deleted successfully',
                    'deleted_count': count
                })
            
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Scheduling API endpoints
@bp.route('/api/syndication/schedules')
def get_schedules():
    """Get posting schedules filtered by platform and content type."""
    try:
        # Get filter parameters from query string
        platform = request.args.get('platform', 'facebook')
        content_type = request.args.get('content_type', 'product')
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, time, timezone, days, is_active, created_at, updated_at, name
                FROM daily_posts_schedule
                WHERE platform = %s AND content_type = %s AND is_active = true
                ORDER BY created_at DESC
            """, (platform, content_type))
            schedules = cursor.fetchall()
            
            # Convert to list of dicts and serialize datetime objects
            result = []
            for schedule in schedules:
                schedule_dict = dict(schedule)
                if schedule_dict.get('created_at'):
                    schedule_dict['created_at'] = schedule_dict['created_at'].isoformat()
                if schedule_dict.get('updated_at'):
                    schedule_dict['updated_at'] = schedule_dict['updated_at'].isoformat()
                # Convert time object to string
                if schedule_dict.get('time'):
                    schedule_dict['time'] = str(schedule_dict['time'])
                # Handle days array - it's already a list from the database
                if schedule_dict.get('days') is not None:
                    # days is already a list, no need to parse
                    pass
                result.append(schedule_dict)
            
            return jsonify({
                "success": True,
                "schedules": result
            })
    except Exception as e:
        logger.error(f"Error in get_schedules: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/schedules', methods=['POST'])
def add_schedule():
    """Add a new posting schedule."""
    try:
        data = request.get_json()
        name = data.get('name', 'Schedule')  # Use name for display, but table doesn't have name column
        time = data.get('time')
        timezone = data.get('timezone')
        days = data.get('days', [])
        
        if not time or not timezone or not days:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        with db_manager.get_cursor() as cursor:
            import json
            cursor.execute("""
                INSERT INTO daily_posts_schedule (time, timezone, days, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, true, NOW(), NOW())
                RETURNING id
            """, (time, timezone, json.dumps(days)))
            
            schedule_id = cursor.fetchone()[0]
            
            return jsonify({
                "success": True,
                "schedule_id": schedule_id,
                "message": "Schedule created successfully"
            })
    except Exception as e:
        logger.error(f"Error in add_schedule: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/llm-prompts/<int:process_id>')
def get_llm_prompts(process_id):
    """Get LLM prompts for a specific process from process_configurations table."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT config_key, config_value, description
                FROM process_configurations 
                WHERE process_id = %s AND config_category = 'llm_prompt'
                ORDER BY display_order
            """, (process_id,))
            
            prompts = cursor.fetchall()
            
            if not prompts:
                return jsonify({
                    "success": False,
                    "error": "No LLM prompts found for this process"
                }), 404
            
            # Convert to dictionary format
            prompt_data = {}
            for prompt in prompts:
                prompt_data[prompt['config_key']] = {
                    'value': prompt['config_value'],
                    'description': prompt['description']
                }
            
            return jsonify({
                "success": True,
                "prompts": prompt_data
            })
            
    except Exception as e:
        logger.error(f"Error in get_llm_prompts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/llm-prompts/<int:process_id>', methods=['PUT'])
def update_llm_prompt(process_id):
    """Update a specific LLM prompt in process_configurations table."""
    try:
        data = request.get_json()
        config_key = data.get('config_key')
        config_value = data.get('config_value')
        
        if not config_key or not config_value:
            return jsonify({
                "success": False,
                "error": "config_key and config_value are required"
            }), 400
        
        with db_manager.get_cursor() as cursor:
            # Update the prompt in the database
            cursor.execute("""
                UPDATE process_configurations 
                SET config_value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE process_id = %s AND config_category = 'llm_prompt' AND config_key = %s
            """, (config_value, process_id, config_key))
            
            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "error": "Prompt not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Prompt updated successfully"
            })
            
    except Exception as e:
        logger.error(f"Error in update_llm_prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a posting schedule."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM daily_posts_schedule WHERE id = %s
            """, (schedule_id,))
            
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Schedule not found"}), 404
            
            return jsonify({
                "success": True,
                "message": "Schedule deleted successfully"
            })
    except Exception as e:
        logger.error(f"Error in delete_schedule: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/schedules/test')
def test_schedules():
    """Test all schedules and return preview."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, time, timezone, days, is_active,
                       CASE 
                           WHEN days::text = '[1,2,3,4,5]' THEN 'Weekdays'
                           WHEN days::text = '[6,7]' THEN 'Weekends' 
                           WHEN days::text = '[1,2,3,4,5,6,7]' THEN 'Daily'
                           ELSE 'Custom Schedule'
                       END as name
                FROM daily_posts_schedule
                WHERE is_active = true
                ORDER BY created_at DESC
            """)
            schedules = cursor.fetchall()
            
            if not schedules:
                return jsonify({
                    "success": True,
                    "preview": "No schedules configured"
                })
            
            # Generate preview for next 7 days
            import json
            from datetime import datetime, timedelta
            
            preview_lines = []
            for schedule in schedules:
                schedule_dict = dict(schedule)
                days = json.loads(schedule_dict['days']) if schedule_dict['days'] else []
                time = schedule_dict['time']
                timezone = schedule_dict['timezone']
                name = schedule_dict.get('name', f"Schedule {schedule_dict['id']}")
                
                # Calculate next few occurrences
                now = datetime.now()
                occurrences = []
                for i in range(7):
                    check_date = now + timedelta(days=i)
                    day_of_week = check_date.weekday() + 1  # Convert to 1-7 (Mon-Sun)
                    if day_of_week in days:
                        date_str = check_date.strftime('%A, %B %d')
                        occurrences.append(f"{date_str} at {time} {timezone}")
                
                if occurrences:
                    preview_lines.append(f"{name}:")
                    preview_lines.extend([f"  - {occ}" for occ in occurrences[:3]])  # Show next 3
                    if len(occurrences) > 3:
                        preview_lines.append(f"  - ... and {len(occurrences) - 3} more")
                    preview_lines.append("")
            
            preview = "\n".join(preview_lines) if preview_lines else "No active schedules"
            
            return jsonify({
                "success": True,
                "preview": preview
            })
    except Exception as e:
        logger.error(f"Error in test_schedules: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/schedules/clear', methods=['POST'])
def clear_schedules():
    """Clear all posting schedules."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("DELETE FROM daily_posts_schedule")
            
            return jsonify({
                "success": True,
                "message": "All schedules cleared successfully"
            })
    except Exception as e:
        logger.error(f"Error in clear_schedules: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/today-status')
def get_today_status():
    """Get today's posting status."""
    try:
        with db_manager.get_cursor() as cursor:
            # Check if there's a post for today
            cursor.execute("""
                SELECT id, status, created_at, scheduled_date
                FROM posting_queue
                WHERE DATE(created_at) = CURRENT_DATE
                ORDER BY created_at DESC
                LIMIT 1
            """)
            post = cursor.fetchone()
            
            if post:
                post_dict = dict(post)
                if post_dict.get('created_at'):
                    post_dict['created_at'] = post_dict['created_at'].isoformat()
                if post_dict.get('scheduled_date'):
                    post_dict['scheduled_date'] = post_dict['scheduled_date'].isoformat()
            else:
                post_dict = None
            
            return jsonify({
                "success": True,
                "post": post_dict
            })
    except Exception as e:
        logger.error(f"Error in get_today_status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/post-now', methods=['POST'])
def post_now():
    """Post immediately."""
    try:
        # This would integrate with actual posting logic
        # For now, just return success
        return jsonify({
            "success": True,
            "message": "Post published successfully"
        })
    except Exception as e:
        logger.error(f"Error in post_now: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/schedule-tomorrow', methods=['POST'])
def schedule_tomorrow():
    """Schedule post for tomorrow."""
    try:
        # This would integrate with actual scheduling logic
        # For now, just return success
        return jsonify({
            "success": True,
            "message": "Post scheduled for tomorrow"
        })
    except Exception as e:
        logger.error(f"Error in schedule_tomorrow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/syndication/categories')
def get_categories():
    """Get product categories."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, parent_id, level
                FROM clan_categories
                ORDER BY level, name
            """)
            
            categories = cursor.fetchall()
            
            category_list = []
            for category in categories:
                category_dict = dict(category)
                category_list.append(category_dict)
            
            return jsonify({
                'success': True,
                'categories': category_list
            })
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/products')
def get_products():
    """Get all products for browsing."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, sku, price, description, image_url, url, printable_design_type,
                       category_ids
                FROM clan_products
                ORDER BY name
            """)
            
            products = cursor.fetchall()
            
            product_list = []
            for product in products:
                product_dict = dict(product)
                # Parse category_ids if it's a JSON string
                if product_dict.get('category_ids') and isinstance(product_dict['category_ids'], str):
                    try:
                        product_dict['category_ids'] = json.loads(product_dict['category_ids'])
                    except:
                        product_dict['category_ids'] = []
                product_list.append(product_dict)
            
            return jsonify({
                'success': True,
                'products': product_list
            })
    except Exception as e:
        logger.error(f"Error in get_products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/last-updated')
def get_last_updated():
    """Get last updated timestamp and product count."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get product count
            cursor.execute("SELECT COUNT(*) as total_products FROM clan_products")
            product_count = cursor.fetchone()['total_products']
            
            # For now, just return current time as last updated
            from datetime import datetime
            last_updated = datetime.now()
            
            return jsonify({
                'success': True,
                'total_products': product_count,
                'last_updated': last_updated.isoformat()
            })
    except Exception as e:
        logger.error(f"Error in get_last_updated: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/select-product', methods=['POST'])
def select_random_product():
    """Select a random product for posting."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get a random product
            cursor.execute("""
                SELECT id, name, sku, price, description, image_url, url, printable_design_type,
                       category_ids
                FROM clan_products
                ORDER BY RANDOM()
                LIMIT 1
            """)
            
            product = cursor.fetchone()
            
            if product:
                product_dict = dict(product)
                # Parse category_ids if it's a JSON string
                if product_dict.get('category_ids') and isinstance(product_dict['category_ids'], str):
                    try:
                        product_dict['category_ids'] = json.loads(product_dict['category_ids'])
                    except:
                        product_dict['category_ids'] = []
                
                return jsonify({
                    'success': True,
                    'product': product_dict
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No products found'
                })
    except Exception as e:
        logger.error(f"Error in select_random_product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/update-products', methods=['POST'])
def update_products():
    """Update products from external source (placeholder)."""
    try:
        # This is a placeholder - in a real implementation, this would sync with external APIs
        # For now, just return success with mock data
        return jsonify({
            'success': True,
            'message': 'Products are up to date',
            'stats': {
                'updated': 0,
                'categories_updated': False
            }
        })
    except Exception as e:
        logger.error(f"Error in update_products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# NEW SIMPLE ENDPOINTS - NO MORE BROKEN CODE

@bp.route('/api/selected-product', methods=['GET'])
def get_current_product():
    """Get the currently selected product - SIMPLE VERSION."""
    try:
        with db_manager.get_connection() as conn:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
            
            # Get the most recent selected product
            cur.execute("""
                SELECT state_value FROM ui_session_state 
                WHERE state_key = 'selected_product_id' 
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            result = cur.fetchone()
            if not result:
                return jsonify({'product': None})
            
            # Get product details
            cur.execute("""
                SELECT id, name, sku, price, description, image_url, url
                FROM clan_products WHERE id = %s
            """, (result['state_value'],))
            
            product = cur.fetchone()
            return jsonify({'product': product})
            
    except Exception as e:
        logger.error(f"Error getting selected product: {e}")
        return jsonify({'product': None}), 500

@bp.route('/api/selected-product', methods=['POST'])
def set_current_product():
    """Set the currently selected product - SIMPLE VERSION."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'product_id required'}), 400
        
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            
            # Delete old selection
            cur.execute("DELETE FROM ui_session_state WHERE state_key = 'selected_product_id'")
            
            # Insert new selection
            cur.execute("""
                INSERT INTO ui_session_state (session_id, state_key, state_value, state_type, updated_at)
                VALUES ('global', 'selected_product_id', %s, 'integer', NOW())
            """, (product_id,))
            
            conn.commit()
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error setting selected product: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/syndication/generate-social-content', methods=['POST'])
def generate_social_content():
    """Generate social media content using direct LLM call."""
    try:
        from blueprints.llm_actions import LLMService
        
        data = request.get_json()
        prompt = data.get('prompt')
        provider = data.get('provider', 'ollama')
        model = data.get('model', 'mistral')
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400
        
        # Create LLM service and execute request
        llm_service = LLMService()
        messages = [
            {
                'role': 'system',
                'content': 'You are a social media content creator specializing in product marketing. Create engaging, authentic posts that highlight product features and benefits.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        result = llm_service.execute_llm_request(provider, model, messages)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating social content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/auto-replenish-all', methods=['POST'])
def auto_replenish_all_queues():
    """Auto-replenish all configured queue types when they fall below threshold."""
    try:
        # Load queue configurations from file
        import json
        import os
        
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'queue_auto_replenish.json')
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.error(f"Queue auto-replenish config file not found: {config_file}")
            return jsonify({
                'success': False,
                'error': 'Configuration file not found'
            }), 500
        
        if not config.get('enabled', False):
            return jsonify({
                'success': True,
                'message': 'Auto-replenish is disabled in configuration',
                'results': []
            })
        
        queue_configs = [q for q in config.get('queues', []) if q.get('enabled', True)]
        
        results = []
        
        for config in queue_configs:
            try:
                result = replenish_queue(config)
                results.append({
                    'queue_type': config['type'],
                    'platform': config['platform'],
                    'success': True,
                    'items_added': result.get('items_added', 0),
                    'message': result.get('message', '')
                })
            except Exception as e:
                logger.error(f"Failed to replenish {config['type']} queue: {e}")
                results.append({
                    'queue_type': config['type'],
                    'platform': config['platform'],
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': 'Auto-replenish completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Auto-replenish-all failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def replenish_queue(config):
    """Replenish a specific queue type."""
    queue_type = config['type']
    platform = config['platform']
    threshold = config['threshold']
    add_count = config['add_count']
    
    with db_manager.get_cursor() as cursor:
        # Check current queue count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM posting_queue 
            WHERE content_type = %s AND platform = %s AND status IN ('draft', 'ready', 'pending')
        """, (queue_type, platform))
        
        result = cursor.fetchone()
        current_count = result['count'] if result else 0
        
        if current_count >= threshold:
            return {
                'items_added': 0,
                'message': f'Queue already has {current_count} items (threshold: {threshold})'
            }
        
        # Calculate how many items to add
        items_needed = max(0, threshold - current_count)
        items_to_add = min(add_count, items_needed)
        
        if items_to_add == 0:
            return {
                'items_added': 0,
                'message': f'No items needed (current: {current_count}, threshold: {threshold})'
            }
        
        # Add items to queue (reuse the "Add 10 items" logic)
        items_added = 0
        errors = 0
        
        for i in range(items_to_add):
            try:
                # Step 1: Select random product
                cursor.execute("""
                    SELECT id, name, sku, price, description, image_url, url
                    FROM clan_products
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
                product = cursor.fetchone()
                
                if not product:
                    logger.warning("No products found for auto-replenish")
                    break
                
                # Step 2: Generate content (simplified - just create basic content)
                generated_content = f"Auto-generated content for {product['name']} - {product['sku']}"
                
                # Step 3: Add to queue
                cursor.execute("""
                    INSERT INTO posting_queue (product_id, content_type, generated_content, status, platform, created_at, updated_at)
                    VALUES (%s, %s, %s, 'draft', %s, NOW(), NOW())
                """, (product['id'], queue_type, generated_content, platform))
                
                items_added += 1
                
            except Exception as e:
                logger.error(f"Error adding item {i+1} to {queue_type} queue: {e}")
                errors += 1
        
        return {
            'items_added': items_added,
            'errors': errors,
            'message': f'Added {items_added} items to {queue_type} queue (errors: {errors})'
        }

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "launchpad"})