# blueprints/launchpad_core.py
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

bp = Blueprint('launchpad_core', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Main launchpad dashboard."""
    return render_template('launchpad/index.html')

@bp.route('/cross-promotion')
def cross_promotion():
    """Cross-promotion management."""
    return render_template('launchpad/cross_promotion.html')

@bp.route('/publishing')
def publishing():
    """Publishing management."""
    return render_template('launchpad/publishing.html')

@bp.route('/syndication/dashboard')
def syndication_dashboard():
    """Syndication dashboard."""
    return render_template('launchpad/syndication_dashboard.html')

@bp.route('/syndication')
def syndication():
    """Main syndication page."""
    try:
        with db_manager.get_cursor() as cursor:
            # Get platforms
            cursor.execute("""
                SELECT id, name, display_name, logo_url, development_status
                FROM platforms
                ORDER BY display_name
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
        
        # Create a basic content process structure
        content_process = {
            'id': 1,
            'platform_id': platform['id'],
            'channel_type_id': 1,
            'name': f'{platform["display_name"]} {channel_type_info["display_name"]}',
            'description': channel_type_info['description']
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
            
            return jsonify({
                'success': True,
                'posts': posts
            })
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/posts')
def get_syndication_posts():
    """Get syndication posts."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, created_at, updated_at, status, platform, content_type
                FROM syndication_posts
                ORDER BY created_at DESC
            """)
            posts = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'posts': posts
            })
    except Exception as e:
        logger.error(f"Error getting syndication posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/social-media-platforms')
def get_social_media_platforms():
    """Get social media platforms."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, display_name, logo_url, development_status
                FROM platforms
                ORDER BY display_name
            """)
            platforms = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'platforms': platforms
            })
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/syndication/content-processes')
def get_content_processes():
    """Get content processes."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT cp.id, cp.platform_id, cp.channel_type_id,
                       p.name as platform_name, p.display_name as platform_display_name
                FROM content_processes cp
                JOIN platforms p ON cp.platform_id = p.id
                ORDER BY p.display_name
            """)
            content_processes = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'content_processes': content_processes
            })
    except Exception as e:
        logger.error(f"Error getting content processes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/social-media-command-center')
def social_media_command_center():
    """Main Social Media Command Center dashboard."""
    return render_template('launchpad/social_media_command_center.html')

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})