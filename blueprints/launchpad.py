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
        with db_manager.get_cursor() as cursor:
            # Get platform info
            cursor.execute("""
                SELECT p.id, p.name, p.display_name, p.logo_url, p.development_status
                FROM platforms p
                WHERE p.name ILIKE %s
            """, (platform_name,))
            platform = cursor.fetchone()
            
            if not platform:
                return jsonify({"error": "Platform not found"}), 404
            
            # Get channel type info
            cursor.execute("""
                SELECT ct.id, ct.name, ct.display_name, ct.description
                FROM channel_types ct
                WHERE ct.name ILIKE %s
            """, (channel_type,))
            channel_type_info = cursor.fetchone()
            
            if not channel_type_info:
                return jsonify({"error": "Channel type not found"}), 404
            
            # Get content process
            cursor.execute("""
                SELECT cp.id, cp.name, cp.config, cp.status
                FROM content_processes cp
                JOIN platforms p ON cp.platform_id = p.id
                JOIN channel_types ct ON cp.channel_type = ct.name
                WHERE p.name ILIKE %s AND ct.name ILIKE %s
            """, (platform_name, channel_type))
            content_process = cursor.fetchone()
            
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

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "launchpad"})