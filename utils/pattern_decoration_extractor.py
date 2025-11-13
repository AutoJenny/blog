"""
LLM-Based Pattern and Decoration Extractor

Extracts patterns (repeating designs) and decorations (specific motifs) from products.
Uses LLM to analyze product name, description, and specifications.
"""

import json
import logging
import re
from typing import Dict, Optional, List
from blueprints.llm_actions import LLMService

logger = logging.getLogger(__name__)

# Valid patterns (repeating designs)
VALID_PATTERNS = {
    'tartan',
    'harris_tweed',
    'celtic_knotwork',
    'check',
    'argyle',
    'herringbone',
    'fairisle',
    'striped',
    'polka_dot',
    'paisley',
}

# Valid decorations (specific motifs)
VALID_DECORATIONS = {
    'clan_crest',
    'lion_rampant',
    'thistle',
    'stag',
    'shamrock',
    'sword',
    'rose',
    'dragon',
    'knot',
    'celtic_knotwork',
    'masonic',
    'viking',
    'highland_cow',
}

class PatternDecorationExtractor:
    """Uses LLM to extract patterns and decorations from products."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize extractor.
        
        Args:
            llm_service: LLMService instance (creates new one if not provided)
        """
        self.llm_service = llm_service or LLMService()
    
    def extract_patterns_decorations(self,
                                    product_name: str,
                                    description: Optional[str] = None,
                                    short_description: Optional[str] = None,
                                    additional_data: Optional[Dict] = None) -> Dict:
        """
        Extract patterns and decorations from product information.
        
        Args:
            product_name: Product name/title
            description: Product description
            short_description: Product short description
            additional_data: Product specifications/additional data
            
        Returns:
            Dictionary with:
            - patterns: List of pattern names (repeating designs)
            - decorations: List of decoration names (specific motifs)
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Brief explanation
            - error: Error message if extraction failed
        """
        try:
            # Build context from all available information
            context_parts = []
            if product_name:
                context_parts.append(f"Product Name: {product_name}")
            if short_description:
                # Clean HTML tags
                import re as re_module
                clean_desc = re_module.sub(r'<[^>]+>', '', short_description)
                context_parts.append(f"Short Description: {clean_desc[:300]}")
            if description:
                clean_desc = re_module.sub(r'<[^>]+>', '', description)
                context_parts.append(f"Description: {clean_desc[:500]}")
            if additional_data:
                # Extract relevant specification fields
                spec_text = []
                for key, value in additional_data.items():
                    if isinstance(value, dict):
                        spec_text.append(f"{value.get('label', key)}: {value.get('value', '')}")
                    else:
                        spec_text.append(f"{key}: {value}")
                if spec_text:
                    context_parts.append(f"Specifications: {'; '.join(spec_text[:200])}")
            
            context = "\n".join(context_parts)
            
            # Build prompt
            patterns_list = ', '.join(sorted(VALID_PATTERNS))
            decorations_list = ', '.join(sorted(VALID_DECORATIONS))
            
            prompt = f"""Analyze this product and extract PATTERNS (repeating designs) and DECORATIONS (specific motifs).

PATTERNS are repeating designs/textures like:
- tartan (plaid patterns)
- harris_tweed (tweed fabric)
- celtic_knotwork (interlaced knot patterns)
- check (checked/grid patterns)
- argyle (diamond patterns)
- herringbone (zigzag weave)
- fairisle (colorwork patterns)
- striped, polka_dot, paisley

DECORATIONS are specific motifs/symbols like:
- clan_crest (clan crests, family crests)
- lion_rampant (Scottish lion symbol)
- thistle (Scottish thistle)
- stag (deer/stag motifs)
- shamrock (Irish shamrock)
- sword (sword motifs)
- rose (rose motifs)
- dragon (dragon motifs)
- knot, celtic_knotwork (knot designs)
- masonic (Masonic symbols)
- viking (Viking symbols)
- highland_cow (Highland cow motifs)

Valid patterns: {patterns_list}
Valid decorations: {decorations_list}

Product Information:
{context}

Return JSON with:
{{
  "patterns": ["pattern1", "pattern2"],  // Array of pattern names from valid list, or empty array
  "decorations": ["decoration1", "decoration2"],  // Array of decoration names from valid list, or empty array
  "confidence": 0.0-1.0,  // Confidence in extraction
  "reasoning": "Brief explanation of what was found and why"
}}

Rules:
- Only include patterns/decorations that are clearly present
- Use exact names from the valid lists above
- If a product mentions "tartan" but doesn't specify which, use "tartan"
- If a product has "clan crest" or "family crest", use "clan_crest"
- If a product has "celtic knot" or "celtic knotwork", use "celtic_knotwork"
- If unsure, don't include it (empty array is fine)
- Some products may have multiple patterns or decorations
- Some products may have none

Return only valid JSON, no markdown formatting, no code blocks."""

            messages = [
                {
                    'role': 'system',
                    'content': 'You are a product analysis expert. Extract patterns and decorations accurately. Return only valid JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Use Ollama
            result = self.llm_service.execute_llm_request(
                provider='ollama',
                model='mistral',
                messages=messages
            )
            
            if result and 'error' in result:
                return {
                    'patterns': [],
                    'decorations': [],
                    'confidence': 0.0,
                    'reasoning': None,
                    'error': result.get('error')
                }
            
            content = result.get('content', '') if result else ''
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    data = json.loads(json_str)
                    
                    # Validate and normalize patterns
                    patterns = []
                    if 'patterns' in data and isinstance(data['patterns'], list):
                        for p in data['patterns']:
                            # Normalize to valid pattern
                            normalized = self._normalize_pattern(p)
                            if normalized and normalized not in patterns:
                                patterns.append(normalized)
                    
                    # Validate and normalize decorations
                    decorations = []
                    if 'decorations' in data and isinstance(data['decorations'], list):
                        for d in data['decorations']:
                            # Normalize to valid decoration
                            normalized = self._normalize_decoration(d)
                            if normalized and normalized not in decorations:
                                decorations.append(normalized)
                    
                    return {
                        'patterns': sorted(patterns),
                        'decorations': sorted(decorations),
                        'confidence': float(data.get('confidence', 0.5)),
                        'reasoning': data.get('reasoning', ''),
                        'error': None
                    }
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error: {e}")
                    return {
                        'patterns': [],
                        'decorations': [],
                        'confidence': 0.0,
                        'reasoning': None,
                        'error': f'JSON decode error: {str(e)}'
                    }
            else:
                return {
                    'patterns': [],
                    'decorations': [],
                    'confidence': 0.0,
                    'reasoning': None,
                    'error': 'No JSON found in response'
                }
        
        except Exception as e:
            logger.error(f"Error extracting patterns/decorations: {e}", exc_info=True)
            return {
                'patterns': [],
                'decorations': [],
                'confidence': 0.0,
                'reasoning': None,
                'error': str(e)
            }
    
    def _normalize_pattern(self, pattern: str) -> Optional[str]:
        """Normalize pattern name to valid pattern."""
        if not pattern:
            return None
        
        pattern_lower = pattern.lower().strip()
        
        # Direct matches
        if pattern_lower in VALID_PATTERNS:
            return pattern_lower
        
        # Normalizations
        normalizations = {
            'tartan': 'tartan',
            'plaid': 'tartan',
            'harris tweed': 'harris_tweed',
            'tweed': 'harris_tweed',
            'celtic knot': 'celtic_knotwork',
            'celtic knotwork': 'celtic_knotwork',
            'knotwork': 'celtic_knotwork',
            'knot': 'celtic_knotwork',
            'checked': 'check',
            'check': 'check',
            'argyll': 'argyle',
            'argyle': 'argyle',
            'herringbone': 'herringbone',
            'fairisle': 'fairisle',
            'fair isle': 'fairisle',
            'striped': 'striped',
            'stripe': 'striped',
            'polka dot': 'polka_dot',
            'polkadot': 'polka_dot',
            'paisley': 'paisley',
        }
        
        return normalizations.get(pattern_lower)
    
    def _normalize_decoration(self, decoration: str) -> Optional[str]:
        """Normalize decoration name to valid decoration."""
        if not decoration:
            return None
        
        decoration_lower = decoration.lower().strip()
        
        # Direct matches
        if decoration_lower in VALID_DECORATIONS:
            return decoration_lower
        
        # Normalizations
        normalizations = {
            'clan crest': 'clan_crest',
            'clan_crest': 'clan_crest',
            'family crest': 'clan_crest',
            'crest': 'clan_crest',
            'lion rampant': 'lion_rampant',
            'lion_rampant': 'lion_rampant',
            'thistle': 'thistle',
            'stag': 'stag',
            'deer': 'stag',
            'shamrock': 'shamrock',
            'sword': 'sword',
            'rose': 'rose',
            'dragon': 'dragon',
            'knot': 'celtic_knotwork',
            'celtic knot': 'celtic_knotwork',
            'celtic knotwork': 'celtic_knotwork',
            'masonic': 'masonic',
            'viking': 'viking',
            'highland cow': 'highland_cow',
            'highland_cow': 'highland_cow',
        }
        
        return normalizations.get(decoration_lower)

