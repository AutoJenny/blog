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
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
        from app.llm.services import LLMService
        llm_service = LLMService()
    except ImportError:
        try:
            from modules.llm_service import LLMService
            llm_service = LLMService()
        except ImportError:
            logger.error("Could not import LLMService - suitability analysis will use fallback")
            return _fallback_suitability_analysis(title, description)
    
    # Construct prompt for content analysis
    prompt = f"""You are analyzing news articles for a Scottish heritage and culture newsletter with a primarily US-Scots diaspora audience - people of Scottish descent living in the United States, Canada, Australia, and other countries who maintain an interest in the history and culture of their "old country".

Imagine a typical reader: someone of Scottish descent living in the US, with family connections to Scotland, interested in learning about the "old country" - its history, culture, traditions, and contemporary developments that matter.

Article Title: {title}
{f"Description: {description[:500]}" if description else ""}

Rate this article on FIVE separate dimensions, each on a scale of 1-100 (use the FULL range, be nuanced):

1. HISTORICAL INTEREST (1-100): How interesting is this from a historical perspective? Does it reveal something about Scotland's past, heritage sites, archaeology, historical figures, or preservation of historical artifacts/buildings?

2. CULTURAL INTEREST (1-100): How interesting is this from a cultural perspective? Does it relate to Scottish traditions, language, music, literature, arts, festivals, or cultural identity?

3. QUIRKY INTEREST (1-100): How interesting is this from a quirky/unique perspective? Does it have an unusual angle, local color, human interest, or something charmingly Scottish that would make diaspora readers smile?

4. ECONOMIC IMPORTANCE (1-100): How significant is this economically? Does it affect Scotland's economy, businesses, tourism, industry, or economic development in ways diaspora might care about?

5. POLITICAL IMPORTANCE (1-100): How significant is this politically? Does it relate to Scottish governance, devolution, independence, or political developments that matter beyond daily party politics?

For each dimension, use the FULL 1-100 range thoughtfully:
- Low scores (1-30): Minimal relevance to this dimension
- Moderate scores (31-60): Some relevance but not compelling
- High scores (61-80): Strong relevance, would genuinely interest diaspora readers
- Very high scores (81-100): Exceptional relevance, compelling and significant

Be nuanced and thoughtful. A story about a local council decision might score: Historical=15, Cultural=20, Quirky=30, Economic=25, Political=40 (average=26 → score 2.6).

A story about preserving a historic Highland estate might score: Historical=85, Cultural=75, Quirky=60, Economic=45, Political=30 (average=59 → score 5.9).

A major archaeological discovery might score: Historical=95, Cultural=80, Quirky=70, Economic=50, Political=20 (average=63 → score 6.3).

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
        # Use LLM to analyze
        response = llm_service.generate(
            prompt=prompt,
            model_name=os.environ.get('DEFAULT_LLM_MODEL', 'llama3.1:70b'),
            temperature=0.3,  # Lower temperature for more consistent scoring
            max_tokens=300
        )
        
        if not response:
            logger.warning("LLM returned empty response for suitability analysis")
            return _fallback_suitability_analysis(title, description)
        
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
                logger.warning(f"Could not parse LLM JSON response: {e}")
        
        # Fallback: try to extract dimension scores from text
        # Look for patterns like "historical_interest: 75" or "historical: 75"
        historical = 50.0
        cultural = 50.0
        quirky = 50.0
        economic = 50.0
        political = 50.0
        
        for key in ['historical', 'cultural', 'quirky', 'economic', 'political']:
            pattern = rf'{key}["\s:]*(\d+\.?\d*)'
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if key == 'historical':
                    historical = max(1.0, min(100.0, val))
                elif key == 'cultural':
                    cultural = max(1.0, min(100.0, val))
                elif key == 'quirky':
                    quirky = max(1.0, min(100.0, val))
                elif key == 'economic':
                    economic = max(1.0, min(100.0, val))
                elif key == 'political':
                    political = max(1.0, min(100.0, val))
        
        # Calculate score from dimensions (each already clamped to 1-100)
        average = (historical + cultural + quirky + economic + political) / 5.0
        score = ((average - 1.0) / 99.0) * 8.0 + 1.0
        
        return {
            'suitability_score': round(score, 1),
            'suitability_notes': response[:500],
            'relevant': score >= DEFAULT_SUITABILITY_THRESHOLD,
        }
        
        # Complete fallback
        return _fallback_suitability_analysis(title, description)
        
    except Exception as e:
        logger.error(f"Error in LLM suitability analysis: {e}", exc_info=True)
        return _fallback_suitability_analysis(title, description)


def _fallback_suitability_analysis(title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Fallback keyword-based suitability analysis when LLM is unavailable."""
    scottish_keywords = [
        'scotland', 'scottish', 'scots', 'scot', 'edinburgh', 'glasgow', 
        'highlands', 'highland', 'aberdeen', 'inverness', 'dundee', 
        'scotland\'s', 'heritage', 'tartan', 'kilt', 'celtic', 'gaelic',
        'loch', 'isle', 'hebrides', 'orkney', 'shetland', 'border',
        'clan', 'castle', 'whisky', 'whiskey', 'scotch', 'st andrews',
        'bagpipe', 'haggis', 'burns', 'robert burns', 'braveheart',
        'bonnie', 'dreich', 'wee', 'braw', 'ken', 'aye', 'och'
    ]
    
    text_to_check = f"{title} {description or ''}".lower()
    
    # Count keyword matches
    matches = sum(1 for keyword in scottish_keywords if keyword in text_to_check)
    
    # Simple scoring: 1 point per keyword match, max 7
    score = min(7.0, matches * 1.2)
    
    # Boost score if multiple keywords
    if matches >= 3:
        score += 0.5
    if matches >= 5:
        score += 0.5
    
    score = min(9.0, max(1.0, score))  # Clamp to 1-9 range
    
    return {
        'suitability_score': round(score, 1),
        'suitability_notes': f'Keyword-based analysis: {matches} Scottish keywords found',
        'relevant': score >= DEFAULT_SUITABILITY_THRESHOLD,
    }


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

