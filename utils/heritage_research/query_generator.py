"""
Query Generator

Generates specific, contextualized search queries for each research dimension
using LLM to create targeted queries based on category hierarchy.
"""

import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates research queries for heritage research dimensions"""
    
    def __init__(self, llm_service=None):
        """
        Initialize query generator.
        
        Args:
            llm_service: LLM service instance (optional)
        """
        if llm_service is None:
            try:
                from blueprints.llm_actions import LLMService
                self.llm_service = LLMService()
            except ImportError:
                logger.warning("LLM service not available, query generation will be limited")
                self.llm_service = None
        else:
            self.llm_service = llm_service
    
    def generate_queries(self, category_name: str, hierarchy_context: str, 
                        dimensions: List[str]) -> Dict[str, List[str]]:
        """
        Generate search queries for each research dimension.
        
        Args:
            category_name: Name of the category
            hierarchy_context: Full category path (e.g., "Products > Men > Shirts")
            dimensions: List of research dimensions
            
        Returns:
            Dictionary mapping dimension names to lists of queries
        """
        if not self.llm_service:
            # Fallback to simple query generation
            return self._generate_simple_queries(category_name, hierarchy_context, dimensions)
        
        try:
            prompt = self._build_query_prompt(category_name, hierarchy_context, dimensions)
            
            messages = [
                {'role': 'system', 'content': 'You are a research assistant generating precise Wikipedia search queries for Scottish heritage research.'},
                {'role': 'user', 'content': prompt}
            ]
            
            # Use Ollama first for query generation (free, local)
            # Only use OpenAI if explicitly needed for high-priority tasks
            result = self.llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if result and 'error' in result:
                # Log error but don't fallback to OpenAI for bulk/automated research
                logger.warning(f"Ollama query generation failed: {result.get('error')}, using simple query generation fallback")
                return self._generate_simple_queries(category_name, hierarchy_context, dimensions)
            
            if result and result.get('content'):
                content = result.get('content', '').strip()
                
                # Try to parse JSON response
                try:
                    # Remove markdown code blocks if present
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1])
                    
                    queries = json.loads(content)
                    return queries
                except json.JSONDecodeError:
                    logger.warning("LLM returned non-JSON response, using fallback")
                    return self._generate_simple_queries(category_name, hierarchy_context, dimensions)
            
            return self._generate_simple_queries(category_name, hierarchy_context, dimensions)
            
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return self._generate_simple_queries(category_name, hierarchy_context, dimensions)
    
    def _build_query_prompt(self, category_name: str, hierarchy_context: str, 
                           dimensions: List[str]) -> str:
        """Build prompt for LLM query generation"""
        
        dimension_descriptions = {
            'historical_origins': 'the historical origins and early development of this category in Scotland - when it first appeared, how it developed, key historical periods',
            'cultural_significance': 'the cultural significance and role in Scottish traditions, identity, and heritage - what it means to Scottish culture',
            'evolution': 'how this category has evolved and changed over time in Scotland - historical changes, adaptations, modern developments',
            'scottish_heritage_connections': 'specific connections to Scottish clans, regions, events, traditions, and cultural practices',
            'industrial_legacy': 'historical Scottish producers, manufacturing processes, regional specializations, and traditional craftsmanship (historical only, not modern)'
        }
        
        dimension_queries = []
        for dim in dimensions:
            desc = dimension_descriptions.get(dim, dim)
            dimension_queries.append(f"- {dim}: {desc}")
        
        return f"""You are generating precise Wikipedia search queries for researching Scottish heritage about a product category.

Category: {category_name}
Category Hierarchy: {hierarchy_context}

For each research dimension below, generate 3-5 specific Wikipedia article titles or search terms that will find comprehensive articles about that aspect of Scottish heritage.

Research Dimensions:
{chr(10).join(dimension_queries)}

IMPORTANT GUIDELINES:
1. Think of actual Wikipedia article titles that would exist (e.g., "History of tartan", "Scottish textile industry", "Highland dress")
2. Use terms that Wikipedia articles are likely to have (not generic web search terms)
3. Focus on Scottish-specific topics, not general topics
4. For historical_origins: Think of articles about the history of this category in Scotland
5. For cultural_significance: Think of articles about Scottish culture, traditions, identity related to this
6. For evolution: Think of articles about how this category changed over time in Scotland
7. For scottish_heritage_connections: Think of articles about Scottish clans, regions, events related to this
8. For industrial_legacy: Think of articles about historical Scottish manufacturing, producers, traditional crafts

Examples of good queries:
- "Tartan" (for finding the main tartan article)
- "History of Scottish textiles"
- "Highland dress"
- "Scottish clan system"
- "Harris Tweed" (for regional specialization)

Return a JSON object with this structure:
{{
  "historical_origins": ["Wikipedia article title 1", "Wikipedia article title 2", "Wikipedia article title 3"],
  "cultural_significance": ["Wikipedia article title 1", "Wikipedia article title 2", "Wikipedia article title 3"],
  "evolution": ["Wikipedia article title 1", "Wikipedia article title 2", "Wikipedia article title 3"],
  "scottish_heritage_connections": ["Wikipedia article title 1", "Wikipedia article title 2", "Wikipedia article title 3"],
  "industrial_legacy": ["Wikipedia article title 1", "Wikipedia article title 2", "Wikipedia article title 3"]
}}

Return only valid JSON, no additional text."""
    
    def _generate_simple_queries(self, category_name: str, hierarchy_context: str,
                                 dimensions: List[str]) -> Dict[str, List[str]]:
        """
        Generate simple queries without LLM (fallback).
        
        Args:
            category_name: Category name
            hierarchy_context: Category hierarchy
            dimensions: Research dimensions
            
        Returns:
            Dictionary of queries per dimension
        """
        queries = {}
        
        # Base query terms
        base_terms = f"{category_name} Scotland"
        scottish_terms = "Scottish " + category_name.lower()
        
        for dimension in dimensions:
            if dimension == 'historical_origins':
                queries[dimension] = [
                    f"history of {scottish_terms}",
                    f"origins of {category_name} Scotland",
                    f"historical {category_name} Scotland"
                ]
            elif dimension == 'cultural_significance':
                queries[dimension] = [
                    f"{scottish_terms} cultural significance",
                    f"{category_name} Scottish traditions",
                    f"{category_name} Scottish identity"
                ]
            elif dimension == 'evolution':
                queries[dimension] = [
                    f"evolution of {scottish_terms}",
                    f"{category_name} Scotland history development",
                    f"changes in {category_name} Scotland"
                ]
            elif dimension == 'scottish_heritage_connections':
                queries[dimension] = [
                    f"{scottish_terms} clans",
                    f"{category_name} Scottish heritage",
                    f"{category_name} Scotland regional traditions"
                ]
            elif dimension == 'industrial_legacy':
                queries[dimension] = [
                    f"historical {scottish_terms} manufacturers",
                    f"traditional {category_name} making Scotland",
                    f"historical {category_name} production Scotland"
                ]
            else:
                queries[dimension] = [f"{scottish_terms} {dimension}"]
        
        return queries

