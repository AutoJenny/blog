"""
Automation Core Module
Main blueprint that imports and orchestrates all automation modules
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Import execution functions
from blueprints.automation_execute import (
    execute_topic_allocation,
    execute_section_titling,
    execute_topic_brainstorming,
    execute_section_structure,
    execute_author_first_drafts,
    execute_image_concepts,
    execute_image_prompts,
    execute_image_captions
)

# Import other modules
from blueprints.automation_calendar import bp as calendar_bp
from blueprints.automation_pipeline import bp as pipeline_bp
from blueprints.automation_settings import bp as settings_bp

# Create main blueprint
bp = Blueprint('automation_core', __name__, url_prefix='/launchpad/one-click-blog/api')

# Register sub-blueprints
bp.register_blueprint(calendar_bp)
bp.register_blueprint(pipeline_bp)
bp.register_blueprint(settings_bp)

@bp.route('/execute-substage/<stage>/<substage>', methods=['POST'])
def execute_substage(stage, substage):
    """Main router for substage execution"""
    try:
        data = request.get_json() or {}
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({"success": False, "error": "Post ID is required"}), 400
        
        # Route to appropriate execution function
        if stage == 'planning':
            if substage == 'topic_brainstorming':
                result = execute_topic_brainstorming(post_id, data)
            elif substage == 'section_structure':
                result = execute_section_structure(post_id, data)
            elif substage == 'topic_allocation':
                result = execute_topic_allocation(post_id, data)
            elif substage == 'section_titling':
                result = execute_section_titling(post_id, data)
            else:
                return jsonify({"success": False, "error": f"Unknown planning substage: {substage}"}), 400
        elif stage == 'authoring':
            if substage == 'author_first_drafts':
                result = execute_author_first_drafts(post_id, data)
            elif substage == 'image_concepts':
                result = execute_image_concepts(post_id, data)
            elif substage == 'image_prompts':
                result = execute_image_prompts(post_id, data)
            elif substage == 'image_captions':
                result = execute_image_captions(post_id, data)
            else:
                return jsonify({"success": False, "error": f"Unknown authoring substage: {substage}"}), 400
        else:
            return jsonify({"success": False, "error": f"Unknown stage: {stage}"}), 400
        
        # Handle result (could be tuple or direct response)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error executing substage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/settings', methods=['GET'])
def get_settings():
    """Get automation settings"""
    try:
        # Return empty settings if table doesn't exist
        return jsonify({
            "success": True,
            "settings": {}
        })
            
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/settings', methods=['POST'])
def save_settings():
    """Save automation settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        with db_manager.get_cursor() as cursor:
            for key, value in data.items():
                cursor.execute("""
                    INSERT INTO automation_settings (setting_key, setting_value)
                    VALUES (%s, %s)
                    ON CONFLICT (setting_key) 
                    DO UPDATE SET 
                        setting_value = EXCLUDED.setting_value,
                        updated_at = NOW()
                """, (key, str(value)))
            
            return jsonify({
                "success": True,
                "message": "Settings saved successfully"
            })
            
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/pause-post/<int:post_id>', methods=['POST'])
def pause_post(post_id):
    """Pause automation for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post 
                SET status = 'paused', updated_at = NOW()
                WHERE id = %s
            """, (post_id,))
            
            return jsonify({
                "success": True,
                "message": "Post paused successfully"
            })
            
    except Exception as e:
        logger.error(f"Error pausing post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/resume-post/<int:post_id>', methods=['POST'])
def resume_post(post_id):
    """Resume automation for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post 
                SET status = 'in_progress', updated_at = NOW()
                WHERE id = %s
            """, (post_id,))
            
            return jsonify({
                "success": True,
                "message": "Post resumed successfully"
            })
            
    except Exception as e:
        logger.error(f"Error resuming post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/delete-post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE post 
                SET status = 'deleted', updated_at = NOW()
                WHERE id = %s
            """, (post_id,))
            
            return jsonify({
                "success": True,
                "message": "Post deleted successfully"
            })
            
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/create-post', methods=['POST'])
def create_post():
    """Create a new post"""
    try:
        data = request.get_json()
        title = data.get('title')
        idea_seed = data.get('idea_seed')
        
        if not title:
            return jsonify({"success": False, "error": "Title is required"}), 400
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO post (title, status, created_at, updated_at)
                VALUES (%s, 'draft', NOW(), NOW())
                RETURNING id
            """, (title,))
            
            post_id = cursor.fetchone()['id']
            
            # Create post_development entry
            cursor.execute("""
                INSERT INTO post_development (post_id, idea_seed, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """, (post_id, idea_seed or ''))
            
            return jsonify({
                "success": True,
                "post_id": post_id,
                "message": "Post created successfully"
            })
            
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
