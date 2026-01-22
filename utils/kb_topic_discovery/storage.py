"""
Topic Storage Utilities

Utilities for storing discovered topics in database.
"""

import logging
from datetime import datetime
from typing import List, Dict
from config.database import db_manager

logger = logging.getLogger(__name__)


def store_topics(topics: List[Dict]) -> bool:
    """
    Store discovered topics in database.
    
    Args:
        topics: List of topic dictionaries with:
            - topic_name
            - topic_description (optional)
            - keywords
            - cluster_id (optional)
            - centroid_embedding
            - article_ids
            - category_ids
            - topic_type
    
    Returns:
        True if successful
    """
    logger.info(f"Storing {len(topics)} topics in database")
    
    try:
        with db_manager.get_cursor() as cursor:
            for topic in topics:
                # Convert embedding to PostgreSQL array format
                embedding_array = topic['centroid_embedding']
                
                cursor.execute("""
                    INSERT INTO kb_topics
                        (topic_name, topic_description, topic_keywords, cluster_id,
                         embedding_vector, article_ids, category_ids, topic_type,
                         priority, is_active, discovered_at, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    topic['topic_name'],
                    topic.get('topic_description'),
                    topic.get('keywords', []),
                    topic.get('cluster_id'),
                    embedding_array,
                    topic.get('article_ids', []),
                    topic.get('category_ids', []),
                    topic.get('topic_type', 'general'),
                    0,  # Default priority
                    True,  # Active by default
                    datetime.now(),
                    datetime.now()
                ))
                
                # Get the inserted topic ID
                result = cursor.fetchone()
                topic['id'] = result['id']
                logger.debug(f"Stored topic: {topic['topic_name']} (ID: {topic['id']})")
        
        logger.info(f"Successfully stored {len(topics)} topics")
        return True
    except Exception as e:
        logger.error(f"Error storing topics: {e}")
        import traceback
        traceback.print_exc()
        return False
