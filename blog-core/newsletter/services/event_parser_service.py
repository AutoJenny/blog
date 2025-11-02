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
    
    prompt = f"""You are a JSON extraction tool. Your ONLY job is to extract structured data from this event entry and return it as valid JSON. Do NOT write code, explanations, or markdown. Return ONLY the JSON object.

Event Title: {title}
Date Text (from page): {date_text}
Description: {description[:300] if description else '(none)'}
URL: {url if url else '(none)'}

Extract and return this data as JSON:

1. TITLE: Clean event title without date information or recurring patterns.
   - Remove: "9 - 12 July 2026", "Every second week", concatenated text like "FlightEvery"
   - Keep: Just the event name
   - Example: "Genesis Scottish Open - 9 - 12 July 2026" → "Genesis Scottish Open"
   - Example: "Relaxed Morning: National Museum of FlightEvery second" → "Relaxed Morning: National Museum of Flight"

2. EVENT_DATE: Start date as YYYY-MM-DD or null
   - "9 July 2026" → "2026-07-09"
   - "9 - 12 July 2026" → "2026-07-09"
   - "August 2026" → "2026-08-01"
   - "July - August 2026" → "2026-07-01"
   - Return null if cannot determine

3. END_DATE: End date as YYYY-MM-DD or null (only for date ranges)
   - "9 - 12 July 2026" → "2026-07-12"
   - "July - August 2026" → "2026-08-31"
   - Return null if not a range

4. LOCATION: Location/venue string or null
   - Extract from description or title if mentioned

5. RECURRING_INFO: Recurring pattern string or null
   - "Every second Saturday" → "Every second Saturday"
   - "Every second week" → "Every second week"
   - Return null for one-time events

6. SUMMARY: 2-3 sentence summary combining description and details

7. DATE_TEXT_PRESERVED: Original date_text exactly as provided

8. PARSING_NOTES: Brief notes on parsing uncertainties or null

CRITICAL: Return ONLY valid JSON. No markdown code blocks, no explanations, no Python code. Just the JSON object starting with {{ and ending with }}.

{{
    "title": "",
    "event_date": null,
    "end_date": null,
    "location": null,
    "recurring_info": null,
    "summary": "",
    "date_text_preserved": "",
    "parsing_notes": null
}}"""
    
    try:
        # Use available model
        model_name = os.environ.get('DEFAULT_LLM_MODEL', 'llama3.2:latest')
        # LLMService has 'generate' method
        response = llm_service.generate(
            prompt=prompt,
            model_name=model_name,
            temperature=0.2,  # Low temperature for consistent parsing
            max_tokens=600
        )
        
        if not response:
            raise ValueError("LLM returned empty response for event parsing - cannot proceed without LLM")
        
        # Parse JSON from response
        # Try multiple strategies to extract JSON
        json_text = None
        
        # Strategy 1: Try to find JSON in markdown code block
        json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_block_match:
            json_text = json_block_match.group(1)
        
        # Strategy 2: Try to find JSON object directly (may be incomplete, try to fix)
        if not json_text:
            json_match = re.search(r'\{.*', response, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                # Try to find the matching closing brace
                brace_count = json_text.count('{') - json_text.count('}')
                if brace_count > 0:
                    # Missing closing braces, try to find them in the rest of the response
                    remaining = response[json_match.end():]
                    # Count how many more braces we need
                    for i, char in enumerate(remaining):
                        if char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_text += remaining[:i+1]
                                break
                elif brace_count < 0:
                    # Too many closing braces, trim from end
                    closing_braces = abs(brace_count)
                    for _ in range(closing_braces):
                        last_brace = json_text.rfind('}')
                        if last_brace > 0:
                            json_text = json_text[:last_brace]
        
        # Strategy 3: Try to find JSON that starts the response (common pattern)
        if not json_text:
            if response.strip().startswith('{'):
                json_text = response.strip()
                # Try to balance braces
                brace_count = json_text.count('{') - json_text.count('}')
                if brace_count > 0:
                    json_text += '}' * brace_count
                elif brace_count < 0:
                    json_text = json_text.rstrip('}')
        
        if not json_text:
            raise ValueError(f"LLM response did not contain valid JSON. Response: {response[:500]}")
        
        # Remove JSON comments (// comments and /* */ comments) which break JSON parsing
        # This is a simple approach - remove // comments on lines
        lines = json_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments but preserve // in URLs
            if '//' in line and 'http' not in line.lower():
                line = line.split('//')[0].rstrip()
            cleaned_lines.append(line)
        json_text = '\n'.join(cleaned_lines)
        
        # Remove /* */ block comments
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        if json_text:
            try:
                parsed = json.loads(json_text)
                
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
                
                # Ensure title is cleaned - remove any trailing recurring patterns that might have been concatenated
                cleaned_title = parsed.get('title', title)
                
                # Aggressive cleanup for concatenated patterns like "FlightEvery" or "FlightEvery second"
                # First, fix camelCase concatenation (add space between lowercase and uppercase)
                cleaned_title = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_title)
                
                # Remove "Every" patterns at the end (with or without space before)
                cleaned_title = re.sub(r'\s*every\s+(second|week|month|year|saturday|sunday|tuesday|wednesday|thursday|friday).*$', '', cleaned_title, flags=re.IGNORECASE).strip()
                
                # Remove standalone "Every" at the end
                cleaned_title = re.sub(r'\s+every\s*$', '', cleaned_title, flags=re.IGNORECASE).strip()
                
                # Fix patterns like "Flight Every" → "Flight" (if "Every" is a separate word at end)
                if cleaned_title.lower().endswith(' every'):
                    cleaned_title = cleaned_title[:-6].strip()
                
                # Final cleanup: remove trailing dashes, colons, or spaces
                cleaned_title = re.sub(r'[\s\-:]+$', '', cleaned_title).strip()
                
                return {
                    'title': cleaned_title,
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

