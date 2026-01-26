"""
Diversity Management Module

Manages diversity calculations for rota generation.
"""

import logging
from typing import List, Dict, Optional
from .similarity import TopicSimilarityCalculator

logger = logging.getLogger(__name__)


class DiversityManager:
    """
    Manages diversity calculations for rota generation.
    """
    
    def __init__(self):
        """Initialize diversity manager."""
        self.similarity_calculator = TopicSimilarityCalculator()
    
    def calculate_diversity(self,
                           topic: Dict,
                           recent_topics: List[Dict],
                           min_similarity_gap: float = 0.7) -> float:
        """
        Calculate how diverse this topic is from recent topics.
        Higher score = more diverse.
        
        Args:
            topic: Topic dictionary with 'id', 'centroid_embedding', 'topic_type', 'parent_id', 'level'
            recent_topics: List of recent topic dictionaries (most recent first)
            min_similarity_gap: Minimum similarity threshold to avoid (0.0-1.0)
        
        Returns:
            Diversity score (0.0 to 1.0+)
        """
        if not recent_topics:
            return 1.0  # No recent topics = maximum diversity
        
        # Get similarity scores to recent topics (most recent first)
        similarities = []
        for i, recent in enumerate(recent_topics):
            similarity = self._get_topic_similarity(topic['id'], recent['id'])
            if similarity is not None:
                similarities.append((similarity, i))  # Store with index for recency weighting
        
        if not similarities:
            # If we can't get similarities, assume moderate diversity
            return 0.5
        
        # Minimum similarity (worst case - most similar to recent)
        min_similarity = min(sim[0] for sim in similarities)
        
        # Diversity score: lower similarity = higher diversity
        diversity_score = 1.0 - min_similarity
        
        # STRONG PENALTY: Same topic type in immediate previous week (index 0)
        if recent_topics and len(recent_topics) > 0:
            most_recent = recent_topics[0]
            if topic.get('topic_type') and most_recent.get('topic_type'):
                if topic['topic_type'] == most_recent['topic_type']:
                    # Strong penalty for same type in consecutive weeks
                    diversity_score *= 0.3  # Reduce by 70%
                    logger.debug(f"Penalty: Same topic type '{topic['topic_type']}' as previous week")
        
        # STRONG PENALTY: Same parent topic in immediate previous week
        if recent_topics and len(recent_topics) > 0:
            most_recent = recent_topics[0]
            topic_parent = topic.get('parent_id') or topic.get('id')
            recent_parent = most_recent.get('parent_id') or most_recent.get('id')
            
            if topic_parent == recent_parent:
                # Very strong penalty for same parent in consecutive weeks
                diversity_score *= 0.2  # Reduce by 80%
                logger.debug(f"Penalty: Same parent topic {topic_parent} as previous week")
        
        # STRONG PENALTY: High similarity in immediate previous week
        if similarities:
            most_recent_similarity = similarities[0][0]  # First item is most recent
            if most_recent_similarity > 0.75:  # Very similar
                diversity_score *= 0.4  # Reduce by 60%
                logger.debug(f"Penalty: High similarity ({most_recent_similarity:.2f}) to previous week")
            elif most_recent_similarity > 0.65:  # Moderately similar
                diversity_score *= 0.6  # Reduce by 40%
        
        # Bonus for different topic type (but only if not already penalized)
        recent_types = {r.get('topic_type') for r in recent_topics if r.get('topic_type')}
        if topic.get('topic_type') and topic['topic_type'] not in recent_types:
            diversity_score += 0.2  # Increased bonus
        
        # Bonus for different parent topic
        recent_parents = {r.get('parent_id') or r.get('id') for r in recent_topics}
        topic_parent = topic.get('parent_id') or topic.get('id')
        if topic_parent not in recent_parents:
            diversity_score += 0.15  # Bonus for different parent
        
        # Bonus for different category areas
        recent_categories = set()
        for r in recent_topics:
            if r.get('category_ids'):
                recent_categories.update(r['category_ids'])
        
        topic_categories = set(topic.get('category_ids', []))
        if topic_categories:
            category_overlap = len(recent_categories & topic_categories) / len(topic_categories)
            category_bonus = (1.0 - category_overlap) * 0.1
            diversity_score += category_bonus
        
        # Additional penalty if too similar overall
        if min_similarity > min_similarity_gap:
            diversity_score *= 0.5  # Reduce score if too similar
        
        # Ensure minimum diversity for consecutive weeks with same type/parent
        if recent_topics and len(recent_topics) > 0:
            most_recent = recent_topics[0]
            if (topic.get('topic_type') == most_recent.get('topic_type') or
                (topic.get('parent_id') or topic.get('id')) == (most_recent.get('parent_id') or most_recent.get('id'))):
                # Cap diversity score for consecutive similar topics
                diversity_score = min(diversity_score, 0.3)
        
        return max(0.0, min(diversity_score, 1.5))  # Cap at 1.5, floor at 0.0
    
    def _get_topic_similarity(self, topic1_id: int, topic2_id: int) -> Optional[float]:
        """
        Get similarity between two topics.
        
        Args:
            topic1_id: First topic ID
            topic2_id: Second topic ID
        
        Returns:
            Similarity score or None
        """
        return self.similarity_calculator.get_similarity(topic1_id, topic2_id)
