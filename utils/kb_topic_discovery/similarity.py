"""
Topic Similarity Calculation Module

Calculates similarity between topics for diversity scheduling.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from config.database import db_manager

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine similarity (0.0 to 1.0)
    """
    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
    
    # Calculate cosine similarity
    similarity = np.dot(vec1_norm, vec2_norm)
    
    # Clamp to [0, 1] range
    return max(0.0, min(1.0, similarity))


class TopicSimilarityCalculator:
    """
    Calculates similarity between topics for diversity scheduling.
    """
    
    def compute_similarity_matrix(self, topics: List[Dict]) -> Dict[Tuple[int, int], float]:
        """
        Compute pairwise similarity between all topics.
        Stores in kb_topic_similarity table.
        
        Args:
            topics: List of topic dictionaries with 'id' and 'centroid_embedding'
        
        Returns:
            Dictionary mapping (topic1_id, topic2_id) -> similarity_score
        """
        logger.info(f"Computing similarity matrix for {len(topics)} topics")
        
        similarities = {}
        
        for i, topic1 in enumerate(topics):
            embedding1 = np.array(topic1['centroid_embedding'])
            topic1_id = topic1['id']
            
            for j, topic2 in enumerate(topics[i+1:], start=i+1):
                embedding2 = np.array(topic2['centroid_embedding'])
                topic2_id = topic2['id']
                
                # Calculate cosine similarity
                similarity = cosine_similarity(embedding1, embedding2)
                
                # Store in dictionary (ensure topic1_id < topic2_id)
                if topic1_id < topic2_id:
                    key = (topic1_id, topic2_id)
                else:
                    key = (topic2_id, topic1_id)
                
                similarities[key] = similarity
                
                # Store in database
                self._store_similarity(topic1_id, topic2_id, similarity)
        
        logger.info(f"Computed {len(similarities)} similarity pairs")
        return similarities
    
    def _store_similarity(self, topic1_id: int, topic2_id: int, similarity: float):
        """
        Store similarity in database.
        
        Args:
            topic1_id: First topic ID
            topic2_id: Second topic ID
            similarity: Similarity score (0.0 to 1.0)
        """
        # Ensure topic1_id < topic2_id for consistency
        if topic1_id > topic2_id:
            topic1_id, topic2_id = topic2_id, topic1_id
        
        # Calculate L2 distance (for reference)
        # Cosine distance = 1 - cosine similarity
        distance = 1.0 - similarity
        
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO kb_topic_similarity 
                        (topic1_id, topic2_id, similarity_score, distance, computed_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (topic1_id, topic2_id) 
                    DO UPDATE SET 
                        similarity_score = EXCLUDED.similarity_score,
                        distance = EXCLUDED.distance,
                        computed_at = CURRENT_TIMESTAMP
                """, (topic1_id, topic2_id, float(similarity), float(distance)))
        except Exception as e:
            logger.warning(f"Error storing similarity for topics {topic1_id}, {topic2_id}: {e}")
    
    def get_similarity(self, topic1_id: int, topic2_id: int) -> Optional[float]:
        """
        Get similarity between two topics from database.
        
        Args:
            topic1_id: First topic ID
            topic2_id: Second topic ID
        
        Returns:
            Similarity score (0.0 to 1.0) or None if not found
        """
        # Ensure topic1_id < topic2_id
        if topic1_id > topic2_id:
            topic1_id, topic2_id = topic2_id, topic1_id
        
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT similarity_score
                    FROM kb_topic_similarity
                    WHERE topic1_id = %s AND topic2_id = %s
                """, (topic1_id, topic2_id))
                
                result = cursor.fetchone()
                if result:
                    return float(result['similarity_score'])
        except Exception as e:
            logger.warning(f"Error getting similarity for topics {topic1_id}, {topic2_id}: {e}")
        
        return None
