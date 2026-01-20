"""
Content Synthesizer
Synthesizes extracted facts into coherent paragraphs.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContentSynthesizer:
    """Synthesizes facts into coherent narrative paragraphs."""
    
    SYNTHESIS_SYSTEM_PROMPT = """You are a historical writer specializing in Scottish food history and culture.

Your task is to synthesize factual information about {topic_label} for {item_name} into a coherent, engaging paragraph.

{topic_focus_instructions}

You must:
- Write in a warm, storytelling voice (not academic)
- Use ONLY the facts provided - do not invent specific claims
- Integrate facts naturally into narrative flow
- Handle uncertainties appropriately (e.g., "tradition says", "some sources claim")
- Write for general readers, not academics
- Keep the paragraph focused and engaging (target: {word_target} words)
- Use proper HTML formatting: <p> tags for paragraphs
- Focus on SPECIFIC, PRECISE information - avoid vague generalizations"""

    SYNTHESIS_USER_PROMPT = """Synthesize the following facts about {topic_label} for {item_name} into a coherent paragraph:

FACTS:
{dates_section}
{locations_section}
{events_section}
{people_section}
{cultural_notes_section}
{uncertainties_section}
{conflicts_section}
{quotations_section}

SOURCES USED:
{sources_list}

{topic_specific_requirements}

Requirements:
- Write 1-2 paragraphs (target: {word_target} words)
- Use warm, storytelling voice
- Integrate facts naturally
- Handle uncertainties appropriately
- Use HTML format: <p>Your paragraph here</p>
- Do NOT invent specific facts not in the provided data
- You MAY add general historical context to connect facts
- PRIORITIZE specific, precise information over vague generalizations

Return ONLY the synthesized paragraph(s) in HTML format, no commentary."""

    def __init__(self, llm_service, post_id=None):
        """
        Initialize content synthesizer.
        
        Args:
            llm_service: LLM service instance for synthesis
            post_id: Optional post ID for intercept_context
        """
        self.llm_service = llm_service
        self.post_id = post_id
    
    def synthesize_paragraph(self, facts: Dict, topic_label: str, item_name: str, 
                           sources: List[Dict], word_target: int = 150, 
                           topic_key: str = None, focus_areas: List[str] = None) -> str:
        """
        Synthesize facts into coherent paragraph(s).
        
        Args:
            facts (dict): Structured facts from extraction
            topic_label (str): Research topic label
            item_name (str): Item name
            sources (list): List of source dicts used
            word_target (int): Target word count
        
        Returns:
            str: Synthesized paragraph(s) in HTML format
        """
        # Format facts sections
        dates_section = self._format_facts_section("Dates", facts.get('dates', []))
        locations_section = self._format_facts_section("Locations", facts.get('locations', []))
        events_section = self._format_facts_section("Events", facts.get('events', []))
        people_section = self._format_facts_section("People", facts.get('people', []))
        cultural_notes_section = self._format_facts_section("Cultural Notes", facts.get('cultural_notes', []))
        
        uncertainties_section = ""
        if facts.get('uncertainties'):
            uncertainties_section = "UNCERTAINTIES:\n" + "\n".join(f"- {u}" for u in facts['uncertainties'])
        
        conflicts_section = ""
        if facts.get('conflicts'):
            conflicts_section = "CONFLICTS:\n" + "\n".join(f"- {c}" for c in facts['conflicts'])
        
        quotations_section = ""
        if facts.get('quotations'):
            quotations_section = "QUOTATIONS:\n" + "\n".join(
                f"- \"{q.get('text', '')}\" - {q.get('attributed_to', 'Unknown')}"
                for q in facts['quotations']
            )
        
        # Format sources
        sources_list = "\n".join(
            f"- {s.get('title', 'Unknown')} ({s.get('url', '')})"
            for s in sources[:5]  # Top 5 sources
        )
        
        # Generate topic-specific focus instructions
        topic_focus_instructions = self._get_topic_focus_instructions(topic_key, topic_label, focus_areas)
        topic_specific_requirements = self._get_topic_specific_requirements(topic_key, topic_label)
        
        system_prompt = self.SYNTHESIS_SYSTEM_PROMPT.format(
            topic_label=topic_label,
            item_name=item_name,
            word_target=word_target,
            topic_focus_instructions=topic_focus_instructions
        )
        
        user_prompt = self.SYNTHESIS_USER_PROMPT.format(
            topic_label=topic_label,
            item_name=item_name,
            dates_section=dates_section,
            locations_section=locations_section,
            events_section=events_section,
            people_section=people_section,
            cultural_notes_section=cultural_notes_section,
            uncertainties_section=uncertainties_section or "None",
            conflicts_section=conflicts_section or "None",
            quotations_section=quotations_section or "None",
            sources_list=sources_list or "None",
            word_target=word_target,
            topic_specific_requirements=topic_specific_requirements
        )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        try:
            # Prepare intercept_context if needed
            intercept_context = None
            if self.post_id:
                intercept_context = {'post_id': self.post_id}
            
            # Check if LLMService requires intercept_context
            import inspect
            sig = inspect.signature(self.llm_service.execute_llm_request)
            if 'intercept_context' in sig.parameters:
                result = self.llm_service.execute_llm_request(
                    'ollama',
                    'llama3.2:latest',
                    messages,
                    intercept_context=intercept_context or {'post_id': 0}
                )
            else:
                result = self.llm_service.execute_llm_request(
                    'ollama',
                    'llama3.2:latest',
                    messages
                )
            
            if 'error' in result:
                logger.error(f"LLM error in synthesis: {result['error']}")
                return f"<p>Error synthesizing content: {result['error']}</p>"
            
            content = result.get('content', '').strip()
            
            # Ensure HTML format
            if not content.startswith('<p>'):
                content = f"<p>{content}</p>"
            
            return content
            
        except Exception as e:
            logger.error(f"Error synthesizing content: {e}")
            return f"<p>Error synthesizing content: {str(e)}</p>"
    
    def _get_topic_focus_instructions(self, topic_key: str, topic_label: str, focus_areas: List[str] = None) -> str:
        """Generate topic-specific focus instructions for the synthesis."""
        if topic_key == 'geographic_spread':
            return """CRITICAL FOCUS: This topic is about GEOGRAPHIC SPREAD and REGIONAL VARIATIONS.
- Prioritize SPECIFIC locations, towns, regions, and areas mentioned
- Emphasize regional differences: different names, ingredient variations, method differences
- Include specific places where this is made, sold, or popular
- Focus on geographic distribution patterns across Scotland
- Avoid vague statements about "Scotland" or "Scottish" - use specific place names
- If locations are mentioned, prioritize them heavily in the synthesis"""
        elif topic_key == 'origins':
            return """FOCUS: This topic is about ORIGINS and EARLY HISTORY.
- Prioritize specific dates, first mentions, original locations
- Emphasize earliest documented evidence
- Include origin stories and creation narratives
- Focus on historical timeline and first appearances"""
        elif topic_key == 'evolution':
            return """FOCUS: This topic is about EVOLUTION OVER TIME.
- Prioritize changes: ingredient changes, method changes, when changes occurred
- Emphasize comparisons between historical and modern versions
- Include specific dates or periods when changes happened
- Focus on chronological development"""
        elif topic_key == 'cultural_significance':
            return """FOCUS: This topic is about CULTURAL SIGNIFICANCE and TRADITIONS.
- Prioritize traditional occasions, festivals, ceremonies
- Emphasize cultural meaning and social context
- Include seasonal associations and ritual uses
- Focus on how it fits into Scottish cultural practices"""
        elif topic_key == 'modern_incarnations':
            return """FOCUS: This topic is about MODERN INCARNATIONS and CONTEMPORARY USE.
- Prioritize current uses, modern adaptations, contemporary popularity
- Emphasize how it's used today vs historically
- Include modern variations and innovations
- Focus on present-day relevance and usage"""
        else:
            # Generic instructions
            if focus_areas:
                return f"FOCUS AREAS: {', '.join(focus_areas)}. Prioritize facts related to these areas."
            return "Focus on the specific aspects mentioned in the facts provided."
    
    def _get_topic_specific_requirements(self, topic_key: str, topic_label: str) -> str:
        """Generate topic-specific requirements for synthesis."""
        if topic_key == 'geographic_spread':
            return """CRITICAL REQUIREMENTS FOR GEOGRAPHIC SPREAD:
- MUST prioritize LOCATIONS section - if locations are provided, they should be the primary focus
- Include specific place names: towns, regions, areas (e.g., "Forfar, Angus", "Aberdeen", "the Highlands")
- Describe regional variations: different names by region, ingredient differences, method differences
- Mention specific places where it's made, sold, or particularly popular
- Avoid generic statements like "throughout Scotland" - use specific locations
- If no specific locations are in the facts, state that clearly rather than making vague geographic claims"""
        elif topic_key == 'origins':
            return """REQUIREMENTS FOR ORIGINS:
- Prioritize dates and first mentions
- Include original location if specified
- Emphasize earliest documented evidence"""
        elif topic_key == 'evolution':
            return """REQUIREMENTS FOR EVOLUTION:
- Emphasize changes over time
- Include specific periods or dates when changes occurred
- Compare historical vs modern versions"""
        elif topic_key == 'cultural_significance':
            return """REQUIREMENTS FOR CULTURAL SIGNIFICANCE:
- Emphasize traditional occasions and festivals
- Include cultural meaning and social context"""
        elif topic_key == 'modern_incarnations':
            return """REQUIREMENTS FOR MODERN INCARNATIONS:
- Focus on current uses and modern adaptations
- Compare to historical versions"""
        else:
            return ""
    
    def _format_facts_section(self, section_name: str, facts: List) -> str:
        """Format a section of facts for the prompt."""
        if not facts:
            return f"{section_name}: None"
        
        lines = [f"{section_name}:"]
        for fact in facts:
            if isinstance(fact, dict):
                value = fact.get('value', '')
                context = fact.get('context', '')
                uncertainty = fact.get('uncertainty', False)
                uncertainty_marker = " (uncertain)" if uncertainty else ""
                lines.append(f"  - {value}: {context}{uncertainty_marker}")
            else:
                lines.append(f"  - {fact}")
        
        return "\n".join(lines)
    
    def integrate_sources(self, content: str, sources: List[Dict]) -> str:
        """
        Integrate source citations into content.
        
        Args:
            content (str): Synthesized content
            sources (list): List of source dicts
        
        Returns:
            str: Content with integrated source citations
        """
        # For now, sources are mentioned in the synthesis prompt
        # Could add explicit citations here if needed
        return content
    
    def handle_uncertainties(self, content: str, uncertainties: List[str]) -> str:
        """
        Handle uncertainties in content appropriately.
        
        Args:
            content (str): Synthesized content
            uncertainties (list): List of uncertainty descriptions
        
        Returns:
            str: Content with uncertainties handled
        """
        # Uncertainties are handled in the synthesis prompt
        # This method could add explicit uncertainty markers if needed
        return content
