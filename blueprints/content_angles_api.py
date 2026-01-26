"""
Content Angles API

Phase 3: API endpoints for angle proposal, creation, and retrieval.
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from config.database import db_manager
from utils.content_angles.angle_proposer import AngleProposer

bp = Blueprint('content_angles_api', __name__, url_prefix='/api/content-angles')
logger = logging.getLogger(__name__)


@bp.route('/propose', methods=['POST'])
def propose_angles():
    """
    Propose angle candidates for a topic (read-only, no persistence).
    
    Body:
        topic_id: KB topic ID (required)
        num_candidates: Number of candidates (optional, default: 5)
        context: Optional context (rota_year, rota_week)
    
    Returns:
        JSON with angle candidates
    """
    try:
        data = request.get_json() or {}
        
        topic_id = data.get('topic_id')
        if not topic_id:
            return jsonify({
                'success': False,
                'error': 'topic_id is required',
                'error_code': 'VALIDATION_FAILED'
            }), 400
        
        num_candidates = data.get('num_candidates', 5)
        if not isinstance(num_candidates, int) or num_candidates < 1 or num_candidates > 10:
            num_candidates = 5
        
        # Propose angles
        proposer = AngleProposer()
        result = proposer.propose_angles(topic_id, num_candidates)
        
        if not result.get('success'):
            error_code = result.get('error_code', 'GENERATION_FAILED')
            status_code = 404 if error_code == 'TOPIC_NOT_FOUND' else 500
            return jsonify(result), status_code
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error proposing angles: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Angle proposal failed: {str(e)}',
            'error_code': 'GENERATION_FAILED'
        }), 500


@bp.route('/angle', methods=['POST'])
def create_or_update_angle():
    """
    Create or update an angle.
    
    Body:
        angle_id: null for create, integer for update
        angle_name: Required
        narrative_intent: Required
        topic_id: Required
        source_article_ids: Required (array)
        source_chunk_ids: Optional (array)
        notes: Optional
        recommended_roles: Optional (array)
        suggested_channels: Optional (array)
    
    Returns:
        JSON with created/updated angle
    """
    try:
        data = request.get_json() or {}
        
        angle_id = data.get('angle_id')
        angle_name = data.get('angle_name', '').strip()
        narrative_intent = data.get('narrative_intent', '').strip()
        topic_id = data.get('topic_id')
        source_article_ids = data.get('source_article_ids', [])
        
        # Validation
        if not angle_name:
            return jsonify({
                'success': False,
                'error': 'angle_name is required',
                'error_code': 'VALIDATION_FAILED'
            }), 400
        
        if not narrative_intent:
            return jsonify({
                'success': False,
                'error': 'narrative_intent is required',
                'error_code': 'VALIDATION_FAILED'
            }), 400
        
        if not topic_id:
            return jsonify({
                'success': False,
                'error': 'topic_id is required',
                'error_code': 'VALIDATION_FAILED'
            }), 400
        
        if not source_article_ids or not isinstance(source_article_ids, list):
            return jsonify({
                'success': False,
                'error': 'source_article_ids must be a non-empty array',
                'error_code': 'VALIDATION_FAILED'
            }), 400
        
        # Validate topic exists
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT id FROM kb_topics WHERE id = %s", (topic_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Topic not found',
                    'error_code': 'TOPIC_NOT_FOUND'
                }), 404
            
            # Validate source articles exist (optional check)
            if source_article_ids:
                cursor.execute("""
                    SELECT id FROM clan_kb_articles 
                    WHERE id = ANY(%s) AND is_active = TRUE
                """, (source_article_ids,))
                found_ids = [row['id'] for row in cursor.fetchall()]
                if len(found_ids) != len(source_article_ids):
                    # Warn but don't fail (flexibility for cross-topic angles)
                    logger.warning(f"Some source article IDs not found: {source_article_ids}")
        
        # Optional fields
        source_chunk_ids = data.get('source_chunk_ids')
        notes = data.get('notes', '').strip()
        recommended_roles = data.get('recommended_roles', [])
        suggested_channels = data.get('suggested_channels', [])
        
        with db_manager.get_cursor() as cursor:
            if angle_id:
                # Update existing angle
                cursor.execute("""
                    SELECT id FROM content_angles WHERE id = %s
                """, (angle_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'error': 'Angle not found',
                        'error_code': 'ANGLE_NOT_FOUND'
                    }), 404
                
                cursor.execute("""
                    UPDATE content_angles
                    SET angle_name = %s,
                        angle_description = %s,
                        narrative_intent = %s,
                        topic_id = %s,
                        source_article_ids = %s,
                        source_chunk_ids = %s,
                        notes = %s,
                        recommended_roles = %s,
                        suggested_channels = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, angle_name, narrative_intent, topic_id,
                              source_article_ids, is_active, created_at, updated_at,
                              usage_count
                """, (
                    angle_name,
                    data.get('angle_description', '').strip() or None,
                    narrative_intent,
                    topic_id,
                    source_article_ids,
                    source_chunk_ids,
                    notes or None,
                    recommended_roles,
                    suggested_channels,
                    angle_id
                ))
                
                angle = cursor.fetchone()
                
                return jsonify({
                    'success': True,
                    'angle': dict(angle)
                })
            else:
                # Create new angle
                cursor.execute("""
                    INSERT INTO content_angles
                        (angle_name, angle_description, narrative_intent, topic_id,
                         source_article_ids, source_chunk_ids, notes,
                         recommended_roles, suggested_channels)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, angle_name, narrative_intent, topic_id,
                              source_article_ids, is_active, created_at, updated_at,
                              usage_count
                """, (
                    angle_name,
                    data.get('angle_description', '').strip() or None,
                    narrative_intent,
                    topic_id,
                    source_article_ids,
                    source_chunk_ids,
                    notes or None,
                    recommended_roles,
                    suggested_channels
                ))
                
                angle = cursor.fetchone()
                
                return jsonify({
                    'success': True,
                    'angle': dict(angle)
                }), 201
    
    except Exception as e:
        logger.error(f"Error creating/updating angle: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to create/update angle: {str(e)}',
            'error_code': 'GENERATION_FAILED'
        }), 500


@bp.route('/angle/<int:angle_id>', methods=['GET'])
def get_angle(angle_id):
    """
    Get angle by ID.
    
    Returns:
        JSON with angle details
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT a.id, a.angle_name, a.angle_description, a.narrative_intent,
                       a.topic_id, t.topic_name, a.source_article_ids, a.source_chunk_ids,
                       a.is_active, a.usage_count, a.last_used_at, a.last_used_year,
                       a.last_used_week, a.created_at, a.updated_at, a.notes
                FROM content_angles a
                LEFT JOIN kb_topics t ON a.topic_id = t.id
                WHERE a.id = %s
            """, (angle_id,))
            
            angle = cursor.fetchone()
            
            if not angle:
                return jsonify({
                    'success': False,
                    'error': 'Angle not found',
                    'error_code': 'ANGLE_NOT_FOUND'
                }), 404
            
            return jsonify({
                'success': True,
                'angle': dict(angle)
            })
    
    except Exception as e:
        logger.error(f"Error getting angle {angle_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get angle: {str(e)}',
            'error_code': 'GENERATION_FAILED'
        }), 500


@bp.route('/topic/<int:topic_id>', methods=['GET'])
def get_angles_by_topic(topic_id):
    """
    Get all angles for a topic.
    
    Query params:
        include_inactive: boolean (default: false)
    
    Returns:
        JSON with list of angles
    """
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        with db_manager.get_cursor() as cursor:
            # Verify topic exists
            cursor.execute("SELECT id, topic_name FROM kb_topics WHERE id = %s", (topic_id,))
            topic = cursor.fetchone()
            
            if not topic:
                return jsonify({
                    'success': False,
                    'error': 'Topic not found',
                    'error_code': 'TOPIC_NOT_FOUND'
                }), 404
            
            # Get angles
            if include_inactive:
                cursor.execute("""
                    SELECT id, angle_name, narrative_intent, is_active,
                           usage_count, last_used_at, last_used_year, last_used_week
                    FROM content_angles
                    WHERE topic_id = %s
                    ORDER BY created_at DESC
                """, (topic_id,))
            else:
                cursor.execute("""
                    SELECT id, angle_name, narrative_intent, is_active,
                           usage_count, last_used_at, last_used_year, last_used_week
                    FROM content_angles
                    WHERE topic_id = %s AND is_active = TRUE
                    ORDER BY created_at DESC
                """, (topic_id,))
            
            angles = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'topic_id': topic_id,
                'topic_name': topic['topic_name'],
                'angles': [dict(angle) for angle in angles]
            })
    
    except Exception as e:
        logger.error(f"Error getting angles for topic {topic_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get angles: {str(e)}',
            'error_code': 'GENERATION_FAILED'
        }), 500


@bp.route('/usage', methods=['GET'])
def get_angles_by_usage():
    """
    Get angles filtered by usage history.
    
    Query params:
        year: Filter by last_used_year
        week: Filter by last_used_week
        min_usage_count: Minimum usage count
        topic_id: Filter by topic
    
    Returns:
        JSON with filtered angles
    """
    try:
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        min_usage_count = request.args.get('min_usage_count', type=int)
        topic_id = request.args.get('topic_id', type=int)
        
        with db_manager.get_cursor() as cursor:
            query = """
                SELECT a.id, a.angle_name, a.topic_id, t.topic_name,
                       a.usage_count, a.last_used_year, a.last_used_week
                FROM content_angles a
                LEFT JOIN kb_topics t ON a.topic_id = t.id
                WHERE a.is_active = TRUE
            """
            params = []
            
            if year:
                query += " AND a.last_used_year = %s"
                params.append(year)
            
            if week:
                query += " AND a.last_used_week = %s"
                params.append(week)
            
            if min_usage_count is not None:
                query += " AND a.usage_count >= %s"
                params.append(min_usage_count)
            
            if topic_id:
                query += " AND a.topic_id = %s"
                params.append(topic_id)
            
            query += " ORDER BY a.last_used_year DESC, a.last_used_week DESC, a.usage_count DESC"
            
            cursor.execute(query, params)
            angles = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'filters': {
                    'year': year,
                    'week': week,
                    'min_usage_count': min_usage_count,
                    'topic_id': topic_id
                },
                'angles': [dict(angle) for angle in angles]
            })
    
    except Exception as e:
        logger.error(f"Error getting angles by usage: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get angles: {str(e)}',
            'error_code': 'GENERATION_FAILED'
        }), 500
