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
            
            result = self.llm_service.generate(
                prompt=prompt,
                model='ollama/llama3.2',
                temperature=0.7,
                max_tokens=1000
            )
            
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
        return f"""You are generating specific search queries for researching Scottish heritage information about a product category.

Category: {category_name}
Category Hierarchy: {hierarchy_context}

Generate 3-5 specific search queries for each of these research dimensions:
{', '.join(dimensions)}

For each dimension, create queries that:
1. Are specific to Scottish context
2. Include relevant historical/cultural terms
3. Target credible sources (museums, academic institutions, heritage organizations)
4. Are suitable for Wikipedia and web search

Return a JSON object with this structure:
{{
  "historical_origins": ["query 1", "query 2", "query 3"],
  "cultural_significance": ["query 1", "query 2", "query 3"],
  "evolution": ["query 1", "query 2", "query 3"],
  "scottish_heritage_connections": ["query 1", "query 2", "query 3"],
  "industrial_legacy": ["query 1", "query 2", "query 3"]
}}

Focus on historical producers and processes for industrial_legacy (not modern manufacturers).

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

