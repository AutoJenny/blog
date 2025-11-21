"""
Profile Matching Module

Provides functionality for matching posts to products, suppliers, and categories
using vector embeddings and semantic similarity.
"""

from .post_matcher import find_similar_entities
from .normalization import normalize_and_select_best

__all__ = ['find_similar_entities', 'normalize_and_select_best']

