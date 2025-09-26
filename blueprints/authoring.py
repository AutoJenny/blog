"""
Authoring Blueprint - Dedicated content creation workspace
Handles Sections, Post Info, and Images authoring phases
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Create authoring blueprint
bp = Blueprint('authoring', __name__, url_prefix='/authoring')

@bp.route('/')
def authoring_dashboard():
    """Main authoring dashboard"""
    return render_template('authoring/dashboard.html', blueprint_name='authoring')

@bp.route('/posts/<int:post_id>')
def authoring_post_overview(post_id):
    """Authoring overview for a specific post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            # Get authoring progress
            cursor.execute("""
                SELECT stage_id, sub_stage_id, status, updated_at
                FROM post_workflow_stage 
                WHERE post_id = %s AND stage_id IN (
                    SELECT id FROM workflow_stage_entity WHERE name = 'writing'
                )
                ORDER BY stage_id, sub_stage_id
            """, (post_id,))
            progress = cursor.fetchall()
            
            return render_template('authoring/post_overview.html', 
                                 post=post, progress=progress, blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_post_overview: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/sections')
def authoring_sections(post_id):
    """Sections authoring phase"""
    return render_template('authoring/sections.html', post_id=post_id, blueprint_name='authoring')

@bp.route('/posts/<int:post_id>/post-info')
def authoring_post_info(post_id):
    """Post info authoring phase"""
    return render_template('authoring/post_info.html', post_id=post_id, blueprint_name='authoring')

@bp.route('/posts/<int:post_id>/images')
def authoring_images(post_id):
    """Images authoring phase"""
    return render_template('authoring/images.html', post_id=post_id, blueprint_name='authoring')

@bp.route('/api/posts')
def api_posts():
    """API endpoint to get posts for authoring"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE status IN ('draft', 'in_process', 'published')
                ORDER BY updated_at DESC
                LIMIT 20
            """)
            posts = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'posts': [dict(post) for post in posts]
            })
            
    except Exception as e:
        logger.error(f"Error in api_posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/posts/<int:post_id>/progress')
def api_post_progress(post_id):
    """API endpoint to get authoring progress for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    wse.name as stage_name,
                    wsse.name as sub_stage_name,
                    pws.status,
                    pws.updated_at
                FROM post_workflow_stage pws
                JOIN workflow_stage_entity wse ON pws.stage_id = wse.id
                LEFT JOIN workflow_sub_stage_entity wsse ON pws.sub_stage_id = wsse.id
                WHERE pws.post_id = %s AND wse.name = 'writing'
                ORDER BY wse.stage_order, wsse.sub_stage_order
            """, (post_id,))
            progress = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'progress': [dict(p) for p in progress]
            })
            
    except Exception as e:
        logger.error(f"Error in api_post_progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
