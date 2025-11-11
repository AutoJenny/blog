"""
Enhanced Heritage Research System

Multi-stage research system for generating authentic, well-sourced heritage data
for product categories using Wikipedia API, Google Custom Search, and LLM synthesis.
"""

from .wikipedia_researcher import WikipediaResearcher
from .query_generator import QueryGenerator
from .source_filter import SourceFilter
from .research_synthesizer import ResearchSynthesizer
from .config import RESEARCH_DIMENSIONS, RESEARCH_FREQUENCY

__all__ = [
    'WikipediaResearcher',
    'QueryGenerator',
    'SourceFilter',
    'ResearchSynthesizer',
    'RESEARCH_DIMENSIONS',
    'RESEARCH_FREQUENCY'
]

