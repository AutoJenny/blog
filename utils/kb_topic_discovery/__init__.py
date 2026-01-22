"""
KB Topic Discovery Module

Discovers topics from Knowledge Base articles using clustering on embeddings.
"""

from .clustering import KBTopicClusterer
from .similarity import TopicSimilarityCalculator
from .diversity import DiversityManager
from .rota_generator import RotaGenerator
from .content_aggregator import TopicContentAggregator
from .storage import store_topics

__all__ = [
    'KBTopicClusterer',
    'TopicSimilarityCalculator',
    'DiversityManager',
    'RotaGenerator',
    'TopicContentAggregator',
    'store_topics'
]
