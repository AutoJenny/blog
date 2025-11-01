"""News synopsis service for analyzing and summarizing news articles."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
import logging
import re
from datetime import datetime, timedelta, date
from config.database import db_manager

logger = logging.getLogger(__name__)


def clean_subscription_text(text: str) -> str:
    """Remove subscription marketing text, bylines, and boilerplate from article content.
    
    Args:
        text: Article text or synopsis
        
    Returns:
        Cleaned text with subscription messages and bylines removed
    """
    if not text:
        return text
    
    # Common subscription patterns (case-insensitive)
    subscription_patterns = [
        r'Did you know with a Digital Subscription to.*?much more\.\s*',
        r'Subscribe to.*?for.*?\.\s*',
        r'Get unlimited access.*?\.\s*',
        r'Sign up for.*?newsletter.*?\.\s*',
        r'Start your.*?subscription.*?\.\s*',
        r'Become a member.*?\.\s*',
        r'Join.*?for exclusive.*?\.\s*',
        r'Unlock.*?premium content.*?\.\s*',
        r'Support.*?journalism.*?subscribe.*?\.\s*',
        r'Enjoy.*?benefits.*?subscription.*?\.\s*',
    ]
    
    # Bylines and author credits (typically at start of text)
    # Order matters - more specific patterns first
    byline_patterns = [
        r'^Editor,\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+',  # e.g., "Editor, Fife Free Press "
        r'^[A-Z][a-z]+\s+Editor,\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+',  # e.g., "Lifestyle Editor, Publication Name "
        r'^[A-Z][a-z]+\s+and\s+[a-z]+\s+(?:correspondent|reporter|writer|editor)\s+',  # e.g., "Arts and culture correspondent "
        r'^[A-Z][a-z]+\s+(?:Editor|Correspondent|Reporter|Writer|Specialist|Journalist|Columnist)\s+',  # e.g., "Digital Reporter ", "Lifestyle Editor "
        r'^Golf\s+Specialist\s+',  # Specific case
        r'^Food\s+and\s+drink\s+writer\s+',  # Specific case
    ]
    
    cleaned = text
    
    # First remove bylines (at start of text)
    for pattern in byline_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Then remove subscription patterns
    for pattern in subscription_patterns:
        # Remove the pattern (case-insensitive, dotall)
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove multiple consecutive whitespace/newlines
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    
    return cleaned.strip()


def fetch_article_content(url: str) -> Optional[str]:
    """Fetch and extract main article content from a news URL.
    
    Args:
        url: Article URL
        
    Returns:
        Extracted article text content, or None if fetch fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
        }
        
        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script.decompose()
        
        # Site-specific content extraction
        content = None
        
        # BBC Scotland news
        if 'bbc.co.uk' in url or 'bbc.com' in url:
            # Try common BBC article selectors
            content_elem = soup.select_one('article, [data-component="text-block"], .story-body__inner, .ssrcss-18snukc-RichTextContainer')
            if content_elem:
                # Extract paragraphs
                paragraphs = content_elem.select('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # The Scotsman
        elif 'scotsman.com' in url:
            content_elem = soup.select_one('article, .article-content, [class*="article-body"], [class*="content"]')
            if content_elem:
                paragraphs = content_elem.select('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Generic fallback
        if not content:
            # Try common article selectors
            for selector in ['article', '[role="article"]', '.article-content', '.post-content', '.entry-content', 'main article']:
                content_elem = soup.select_one(selector)
                if content_elem:
                    paragraphs = content_elem.select('p')
                    if paragraphs:
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        break
        
        # Last resort: extract all paragraph text
        if not content:
            paragraphs = soup.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Clean up whitespace
        if content:
            content = ' '.join(content.split())
            # Remove subscription marketing text
            content = clean_subscription_text(content)
            # Limit length to avoid token limits (roughly 5000 words)
            if len(content) > 30000:
                content = content[:30000] + '...'
        
        return content
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch article content from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting article content from {url}: {e}", exc_info=True)
        return None


def generate_article_synopsis(title: str, article_content: str, url: Optional[str] = None) -> Dict[str, Any]:
    """Use LLM to analyze article and generate synopsis.
    
    Args:
        title: Article title
        article_content: Full article text content
        url: Article URL (optional)
        
    Returns:
        Dict with:
        {
            'suitability_score': float (0-10),
            'suitability_notes': str (reasoning),
            'synopsis': str (brief summary of the article),
            'relevant': bool (score >= threshold)
        }
    """
    # Import LLM service - MUST succeed, no fallback
    import os
    import sys
    
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from app.llm.services import LLMService
        llm_service = LLMService()
    except ImportError:
        from modules.llm_service import LLMService
        llm_service = LLMService()
    
    # Construct prompt for analysis and synopsis
    content_preview = article_content[:2000] if len(article_content) > 2000 else article_content
    
    prompt = f"""You are analyzing news articles for a Scottish heritage and culture newsletter with a primarily US-Scots diaspora audience - people of Scottish descent living in the United States, Canada, Australia, and other countries who maintain an interest in the history and culture of their "old country".

Imagine a typical reader: someone of Scottish descent living in the US, with family connections to Scotland, interested in learning about the "old country" - its history, culture, traditions, and contemporary developments that matter.

Article Title: {title}
{f"URL: {url}" if url else ""}

Article Content (first 2000 chars):
{content_preview}

Your task:
1. Rate this article on FIVE separate dimensions, each on a scale of 1-100. CRITICAL: Most stories should have MOST dimensions scoring 10-40. Only truly exceptional stories should have dimensions above 70. Be CRITICAL and use LOW scores liberally.

   HISTORICAL INTEREST (1-100): 
   - Scores 1-20: No historical content, just current events
   - Scores 21-40: Minor historical mention or local history
   - Scores 41-60: Some historical context
   - Scores 61-80: Substantial historical content, heritage sites, notable historical figures
   - Scores 81-100: Major historical discoveries, archaeology, preservation of national heritage

   CULTURAL INTEREST (1-100):
   - Scores 1-20: No cultural content, just daily news
   - Scores 21-40: Minor cultural mention
   - Scores 41-60: Some cultural context
   - Scores 61-80: Substantial cultural content (traditions, language, arts)
   - Scores 81-100: Major cultural significance, festivals, cultural revivals

   QUIRKY INTEREST (1-100):
   - Scores 1-20: Mundane, everyday news
   - Scores 21-40: Slightly interesting angle
   - Scores 41-60: Moderately interesting, some human interest
   - Scores 61-80: Very quirky/interesting, would make diaspora smile
   - Scores 81-100: Exceptionally quirky, charmingly Scottish

   ECONOMIC IMPORTANCE (1-100):
   - Scores 1-20: No economic significance
   - Scores 21-40: Minor local economic impact
   - Scores 41-60: Some economic relevance
   - Scores 61-80: Significant economic developments diaspora might care about
   - Scores 81-100: Major economic significance (tourism, major industries)

   POLITICAL IMPORTANCE (1-100):
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

   MOST daily news stories should have MOST dimensions in the 10-40 range. Be strict and use LOW scores!

2. Generate a brief synopsis (2-3 sentences) summarizing the key points relevant to Scottish heritage/culture from a diaspora perspective.

Provide your assessment in JSON format:
{{
    "historical_interest": <number 1-100>,
    "cultural_interest": <number 1-100>,
    "quirky_interest": <number 1-100>,
    "economic_importance": <number 1-100>,
    "political_importance": <number 1-100>,
    "reasoning": "<brief explanation of your scores for each dimension>",
    "synopsis": "<2-3 sentence summary focusing on Scottish heritage/culture relevance from diaspora perspective>",
    "relevant": <true if calculated average/10 >= 6.0, false otherwise>
}}
"""
    
    try:
        response = llm_service.generate(
            prompt=prompt,
            model_name=os.environ.get('DEFAULT_LLM_MODEL', 'llama3.1:70b'),
            temperature=0.3,
            max_tokens=500
        )
        
            if not response:
                raise ValueError("LLM returned empty response for synopsis generation - cannot proceed without LLM")
        
        # Parse JSON from response
        import json
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
                average = (historical + cultural + quirky + economic + political) / 5.0
                
                # Map 1-100 average to 1-9 range: (average - 1) / 99 * 8 + 1
                # This formula ensures: average=1 -> score=1, average=100 -> score=9
                score = ((average - 1.0) / 99.0) * 8.0 + 1.0
                
                reasoning = result.get('reasoning', 'No reasoning provided')
                if not reasoning or reasoning == 'No reasoning provided':
                    # Build reasoning from dimension scores
                    reasoning = f"Historical: {historical:.0f}/100, Cultural: {cultural:.0f}/100, Quirky: {quirky:.0f}/100, Economic: {economic:.0f}/100, Political: {political:.0f}/100. Average: {average:.1f}/100."
                
                synopsis = result.get('synopsis', 'No synopsis generated')
                relevant = result.get('relevant', score >= 6.0)
                
                # Clean subscription text from synopsis
                synopsis = clean_subscription_text(synopsis)
                
                return {
                    'suitability_score': round(score, 1),
                    'suitability_notes': reasoning[:500],
                    'synopsis': synopsis[:1000],  # Limit synopsis length
                    'relevant': bool(relevant),
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Could not parse LLM JSON response: {e}")
                # Fall through to dimension extraction fallback
        
        # Fallback: try to extract dimension scores from text
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
        
                # Extract synopsis from LLM response
                synopsis = result.get('synopsis', 'No synopsis generated')
                if not synopsis or synopsis == 'No synopsis generated':
                    raise ValueError("LLM response did not include synopsis")
                
                # Clean subscription text from synopsis
                synopsis = clean_subscription_text(synopsis)
                
                return {
                    'suitability_score': round(score, 1),
                    'suitability_notes': reasoning[:500],
                    'synopsis': synopsis[:1000],  # Limit synopsis length
                    'relevant': bool(relevant),
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                raise ValueError(f"Could not parse LLM JSON response: {e}. Response was: {response[:500]}")
        
        # If we can't extract JSON, raise error
        raise ValueError(f"LLM response did not contain valid JSON. Response: {response[:500]}")
        
    except Exception as e:
        logger.error(f"Error in LLM synopsis generation: {e}", exc_info=True)
        raise  # Re-raise exception - no fallback


def process_news_with_synopsis(item: Dict[str, Any], cache_results: bool = True) -> Optional[Dict[str, Any]]:
    """Process a news item: fetch content, analyze, generate synopsis.
    
    Args:
        item: Normalized news item with title, url, etc.
        cache_results: If True, check cache first
        
    Returns:
        Updated item with synopsis and analysis, or None if not relevant
    """
    # Only process news category items
    if item.get('category') != 'news':
        return None
    
    url = item.get('url')
    title = item.get('title', '')
    
    if not url or not title:
        return None
    
    # Check cache if enabled
    # If cache_results is False, skip cache entirely (for re-analysis)
    if cache_results:
        cached = _get_cached_news_synopsis(url)
        if cached:
            item.update(cached)
            return item if item.get('suitability_score', 0) >= 6.0 else None
    # If cache_results is False, we skip cache and continue to fresh analysis
    
    # Fetch full article content
    logger.info(f"Fetching article content from {url}")
    article_content = fetch_article_content(url)
    
    if not article_content:
        logger.warning(f"Could not fetch content from {url}")
        # Fallback to description/summary if available
        article_content = item.get('description') or item.get('raw_data', {}).get('summary', '') or item.get('raw_data', {}).get('description', '')
    
    if not article_content:
        logger.warning(f"No content available for {url}")
        return None
    
    # Generate synopsis using LLM
    logger.info(f"Generating synopsis for: {title}")
    result = generate_article_synopsis(title, article_content, url)
    
    # Note: We return the item even if below threshold - let caller decide what to do with it
    # This allows re-analysis to update ALL scores, not just those above threshold
    
    # Update item with synopsis and analysis
    # Ensure synopsis is cleaned (in case it wasn't cleaned during generation)
    synopsis = clean_subscription_text(result['synopsis'])
    
    item['suitability_score'] = result['suitability_score']
    item['suitability_notes'] = result['suitability_notes']
    item['synopsis'] = synopsis
    
    # Store synopsis in raw_data (use cleaned version)
    if 'raw_data' not in item:
        item['raw_data'] = {}
    item['raw_data']['synopsis'] = synopsis
    item['raw_data']['article_content_length'] = len(article_content)
    
    # Cache result
    if cache_results:
        _cache_news_synopsis(url, result)
    
    return item


def _get_cached_news_synopsis(url: str) -> Optional[Dict[str, Any]]:
    """Get cached synopsis from database."""
    try:
        import hashlib
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT suitability_score, suitability_notes, raw_data
                    FROM newsletter_source_item
                    WHERE source_url_hash = %s
                    AND category = 'news'
                    AND suitability_score IS NOT NULL
                    LIMIT 1
                """, (url_hash,))
                
                row = cur.fetchone()
                if row:
                    raw_data = row['raw_data'] or {}
                    return {
                        'suitability_score': row['suitability_score'],
                        'suitability_notes': row['suitability_notes'],
                        'synopsis': raw_data.get('synopsis', ''),
                    }
    except Exception as e:
        logger.debug(f"Error checking synopsis cache: {e}")
    
    return None


def _cache_news_synopsis(url: str, result: Dict[str, Any]) -> None:
    """Cache synopsis result in database."""
    try:
        import hashlib
        from psycopg.types.json import Json
        
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get existing raw_data
                cur.execute("""
                    SELECT raw_data FROM newsletter_source_item 
                    WHERE source_url_hash = %s AND category = 'news'
                    LIMIT 1
                """, (url_hash,))
                row = cur.fetchone()
                existing_raw = row['raw_data'] if row and row.get('raw_data') else {}
                
                # Merge synopsis into existing raw_data
                if not isinstance(existing_raw, dict):
                    existing_raw = {}
                existing_raw['synopsis'] = result['synopsis']
                
                cur.execute("""
                    UPDATE newsletter_source_item
                    SET suitability_score = %s, 
                        suitability_notes = %s,
                        raw_data = %s
                    WHERE source_url_hash = %s
                    AND category = 'news'
                """, (
                    result['suitability_score'],
                    result['suitability_notes'],
                    Json(existing_raw),
                    url_hash
                ))
                conn.commit()
    except Exception as e:
        logger.debug(f"Error caching synopsis: {e}")


def get_news_items(days_back: int = 7) -> List[Dict[str, Any]]:
    """Get news items from database for specified date range.
    
    Args:
        days_back: Number of days in the past to include
        
    Returns:
        List of news items with synopses
    """
    today = date.today()
    start_date = today - timedelta(days=days_back)
    
    sql = """
        SELECT DISTINCT ON (source_url_hash) 
               id, source_name, title, url, published_at, 
               suitability_score, suitability_notes, raw_data,
               signal_score, freshness_score, combined_score
        FROM newsletter_source_item
        WHERE category = 'news'
          AND published_at IS NOT NULL
          AND published_at::date >= %s
          AND source_url_hash IS NOT NULL
          AND (
            suitability_score >= 6.0
            OR suitability_score IS NULL
          )
        ORDER BY 
          source_url_hash,
          CASE WHEN suitability_score >= 6.0 THEN 0 ELSE 1 END,
          published_at DESC, 
          combined_score DESC NULLS LAST,
          id DESC
    """
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (start_date,))
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]


def generate_news_summary(days_back: int = 7, limit: int = 100, sort_by: str = 'combined_score') -> Dict[str, Any]:
    """Generate news summary from synopses.
    
    Args:
        days_back: Days to look back
        limit: Maximum number of stories to return
        sort_by: Sort key - 'combined_score', 'suitability_score', or 'published_at'
        
    Returns:
        Dict with summary and top stories
    """
    items = get_news_items(days_back=days_back)
    
    # Filter to only items that have been analyzed and passed threshold
    # Handle None values: item.get('suitability_score') can return None, so use or 0
    analyzed_items = [item for item in items if (item.get('suitability_score') or 0) >= 6.0]
    unanalyzed_count = len(items) - len(analyzed_items)
    
    if not analyzed_items:
        summary_msg = 'No relevant news stories found for this period.'
        if unanalyzed_count > 0:
            summary_msg += f' {unanalyzed_count} items need analysis. Click "Re-analyze News" to process them.'
        return {
            'generated_at': datetime.now(),
            'days_back': days_back,
            'total_stories': 0,
            'unanalyzed_count': unanalyzed_count,
            'summary_text': summary_msg,
            'top_stories': [],
            'sources': {},
        }
    
    # Group by source
    sources = {}
    for item in analyzed_items:
        source_name = item.get('source_name', 'Unknown')
        if source_name not in sources:
            sources[source_name] = []
        sources[source_name].append(item)
    
    # Sort stories based on requested sort order
    if sort_by == 'suitability_score':
        # Sort by suitability score (relevance to values) - highest first
        top_stories = sorted(analyzed_items, key=lambda x: x.get('suitability_score', 0) or 0, reverse=True)
    elif sort_by == 'published_at':
        # Sort by recency - newest first
        top_stories = sorted(analyzed_items, key=lambda x: x.get('published_at') or datetime.min, reverse=True)
    else:
        # Default: sort by combined score (relevance + freshness)
        top_stories = sorted(analyzed_items, key=lambda x: x.get('combined_score', 0) or 0, reverse=True)
    
    # Apply limit
    if limit > 0:
        top_stories = top_stories[:limit]
    
    # Generate summary text from top stories
    summary_parts = []
    if top_stories:
        summary_parts.append(f"This week we found {len(items)} relevant news stories from {len(sources)} sources.")
        
        # Group by theme/topic if possible, otherwise just list top stories
        for i, story in enumerate(top_stories[:5], 1):
            synopsis = story.get('raw_data', {}).get('synopsis', '')
            if not synopsis:
                synopsis = story.get('title', '')
            
            # Clean up synopsis - remove "Not relevant" messages
            if 'not relevant' in synopsis.lower():
                synopsis = story.get('title', '')
            
            if synopsis:
                summary_parts.append(f"{synopsis}")
    
    summary_text = ' '.join(summary_parts) if summary_parts else f'No relevant news stories found for the past {days_back} days.'
    
    return {
        'generated_at': datetime.now(),
        'days_back': days_back,
        'total_stories': len(analyzed_items),
        'unanalyzed_count': unanalyzed_count,
        'summary_text': summary_text,
        'top_stories': [
            {
                'title': s.get('title', ''),
                'url': s.get('url', ''),
                'source': s.get('source_name', ''),
                'published_at': s.get('published_at').isoformat() if s.get('published_at') else None,
                'synopsis': s.get('raw_data', {}).get('synopsis', ''),
                'suitability_score': s.get('suitability_score'),
                'combined_score': s.get('combined_score', 0),
            }
            for s in top_stories
        ],
        'sources': {
            name: len(stories) for name, stories in sources.items()
        },
    }

