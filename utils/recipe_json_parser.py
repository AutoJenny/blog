"""
Recipe JSON Parser Utilities

Functions to extract and validate JSON from LLM responses for recipe sections.
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> dict:
    """
    Extract JSON object from LLM response, handling markdown code blocks and extra text.
    
    Args:
        content: Raw LLM response text
        
    Returns:
        Parsed JSON dict, or None if no valid JSON found
    """
    if not content or not isinstance(content, str):
        return None
    
    content = content.strip()
    
    # Method 1: Extract from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        json_text = json_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from code block: {json_text[:100]}")
    
    # Method 2: Find JSON object boundaries
    json_start = content.find('{')
    if json_start == -1:
        return None
    
    # Find matching closing brace by counting
    brace_count = 0
    json_end = -1
    for i in range(json_start, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    
    if json_end == -1:
        return None
    
    json_text = content[json_start:json_end]
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return None


def validate_ingredients_json(data: dict) -> bool:
    """Validate ingredients JSON structure"""
    if not isinstance(data, dict):
        return False
    if 'ingredients' not in data:
        return False
    if not isinstance(data['ingredients'], list):
        return False
    for ing in data['ingredients']:
        if not isinstance(ing, dict):
            return False
        if 'item' not in ing:
            return False
        if 'amount_imperial' not in ing or 'amount_metric' not in ing:
            return False
    return True


def validate_method_json(data: dict) -> bool:
    """Validate method JSON structure"""
    if not isinstance(data, dict):
        return False
    if 'steps' not in data:
        return False
    if not isinstance(data['steps'], list):
        return False
    for step in data['steps']:
        if not isinstance(step, dict):
            return False
        if 'number' not in step or 'instruction' not in step:
            return False
    return True


def validate_variants_json(data: dict) -> bool:
    """Validate variants JSON structure"""
    if not isinstance(data, dict):
        return False
    if 'variants' not in data:
        return False
    if not isinstance(data['variants'], list):
        return False
    for variant in data['variants']:
        if not isinstance(variant, dict):
            return False
        if 'name' not in variant or 'description' not in variant:
            return False
    return True


def validate_serving_json(data: dict) -> bool:
    """Validate serving suggestions JSON structure"""
    if not isinstance(data, dict):
        return False
    if 'serving_suggestions' not in data:
        return False
    if not isinstance(data['serving_suggestions'], list):
        return False
    return True


def validate_further_reading_json(data: dict) -> bool:
    """Validate further reading JSON structure"""
    if not isinstance(data, dict):
        return False
    if 'sources' not in data:
        return False
    if not isinstance(data['sources'], list):
        return False
    for source in data['sources']:
        if not isinstance(source, dict):
            return False
        if 'title' not in source or 'url' not in source:
            return False
    return True


def sort_ingredients_by_weight(ingredients: list) -> list:
    """
    Sort ingredients by weight (heaviest first).
    Converts all weights to grams for comparison.
    """
    def weight_to_grams(amount_str: str) -> float:
        """Convert weight string to grams"""
        if not amount_str:
            return 0.0
        
        amount_str = amount_str.strip().lower()
        
        # Extract number
        match = re.search(r'(\d+(?:\.\d+)?)', amount_str)
        if not match:
            return 0.0
        
        value = float(match.group(1))
        
        # Convert to grams based on unit
        if 'kg' in amount_str or 'kilogram' in amount_str:
            return value * 1000
        elif 'g' in amount_str or 'gram' in amount_str:
            return value
        elif 'oz' in amount_str or 'ounce' in amount_str:
            return value * 28.35
        elif 'lb' in amount_str or 'pound' in amount_str:
            return value * 453.6
        else:
            # Assume grams if no unit specified
            return value
    
    # Sort by weight (descending)
    sorted_ingredients = sorted(
        ingredients,
        key=lambda x: weight_to_grams(x.get('amount_metric', x.get('amount_imperial', ''))),
        reverse=True
    )
    
    return sorted_ingredients

