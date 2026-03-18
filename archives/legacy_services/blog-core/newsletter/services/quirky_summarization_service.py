"""LLM-based summarization service for quirky news highlights.

Generates newsletter-ready and social-media-ready summaries in the house style.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from config.database import db_manager

logger = logging.getLogger(__name__)


def summarize_highlight_item(item_id: int) -> Dict[str, Any]:
    """Generate summaries for a weekly highlight item.
    
    Args:
        item_id: weekly_highlights_items.id
    
    Returns:
        Dict with generated content:
        {
            'title_internal': str,
            'summary_newsletter': str,
            'summary_social': str,
            'location_label': str,
            'source_label': str
        }
    """
    # Get item and article data
    item_data = _get_item_data(item_id)
    if not item_data:
        return {'success': False, 'error': 'Item not found'}
    
    # Import LLM service
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from blueprints.header.llm_service import LLMService
        llm_service = LLMService()
    except ImportError:
        logger.error("Could not import LLMService")
        return {'success': False, 'error': 'LLM service unavailable'}
    
    # Build prompt
    article = item_data['article']
    system_prompt = """You are writing content for a Scottish heritage newsletter with a warm, engaging, conversational tone.

Generate content that is:
- Warm and friendly (like sharing news with a friend)
- Light-hearted and charming (for quirky stories)
- Respectful of Scottish culture and traditions
- Engaging for a US-Scots diaspora audience

Write in a natural, conversational style - not formal or stilted."""

    user_prompt = f"""Create newsletter content for this quirky Scottish news story:

Headline: {article.get('title', '')}
Summary: {article.get('llm_summary_raw', '')}
Source: {article.get('source_name', '')}
Location: {article.get('location', '') or 'Scotland'}
Region: {item_data.get('region', '')}

Generate:
1. TITLE_INTERNAL: A short, punchy title (not necessarily the original headline)
2. SUMMARY_NEWSLETTER: 2-3 sentences in newsletter tone (warm, conversational)
3. SUMMARY_SOCIAL: 1-2 sentences, more playful and engaging for social media
4. LOCATION_LABEL: Simple location label (e.g., "Oban, Argyll" or "Edinburgh")
5. SOURCE_LABEL: Source attribution (e.g., "Spotted in the Oban Times")

Respond in this exact format:
TITLE: [short punchy title]
NEWSLETTER: [2-3 sentence summary]
SOCIAL: [1-2 sentence playful summary]
LOCATION: [location label]
SOURCE: [source label]"""

    try:
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in result:
            logger.warning(f"LLM summarization error: {result['error']}")
            return {'success': False, 'error': result['error']}
        
        response = result.get('content', '').strip()
        summaries = _parse_summarization_response(response)
        
        # Update database
        _update_item_summaries(item_id, summaries)
        
        return {'success': True, **summaries}
        
    except Exception as e:
        logger.error(f"Error in summarization: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def _get_item_data(item_id: int) -> Dict[str, Any]:
    """Get item and article data for summarization."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT whi.id, whi.article_id, whi.position,
                       nsi.title, nsi.source_name, nsi.url, nsi.location,
                       nsi.llm_summary_raw, nsi.llm_quirky_score,
                       ns.region
                FROM weekly_highlights_items whi
                JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                LEFT JOIN newsletter_snapshot_source ns ON nsi.source_name = ns.name
                WHERE whi.id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            return {
                'item_id': row[0],
                'article_id': row[1],
                'position': row[2],
                'article': {
                    'title': row[3],
                    'source_name': row[4],
                    'url': row[5],
                    'location': row[6],
                    'llm_summary_raw': row[7],
                    'llm_quirky_score': row[8],
                },
                'region': row[9]
            }


def _parse_summarization_response(response: str) -> Dict[str, str]:
    """Parse LLM response into structured summaries."""
    result = {
        'title_internal': '',
        'summary_newsletter': '',
        'summary_social': '',
        'location_label': '',
        'source_label': ''
    }
    
    response_lower = response.lower()
    
    # Extract each field
    fields = {
        'title': 'title_internal',
        'newsletter': 'summary_newsletter',
        'social': 'summary_social',
        'location': 'location_label',
        'source': 'source_label'
    }
    
    for field_key, result_key in fields.items():
        if f'{field_key}:' in response_lower:
            lines = response.split('\n')
            for line in lines:
                if line.lower().startswith(field_key + ':'):
                    value = line.split(':', 1)[1].strip()
                    result[result_key] = value
                    break
    
    return result


def _update_item_summaries(item_id: int, summaries: Dict[str, str]) -> None:
    """Update weekly_highlights_items with generated summaries."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE weekly_highlights_items
                SET title_internal = %s,
                    summary_newsletter = %s,
                    summary_social = %s,
                    location_label = %s,
                    source_label = %s
                WHERE id = %s
            """, (
                summaries.get('title_internal'),
                summaries.get('summary_newsletter'),
                summaries.get('summary_social'),
                summaries.get('location_label'),
                summaries.get('source_label'),
                item_id
            ))
            conn.commit()

