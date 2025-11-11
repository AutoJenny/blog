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
            
            messages = [
                {'role': 'system', 'content': 'You are a Scottish heritage expert synthesizing research from Wikipedia articles. Extract specific factual information and create coherent narratives.'},
                {'role': 'user', 'content': prompt}
            ]
            
            # Use Ollama first for heritage research (free, local)
            # Only use OpenAI if explicitly needed for high-priority tasks
            result = self.llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if result and 'error' in result:
                # Log error but don't fallback to OpenAI for bulk/automated research
                logger.warning(f"Ollama synthesis failed: {result.get('error')}, using simple synthesis fallback")
                return self._simple_synthesis(dimension, sources)
            
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
        
        # Prepare source text with full content
        source_text = ""
        for i, source in enumerate(sources[:5], 1):  # Top 5 sources (with full content)
            source_text += f"\n\n=== Source {i}: {source.get('title', 'Unknown')} ===\n"
            source_text += f"URL: {source.get('url', '')}\n"
            
            # Use full_content if available, otherwise fall back to summary
            content = source.get('full_content') or source.get('summary', '')
            if content:
                source_text += f"\nContent:\n{content}\n"
            
            # Add references if available
            references = source.get('references', [])
            if references:
                source_text += f"\nReferences to external sources: {len(references)} found\n"
        
        dimension_descriptions = {
            'historical_origins': {
                'focus': 'the historical origins and early development of this category in Scotland',
                'what_to_extract': 'when it first appeared, key historical periods, how it developed, important dates, early forms, historical context'
            },
            'cultural_significance': {
                'focus': 'the cultural significance and role in Scottish traditions, identity, and heritage',
                'what_to_extract': 'what it means to Scottish culture, traditions associated with it, symbolic meanings, role in Scottish identity, cultural practices'
            },
            'evolution': {
                'focus': 'how this category has evolved and changed over time in Scotland',
                'what_to_extract': 'historical changes, adaptations, developments over centuries, modern forms, how it transformed, continuity and change'
            },
            'scottish_heritage_connections': {
                'focus': 'specific connections to Scottish clans, regions, events, and traditions',
                'what_to_extract': 'clan associations, regional variations, connections to historical events, traditional uses, regional specializations, local traditions'
            },
            'industrial_legacy': {
                'focus': 'historical Scottish producers, manufacturing processes, and regional specializations',
                'what_to_extract': 'famous historical producers, traditional manufacturing methods, regional specializations, historical craftsmanship, traditional processes (historical only, exclude modern)'
            }
        }
        
        dimension_info = dimension_descriptions.get(dimension, {'focus': dimension, 'what_to_extract': 'relevant information'})
        
        return f"""You are a Scottish heritage expert synthesizing research about {dimension_info['focus']} of a product category.

Category: {category_name}
Category Hierarchy: {hierarchy_context}

Research Sources (full Wikipedia articles):
{source_text}

TASK: Carefully read through all the source material above and extract specific, factual information about {dimension_info['what_to_extract']}.

IMPORTANT INSTRUCTIONS:
1. Extract SPECIFIC FACTUAL INFORMATION from the sources (dates, names, places, events, processes)
2. Focus ONLY on information directly relevant to {dimension_info['focus']}
3. Ignore generic or irrelevant information
4. Extract individual factoids and interesting details
5. Maintain focus on Scottish context and heritage
6. For industrial_legacy: ONLY include historical producers/processes, exclude anything modern

Create a comprehensive narrative (300-500 words) that:
- Synthesizes the extracted factual information into a coherent story
- Identifies 3-5 key themes that emerge from the research
- Lists 3-5 significant elements (specific facts, dates, people, events, processes) that are particularly interesting or important
- Maintains focus on Scottish heritage and the specific category
- Uses information directly from the sources (don't make things up)

Return a JSON object with this structure:
{{
  "narrative": "300-500 word synthesized narrative based on extracted facts from sources...",
  "key_themes": ["Theme 1 (specific theme from sources)", "Theme 2", "Theme 3"],
  "significant_elements": ["Specific factoid 1 (e.g., 'Tartan was first recorded in 3rd century AD')", "Specific factoid 2", "Specific factoid 3"]
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
        # Combine full content from sources
        all_content = []
        for source in sources:
            content = source.get('full_content') or source.get('summary', '')
            if content:
                all_content.append(content)
        
        # Create simple narrative from content
        # TODO: Remove arbitrary 1000 char limit - this causes mid-sentence truncation
        # Should allow full narrative or check for proper sentence endings
        narrative = " ".join(all_content[:3])[:1000]  # First 3 sources, max 1000 chars
        
        return {
            'narrative': narrative,
            'key_themes': [],
            'significant_elements': []
        }

