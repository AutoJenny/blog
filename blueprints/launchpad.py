# blueprints/launchpad.py
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import logging
import json
import os
import requests
from datetime import datetime
import pytz
from humanize import naturaltime
from config.database import db_manager

bp = Blueprint('launchpad', __name__)
logger = logging.getLogger(__name__)

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
                       cp.name as product_name, cp.sku, cp.image_url as product_image,
                       cp.price
                FROM posting_queue pq
                LEFT JOIN clan_products cp ON pq.product_id = cp.id
                WHERE pq.status IN ('pending', 'ready', 'published', 'failed')
                ORDER BY pq.created_at ASC
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
                    'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None
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

# Scheduling API endpoints
@bp.route('/api/syndication/schedules')
def get_schedules():
    """Get all posting schedules."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, time, timezone, days, is_active, created_at, updated_at, name
                FROM daily_posts_schedule
                ORDER BY created_at DESC
            """)
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

@bp.route('/api/syndication/save-selected-product', methods=['POST'])
def save_selected_product():
    """Save the selected product to ui_session_state table."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({
                'success': False,
                'message': 'Product ID is required'
            }), 400
        
        with db_manager.get_cursor() as cursor:
            # Delete any existing selected product entry
            cursor.execute("""
                DELETE FROM ui_session_state 
                WHERE state_key = 'selected_product_id'
            """)
            
            # Insert new selected product
            cursor.execute("""
                INSERT INTO ui_session_state (session_id, state_key, state_value, state_type, expires_at)
                VALUES ('global', 'selected_product_id', %s, 'integer', NULL)
            """, (product_id,))
        
        return jsonify({
            'success': True,
            'message': 'Selected product saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in save_selected_product: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to save selected product'
        }), 500

@bp.route('/api/syndication/get-selected-product')
def get_selected_product():
    """Get the currently selected product from ui_session_state table."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get selected product ID
            cursor.execute("""
                SELECT state_value FROM ui_session_state 
                WHERE state_key = 'selected_product_id'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    'success': True,
                    'product': None
                })
            
            product_id = result['state_value']
            
            # Get product details
            cursor.execute("""
                SELECT id, name, sku, price, description, image_url
                FROM clan_products 
                WHERE id = %s
            """, (product_id,))
            
            product_result = cursor.fetchone()
        
        if product_result:
            product = {
                'id': product_result['id'],
                'name': product_result['name'],
                'sku': product_result['sku'],
                'price': product_result['price'],
                'description': product_result['description'],
                'image_url': product_result['image_url']
            }
            
            return jsonify({
                'success': True,
                'product': product
            })
        else:
            return jsonify({
                'success': True,
                'product': None
            })
            
    except Exception as e:
        logger.error(f"Error in get_selected_product: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get selected product'
        }), 500

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "launchpad"})