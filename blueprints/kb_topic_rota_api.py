"""
KB Topic Rota API Blueprint

API endpoints for KB topic discovery, rota management, and content retrieval.
"""

from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from typing import Optional
import logging

from config.database import db_manager
from utils.kb_topic_discovery.clustering import KBTopicClusterer
from utils.kb_topic_discovery.similarity import TopicSimilarityCalculator
from utils.kb_topic_discovery.rota_generator import RotaGenerator
from utils.kb_topic_discovery.content_aggregator import TopicContentAggregator

logger = logging.getLogger(__name__)

bp = Blueprint('kb_topic_rota_api', __name__, url_prefix='/api/kb-topics')


@bp.route('/rota', methods=['GET'])
def get_rota():
    """
    Get weekly rota schedule.
    
    Query params:
        year: Year (default: current year)
        week: ISO week number (default: current week)
    
    Returns:
        JSON with topic and aggregated content for specified week
    """
    try:
        # Get year and week from query params
        year = request.args.get('year', type=int)
        week = request.args.get('week', type=int)
        
        # Default to current week if not specified
        if not year or not week:
            today = date.today()
            year, week, _ = today.isocalendar()
        
        # Get rota entry for week
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.id as rota_id,
                    r.topic_id,
                    r.scheduled_year,
                    r.scheduled_week,
                    r.scheduled_date,
                    r.diversity_score,
                    r.status,
                    r.content_summary,
                    r.source_article_ids,
                    t.topic_name,
                    t.topic_description,
                    t.topic_keywords,
                    t.topic_type,
                    t.article_ids,
                    t.category_ids
                FROM kb_topic_rota r
                JOIN kb_topics t ON r.topic_id = t.id
                WHERE r.scheduled_year = %s AND r.scheduled_week = %s
            """, (year, week))
            
            rota_entry = cursor.fetchone()
        
        if not rota_entry:
            return jsonify({
                'success': False,
                'message': f'No rota entry found for year {year}, week {week}',
                'year': year,
                'week': week
            }), 200  # Return 200 OK with success: false, not 404
        
        # Get aggregated content if available
        content = None
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT aggregated_text, source_article_ids, source_chunk_ids, word_count
                FROM kb_topic_content
                WHERE topic_id = %s AND rota_id = %s
            """, (rota_entry['topic_id'], rota_entry['rota_id']))
            
            content_data = cursor.fetchone()
            if content_data:
                content = dict(content_data)
        
        # Format response
        response = {
            'success': True,
            'topic': {
                'id': rota_entry['topic_id'],
                'name': rota_entry['topic_name'],
                'description': rota_entry['topic_description'],
                'keywords': rota_entry['topic_keywords'],
                'type': rota_entry['topic_type'],
                'article_ids': rota_entry['article_ids'],
                'category_ids': rota_entry['category_ids']
            },
            'content': content,
            'schedule': {
                'year': rota_entry['scheduled_year'],
                'week': rota_entry['scheduled_week'],
                'date': rota_entry['scheduled_date'].isoformat() if rota_entry['scheduled_date'] else None,
                'diversity_score': float(rota_entry['diversity_score']) if rota_entry['diversity_score'] else None,
                'status': rota_entry['status']
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting rota: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/<int:topic_id>/content', methods=['GET'])
def get_topic_content(topic_id: int):
    """
    Get aggregated content for a topic.
    
    Args:
        topic_id: Topic ID
    
    Returns:
        JSON with topic metadata and aggregated content
    """
    try:
        # Get topic
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, topic_name, topic_description, topic_keywords,
                       topic_type, article_ids, category_ids
                FROM kb_topics
                WHERE id = %s
            """, (topic_id,))
            
            topic = cursor.fetchone()
        
        if not topic:
            return jsonify({
                'success': False,
                'message': f'Topic {topic_id} not found'
            }), 404
        
        # Get aggregated content
        aggregator = TopicContentAggregator()
        content_data = aggregator.aggregate_content(topic_id, limit=5)
        
        if not content_data:
            return jsonify({
                'success': False,
                'message': f'No content aggregated for topic {topic_id}'
            }), 404
        
        response = {
            'success': True,
            'topic': {
                'id': topic['id'],
                'name': topic['topic_name'],
                'description': topic['topic_description'],
                'keywords': topic['topic_keywords'],
                'type': topic['topic_type'],
                'article_ids': topic['article_ids'],
                'category_ids': topic['category_ids']
            },
            'content': {
                'aggregated_text': content_data['aggregated_text'],
                'source_article_ids': content_data['source_article_ids'],
                'source_chunk_ids': content_data['source_chunk_ids'],
                'word_count': content_data['word_count']
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting topic content: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/discover', methods=['POST'])
def discover_topics():
    """
    Trigger topic discovery (clustering) process.
    
    Body (JSON):
        method: Clustering method ('kmeans', 'dbscan', 'hierarchical')
        n_clusters: Number of clusters (optional)
        min_cluster_size: Minimum cluster size (default: 3)
        similarity_threshold: Similarity threshold (default: 0.7)
        compute_similarity: Whether to compute similarity matrix (default: true)
    
    Returns:
        JSON with discovered topics
    """
    try:
        data = request.get_json() or {}
        
        method = data.get('method', 'kmeans')
        n_clusters = data.get('n_clusters')
        min_cluster_size = data.get('min_cluster_size', 3)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        compute_similarity = data.get('compute_similarity', True)
        
        # Discover topics
        clusterer = KBTopicClusterer()
        topics = clusterer.discover_topics(
            method=method,
            n_clusters=n_clusters,
            min_cluster_size=min_cluster_size,
            similarity_threshold=similarity_threshold
        )
        
        if not topics:
            return jsonify({
                'success': False,
                'message': 'No topics discovered'
            }), 400
        
        # Store topics in database
        from utils.kb_topic_discovery.storage import store_topics
        if not store_topics(topics):
            return jsonify({
                'success': False,
                'message': 'Failed to store topics'
            }), 500
        
        # Compute similarity matrix if requested
        if compute_similarity:
            similarity_calc = TopicSimilarityCalculator()
            similarities = similarity_calc.compute_similarity_matrix(topics)
        
        response = {
            'success': True,
            'topics_discovered': len(topics),
            'topics': [
                {
                    'id': topic.get('id'),
                    'name': topic['topic_name'],
                    'type': topic.get('topic_type', 'general'),
                    'article_count': topic.get('article_count', 0),
                    'keywords': topic.get('keywords', [])[:5]  # Top 5 keywords
                }
                for topic in topics
            ]
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error discovering topics: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/regenerate-rota', methods=['POST'])
def regenerate_rota():
    """
    Regenerate rota with diversity constraints.
    
    Body (JSON):
        start_date: Start date (YYYY-MM-DD, default: next Monday)
        weeks: Number of weeks to schedule (default: 52)
        lookback_weeks: Lookback window for diversity (default: 6)
        min_similarity_gap: Minimum similarity gap (default: 0.7)
    
    Returns:
        JSON with generated rota
    """
    try:
        data = request.get_json() or {}
        
        # Parse start date
        start_date_str = data.get('start_date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            # Default to next Monday
            today = date.today()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            start_date = today + timedelta(days=days_until_monday)
        
        weeks = data.get('weeks')
        lookback_weeks = data.get('lookback_weeks', 6)
        min_similarity_gap = data.get('min_similarity_gap', 0.7)
        include_all_topics = data.get('include_all_topics', True)
        
        logger.info(f"Generating rota: start_date={start_date}, weeks={weeks}, include_all_topics={include_all_topics}")
        
        # Generate rota
        rota_gen = RotaGenerator()
        rota = rota_gen.generate_rota(
            start_date=start_date,
            weeks=weeks,
            lookback_weeks=lookback_weeks,
            min_similarity_gap=min_similarity_gap,
            include_all_topics=include_all_topics
        )
        
        logger.info(f"Generated {len(rota)} rota entries")
        
        # Save rota
        if not rota_gen.save_rota(rota):
            return jsonify({
                'success': False,
                'message': 'Failed to save rota'
            }), 500
        
        response = {
            'success': True,
            'rota_entries': len(rota),
            'start_date': start_date.isoformat(),
            'weeks': len(rota) if weeks is None else weeks,
            'message': f'Generated {len(rota)} rota entries',
            'rota': [
                {
                    'topic_id': entry['topic_id'],
                    'year': entry['scheduled_year'],
                    'week': entry['scheduled_week'],
                    'date': entry['scheduled_date'].isoformat(),
                    'diversity_score': entry['diversity_score']
                }
                for entry in rota[:10]  # First 10 entries
            ]
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error regenerating rota: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/topics', methods=['GET'])
def list_topics():
    """
    List all topics.
    
    Query params:
        active_only: Only return active topics (default: true)
    
    Returns:
        JSON list of topics
    """
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        with db_manager.get_cursor() as cursor:
            if active_only:
                cursor.execute("""
                    SELECT id, topic_name, topic_description, topic_keywords,
                           topic_type, article_ids, category_ids, is_active,
                           discovered_at
                    FROM kb_topics
                    WHERE is_active = TRUE
                    ORDER BY priority DESC, discovered_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, topic_name, topic_description, topic_keywords,
                           topic_type, article_ids, category_ids, is_active,
                           discovered_at
                    FROM kb_topics
                    ORDER BY priority DESC, discovered_at DESC
                """)
            
            topics = cursor.fetchall()
        
        response = {
            'success': True,
            'count': len(topics),
            'topics': [
                {
                    'id': topic['id'],
                    'name': topic['topic_name'],
                    'description': topic['topic_description'],
                    'keywords': topic['topic_keywords'],
                    'type': topic['topic_type'],
                    'article_count': len(topic['article_ids']) if topic['article_ids'] else 0,
                    'category_count': len(topic['category_ids']) if topic['category_ids'] else 0,
                    'is_active': topic['is_active'],
                    'discovered_at': topic['discovered_at'].isoformat() if topic['discovered_at'] else None
                }
                for topic in topics
            ]
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error listing topics: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/rota-editor/data', methods=['GET'])
def get_rota_editor_data():
    """
    Get all data needed for rota editor UI.
    
    Returns:
        JSON with topics (hierarchical), current rota, and validation data
    """
    try:
        # Get all topics with hierarchy
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t1.id, t1.topic_name, t1.topic_description, t1.topic_type,
                    t1.level, t1.is_broad, t1.parent_id,
                    t1.is_excluded, t1.is_used, t1.used_at, t1.excluded_at,
                    array_length(t1.article_ids, 1) as article_count,
                    t2.topic_name as parent_name,
                    t2.id as parent_topic_id
                FROM kb_topics t1
                LEFT JOIN kb_topics t2 ON t1.parent_id = t2.id
                WHERE t1.is_active = TRUE
                ORDER BY COALESCE(t1.parent_id, t1.id), t1.level, t1.id
            """)
            topics = cursor.fetchall()
        
        # Get current rota
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    r.id as rota_id,
                    r.topic_id,
                    r.scheduled_year,
                    r.scheduled_week,
                    r.scheduled_date,
                    r.diversity_score,
                    r.status,
                    t.topic_name,
                    t.parent_id,
                    t.level
                FROM kb_topic_rota r
                JOIN kb_topics t ON r.topic_id = t.id
                ORDER BY r.scheduled_date, r.scheduled_week
            """)
            rota_entries = cursor.fetchall()
        
        # Get similarity matrix for validation
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT topic1_id, topic2_id, similarity_score
                FROM kb_topic_similarity
            """)
            similarities = cursor.fetchall()
        
        # Organize topics hierarchically
        topics_dict = {}
        
        for topic in topics:
            topic_id = topic['id']
            topic_data = {
                'id': topic_id,
                'name': topic['topic_name'],
                'description': topic.get('topic_description'),
                'type': topic['topic_type'],
                'level': topic['level'],
                'is_broad': topic['is_broad'],
                'article_count': topic['article_count'] or 0,
                'parent_id': topic.get('parent_id'),
                'parent_name': topic.get('parent_name'),
                'parent_topic_id': topic.get('parent_topic_id'),
                'is_excluded': topic.get('is_excluded', False),
                'is_used': topic.get('is_used', False),
                'used_at': topic.get('used_at').isoformat() if topic.get('used_at') else None,
                'excluded_at': topic.get('excluded_at').isoformat() if topic.get('excluded_at') else None
            }
            topics_dict[topic_id] = topic_data
        
        # Organize rota by week
        rota_by_week = {}
        for entry in rota_entries:
            week_key = f"{entry['scheduled_year']}_W{entry['scheduled_week']}"
            if week_key not in rota_by_week:
                rota_by_week[week_key] = []
            rota_by_week[week_key].append({
                'rota_id': entry['rota_id'],
                'topic_id': entry['topic_id'],
                'topic_name': entry['topic_name'],
                'year': entry['scheduled_year'],
                'week': entry['scheduled_week'],
                'date': entry['scheduled_date'].isoformat() if entry['scheduled_date'] else None,
                'diversity_score': float(entry['diversity_score']) if entry['diversity_score'] else None,
                'status': entry['status'],
                'parent_id': entry.get('parent_id'),
                'level': entry['level']
            })
        
        # Build similarity map
        similarity_map = {}
        for sim in similarities:
            t1 = sim['topic1_id']
            t2 = sim['topic2_id']
            score = float(sim['similarity_score'])
            similarity_map[f"{t1}_{t2}"] = score
            similarity_map[f"{t2}_{t1}"] = score
        
        return jsonify({
            'success': True,
            'topics': list(topics_dict.values()),
            'rota': rota_by_week,
            'similarity_map': similarity_map
        })
    
    except Exception as e:
        logger.error(f"Error getting rota editor data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/topic/<int:topic_id>/exclude', methods=['POST'])
def toggle_topic_exclusion(topic_id):
    """
    Toggle exclusion status of a topic.
    
    Body (JSON):
        exclude: boolean - True to exclude, False to include
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json() or {}
        exclude = data.get('exclude', True)
        
        from datetime import datetime
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE kb_topics
                SET is_excluded = %s,
                    excluded_at = CASE WHEN %s THEN %s ELSE NULL END,
                    last_updated = %s
                WHERE id = %s
                RETURNING id, topic_name, is_excluded
            """, (exclude, exclude, datetime.now(), datetime.now(), topic_id))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': f'Topic {topic_id} not found'
                }), 404
        
        action = 'excluded' if exclude else 'included'
        logger.info(f"Topic {topic_id} ({result['topic_name']}) {action}")
        
        return jsonify({
            'success': True,
            'message': f'Topic {action} successfully',
            'topic_id': topic_id,
            'is_excluded': exclude
        })
    
    except Exception as e:
        logger.error(f"Error toggling topic exclusion: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/topic/<int:topic_id>/mark-used', methods=['POST'])
def mark_topic_used(topic_id):
    """
    Mark a topic as used for content generation.
    
    Returns:
        JSON with success status
    """
    try:
        from datetime import datetime
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE kb_topics
                SET is_used = TRUE,
                    used_at = %s,
                    last_updated = %s
                WHERE id = %s
                RETURNING id, topic_name
            """, (datetime.now(), datetime.now(), topic_id))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': f'Topic {topic_id} not found'
                }), 404
        
        logger.info(f"Topic {topic_id} ({result['topic_name']}) marked as used")
        
        return jsonify({
            'success': True,
            'message': 'Topic marked as used',
            'topic_id': topic_id
        })
    
    except Exception as e:
        logger.error(f"Error marking topic as used: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/topics/reset-used', methods=['POST'])
def reset_used_topics():
    """
    Reset all topics' used status (when full cycle complete).
    
    Returns:
        JSON with success status and count reset
    """
    try:
        with db_manager.get_cursor() as cursor:
            # First count how many will be reset
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM kb_topics
                WHERE is_used = TRUE
            """)
            count_result = cursor.fetchone()
            count = count_result['count'] if count_result else 0
            
            # Then reset them
            cursor.execute("""
                UPDATE kb_topics
                SET is_used = FALSE,
                    used_at = NULL,
                    last_updated = CURRENT_TIMESTAMP
                WHERE is_used = TRUE
            """)
        
        logger.info(f"Reset {count} topics' used status")
        
        return jsonify({
            'success': True,
            'message': f'Reset {count} topics',
            'count': count
        })
    
    except Exception as e:
        logger.error(f"Error resetting used topics: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/rota-editor/save', methods=['POST'])
def save_rota_editor():
    """
    Save rota arrangement from editor.
    
    Body (JSON):
        rota: Array of {topic_id, year, week, date} objects
        validate: Whether to validate placements (default: true)
    
    Returns:
        JSON with success status and validation warnings
    """
    try:
        data = request.get_json() or {}
        rota_entries = data.get('rota', [])
        validate = data.get('validate', True)
        
        warnings = []
        
        # Validate if requested
        if validate and rota_entries:
            # Get similarity map
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT topic1_id, topic2_id, similarity_score
                    FROM kb_topic_similarity
                """)
                similarities = cursor.fetchall()
            
            similarity_map = {}
            for sim in similarities:
                t1 = sim['topic1_id']
                t2 = sim['topic2_id']
                score = float(sim['similarity_score'])
                similarity_map[f"{t1}_{t2}"] = score
                similarity_map[f"{t2}_{t1}"] = score
            
            # Get topic parent info
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, parent_id, topic_name
                    FROM kb_topics
                    WHERE is_active = TRUE
                """)
                topics = {t['id']: t for t in cursor.fetchall()}
            
            # Check for issues
            for i, entry in enumerate(rota_entries):
                topic_id = entry['topic_id']
                week = entry['week']
                year = entry['year']
                
                # Check adjacent weeks for same parent
                for j, other_entry in enumerate(rota_entries):
                    if i == j:
                        continue
                    if other_entry['year'] != year:
                        continue
                    other_week = other_entry['week']
                    other_topic_id = other_entry['topic_id']
                    
                    # Same parent in consecutive weeks
                    if abs(week - other_week) == 1:
                        topic = topics.get(topic_id)
                        other_topic = topics.get(other_topic_id)
                        if topic and other_topic:
                            topic_parent = topic.get('parent_id') or topic_id
                            other_parent = other_topic.get('parent_id') or other_topic_id
                            if topic_parent == other_parent:
                                warnings.append({
                                    'type': 'same_parent_consecutive',
                                    'week1': week,
                                    'week2': other_week,
                                    'topic1': topic['topic_name'],
                                    'topic2': other_topic['topic_name'],
                                    'message': f'Same parent group in weeks {week} and {other_week}'
                                })
                    
                    # Similar topics within 6 weeks
                    if abs(week - other_week) <= 6:
                        sim_key = f"{topic_id}_{other_topic_id}"
                        similarity = similarity_map.get(sim_key, 0)
                        if similarity > 0.7:
                            warnings.append({
                                'type': 'similar_topics_close',
                                'week1': week,
                                'week2': other_week,
                                'similarity': similarity,
                                'topic1': topics.get(topic_id, {}).get('topic_name', 'Unknown'),
                                'topic2': topics.get(other_topic_id, {}).get('topic_name', 'Unknown'),
                                'message': f'Similar topics in weeks {week} and {other_week} (similarity: {similarity:.2f})'
                            })
        
        # Save to database
        with db_manager.get_cursor() as cursor:
            # Clear existing rota
            cursor.execute("DELETE FROM kb_topic_rota")
            
            # Insert new rota entries
            for entry in rota_entries:
                scheduled_date = datetime.strptime(entry['date'], '%Y-%m-%d').date() if entry.get('date') else None
                
                cursor.execute("""
                    INSERT INTO kb_topic_rota
                        (topic_id, scheduled_year, scheduled_week, scheduled_date,
                         diversity_score, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (scheduled_year, scheduled_week)
                    DO UPDATE SET
                        topic_id = EXCLUDED.topic_id,
                        scheduled_date = EXCLUDED.scheduled_date,
                        diversity_score = EXCLUDED.diversity_score,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    entry['topic_id'],
                    entry['year'],
                    entry['week'],
                    scheduled_date,
                    entry.get('diversity_score'),
                    entry.get('status', 'scheduled')
                ))
        
        return jsonify({
            'success': True,
            'warnings': warnings,
            'message': f'Saved {len(rota_entries)} rota entries'
        })
    
    except Exception as e:
        logger.error(f"Error saving rota: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
