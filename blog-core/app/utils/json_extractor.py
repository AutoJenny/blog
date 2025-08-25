"""
JSON extraction utilities for LLM responses.

This module provides robust functions to extract JSON from LLM responses
that may contain markdown formatting, commentary, or other non-JSON content.
"""

import json
import re
from typing import Optional, Dict, Any, Tuple


def extract_json_from_markdown(text: str) -> Optional[str]:
    """
    Extract JSON from markdown text, handling various formats.
    
    Args:
        text: Raw text that may contain JSON embedded in markdown
        
    Returns:
        Extracted JSON string if found, None otherwise
        
    Examples:
        >>> extract_json_from_markdown('Here is the result: ```json\n{"key": "value"}\n```')
        '{"key": "value"}'
        
        >>> extract_json_from_markdown('The response is: {"key": "value"} with some commentary')
        '{"key": "value"}'
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Method 1: Extract from markdown code blocks
    json_from_blocks = _extract_from_code_blocks(text)
    if json_from_blocks:
        return json_from_blocks
    
    # Method 2: Find JSON boundaries in plain text
    json_from_boundaries = _extract_from_boundaries(text)
    if json_from_boundaries:
        return json_from_boundaries
    
    # Method 3: Try to parse the entire text as JSON
    if _is_valid_json(text):
        return text
    
    return None


def _extract_from_code_blocks(text: str) -> Optional[str]:
    """Extract JSON from markdown code blocks."""
    # Pattern for ```json ... ``` or ``` ... ```
    code_block_patterns = [
        r'```json\s*\n(.*?)\n\s*```',  # ```json ... ```
        r'```\s*\n(.*?)\n\s*```',      # ``` ... ```
        r'```json\s*(.*?)\s*```',      # ```json ... ``` (single line)
        r'```\s*(.*?)\s*```',          # ``` ... ``` (single line)
    ]
    
    for pattern in code_block_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            candidate = match.strip()
            if _is_valid_json(candidate):
                return candidate
    
    return None


def _extract_from_boundaries(text: str) -> Optional[str]:
    """Find JSON by looking for opening and closing braces/brackets."""
    # Find the first { or [ and the last } or ]
    json_start = -1
    json_end = -1
    
    # Look for opening brace/bracket
    for i, char in enumerate(text):
        if char in '{[':
            json_start = i
            break
    
    if json_start == -1:
        return None
    
    # Look for closing brace/bracket from the end
    for i in range(len(text) - 1, json_start, -1):
        char = text[i]
        if char in '}]':
            json_end = i + 1
            break
    
    if json_end == -1 or json_end <= json_start:
        return None
    
    candidate = text[json_start:json_end]
    if _is_valid_json(candidate):
        return candidate
    
    return None


def _is_valid_json(text: str) -> bool:
    """Check if text is valid JSON."""
    if not text or not isinstance(text, str):
        return False
    
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def extract_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from markdown text and parse it into a Python object.
    
    Args:
        text: Raw text that may contain JSON embedded in markdown
        
    Returns:
        Parsed JSON object if found and valid, None otherwise
    """
    json_str = extract_json_from_markdown(text)
    if not json_str:
        return None
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None


def extract_json_with_fallback(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Extract JSON from text with fallback to plain text.
    
    Args:
        text: Raw text that may contain JSON embedded in markdown
        
    Returns:
        Tuple of (parsed_json, fallback_text)
        - parsed_json: Parsed JSON object if found, None otherwise
        - fallback_text: Original text if JSON parsing fails, or extracted JSON string if successful
    """
    parsed_json = extract_and_parse_json(text)
    
    if parsed_json is not None:
        # Successfully extracted and parsed JSON
        return parsed_json, text
    
    # Fallback: return original text as plain text response
    return None, text.strip() 