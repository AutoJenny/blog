"""
Weekly Content Caption Generator
Generates Facebook captions using Ollama with variation library
"""

import json
import random
import re
import logging
from typing import Dict, Optional
from blueprints.planning_llm import LLMService
from config.weekly_content_caption_prompts import (
    SYSTEM_PROMPT,
    VARIATION_PROMPTS,
    get_variation_prompt
)

logger = logging.getLogger(__name__)


def generate_weekly_content_caption(
    category: str,
    scots_text: str,
    translation: str,
    notes: Optional[str] = None,
    variation_seed: Optional[int] = None,
    prompt_style_id: Optional[int] = None
) -> Dict:
    """
    Generate caption using Ollama with variation library.
    
    Parameters
    ----------
    category:
        Content category ('weekly_word', 'weekly_phrase', or 'weekly_insult').
    scots_text:
        The Scots text/phrase/word.
    translation:
        English translation of the Scots text.
    notes:
        Optional notes/provenance from calendar_ideas.
    variation_seed:
        Optional seed for random variation selection (for reproducibility).
    prompt_style_id:
        Optional specific prompt style ID to use (1-30). If None, selects randomly.
    
    Returns
    -------
    Dict with:
    {
        'caption': 'Main caption',
        'pinned_comment': 'Optional comment',
        'alt_caption_1': 'Alternative 1',
        'alt_caption_2': 'Alternative 2',
        'chosen_prompt_style_id': 3,
        'variation_seed': 42,
        'ollama_model': 'llama3.2:latest'
    }
    
    Raises
    ------
    Exception:
        If Ollama call fails or response cannot be parsed.
    """
    # Select variation prompt
    if prompt_style_id:
        variation = get_variation_prompt(prompt_style_id)
    else:
        # Random selection (use seed if provided)
        if variation_seed:
            random.seed(variation_seed)
        variation = random.choice(VARIATION_PROMPTS)
        prompt_style_id = variation['id']
    
    if variation_seed is None:
        variation_seed = random.randint(1, 1000)
    
    # Build user prompt
    category_label = category.replace('weekly_', '').replace('_', ' ').title()
    
    user_prompt = f"""Generate a Facebook caption for this weekly {category_label}.

Category: {category}
Scots Text: {scots_text}
Translation: {translation}
Notes: {notes or 'None provided'}

Style: {variation['style']}
Variation Seed: {variation_seed}

{variation['prompt']}"""
    
    # Call Ollama
    llm_service = LLMService()
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_prompt}
    ]
    
    try:
        response = llm_service.execute_llm_request(
            'ollama',
            'llama3.2:latest',
            messages,
            max_tokens=500,  # Short captions
            temperature=0.8  # Slightly creative but controlled
        )
        
        if 'error' in response:
            raise Exception(f"Ollama error: {response['error']}")
        
        # Parse JSON response
        content = response.get('content', '').strip()
        
        if not content:
            raise Exception("Empty response from Ollama")
        
        # Extract JSON from response (handle cases where LLM adds extra text)
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_text = json_match.group(0)
        else:
            json_text = content
        
        try:
            captions = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}. Response was: {content[:200]}")
            # Fallback: create simple caption
            captions = {
                'caption': f"Did you know this {category.replace('weekly_', '')}? {scots_text} means '{translation}'.",
                'pinned_comment': None,
                'alt_caption_1': None,
                'alt_caption_2': None
            }
        
        # Validate caption structure
        if not isinstance(captions, dict):
            raise ValueError(f"Expected dict, got {type(captions)}")
        
        # Select one caption (prefer main caption)
        selected_caption = (
            captions.get('caption') or 
            captions.get('alt_caption_1') or 
            captions.get('alt_caption_2') or
            f"Did you know this {category.replace('weekly_', '')}? {scots_text} means '{translation}'."
        )
        
        return {
            'caption': selected_caption,
            'pinned_comment': captions.get('pinned_comment'),
            'alt_caption_1': captions.get('alt_caption_1'),
            'alt_caption_2': captions.get('alt_caption_2'),
            'chosen_prompt_style_id': prompt_style_id,
            'variation_seed': variation_seed,
            'ollama_model': 'llama3.2:latest'
        }
        
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        # Return fallback caption
        return {
            'caption': f"Did you know this {category.replace('weekly_', '')}? {scots_text} means '{translation}'.",
            'pinned_comment': None,
            'alt_caption_1': None,
            'alt_caption_2': None,
            'chosen_prompt_style_id': prompt_style_id or 1,
            'variation_seed': variation_seed or 1,
            'ollama_model': 'llama3.2:latest',
            'error': str(e)
        }
