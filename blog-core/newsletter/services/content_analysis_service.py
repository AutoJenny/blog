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

Think like a diaspora community member: What would make someone far from Scotland pause and be genuinely interested? Stories about Scottish history, archaeology, heritage sites, cultural traditions, language, music, literature, notable Scottish figures (past and present), and developments that connect to Scotland's cultural identity.

Article Title: {title}
{f"Description: {description[:500]}" if description else ""}

Rate this article's relevance on a scale of 1-9, where:
- The average score across all articles should be around 5
- Use the FULL range (1-9) - don't cluster scores at the extremes
- Score 1-2: Minimal connection - purely local current events, sports scores, minor local figures, daily politics
- Score 3-4: Some connection but limited diaspora appeal - regional news, local obituaries, current sports news
- Score 5: Moderate relevance - stories with some cultural/historical context that diaspora might find mildly interesting
- Score 6-7: Good relevance - substantial Scottish cultural/historical content, heritage stories, notable developments
- Score 8-9: High relevance - stories of lasting significance: major archaeological discoveries, cultural revivals, heritage preservation, internationally significant Scottish figures/events

Consider:
- Historical/cultural depth vs. fleeting current events
- Interest to someone thousands of miles away vs. someone living in Scotland today
- Long-term significance vs. immediate news value
- Connection to Scottish identity, heritage, traditions vs. just happening to occur in Scotland

Be thoughtful and nuanced. A local politician's daily activities might score 2, while a story about preserving a historic Highland site might score 7. A major archaeological discovery at a Scottish castle would score 8-9, while a Rangers/Celtic match result might score 3. Judge each story on its own merits considering diaspora interest in the "old country".

Provide your assessment in JSON format:
{{
    "score": <number 1-9, average around 5, use full range>,
    "reasoning": "<explain your score focusing on: (1) relevance to Scottish heritage/culture, (2) diaspora appeal from distance, (3) lasting significance vs. ephemeral news>",
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
                
                # Clamp score to 1-9 (diaspora-focused range, averaging 5)
                score = max(1.0, min(9.0, score))
                
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
            score = max(1.0, min(9.0, score))  # Clamp to 1-9 range
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

