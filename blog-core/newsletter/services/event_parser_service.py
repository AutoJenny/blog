"""LLM-based intelligent event parsing service.

This service uses LLM to intelligently extract and parse:
- Event dates (handles complex formats like "every second week", date ranges, etc.)
- Locations
- Titles (may contain date info that needs extraction)
- Descriptions

It converts raw event data into structured format for storage.
"""

import json
import logging
import os
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_event_with_llm(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to intelligently parse event data.
    
    Args:
        event_data: Raw event dict with:
            - title: str (event title, may contain dates)
            - url: str (event URL if available)
            - date_text: str (date text from page, may be empty)
            - description: str (event description)
            - source_url: str (page where event was found)
            - extracted_at: str (ISO timestamp)
    
    Returns:
        Parsed event dict with:
            - title: str (cleaned title without date info)
            - url: str (event URL)
            - event_date: Optional[date] (parsed start date)
            - end_date: Optional[date] (parsed end date if range)
            - date_text: str (original date text preserved)
            - location: Optional[str] (parsed location)
            - description: str (cleaned description)
            - recurring_info: Optional[str] (info about recurring patterns like "every second week")
            - summary: str (all remaining descriptive text)
            - raw_data: Dict (original raw data preserved)
    """
    # Import LLM service - MUST succeed, no fallback
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    try:
        from app.llm.services import LLMService
        llm_service = LLMService()
    except ImportError:
        from modules.llm_service import LLMService
        llm_service = LLMService()
    
    # Construct prompt for event parsing
    title = event_data.get('title', '')
    date_text = event_data.get('date_text', '')
    description = event_data.get('description', '')
    url = event_data.get('url', '')
    
    prompt = f"""You are parsing event information from a Scottish tourism website (VisitScotland). Extract structured data from this event entry.

Event Title: {title}
Date Text (from page): {date_text}
Description: {description[:300] if description else '(none)'}
URL: {url if url else '(none)'}

Your task is to extract and parse:

1. EVENT TITLE: Clean title without any date information. Remove date ranges, "every second week" type text, etc. Just the event name.
   Example: "Genesis Scottish Open - 9 - 12 July 2026" → "Genesis Scottish Open"
   Example: "Relaxed Morning: National Museum of FlightEvery second" → "Relaxed Morning: National Museum of Flight"

2. START DATE: Parse the start date if available. Can be:
   - Single date: "9 July 2026" → 2026-07-09
   - Date range start: "9 - 12 July 2026" → 2026-07-09
   - Month only: "August 2026" → 2026-08-01 (first of month)
   - Month range: "July - August 2026" → 2026-07-01
   - Today's year assumed if year missing
   Return as YYYY-MM-DD or null if cannot be determined

3. END DATE: Parse the end date if it's a date range.
   - "9 - 12 July 2026" → 2026-07-12
   - "15 - 18 July 2026" → 2026-07-18
   - "July - August 2026" → 2026-08-31 (last day of month)
   Return as YYYY-MM-DD or null if not a range or cannot be determined

4. LOCATION: Extract location/venue if mentioned. Examples:
   - "Renaissance Club in East Lothian" → "East Lothian" or "Renaissance Club, East Lothian"
   - "Lews Castle on the stunning island of Lewis" → "Lewis" or "Lews Castle, Lewis"
   - "Edinburgh Castle" → "Edinburgh"
   - "Glasgow Green" → "Glasgow"
   Return location string or null if not found

5. RECURRING INFO: If the event is recurring (e.g., "every second week", "every Tuesday"), extract that pattern.
   Examples:
   - "Every second Saturday" → "Every second Saturday"
   - "Every second week" → "Every second week"
   - "Relaxed Morning... Every second" → "Every second week" (likely pattern)
   Return recurring pattern string or null if one-time event

6. SUMMARY: Combine all descriptive text (description + any details from title/date_text) into a single summary field.
   Preserve all useful information but make it concise (2-3 sentences max).

7. DATE TEXT PRESERVED: Keep the original date_text exactly as extracted from page (for reference).

IMPORTANT:
- If title contains date info (like "9 - 12 July 2026"), extract it and remove from cleaned title
- Handle complex formats: "World Pipe Band Championships - August 2026" (month only, no specific dates)
- If year is missing, assume current year (2025) or next year if month has passed
- Be intelligent about date ranges - "9 - 12 July" means July 9th to 12th
- "July - August 2026" means the event spans both months

Provide your response in JSON format:
{{
    "title": "<cleaned event title>",
    "event_date": "<YYYY-MM-DD or null>",
    "end_date": "<YYYY-MM-DD or null>",
    "location": "<location string or null>",
    "recurring_info": "<recurring pattern or null>",
    "summary": "<2-3 sentence summary combining all descriptive text>",
    "date_text_preserved": "<original date_text>",
    "parsing_notes": "<brief notes about what was parsed and any uncertainties>"
}}
"""
    
    try:
        # Use available model
        model_name = os.environ.get('DEFAULT_LLM_MODEL', 'llama3.2:latest')
        response = llm_service.generate(
            prompt=prompt,
            model_name=model_name,
            temperature=0.2,  # Low temperature for consistent parsing
            max_tokens=600
        )
        
        if not response:
            raise ValueError("LLM returned empty response for event parsing - cannot proceed without LLM")
        
        # Parse JSON from response
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                
                # Convert date strings to date objects
                event_date = None
                if parsed.get('event_date'):
                    try:
                        event_date = datetime.strptime(parsed['event_date'], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse event_date: {parsed.get('event_date')}")
                
                end_date = None
                if parsed.get('end_date'):
                    try:
                        end_date = datetime.strptime(parsed['end_date'], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse end_date: {parsed.get('end_date')}")
                
                return {
                    'title': parsed.get('title', title),
                    'url': url,
                    'event_date': event_date,
                    'end_date': end_date,
                    'date_text': parsed.get('date_text_preserved', date_text),
                    'location': parsed.get('location'),
                    'description': parsed.get('summary', description),
                    'recurring_info': parsed.get('recurring_info'),
                    'summary': parsed.get('summary', description),
                    'parsing_notes': parsed.get('parsing_notes', ''),
                    'raw_data': event_data,  # Preserve all original data
                }
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                raise ValueError(f"Could not parse LLM JSON response: {e}. Response was: {response[:500]}")
        
        # If we can't extract JSON, raise error
        raise ValueError(f"LLM response did not contain valid JSON. Response: {response[:500]}")
        
    except Exception as e:
        logger.error(f"Error in LLM event parsing: {e}", exc_info=True)
        # Return partial data if LLM fails
        return {
            'title': title,
            'url': url,
            'event_date': None,
            'end_date': None,
            'date_text': date_text,
            'location': None,
            'description': description,
            'recurring_info': None,
            'summary': description,
            'parsing_notes': f"LLM parsing failed: {str(e)}",
            'raw_data': event_data,
        }


def parse_events_batch(raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse a batch of raw events using LLM.
    
    Args:
        raw_events: List of raw event dicts
        
    Returns:
        List of parsed event dicts
    """
    parsed_events = []
    
    for i, event in enumerate(raw_events):
        try:
            logger.info(f"Parsing event {i+1}/{len(raw_events)}: {event.get('title', 'Unknown')[:50]}")
            parsed = parse_event_with_llm(event)
            parsed_events.append(parsed)
        except Exception as e:
            logger.error(f"Error parsing event {i+1}: {e}", exc_info=True)
            # Include partial event even if parsing failed
            parsed_events.append({
                'title': event.get('title', 'Unknown'),
                'url': event.get('url', ''),
                'event_date': None,
                'end_date': None,
                'date_text': event.get('date_text', ''),
                'location': None,
                'description': event.get('description', ''),
                'recurring_info': None,
                'summary': event.get('description', ''),
                'parsing_notes': f"Parsing failed: {str(e)}",
                'raw_data': event,
            })
    
    return parsed_events

