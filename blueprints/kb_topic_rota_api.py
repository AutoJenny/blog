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
            }), 404
        
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
        
        weeks = data.get('weeks', 52)
        lookback_weeks = data.get('lookback_weeks', 6)
        min_similarity_gap = data.get('min_similarity_gap', 0.7)
        
        # Generate rota
        rota_gen = RotaGenerator()
        rota = rota_gen.generate_rota(
            start_date=start_date,
            weeks=weeks,
            lookback_weeks=lookback_weeks,
            min_similarity_gap=min_similarity_gap
        )
        
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
            'weeks': weeks,
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
