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
            topic: Topic dictionary with 'id' and 'centroid_embedding'
            recent_topics: List of recent topic dictionaries
            min_similarity_gap: Minimum similarity threshold to avoid (0.0-1.0)
        
        Returns:
            Diversity score (0.0 to 1.0+)
        """
        if not recent_topics:
            return 1.0  # No recent topics = maximum diversity
        
        # Get similarity scores to recent topics
        similarities = []
        for recent in recent_topics:
            similarity = self._get_topic_similarity(topic['id'], recent['id'])
            if similarity is not None:
                similarities.append(similarity)
        
        if not similarities:
            # If we can't get similarities, assume moderate diversity
            return 0.5
        
        # Minimum similarity (worst case - most similar to recent)
        min_similarity = min(similarities)
        
        # Diversity score: lower similarity = higher diversity
        diversity_score = 1.0 - min_similarity
        
        # Bonus for different topic type
        recent_types = {r.get('topic_type') for r in recent_topics if r.get('topic_type')}
        if topic.get('topic_type') and topic['topic_type'] not in recent_types:
            diversity_score += 0.15
        
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
        
        # Penalty if too similar
        if min_similarity > min_similarity_gap:
            diversity_score *= 0.5  # Reduce score if too similar
        
        return min(diversity_score, 1.5)  # Cap at 1.5 to allow bonuses
    
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
