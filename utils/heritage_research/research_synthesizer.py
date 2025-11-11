"""
Research Synthesizer

Synthesizes raw research data into coherent narratives using LLM.
Extracts key themes and significant elements from collected sources.
"""

import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ResearchSynthesizer:
    """Synthesizes research data into heritage narratives"""
    
    def __init__(self, llm_service=None):
        """
        Initialize research synthesizer.
        
        Args:
            llm_service: LLM service instance (optional)
        """
        if llm_service is None:
            try:
                from blueprints.llm_actions import LLMService
                self.llm_service = LLMService()
            except ImportError:
                logger.warning("LLM service not available, synthesis will be limited")
                self.llm_service = None
        else:
            self.llm_service = llm_service
    
    def synthesize_dimension(self, dimension: str, sources: List[Dict], 
                           category_name: str, hierarchy_context: str) -> Dict:
        """
        Synthesize research for a single dimension.
        
        Args:
            dimension: Research dimension name
            sources: List of source dictionaries with snippets
            category_name: Category name
            hierarchy_context: Category hierarchy path
            
        Returns:
            Dictionary with narrative, key_themes, and significant_elements
        """
        if not self.llm_service or not sources:
            # Fallback: combine snippets
            return self._simple_synthesis(dimension, sources)
        
        try:
            prompt = self._build_synthesis_prompt(dimension, sources, category_name, hierarchy_context)
            
            result = self.llm_service.generate(
                prompt=prompt,
                model='ollama/llama3.2',
                temperature=0.7,
                max_tokens=1500
            )
            
            if result and result.get('content'):
                content = result.get('content', '').strip()
                
                # Try to parse JSON response
                try:
                    # Remove markdown code blocks if present
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1])
                    
                    synthesis = json.loads(content)
                    return synthesis
                except json.JSONDecodeError:
                    logger.warning("LLM returned non-JSON response, using fallback")
                    return self._simple_synthesis(dimension, sources)
            
            return self._simple_synthesis(dimension, sources)
            
        except Exception as e:
            logger.error(f"Error synthesizing dimension {dimension}: {e}")
            return self._simple_synthesis(dimension, sources)
    
    def _build_synthesis_prompt(self, dimension: str, sources: List[Dict],
                               category_name: str, hierarchy_context: str) -> str:
        """Build prompt for LLM synthesis"""
        
        # Prepare source text
        source_text = ""
        for i, source in enumerate(sources[:10], 1):  # Top 10 sources
            source_text += f"\n\nSource {i}: {source.get('title', 'Unknown')}\n"
            source_text += f"URL: {source.get('url', '')}\n"
            snippets = source.get('snippets', [])
            if snippets:
                source_text += "Relevant information:\n"
                for snippet in snippets[:3]:  # Top 3 snippets per source
                    source_text += f"- {snippet}\n"
        
        dimension_descriptions = {
            'historical_origins': 'the historical origins and early development',
            'cultural_significance': 'the cultural significance and role in Scottish traditions',
            'evolution': 'how it has evolved and changed over time',
            'scottish_heritage_connections': 'connections to Scottish clans, regions, events, and traditions',
            'industrial_legacy': 'historical producers, manufacturing processes, and regional specializations (historical only, not modern)'
        }
        
        dimension_desc = dimension_descriptions.get(dimension, dimension)
        
        return f"""You are synthesizing research about {dimension_desc} of a Scottish product category.

Category: {category_name}
Category Hierarchy: {hierarchy_context}

Research Sources:
{source_text}

Based on these sources, create a comprehensive narrative (300-500 words) that:
1. Synthesizes information from multiple sources
2. Identifies key themes and significant elements
3. Maintains focus on Scottish heritage and context
4. Attributes information to sources where relevant
5. Highlights interesting and unique insights

For industrial_legacy, focus ONLY on historical producers and processes, not modern manufacturers.

Return a JSON object with this structure:
{{
  "narrative": "300-500 word synthesized narrative...",
  "key_themes": ["Theme 1", "Theme 2", "Theme 3"],
  "significant_elements": ["Element 1", "Element 2", "Element 3"]
}}

Return only valid JSON, no additional text."""
    
    def _simple_synthesis(self, dimension: str, sources: List[Dict]) -> Dict:
        """
        Simple synthesis without LLM (fallback).
        
        Args:
            dimension: Research dimension
            sources: List of sources
            
        Returns:
            Dictionary with basic synthesis
        """
        # Combine snippets from sources
        all_snippets = []
        for source in sources:
            snippets = source.get('snippets', [])
            all_snippets.extend(snippets)
        
        # Create simple narrative from snippets
        narrative = " ".join(all_snippets[:10])[:500]  # First 10 snippets, max 500 chars
        
        return {
            'narrative': narrative,
            'key_themes': [],
            'significant_elements': []
        }

