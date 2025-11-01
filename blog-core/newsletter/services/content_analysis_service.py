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
    prompt = f"""You are analyzing news articles for a Scottish heritage and culture newsletter with an international diaspora audience (especially US-Scots, Canadian-Scots, Australians of Scottish descent, etc.). 

The newsletter focuses on Scottish heritage, culture, traditions, history, and topics of lasting significance. Be STRICT and use the FULL 0-10 range. Most articles should score 3-7, with 10/10 reserved for truly exceptional stories of long-term historical or cultural importance.

Article Title: {title}
{f"Description: {description[:500]}" if description else ""}

Rate the article's suitability on a scale of 0-10, with these STRICT criteria:

10: EXCEPTIONAL - Stories of lasting historical/cultural significance that would interest international diaspora:
   - Major discoveries about Scottish history, archaeology, heritage sites
   - Significant cultural revivals, language preservation, traditional arts
   - Major museum/archive acquisitions of Scottish historical importance
   - Stories about internationally known Scottish figures, landmarks, or traditions

8-9: VERY HIGH - Substantial Scottish cultural/historical content of interest beyond Scotland:
   - Important cultural events, festivals, traditions with broader appeal
   - Notable Scottish heritage sites, museums, cultural institutions
   - Stories about Scottish diaspora communities globally
   - Significant developments in Scottish arts, literature, music with cultural depth

6-7: MODERATE-HIGH - Scottish content with some broader appeal:
   - Regional news with cultural/historical context
   - Current events tied to Scottish identity or traditions
   - Community stories that reflect Scottish culture
   - Sports/cultural events of regional significance (e.g., Highland Games)

4-5: MODERATE - Local Scottish news with limited diaspora appeal:
   - Local current events, politics, local sports
   - Obituaries of regional figures (unless historically significant)
   - Daily news with Scottish setting but no cultural depth
   - Stories that happen to be in Scotland but aren't about Scottish culture

2-3: LOW - Minimal Scottish connection or purely local interest:
   - General UK news with weak Scottish angle
   - Local business, politics without cultural significance
   - Obituaries of minor local figures
   - Sports news (local teams, managers) without broader cultural context

0-1: NOT RELEVANT - No meaningful Scottish heritage/culture connection

CRITICAL DISTINCTIONS:
- "Rangers/Celtic manager news" = 4-5 (local sports interest, current event, limited diaspora appeal)
- "Former footballer dies" = 2-3 (local obituary, unless internationally known figure)
- "Archaeological discovery at Scottish castle" = 8-10 (historical significance, diaspora interest)
- "Scottish language revival program" = 8-10 (cultural significance, diaspora interest)

Use the FULL range. Average scores should be around 5. Reserve 10/10 for truly exceptional stories that would be remembered years from now. Most daily news should score 3-6.

Provide your assessment in JSON format:
{{
    "score": <number 0-10, use full range, be strict>,
    "reasoning": "<explain why this score, specifically address: (1) historical/cultural significance, (2) diaspora appeal, (3) long-term vs short-term interest>",
    "relevant": <true if score >= 6.0, false otherwise>
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
                score = float(result.get('score', 0))
                reasoning = result.get('reasoning', 'No reasoning provided')
                relevant = result.get('relevant', score >= DEFAULT_SUITABILITY_THRESHOLD)
                
                # Clamp score to 0-10
                score = max(0.0, min(10.0, score))
                
                return {
                    'suitability_score': round(score, 1),
                    'suitability_notes': reasoning[:500],  # Limit length
                    'relevant': bool(relevant),
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Could not parse LLM JSON response: {e}")
        
        # Fallback: try to extract score from text
        score_match = re.search(r'score["\s:]*(\d+\.?\d*)', response, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
            score = max(0.0, min(10.0, score))
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
    
    # Simple scoring: 1 point per keyword match, max 8
    score = min(8.0, matches * 1.5)
    
    # Boost score if multiple keywords
    if matches >= 3:
        score += 1.0
    if matches >= 5:
        score += 1.0
    
    score = min(10.0, score)
    
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

