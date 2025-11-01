"""LLM-based content analysis service for news suitability assessment."""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Default suitability threshold (0-10 scale)
DEFAULT_SUITABILITY_THRESHOLD = 6.0


def analyze_news_suitability(title: str, description: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
    """Analyze news article for relevance to Scottish heritage/culture focus.
    
    Args:
        title: Article title
        description: Article description/summary (optional)
        url: Article URL (optional, for context)
    
    Returns:
        Dict with:
        {
            'suitability_score': float (0-10),
            'suitability_notes': str (reasoning),
            'relevant': bool (score >= threshold)
        }
    """
    # Import LLM service - try blog-core version first
    import os
    import sys
    
    # Import LLM service - MUST succeed, no fallback
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from app.llm.services import LLMService
        llm_service = LLMService()
    except ImportError:
        from modules.llm_service import LLMService
        llm_service = LLMService()
    
    # Construct prompt for content analysis
    prompt = f"""You are analyzing news articles for a Scottish heritage and culture newsletter with a primarily US-Scots diaspora audience - people of Scottish descent living in the United States, Canada, Australia, and other countries who maintain an interest in the history and culture of their "old country".

Imagine a typical reader: someone of Scottish descent living in the US, with family connections to Scotland, interested in learning about the "old country" - its history, culture, traditions, and contemporary developments that matter.

Article Title: {title}
{f"Description: {description[:500]}" if description else ""}

Rate this article on FIVE separate dimensions, each on a scale of 1-100. CRITICAL: Most stories should have MOST dimensions scoring 10-40. Only truly exceptional stories should have dimensions above 70. Be CRITICAL and use LOW scores liberally.

1. HISTORICAL INTEREST (1-100): 
   - Scores 1-20: No historical content, just current events
   - Scores 21-40: Minor historical mention or local history
   - Scores 41-60: Some historical context
   - Scores 61-80: Substantial historical content, heritage sites, notable historical figures
   - Scores 81-100: Major historical discoveries, archaeology, preservation of national heritage

2. CULTURAL INTEREST (1-100):
   - Scores 1-20: No cultural content, just daily news
   - Scores 21-40: Minor cultural mention
   - Scores 41-60: Some cultural context
   - Scores 61-80: Substantial cultural content (traditions, language, arts)
   - Scores 81-100: Major cultural significance, festivals, cultural revivals

3. QUIRKY INTEREST (1-100):
   - Scores 1-20: Mundane, everyday news
   - Scores 21-40: Slightly interesting angle
   - Scores 41-60: Moderately interesting, some human interest
   - Scores 61-80: Very quirky/interesting, would make diaspora smile
   - Scores 81-100: Exceptionally quirky, charmingly Scottish

4. ECONOMIC IMPORTANCE (1-100):
   - Scores 1-20: No economic significance
   - Scores 21-40: Minor local economic impact
   - Scores 41-60: Some economic relevance
   - Scores 61-80: Significant economic developments diaspora might care about
   - Scores 81-100: Major economic significance (tourism, major industries)

5. POLITICAL IMPORTANCE (1-100):
   - Scores 1-20: Daily politics, local governance
   - Scores 21-40: Minor political note
   - Scores 41-60: Some political relevance
   - Scores 61-80: Significant political developments (devolution, independence)
   - Scores 81-100: Major political significance affecting Scotland's future

EXAMPLES TO GUIDE YOU:
- "Former footballer dies aged 73" → Historical=15, Cultural=20, Quirky=25, Economic=5, Political=5 (average=14 → score 2.1)
- "Glasgow firework ban zones" → Historical=10, Cultural=15, Quirky=30, Economic=25, Political=40 (average=24 → score 2.9)
- "Local council decision" → Historical=5, Cultural=10, Quirky=15, Economic=20, Political=35 (average=17 → score 2.3)
- "Archaeological discovery at Scottish castle" → Historical=90, Cultural=70, Quirky=60, Economic=50, Political=20 (average=58 → score 5.6)
- "Scottish language revival program" → Historical=60, Cultural=95, Quirky=50, Economic=40, Political=50 (average=59 → score 5.7)

MOST daily news stories should have MOST dimensions in the 10-40 range. Be strict!

Provide your assessment in JSON format:
{{
    "historical_interest": <number 1-100>,
    "cultural_interest": <number 1-100>,
    "quirky_interest": <number 1-100>,
    "economic_importance": <number 1-100>,
    "political_importance": <number 1-100>,
    "reasoning": "<brief explanation of your scores for each dimension>",
    "relevant": <true if calculated score >= 6.0, false otherwise>
}}
"""
    
    try:
        # Use LLM to analyze - use available model (mistral:latest or llama3.2:latest)
        model_name = os.environ.get('DEFAULT_LLM_MODEL', 'mistral:latest')
        response = llm_service.generate(
            prompt=prompt,
            model_name=model_name,
            temperature=0.3,  # Lower temperature for more consistent scoring
            max_tokens=300
        )
        
        if not response:
            raise ValueError("LLM returned empty response for suitability analysis - cannot proceed without LLM")
        
        # Parse JSON from response
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                
                # Calculate score from five dimensions
                historical = float(result.get('historical_interest', 50))
                cultural = float(result.get('cultural_interest', 50))
                quirky = float(result.get('quirky_interest', 50))
                economic = float(result.get('economic_importance', 50))
                political = float(result.get('political_importance', 50))
                
                # Clamp each dimension to 1-100
                historical = max(1.0, min(100.0, historical))
                cultural = max(1.0, min(100.0, cultural))
                quirky = max(1.0, min(100.0, quirky))
                economic = max(1.0, min(100.0, economic))
                political = max(1.0, min(100.0, political))
                
                # Average the five dimensions (each already clamped to 1-100)
                # Since each dimension is 1-100, average will be 1-100
                average = (historical + cultural + quirky + economic + political) / 5.0
                
                # Map 1-100 average to 1-9 range: (average - 1) / 99 * 8 + 1
                # This formula ensures: average=1 -> score=1, average=100 -> score=9
                score = ((average - 1.0) / 99.0) * 8.0 + 1.0
                
                reasoning = result.get('reasoning', 'No reasoning provided')
                if not reasoning or reasoning == 'No reasoning provided':
                    # Build reasoning from dimension scores
                    reasoning = f"Historical: {historical:.0f}/100, Cultural: {cultural:.0f}/100, Quirky: {quirky:.0f}/100, Economic: {economic:.0f}/100, Political: {political:.0f}/100. Average: {average:.1f}/100."
                
                relevant = result.get('relevant', score >= DEFAULT_SUITABILITY_THRESHOLD)
                
                return {
                    'suitability_score': round(score, 1),
                    'suitability_notes': reasoning[:500],  # Limit length
                    'relevant': bool(relevant),
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                raise ValueError(f"Could not parse LLM JSON response: {e}. Response was: {response[:500]}")
        
        # If we can't extract JSON, raise error
        raise ValueError(f"LLM response did not contain valid JSON. Response: {response[:500]}")
        
    except Exception as e:
        logger.error(f"Error in LLM suitability analysis: {e}", exc_info=True)
        raise  # Re-raise exception - no fallback




def analyze_item(item: Dict[str, Any], cache_results: bool = True) -> Dict[str, Any]:
    """Analyze a normalized source item for suitability.
    
    Args:
        item: Normalized item dict with title, description, url, etc.
        cache_results: If True, check cache and store results
    
    Returns:
        Updated item dict with suitability_score and suitability_notes
    """
    # Only analyze news category items
    if item.get('category') != 'news':
        return item
    
    title = item.get('title', '')
    description = item.get('description') or item.get('raw_data', {}).get('description', '')
    url = item.get('url')
    
    if not title:
        return item
    
    # Check cache if enabled
    if cache_results:
        cached_score = _get_cached_suitability(url or title)
        if cached_score:
            item['suitability_score'] = cached_score['suitability_score']
            item['suitability_notes'] = cached_score['suitability_notes']
            return item
    
    # Run analysis
    result = analyze_news_suitability(title, description, url)
    
    # Store results
    item['suitability_score'] = result['suitability_score']
    item['suitability_notes'] = result['suitability_notes']
    
    # Cache result if enabled
    if cache_results and url:
        _cache_suitability(url, result)
    
    return item


def _get_cached_suitability(url_or_title: str) -> Optional[Dict[str, Any]]:
    """Get cached suitability result from database."""
    try:
        from config.database import db_manager
        import hashlib
        
        # Hash URL/title for lookup
        lookup_hash = hashlib.sha256(url_or_title.encode('utf-8')).hexdigest()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT suitability_score, suitability_notes
                    FROM newsletter_source_item
                    WHERE source_url_hash = %s
                    AND suitability_score IS NOT NULL
                    LIMIT 1
                """, (lookup_hash,))
                
                row = cur.fetchone()
                if row:
                    return {
                        'suitability_score': row['suitability_score'],
                        'suitability_notes': row['suitability_notes'],
                    }
    except Exception as e:
        logger.debug(f"Error checking suitability cache: {e}")
    
    return None


def _cache_suitability(url: str, result: Dict[str, Any]) -> None:
    """Cache suitability result in database."""
    try:
        from config.database import db_manager
        import hashlib
        
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE newsletter_source_item
                    SET suitability_score = %s, suitability_notes = %s
                    WHERE source_url_hash = %s
                """, (result['suitability_score'], result['suitability_notes'], url_hash))
                conn.commit()
    except Exception as e:
        logger.debug(f"Error caching suitability result: {e}")

