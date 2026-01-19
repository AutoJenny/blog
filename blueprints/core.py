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
        from datetime import datetime
        
        # Get current week
        now = datetime.now()
        current_year = now.isocalendar()[0]
        current_week = now.isocalendar()[1]
        
        # Try to get post for current week first
        with db_manager.get_cursor() as cursor:
            # Check if calendar_week_posts_v2 exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calendar_week_posts_v2'
                )
            """)
            has_v2_table = cursor.fetchone()['exists']
            
            first_post_id = None
            
            if has_v2_table:
                # Get post scheduled for current week (excluding deleted posts)
                cursor.execute("""
                    SELECT cwp.post_id
                    FROM calendar_week_posts_v2 cwp
                    INNER JOIN post p ON cwp.post_id = p.id
                    WHERE cwp.year = %s 
                      AND cwp.week_number = %s
                      AND p.status != 'deleted'
                    ORDER BY cwp.created_at DESC, cwp.post_id DESC
                    LIMIT 1
                """, (current_year, current_week))
                result = cursor.fetchone()
                if result:
                    first_post_id = result['post_id']
            
            # Fallback to latest post if no current week post found
            if not first_post_id:
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
        current_year = datetime.now().isocalendar()[0]
        current_week = datetime.now().isocalendar()[1]
        stats = {'post_count': 0, 'image_count': 0, 'workflow_count': 0, 'llm_count': 0}
    
    return render_template('index.html', 
                         first_post_id=first_post_id,
                         current_year=current_year,
                         current_week=current_week,
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

@bp.route('/api/ollama/status')
def ollama_status():
    """Check if Ollama is running"""
    try:
        from modules.llm_service import LLMService
        llm_service = LLMService()
        
        # Try to get available models (quick check)
        models = llm_service.get_available_models('ollama')
        
        return jsonify({
            'success': True,
            'is_running': True,
            'models': models,
            'base_url': 'http://localhost:11434'
        })
    except Exception as e:
        logger.error(f"Ollama status check failed: {e}")
        return jsonify({
            'success': True,
            'is_running': False,
            'error': str(e),
            'base_url': 'http://localhost:11434'
        })

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
