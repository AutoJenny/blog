"""
Planning Blueprint - Dedicated planning workspace
Handles Idea, Research, and Structure planning phases
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

@bp.route('/')
def planning_dashboard():
    """Main planning dashboard"""
    return render_template('planning/dashboard.html')

@bp.route('/posts/<int:post_id>')
def planning_post_overview(post_id):
    """Planning overview for a specific post"""
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
            
            # Get planning progress
            cursor.execute("""
                SELECT stage_id, sub_stage_id, status, updated_at
                FROM post_workflow_stage 
                WHERE post_id = %s AND stage_id IN (
                    SELECT id FROM workflow_stage_entity WHERE name = 'planning'
                )
                ORDER BY stage_id, sub_stage_id
            """, (post_id,))
            progress = cursor.fetchall()
            
            return render_template('planning/post_overview.html', 
                                 post=post, progress=progress)
            
    except Exception as e:
        logger.error(f"Error in planning_post_overview: {e}")
        return f"Error: {e}", 500

@bp.route('/posts/<int:post_id>/idea')
def planning_idea(post_id):
    """Idea planning phase"""
    return render_template('planning/idea.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/research')
def planning_research(post_id):
    """Research planning phase"""
    return render_template('planning/research.html', post_id=post_id)

@bp.route('/posts/<int:post_id>/structure')
def planning_structure(post_id):
    """Structure planning phase"""
    return render_template('planning/structure.html', post_id=post_id)

@bp.route('/api/posts')
def api_posts():
    """API endpoint to get posts for planning"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE status IN ('draft', 'in_process')
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
    """API endpoint to get planning progress for a post"""
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
                WHERE pws.post_id = %s AND wse.name = 'planning'
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
