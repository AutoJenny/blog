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
    Handles hierarchical topics by inserting parents first, then children.
    
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
            - parent_id (optional, for hierarchical)
            - level (optional, for hierarchical)
            - is_broad (optional, for hierarchical)
    
    Returns:
        True if successful
    """
    logger.info(f"Storing {len(topics)} topics in database")
    
    try:
        # Separate broad topics (no parent) from granular topics (have parent)
        broad_topics = [t for t in topics if not t.get('parent_id')]
        granular_topics = [t for t in topics if t.get('parent_id')]
        
        # Map of temp_id -> database id
        parent_id_map = {}
        
        with db_manager.get_cursor() as cursor:
            # Step 1: Insert broad topics first (no parent)
            for topic in broad_topics:
                embedding_array = topic['centroid_embedding']
                temp_id = topic.get('temp_id') or topic.get('id')
                
                cursor.execute("""
                    INSERT INTO kb_topics
                        (topic_name, topic_description, topic_keywords, cluster_id,
                         embedding_vector, article_ids, category_ids, topic_type,
                         parent_id, level, is_broad,
                         priority, is_active, discovered_at, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    None,  # No parent
                    topic.get('level', 1),
                    topic.get('is_broad', True),
                    0,
                    True,
                    datetime.now(),
                    datetime.now()
                ))
                
                result = cursor.fetchone()
                db_id = result['id']
                topic['id'] = db_id
                # Map temp_id to database id for child references
                if temp_id:
                    parent_id_map[temp_id] = db_id
                logger.debug(f"Stored broad topic: {topic['topic_name']} (DB ID: {db_id}, temp_id: {temp_id})")
            
            # Step 2: Insert granular topics (with parent references)
            for topic in granular_topics:
                embedding_array = topic['centroid_embedding']
                original_parent_id = topic.get('parent_id')
                
                # Look up database ID of parent using temp_id mapping
                db_parent_id = parent_id_map.get(original_parent_id)
                
                if not db_parent_id:
                    logger.warning(f"Could not find parent ID {original_parent_id} for topic {topic['topic_name']}, skipping")
                    continue
                
                cursor.execute("""
                    INSERT INTO kb_topics
                        (topic_name, topic_description, topic_keywords, cluster_id,
                         embedding_vector, article_ids, category_ids, topic_type,
                         parent_id, level, is_broad,
                         priority, is_active, discovered_at, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    db_parent_id,  # Database ID of parent
                    topic.get('level', 2),
                    topic.get('is_broad', False),
                    0,
                    True,
                    datetime.now(),
                    datetime.now()
                ))
                
                result = cursor.fetchone()
                topic['id'] = result['id']
                logger.debug(f"Stored granular topic: {topic['topic_name']} (DB ID: {result['id']}, Parent: {db_parent_id})")
        
        logger.info(f"Successfully stored {len(broad_topics)} broad topics and {len(granular_topics)} granular topics")
        return True
    except Exception as e:
        logger.error(f"Error storing topics: {e}")
        import traceback
        traceback.print_exc()
        return False
