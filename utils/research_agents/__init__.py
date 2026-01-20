"""
Research Agents Module
Provides agent-based web research capabilities for post background research.

This module contains classes for:
- Web search and content fetching
- Source evaluation and prioritization
- Fact extraction from content
- Content synthesis into paragraphs
"""

from .web_researcher import WebResearcher
from .source_evaluator import SourceEvaluator
from .fact_extractor import FactExtractor
from .content_synthesizer import ContentSynthesizer

__all__ = [
    'WebResearcher',
    'SourceEvaluator',
    'FactExtractor',
    'ContentSynthesizer'
]
