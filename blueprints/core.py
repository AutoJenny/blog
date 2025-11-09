# blueprints/core.py
from flask import Blueprint, render_template, jsonify, request, redirect
import logging
import json
from config.database import db_manager

bp = Blueprint('core', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Main page with header and workflow navigation."""
    try:
        # Get the latest post ID for workflow links
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id
                FROM post p
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            first_post_id = result['id'] if result else 1
            
            # Get stats for the dashboard
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM post WHERE status != 'deleted') as post_count,
                    (SELECT COUNT(*) FROM images) as image_count,
                    (SELECT COUNT(*) FROM workflow) as workflow_count,
                    (SELECT COUNT(*) FROM llm_interaction) as llm_count
            """)
            stats = cursor.fetchone()
            
    except Exception as e:
        logger.warning(f"Could not fetch data: {e}")
        first_post_id = 1
        stats = {'post_count': 0, 'image_count': 0, 'workflow_count': 0, 'llm_count': 0}
    
    return render_template('index.html', 
                         first_post_id=first_post_id,
                         post_count=stats['post_count'],
                         image_count=stats['image_count'],
                         workflow_count=stats['workflow_count'],
                         llm_count=stats['llm_count'],
                         blueprint_name='core')

# ARCHIVED: Old workflow routes have been moved to ARCHIVED_OLD_WORKFLOW/routes/workflow_routes.py
# The following routes were removed:
# - /workflow/
# - /workflow/posts/<post_id>
# - /workflow/posts/<post_id>/<stage>
# - /workflow/posts/<post_id>/<stage>/<substage>
# - /workflow/posts/<post_id>/<stage>/<substage>/<step>
# - /api/llm-actions/content
# 
# These routes are replaced by the unified system:
# - /planning/posts/<post_id>/calendar/week-view
# - /planning/posts/<post_id>/calendar/ideas
# - /authoring/posts/<post_id>/sections/drafting
# - /imaging/posts/<post_id>/sections/image-generation
# 
# See ARCHIVED_OLD_WORKFLOW/README.md for migration details.

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "core"})

@bp.route('/api/posts')
def api_posts():
    """
    API endpoint to get all posts.
    
    TODO: DEPRECATED - Use blueprints.posts.api_posts() instead.
    This endpoint is maintained for backward compatibility but should be replaced.
    The new consolidated endpoint is at /api/posts (blueprints/posts.py).
    This endpoint will be removed in a future refactor.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.idea_seed
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status != 'deleted'
                ORDER BY p.updated_at DESC, p.id DESC
            """)
            posts = cursor.fetchall()
        
        return jsonify({"posts": posts})
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return jsonify({"error": str(e)}), 500
