"""
Pipeline Status and Data API Endpoints
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta, date
from config.database import db_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('automation_pipeline', __name__)

@bp.route('/pipeline-status/<int:post_id>', methods=['GET'])
def get_pipeline_status(post_id):
    """Get current pipeline state for a post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post basic info with timestamps
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.updated_at,
                       pd.sections, pd.topic_allocation, pd.section_structure,
                       pd.idea_scope, pd.structure_design_at, pd.allocation_completed_at,
                       pd.refinement_completed_at, pd.updated_at as sections_updated_at,
                       pd.updated_at as authoring_updated_at,
                       pd.updated_at as image_concepts_updated_at
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
            # Get section completion status
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted,
                       SUM(CASE WHEN image_concepts IS NOT NULL AND image_concepts != '' THEN 1 ELSE 0 END) as image_concepts_count
                FROM post_section
                WHERE post_id = %s
            """, (post_id,))
            
            section_stats = cursor.fetchone()
            
            # Calculate stage statuses
            planning_complete = bool(post['topic_allocation'] and post['section_structure'])
            authoring_progress = 0
            if section_stats and section_stats['total'] > 0:
                authoring_progress = int((section_stats['drafted'] / section_stats['total']) * 100)
            
            # Determine overall progress
            overall_progress = 0
            if planning_complete:
                overall_progress += 40
            overall_progress += int(authoring_progress * 0.6)
            
            # Extract topic brainstorming timestamp from idea_scope
            topic_brainstorming_at = None
            if post['idea_scope']:
                try:
                    idea_scope_data = json.loads(post['idea_scope']) if isinstance(post['idea_scope'], str) else post['idea_scope']
                    if isinstance(idea_scope_data, dict) and 'generated_at' in idea_scope_data:
                        topic_brainstorming_at = datetime.fromisoformat(idea_scope_data['generated_at'])
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
            
            # Build response
            response_data = {
                "success": True,
                "data": {
                    "post_id": post_id,
                    "title": post['title'],
                    "status": post['status'],
                    "overall_progress": overall_progress,
                    "stages": {
                        "planning": {
                            "status": "complete" if planning_complete else "pending",
                            "progress": 100 if planning_complete else 0,
                            "substages": {
                                "topic_brainstorming": {
                                    "status": "complete" if post['idea_scope'] else "pending",
                                    "completed_at": topic_brainstorming_at.isoformat() if topic_brainstorming_at else None
                                },
                                "section_structure": {
                                    "status": "complete" if post['section_structure'] else "pending",
                                    "completed_at": post['structure_design_at'].isoformat() if post['structure_design_at'] else None
                                },
                                "topic_allocation": {
                                    "status": "complete" if post['topic_allocation'] else "pending",
                                    "completed_at": post['allocation_completed_at'].isoformat() if post['allocation_completed_at'] else None
                                },
                                "section_titling": {
                                    "status": "complete" if post['sections'] else "pending",
                                    "completed_at": post['sections_updated_at'].isoformat() if post['sections_updated_at'] else None
                                }
                            }
                        },
                        "authoring": {
                            "status": "complete" if authoring_progress == 100 else ("in_progress" if authoring_progress > 0 else "pending"),
                            "progress": authoring_progress,
                            "substages": {
                                "author_first_drafts": {
                                    "status": "complete" if authoring_progress == 100 else ("in_progress" if authoring_progress > 0 else "pending"),
                                    "completed_at": post['authoring_updated_at'].isoformat() if post['authoring_updated_at'] else None
                                },
                                "image_concepts": {
                                    "status": "complete" if section_stats['image_concepts_count'] == section_stats['total'] else ("in_progress" if section_stats['image_concepts_count'] > 0 else "pending"),
                                    "completed_at": post['image_concepts_updated_at'].isoformat() if post['image_concepts_updated_at'] else None
                                }
                            }
                        }
                    }
                }
            }
            
            return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/posts-in-development', methods=['GET'])
def get_posts_in_development():
    """Get list of posts in development"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.expanded_idea, pd.idea_seed, pd.sections,
                       pd.topic_allocation, pd.section_structure, pd.idea_scope
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status IN ('draft', 'in_process')
                ORDER BY p.updated_at DESC
            """)
            
            posts = cursor.fetchall()
            
            # Calculate progress for each post
            posts_with_progress = []
            for post in posts:
                # Count completed sections
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted
                    FROM post_section
                    WHERE post_id = %s
                """, (post['id'],))
                
                section_stats = cursor.fetchone()
                
                # Calculate progress
                planning_complete = bool(post['topic_allocation'] and post['section_structure'])
                authoring_progress = 0
                if section_stats and section_stats['total'] > 0:
                    authoring_progress = int((section_stats['drafted'] / section_stats['total']) * 100)
                
                overall_progress = 0
                if planning_complete:
                    overall_progress += 40
                overall_progress += int(authoring_progress * 0.6)
                
                posts_with_progress.append({
                    "id": post['id'],
                    "title": post['title'],
                    "status": post['status'],
                    "created_at": post['created_at'].isoformat() if post['created_at'] else None,
                    "updated_at": post['updated_at'].isoformat() if post['updated_at'] else None,
                    "expanded_idea": post['expanded_idea'],
                    "idea_seed": post['idea_seed'],
                    "progress": overall_progress,
                    "planning_complete": planning_complete,
                    "authoring_progress": authoring_progress
                })
            
            return jsonify({
                "success": True,
                "data": posts_with_progress
            })
            
    except Exception as e:
        logger.error(f"Error getting posts in development: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get overdue posts
            cursor.execute("""
                SELECT p.id, p.title, cs.scheduled_date, cs.scheduled_time
                FROM post p
                JOIN post_development pd ON p.id = pd.post_id
                JOIN calendar_schedule cs ON cs.post_id = p.id
                WHERE p.status != 'published' 
                AND cs.scheduled_date < CURRENT_DATE
                AND cs.status = 'planned'
                ORDER BY cs.scheduled_date ASC
            """)
            
            overdue_posts = cursor.fetchall()
            
            # Get posts with automation errors
            cursor.execute("""
                SELECT p.id, p.title, pd.automation_error, pd.automation_error_at
                FROM post p
                JOIN post_development pd ON p.id = pd.post_id
                WHERE pd.automation_error IS NOT NULL
                ORDER BY pd.automation_error_at DESC
            """)
            
            error_posts = cursor.fetchall()
            
            alerts = []
            
            # Add overdue alerts
            for post in overdue_posts:
                alerts.append({
                    "id": f"overdue_{post['id']}",
                    "type": "overdue",
                    "title": "Overdue Post",
                    "message": f"Post '{post['title']}' was scheduled for {post['scheduled_date']} but is not published",
                    "post_id": post['id'],
                    "created_at": post['scheduled_date'].isoformat(),
                    "severity": "high"
                })
            
            # Add error alerts
            for post in error_posts:
                alerts.append({
                    "id": f"error_{post['id']}",
                    "type": "error",
                    "title": "Automation Error",
                    "message": f"Post '{post['title']}' has automation error: {post['automation_error']}",
                    "post_id": post['id'],
                    "created_at": post['automation_error_at'].isoformat() if post['automation_error_at'] else None,
                    "severity": "medium"
                })
            
            return jsonify({
                "success": True,
                "data": alerts
            })
            
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/alert/dismiss/<int:alert_id>', methods=['POST'])
def dismiss_alert():
    """Dismiss an alert"""
    try:
        # For now, just return success - in a real implementation,
        # you might want to store dismissed alerts in a database
        return jsonify({
            "success": True,
            "message": "Alert dismissed"
        })
        
    except Exception as e:
        logger.error(f"Error dismissing alert: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/analytics/<int:post_id>', methods=['GET'])
def get_post_analytics(post_id):
    """Get analytics for a published post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post basic info
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.published_at, p.created_at
                FROM post p
                WHERE p.id = %s AND p.status = 'published'
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return jsonify({"success": False, "error": "Published post not found"}), 404
            
            # Mock analytics data - in a real implementation, you'd query actual analytics
            analytics_data = {
                "post_id": post_id,
                "title": post['title'],
                "published_at": post['published_at'].isoformat() if post['published_at'] else None,
                "views": 0,  # Would come from analytics service
                "clicks": 0,  # Would come from analytics service
                "engagement": 0,  # Would come from analytics service
                "social_shares": 0,  # Would come from analytics service
                "conversion_rate": 0.0  # Would come from analytics service
            }
            
            return jsonify({
                "success": True,
                "data": analytics_data
            })
            
    except Exception as e:
        logger.error(f"Error getting post analytics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
