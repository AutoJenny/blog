"""
Content Roles API

Phase 2: API endpoints for Facebook Sunday DEPTH_LONG posts.

This is a proof of concept implementation - isolated from existing posting logic.
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, date, timedelta
from typing import Optional
import pytz
import json
from config.database import db_manager
from utils.content_roles.depth_long_generator import DepthLongGenerator
from utils.content_roles.validator import ContentRoleValidator
from config.content_roles_schedule_rails import get_rails_for_platform, has_depths_long_rail_for_week

bp = Blueprint('content_roles_api', __name__, url_prefix='/api/content-roles')
logger = logging.getLogger(__name__)


@bp.route('/facebook/sunday/check', methods=['GET'])
def check_sunday_rail():
    """
    Phase 2.1: Check if there's a DEPTH_LONG rail for a given week.
    
    Answers: "Is there a DEPTH_LONG Facebook post for this coming Sunday?"
    
    Query params:
        year: ISO year (optional, defaults to current)
        week: ISO week number (optional, defaults to current)
    
    Returns:
        JSON with rail existence and details
    """
    try:
        # Get year/week from query params or use current
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        if not year or not week:
            # Get current ISO week
            today = date.today()
            year, week, _ = today.isocalendar()
        
        # Check if rail exists
        has_rail = has_depths_long_rail_for_week('facebook', year, week)
        
        rails = get_rails_for_platform('facebook', role='DEPTH_LONG')
        
        return jsonify({
            'success': True,
            'has_rail': has_rail,
            'year': year,
            'week': week,
            'rail': rails[0] if rails else None
        })
    
    except Exception as e:
        logger.error(f"Error checking Sunday rail: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/facebook/sunday/generate', methods=['POST'])
def generate_sunday_depth_long():
    """
    Phase 2.3/3.5: Generate a Sunday DEPTH_LONG post.
    
    Phase 3.5: Now supports optional angle_id for angle-aware generation.
    
    Body:
        topic_id: KB topic ID (required)
        source_page_id: KB article ID (optional if angle_id provided)
        angle_id: Angle ID (optional, Phase 3)
        rota_year: Year of rota week (required)
        rota_week: ISO week number (required)
    
    Returns:
        JSON with generated content and validation results
    """
    try:
        data = request.get_json()
        
        # Phase 2.2: Enforce topic requirement
        topic_id = data.get('topic_id')
        source_page_id = data.get('source_page_id')
        angle_id = data.get('angle_id')  # Phase 3.5: Optional
        rota_year = data.get('rota_year')
        rota_week = data.get('rota_week')
        
        if not topic_id:
            return jsonify({
                'success': False,
                'error': 'topic_id is required for DEPTH_LONG posts'
            }), 400
        
        # Phase 3.5: source_page_id is optional if angle_id provided
        if not angle_id and not source_page_id:
            return jsonify({
                'success': False,
                'error': 'Either source_page_id or angle_id is required'
            }), 400
        
        if not rota_year or not rota_week:
            return jsonify({
                'success': False,
                'error': 'rota_year and rota_week are required'
            }), 400
        
        # Generate content (Phase 3.5: with optional angle_id)
        generator = DepthLongGenerator()
        result = generator.generate(
            topic_id, 
            source_page_id, 
            rota_year, 
            rota_week,
            angle_id=angle_id  # Phase 3.5: Pass angle_id
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        # Phase 2.4: Validate
        validator = ContentRoleValidator()
        validation = validator.validate_depth_long(result['content'], source_page_id)
        
        # Phase 3.5: Update angle usage tracking if angle was used
        if angle_id and result.get('angle_id'):
            _update_angle_usage(angle_id, rota_year, rota_week)
        
        # Store in posting_queue with status='generated'
        post_id = None
        if result['success']:
            post_id = _store_generated_post(
                role='DEPTH_LONG',
                platform='facebook',
                content=result['content'],
                topic_id=topic_id,
                source_page_id=source_page_id,
                rota_year=rota_year,
                rota_week=rota_week,
                validation_report=validation['validation_report_json'],
                angle_id=angle_id  # Phase 3.5: Store angle reference
            )
        
        response = {
            'success': True,
            'post_id': post_id,
            'content': result['content'],
            'word_count': result['word_count'],
            'validation': validation,
            'topic_id': topic_id,
            'source_page_id': source_page_id
        }
        
        # Phase 3.5: Include angle_id in response if used
        if angle_id:
            response['angle_id'] = angle_id
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error generating Sunday DEPTH_LONG: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/facebook/sunday/<int:post_id>/validate', methods=['POST'])
def validate_post(post_id: int):
    """
    Phase 2.4: Re-validate an existing post.
    
    Returns:
        Updated validation results
    """
    try:
        # Get post from database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, role, generated_content, source_page_id, validation_report_json
                FROM posting_queue
                WHERE id = %s AND role = 'DEPTH_LONG'
            """, (post_id,))
            
            post = cursor.fetchone()
        
        if not post:
            return jsonify({
                'success': False,
                'error': f'Post {post_id} not found or not DEPTH_LONG'
            }), 404
        
        # Validate
        validator = ContentRoleValidator()
        validation = validator.validate_depth_long(
            post['generated_content'] or '',
            post['source_page_id']
        )
        
        # Update validation report in database
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE posting_queue
                SET validation_report_json = %s,
                    status = CASE 
                        WHEN %s THEN 'validated_pass'
                        ELSE 'validated_fail'
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                json.dumps(validation['validation_report_json']),
                validation['valid'],
                post_id
            ))
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'validation': validation,
            'post_id': post_id
        })
    
    except Exception as e:
        logger.error(f"Error validating post {post_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/facebook/sunday/<int:post_id>/approve', methods=['POST'])
def approve_post(post_id: int):
    """
    Phase 2.5: Manually approve a post for scheduling.
    
    Body:
        approved_by: User identifier (optional)
    
    Returns:
        Approval status
    """
    try:
        data = request.get_json() or {}
        approved_by = data.get('approved_by', 'system')
        
        # Get post and check it's validated
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, status, validation_report_json
                FROM posting_queue
                WHERE id = %s AND role = 'DEPTH_LONG'
            """, (post_id,))
            
            post = cursor.fetchone()
        
        if not post:
            return jsonify({
                'success': False,
                'error': f'Post {post_id} not found or not DEPTH_LONG'
            }), 404
        
        # Check validation status
        validation_report = post['validation_report_json']
        if isinstance(validation_report, str):
            validation_report = json.loads(validation_report)
        
        if not validation_report or not validation_report.get('valid', False):
            return jsonify({
                'success': False,
                'error': 'Post must pass validation before approval',
                'validation': validation_report
            }), 400
        
        # Approve
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE posting_queue
                SET status = 'approved',
                    approved_at = CURRENT_TIMESTAMP,
                    approved_by = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (approved_by, post_id))
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'status': 'approved',
            'approved_at': datetime.now().isoformat(),
            'approved_by': approved_by
        })
    
    except Exception as e:
        logger.error(f"Error approving post {post_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/facebook/sunday/<int:post_id>/schedule', methods=['POST'])
def schedule_post(post_id: int):
    """
    Phase 2.5: Schedule an approved post for Sunday 15:00 UK.
    
    This is a parallel lane - does not use existing scheduler.
    
    Returns:
        Scheduled post details
    """
    try:
        # Get post and check it's approved
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, status, rota_year, rota_week
                FROM posting_queue
                WHERE id = %s AND role = 'DEPTH_LONG'
            """, (post_id,))
            
            post = cursor.fetchone()
        
        if not post:
            return jsonify({
                'success': False,
                'error': f'Post {post_id} not found or not DEPTH_LONG'
            }), 404
        
        if post['status'] != 'approved':
            return jsonify({
                'success': False,
                'error': f'Post must be approved before scheduling (current status: {post["status"]})'
            }), 400
        
        # Calculate Sunday date for the rota week
        rota_year = post['rota_year']
        rota_week = post['rota_week']
        
        # Get first day of ISO week (Monday)
        jan4 = date(rota_year, 1, 4)
        week_start = jan4 - timedelta(days=jan4.weekday())
        week_start = week_start + timedelta(weeks=rota_week - 1)
        
        # Sunday is 6 days after Monday
        sunday_date = week_start + timedelta(days=6)
        
        # Schedule time: 15:00 UK (Europe/London)
        uk_tz = pytz.timezone('Europe/London')
        scheduled_datetime = uk_tz.localize(
            datetime.combine(sunday_date, datetime.strptime('15:00', '%H:%M').time())
        )
        
        # Convert to UTC for storage
        scheduled_utc = scheduled_datetime.astimezone(pytz.UTC)
        
        # Update post with schedule
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE posting_queue
                SET status = 'scheduled',
                    scheduled_date = %s,
                    scheduled_time = %s,
                    scheduled_timestamp = %s,
                    timezone = 'Europe/London',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                sunday_date,
                scheduled_datetime.time(),
                scheduled_utc,
                post_id
            ))
            cursor.connection.commit()
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'status': 'scheduled',
            'scheduled_date': sunday_date.isoformat(),
            'scheduled_time': '15:00',
            'scheduled_timestamp_utc': scheduled_utc.isoformat(),
            'timezone': 'Europe/London'
        })
    
    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _store_generated_post(role: str, platform: str, content: str,
                          topic_id: int, source_page_id: int,
                          rota_year: int, rota_week: int,
                          validation_report: dict, angle_id: Optional[int] = None) -> int:
    """
    Store generated post in posting_queue.
    
    Returns:
        Post ID
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO posting_queue (
                role, platform, channel_type, content_type,
                generated_content, topic_id, source_page_id,
                rota_year, rota_week, validation_report_json,
                angle_id, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        """, (
            role,
            platform,
            'feed_post',  # Facebook feed post
            'depth_long',  # New content type for DEPTH_LONG
            content,
            topic_id,
            source_page_id,
            rota_year,
            rota_week,
            json.dumps(validation_report),
            angle_id,  # Phase 3.5: Optional angle reference
            'generated'  # Status: generated (needs validation/approval)
        ))
        
        post_id = cursor.fetchone()['id']
        cursor.connection.commit()
        
        return post_id
