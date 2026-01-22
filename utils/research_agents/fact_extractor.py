"""
Fact Extractor
Extracts structured facts from web content using LLM.
"""

import json
import logging
from typing import Dict, List, Optional
from utils.family_research.web_utils import chunk_text

logger = logging.getLogger(__name__)


class FactExtractor:
    """Extracts structured facts from content using LLM."""
    
    FACT_EXTRACTION_SYSTEM_PROMPT = """You are a careful fact extractor for historical and cultural research.

Your job is to extract ONLY verifiable factual information from the given text about {topic_label} for {item_name}.

{topic_extraction_focus}

You must:
- Extract specific facts: dates, locations, people, events, cultural notes
- Identify uncertainties and conflicts when they appear
- NOT invent or infer facts beyond what the text clearly states
- Mark facts as uncertain if the text indicates doubt (e.g., "tradition says", "attributed to", "said to be")
- Return structured JSON with all extracted facts
- Be especially thorough with {priority_fact_type} - extract ALL mentions

Be cautious and accurate. Only extract what is clearly stated in the text."""

    FACT_EXTRACTION_USER_PROMPT = """Extract factual information about {topic_label} for {item_name} from this text:

<<<
{content}
>>>

Return a JSON object with this structure:
{{
  "dates": [
    {{"value": "1851", "context": "First documented", "source_hint": "text excerpt", "uncertainty": false}}
  ],
  "locations": [
    {{"value": "Forfar, Angus", "context": "Origin location", "source_hint": "text excerpt", "uncertainty": false}}
  ],
  "events": [
    {{"value": "Created by local bakers", "context": "Origin story", "source_hint": "text excerpt", "uncertainty": false}}
  ],
  "people": [
    {{"value": "John Smith", "context": "Creator", "source_hint": "text excerpt", "uncertainty": false}}
  ],
  "cultural_notes": [
    {{"value": "Traditionally eaten at festivals", "context": "Cultural use", "source_hint": "text excerpt", "uncertainty": false}}
  ],
  "uncertainties": [
    "Some sources claim X, others claim Y"
  ],
  "conflicts": [
    "Date conflict: Source A says 1851, Source B says 1850"
  ],
  "quotations": [
    {{"text": "Exact quote from text", "attributed_to": "Person or source", "context": "When/where said"}}
  ]
}}

CRITICAL EXTRACTION RULES:
- Extract ALL specific details: names, dates, places, quotes, book titles, publication names
- Include specific years, decades, centuries when mentioned
- Extract full names of people, places, organizations, publications
- Capture exact quotations with attribution
- Include specific historical references (e.g., "JM Barrie's Sentimental Tommy")
- Extract competing claims or origin stories as separate facts
- Include specific recipe details, ingredients, methods if mentioned
- Capture cultural practices, traditions, occasions
- Include publication dates, book titles, article sources
- Extract specific locations: towns, regions, counties, areas
- Mark uncertainty only when text explicitly indicates doubt
- Include source_hint with enough context to verify the fact
- If multiple origin stories exist, extract ALL of them
- Extract specific numbers, quantities, measurements if relevant

Return ONLY valid JSON, no commentary"""

    def __init__(self, llm_service, post_id=None):
        """
        Initialize fact extractor.
        
        Args:
            llm_service: LLM service instance for fact extraction
            post_id: Optional post ID for intercept_context
        """
        self.llm_service = llm_service
        self.post_id = post_id
    
    def extract_facts(self, content: str, topic_label: str, item_name: str, topic_key: str = None) -> Dict:
        """
        Extract structured facts from content.
        
        Args:
            content (str): Text content to analyze
            topic_label (str): Research topic label (e.g., "Origins & Early History")
            item_name (str): Item name (e.g., "Forfar Bridie")
        
        Returns:
            dict: Structured facts with dates, locations, events, etc.
        """
        if not content or len(content.strip()) < 50:
            logger.warning("Content too short for fact extraction")
            return self._empty_facts()
        
        # Process more content for better detail extraction
        # Increased from 4000 to 8000 chars, and process more chunks
        max_content_length = 8000
        if len(content) > max_content_length:
            # Try to keep the beginning (often has key info) and some from middle/end
            # Take first 5000 chars and last 3000 chars if article is very long
            if len(content) > 12000:
                content = content[:5000] + "\n\n[... middle section ...]\n\n" + content[-3000:]
            else:
                content = content[:max_content_length] + "..."
            logger.debug(f"Content truncated to {len(content)} chars for processing")
        
        # Chunk content if too long (LLM context limits)
        # Increased chunk size from 2000 to 3000 for better context
        chunks = chunk_text(content, chunk_size=3000)
        all_facts = {
            'dates': [],
            'locations': [],
            'events': [],
            'people': [],
            'cultural_notes': [],
            'uncertainties': [],
            'conflicts': [],
            'quotations': []
        }
        
        # Get topic-specific extraction focus
        topic_extraction_focus, priority_fact_type = self._get_topic_extraction_focus(topic_key, topic_label)
        
        # Extract facts from more chunks (increased from 2 to 4 chunks)
        # Process up to 4 chunks to capture more detail
        chunks_to_process = min(4, len(chunks))
        logger.debug(f"Processing {chunks_to_process} chunks out of {len(chunks)} total")
        for chunk in chunks[:chunks_to_process]:
            try:
                system_prompt = self.FACT_EXTRACTION_SYSTEM_PROMPT.format(
                    topic_label=topic_label,
                    item_name=item_name,
                    topic_extraction_focus=topic_extraction_focus,
                    priority_fact_type=priority_fact_type
                )
                user_prompt = self.FACT_EXTRACTION_USER_PROMPT.format(
                    topic_label=topic_label,
                    item_name=item_name,
                    content=chunk
                )
                
                messages = [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
                
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
                    logger.warning(f"LLM error in fact extraction: {result['error']}")
                    continue
                
                content_text = result.get('content', '').strip()
                if not content_text:
                    continue
                
                # Try to extract JSON from response
                facts = self._parse_facts_json(content_text)
                if facts:
                    # Merge facts from this chunk
                    for key in all_facts:
                        if key in facts and isinstance(facts[key], list):
                            all_facts[key].extend(facts[key])
                
            except Exception as e:
                logger.warning(f"Error extracting facts from chunk: {e}")
                continue
        
        # Deduplicate facts
        all_facts = self._deduplicate_facts(all_facts)
        
        return all_facts
    
    def _parse_facts_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # Try to find JSON object in text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}")
            return None
    
    def _deduplicate_facts(self, facts: Dict) -> Dict:
        """Remove duplicate facts based on value."""
        deduplicated = {}
        for key, fact_list in facts.items():
            if not isinstance(fact_list, list):
                deduplicated[key] = fact_list
                continue
            
            seen = set()
            unique_facts = []
            for fact in fact_list:
                if isinstance(fact, dict):
                    # Use value as key for deduplication
                    fact_key = fact.get('value', str(fact))
                else:
                    fact_key = str(fact)
                
                if fact_key not in seen:
                    seen.add(fact_key)
                    unique_facts.append(fact)
            
            deduplicated[key] = unique_facts
        
        return deduplicated
    
    def _get_topic_extraction_focus(self, topic_key: str, topic_label: str) -> tuple:
        """Get topic-specific extraction focus instructions."""
        if topic_key == 'geographic_spread':
            return (
                "CRITICAL: This topic is about GEOGRAPHIC SPREAD. You MUST extract ALL location mentions: specific towns, cities, regions, areas, counties. Include regional variations in names, ingredients, or methods. Be extremely thorough with locations - extract every place name mentioned.",
                "locations"
            )
        elif topic_key == 'origins':
            return (
                "FOCUS: This topic is about ORIGINS. Prioritize dates, first mentions, original locations, and creation stories.",
                "dates and locations"
            )
        elif topic_key == 'evolution':
            return (
                "FOCUS: This topic is about EVOLUTION. Prioritize dates of changes, ingredient changes, method changes, and comparisons between historical and modern versions.",
                "dates and events"
            )
        elif topic_key == 'cultural_significance':
            return (
                "FOCUS: This topic is about CULTURAL SIGNIFICANCE. Prioritize traditional occasions, festivals, ceremonies, seasonal associations, and cultural meanings.",
                "cultural_notes and events"
            )
        elif topic_key == 'modern_incarnations':
            return (
                "FOCUS: This topic is about MODERN INCARNATIONS. Prioritize current uses, modern adaptations, contemporary popularity, and present-day variations.",
                "events and cultural_notes"
            )
        else:
            return ("Extract all relevant facts about this topic.", "all fact types")
    
    def _empty_facts(self) -> Dict:
        """Return empty facts structure."""
        return {
            'dates': [],
            'locations': [],
            'events': [],
            'people': [],
            'cultural_notes': [],
            'uncertainties': [],
            'conflicts': [],
            'quotations': []
        }
    
    def structure_facts(self, raw_facts: List[Dict]) -> Dict:
        """
        Structure raw facts into organized format.
        
        Args:
            raw_facts (list): List of raw fact dicts
        
        Returns:
            dict: Structured facts
        """
        structured = self._empty_facts()
        
        for fact in raw_facts:
            fact_type = fact.get('type', 'events')
            if fact_type in structured:
                structured[fact_type].append(fact)
        
        return structured
    
    def identify_uncertainties(self, facts: Dict) -> List[str]:
        """
        Identify and list uncertainties from facts.
        
        Args:
            facts (dict): Structured facts
        
        Returns:
            list: List of uncertainty descriptions
        """
        uncertainties = []
        
        # Add explicit uncertainties
        uncertainties.extend(facts.get('uncertainties', []))
        
        # Check for uncertain facts
        for key in ['dates', 'locations', 'events', 'people']:
            for fact in facts.get(key, []):
                if isinstance(fact, dict) and fact.get('uncertainty'):
                    uncertainties.append(
                        f"{key.title()}: {fact.get('value', 'Unknown')} - {fact.get('context', '')}"
                    )
        
        return uncertainties
