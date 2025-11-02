"""Service for classifying events as annually recurring or one-off occasions."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, Optional
import json
import re

logger = logging.getLogger(__name__)


def classify_event_recurrence(event_data: Dict[str, Any]) -> str:
    """Classify an event as 'annual' (annually recurring) or 'one_off' (special occasion).
    
    Args:
        event_data: Event dict with:
            - title: str (event title)
            - date_text: str (original date text from source)
            - recurring_info: Optional[str] (parsed recurring pattern)
            - description/summary: Optional[str] (event description)
            - location: Optional[str] (event location)
            - source_name: Optional[str] (where event came from)
    
    Returns:
        'annual' if the event recurs every year, 'one_off' if it's a special/one-time occasion
    """
    # Import LLM service
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from app.llm.services import LLMService
        llm_service = LLMService()
    except ImportError:
        from modules.llm_service import LLMService
        llm_service = LLMService()
    
    title = event_data.get('title', '')
    date_text = event_data.get('date_text', '')
    recurring_info = event_data.get('recurring_info')
    description = event_data.get('description', '') or event_data.get('summary', '')
    location = event_data.get('location', '')
    
    # Quick heuristic checks first (can bypass LLM in clear cases)
    # If we have explicit recurring_info, it's likely annual
    if recurring_info and recurring_info.lower() not in ('null', 'none', ''):
        # But check if it's actually annual (not "every second week" which is different)
        if 'annual' in recurring_info.lower() or 'year' in recurring_info.lower():
            return 'annual'
        if 'every second' in recurring_info.lower() or 'every week' in recurring_info.lower():
            # These are not annual - they're more frequent
            return 'one_off'  # Weekly patterns are special occurrences, not annual festivals
    
    # Check title for obvious annual festival indicators
    title_lower = title.lower()
    annual_keywords = [
        'festival', 'festival', 'highland games', 'gathering', 'tattoo',
        'book festival', 'folk festival', 'music festival', 'celtic festival',
        'hogmanay', 'up helly aa', 'royal', 'highland show'
    ]
    
    if any(keyword in title_lower for keyword in annual_keywords):
        # Most festivals are annual, but use LLM for nuanced cases
        pass  # Continue to LLM for final decision
    
    # Build prompt for LLM classification
    prompt = f"""Classify this Scottish event as either ANNUALLY RECURRING or ONE-OFF OCCASION.

Event Title: {title}
Date Text: {date_text if date_text else '(no date info)'}
Recurring Info: {recurring_info if recurring_info else '(none)'}
Location: {location if location else '(none)'}
Description: {description[:200] if description else '(none)'}

ANNUALLY RECURRING means:
- The event happens every year around the same time (e.g., Edinburgh's Hogmanay, Royal Highland Show)
- Well-established festivals that recur annually (e.g., Celtic Connections, Wigtown Book Festival)
- Traditional annual celebrations (e.g., Up Helly Aa, Highland Games)
- Even if dates vary slightly, if it's clearly an annual tradition → ANNUAL

ONE-OFF OCCASION means:
- Special exhibitions with specific dates that won't repeat (e.g., "Maps: Memories from the Second World War")
- Temporary museum exhibitions (e.g., "Decoding the Jewels", "Seeds of Time: Scottish Gardens")
- One-time events, launches, or special occasions
- Walking tours or activities that are not annual traditions
- Events tied to specific anniversaries or commemorations that won't repeat

Examples:
- "Celtic Connections" → ANNUAL (annual music festival)
- "Edinburgh's Hogmanay" → ANNUAL (annual New Year celebration)
- "Royal Highland Show" → ANNUAL (annual agricultural show)
- "Wigtown Book Festival" → ANNUAL (annual book festival)
- "Up Helly Aa" → ANNUAL (annual Shetland fire festival)
- "Maps: Memories from the Second World War" → ONE_OFF (specific exhibition)
- "Decoding the Jewels" → ONE_OFF (temporary exhibition)
- "Ring of Brodgar Walk" → ONE_OFF (walking tour, not annual festival)
- "The Eagle and the Unicorn" → ONE_OFF (special exhibition)

Return ONLY a single word: either "annual" or "one_off". No explanations, no JSON, just the word."""

    try:
        model_name = os.environ.get('DEFAULT_LLM_MODEL', 'llama3.2:latest')
        # LLMService uses 'generate' method
        response = llm_service.generate(
            prompt=prompt,
            model_name=model_name,
            temperature=0.1,  # Very low temperature for consistent classification
            max_tokens=10
        )
        
        if not response:
            # Fallback: use heuristic
            return _classify_heuristic(event_data)
        
        # Extract classification from response
        response_lower = response.strip().lower()
        
        if 'annual' in response_lower or response_lower == 'annual':
            return 'annual'
        elif 'one_off' in response_lower or 'one-off' in response_lower or 'oneoff' in response_lower:
            return 'one_off'
        else:
            # Fallback to heuristic if LLM response unclear
            logger.warning(f"Unclear LLM classification response: {response}, using heuristic")
            return _classify_heuristic(event_data)
            
    except Exception as e:
        logger.error(f"Error in LLM classification: {e}", exc_info=True)
        # Fallback to heuristic
        return _classify_heuristic(event_data)


def _classify_heuristic(event_data: Dict[str, Any]) -> str:
    """Fallback heuristic classification when LLM is unavailable."""
    title = event_data.get('title', '').lower()
    recurring_info = event_data.get('recurring_info', '').lower() if event_data.get('recurring_info') else ''
    
    # Annual indicators
    annual_patterns = [
        'festival', 'highland games', 'gathering', 'tattoo',
        'hogmanay', 'up helly aa', 'royal highland show',
        'book festival', 'folk festival', 'music festival', 'celtic',
        'connections', 'highland show', 'military tattoo'
    ]
    
    # One-off indicators
    one_off_patterns = [
        'exhibition', 'walk', 'tour', 'memories', 'decoding',
        'make a', 'member event', 'test event'
    ]
    
    # Check for annual patterns
    if any(pattern in title for pattern in annual_patterns):
        return 'annual'
    
    # Check for one-off patterns
    if any(pattern in title for pattern in one_off_patterns):
        return 'one_off'
    
    # Default to annual for festivals (conservative)
    if 'festival' in title:
        return 'annual'
    
    # Default to one-off for unclear cases
    return 'one_off'

