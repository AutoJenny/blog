"""LLM-based classification service for quirky news articles.

This service classifies articles as quirky/not_quirky and assigns a quirky score,
then performs a safety check to flag sensitive content.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging
import hashlib
from config.database import db_manager

logger = logging.getLogger(__name__)


def classify_quirky_article(article: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
    """Classify an article as quirky or not using LLM.
    
    Args:
        article: Article dict with title, snippet, source_name, etc.
        use_cache: Whether to use cached results
    
    Returns:
        Dict with:
        {
            'llm_class': 'quirky' | 'not_quirky' | 'uncertain',
            'llm_quirky_score': int (0-100),
            'llm_summary_raw': str,
            'safety_flag': 'none' | 'death' | 'serious_illness' | 'crime' | 'other'
        }
    """
    # Import LLM service
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from blueprints.header.llm_service import LLMService
        llm_service = LLMService()
    except ImportError:
        logger.error("Could not import LLMService")
        return {
            'llm_class': 'uncertain',
            'llm_quirky_score': 0,
            'llm_summary_raw': '',
            'safety_flag': 'none'
        }
    
    # Check cache if enabled
    if use_cache:
        cached = _get_cached_classification(article)
        if cached:
            return cached
    
    # Build prompt
    title = article.get('title', '')
    snippet = article.get('raw_data', {}).get('description', '') or article.get('raw_data', {}).get('summary', '')
    source = article.get('source_name', '')
    region = article.get('location', '') or ''
    
    system_prompt = """You are classifying Scottish local news articles for a "Round Scotland" weekly feature in a Scottish heritage newsletter.

Your task is to determine if an article is "quirky" - meaning it's light-hearted, charming, amusing, or has local human interest that would make readers smile. Think "And finally..." news - the kind of stories that are delightful rather than serious.

Classify articles as:
- "quirky": Light-hearted, amusing, charming, local interest, human interest, celebrations, community events, unusual but harmless stories
- "not_quirky": Serious news, politics, crime, business, routine announcements, standard reporting
- "uncertain": Borderline cases where you're not sure

Also assign a quirky_score from 0-100:
- 0-30: Not quirky at all
- 31-60: Somewhat quirky/interesting
- 61-80: Quirky and charming
- 81-100: Exceptionally quirky and delightful

Generate a neutral 1-2 sentence summary of the story."""

    user_prompt = f"""Classify this article:

Title: {title}
{f"Summary: {snippet[:300]}" if snippet else ""}
Source: {source}
{f"Location: {region}" if region else ""}

Respond in this exact format:
CLASS: [quirky|not_quirky|uncertain]
SCORE: [0-100]
SUMMARY: [1-2 sentence neutral summary]

Example:
CLASS: quirky
SCORE: 75
SUMMARY: Local village holds annual duck race fundraiser raising money for community hall repairs."""

    try:
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in result:
            logger.warning(f"LLM classification error: {result['error']}")
            return {
                'llm_class': 'uncertain',
                'llm_quirky_score': 0,
                'llm_summary_raw': '',
                'safety_flag': 'none'
            }
        
        response = result.get('content', '').strip()
        classification = _parse_classification_response(response)
        
        # Perform safety check
        safety_flag = _check_safety(title, snippet, classification.get('llm_summary_raw', ''))
        classification['safety_flag'] = safety_flag
        
        # Cache result if enabled
        if use_cache:
            _cache_classification(article, classification)
        
        return classification
        
    except Exception as e:
        logger.error(f"Error in quirky classification: {e}", exc_info=True)
        return {
            'llm_class': 'uncertain',
            'llm_quirky_score': 0,
            'llm_summary_raw': '',
            'safety_flag': 'none'
        }


def _parse_classification_response(response: str) -> Dict[str, Any]:
    """Parse LLM response into structured classification."""
    result = {
        'llm_class': 'uncertain',
        'llm_quirky_score': 0,
        'llm_summary_raw': ''
    }
    
    response_lower = response.lower()
    
    # Extract class
    if 'class:' in response_lower:
        class_line = [line for line in response.split('\n') if 'class:' in line.lower()][0]
        class_value = class_line.split(':', 1)[1].strip().lower()
        if 'quirky' in class_value and 'not' not in class_value:
            result['llm_class'] = 'quirky'
        elif 'not_quirky' in class_value or 'not quirky' in class_value:
            result['llm_class'] = 'not_quirky'
        else:
            result['llm_class'] = 'uncertain'
    elif 'quirky' in response_lower[:100]:
        if 'not' not in response_lower[:200]:
            result['llm_class'] = 'quirky'
        else:
            result['llm_class'] = 'not_quirky'
    
    # Extract score
    if 'score:' in response_lower:
        score_line = [line for line in response.split('\n') if 'score:' in line.lower()][0]
        try:
            score_str = score_line.split(':', 1)[1].strip()
            score = int(score_str.split()[0])  # Take first number
            result['llm_quirky_score'] = max(0, min(100, score))
        except (ValueError, IndexError):
            pass
    
    # Extract summary
    if 'summary:' in response_lower:
        summary_line = [line for line in response.split('\n') if 'summary:' in line.lower()][0]
        result['llm_summary_raw'] = summary_line.split(':', 1)[1].strip()
    else:
        # Try to extract summary from end of response
        lines = response.split('\n')
        if len(lines) > 2:
            result['llm_summary_raw'] = lines[-1].strip()
    
    return result


def _check_safety(title: str, snippet: str, summary: str) -> str:
    """Perform safety check to flag sensitive content."""
    text = f"{title} {snippet} {summary}".lower()
    
    # Death/obituary indicators
    death_keywords = ['died', 'death', 'killed', 'murdered', 'obituary', 'funeral', 'mourning']
    if any(kw in text for kw in death_keywords):
        return 'death'
    
    # Serious illness
    illness_keywords = ['cancer', 'terminal', 'illness', 'disease', 'diagnosis', 'treatment']
    if any(kw in text for kw in illness_keywords):
        return 'serious_illness'
    
    # Crime
    crime_keywords = ['arrested', 'charged', 'trial', 'court', 'sentence', 'crime', 'theft', 'assault']
    if any(kw in text for kw in crime_keywords):
        return 'crime'
    
    return 'none'


def _get_cached_classification(article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get cached classification result if available."""
    url = article.get('url', '')
    if not url:
        return None
    
    # Create hash of URL
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT llm_class, llm_quirky_score, llm_summary_raw, safety_flag
                    FROM newsletter_source_item
                    WHERE source_url_hash = %s
                    AND llm_class IS NOT NULL
                    LIMIT 1
                """, (url_hash,))
                row = cur.fetchone()
                if row:
                    return {
                        'llm_class': row[0],
                        'llm_quirky_score': row[1],
                        'llm_summary_raw': row[2] or '',
                        'safety_flag': row[3] or 'none'
                    }
    except Exception as e:
        logger.debug(f"Cache lookup failed: {e}")
    
    return None


def _cache_classification(article: Dict[str, Any], classification: Dict[str, Any]) -> None:
    """Cache classification result in database."""
    url = article.get('url', '')
    if not url:
        return
    
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE newsletter_source_item
                    SET llm_class = %s,
                        llm_quirky_score = %s,
                        llm_summary_raw = %s,
                        safety_flag = %s
                    WHERE source_url_hash = %s
                """, (
                    classification.get('llm_class'),
                    classification.get('llm_quirky_score'),
                    classification.get('llm_summary_raw'),
                    classification.get('safety_flag'),
                    url_hash
                ))
                conn.commit()
    except Exception as e:
        logger.warning(f"Failed to cache classification: {e}")

