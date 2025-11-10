"""
Post Type Pipeline API
Provides endpoints for pipeline configuration based on post type.
"""
from flask import Blueprint, jsonify, request
from config.database import db_manager
from config.post_type_pipeline_configs import get_pipeline_steps, get_step_label
from utils.taxonomy_helpers import get_post_type
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('post_type_pipeline', __name__, url_prefix='/api/post-type-pipeline')

@bp.route('/<post_type>', methods=['GET'])
def get_pipeline_steps_for_type(post_type):
    """Get pipeline steps for a post type."""
    try:
        steps = get_pipeline_steps(post_type)
        
        # Get step details from database if available
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT step_id, step_label, run_function, complete_event, prompt_category
                FROM post_type_pipeline_steps
                WHERE post_type = %s AND is_active = TRUE
                ORDER BY step_order
            """, (post_type,))
            
            db_steps = cursor.fetchall()
            
            # Build response with step details
            steps_with_details = []
            for step_id in steps:
                # Find matching step in database
                db_step = next((s for s in db_steps if (s.get('step_id') if isinstance(s, dict) else s[0]) == step_id), None)
                
                if db_step:
                    if isinstance(db_step, dict):
                        steps_with_details.append({
                            'id': db_step['step_id'],
                            'label': db_step['step_label'] or get_step_label(step_id),
                            'run_function': db_step['run_function'],
                            'complete_event': db_step['complete_event'],
                            'prompt_category': db_step['prompt_category']
                        })
                    else:
                        steps_with_details.append({
                            'id': db_step[0],
                            'label': db_step[1] or get_step_label(step_id),
                            'run_function': db_step[2],
                            'complete_event': db_step[3],
                            'prompt_category': db_step[4] if len(db_step) > 4 else None
                        })
                else:
                    # Fallback to config defaults
                    steps_with_details.append({
                        'id': step_id,
                        'label': get_step_label(step_id),
                        'run_function': None,
                        'complete_event': None,
                        'prompt_category': None
                    })
        
        return jsonify({
            'success': True,
            'post_type': post_type,
            'steps': steps_with_details
        })
        
    except Exception as e:
        logger.error(f"Error fetching pipeline steps for {post_type}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/posts/<int:post_id>/pipeline', methods=['GET'])
def get_pipeline_for_post(post_id):
    """Get pipeline configuration for a specific post."""
    try:
        post_type = get_post_type(post_id)
        steps = get_pipeline_steps(post_type)
        
        # Get post title and content_type for display
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.title, p.content_type_id, ti.slug as content_type_slug
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            
            post_result = cursor.fetchone()
            post_title = None
            content_type_slug = None
            if post_result:
                if isinstance(post_result, dict):
                    post_title = post_result.get('title')
                    content_type_slug = post_result.get('content_type_slug')
                else:
                    post_title = post_result[0] if post_result else None
                    content_type_slug = post_result[2] if len(post_result) > 2 else None
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'post_type': post_type,
            'post_title': post_title,
            'content_type_slug': content_type_slug,
            'steps': steps
        })
        
    except Exception as e:
        logger.error(f"Error fetching pipeline for post {post_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

