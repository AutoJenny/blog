"""
Product Post Caption Generator
Generates Facebook captions for product posts using LLMService with variation library
"""

import random
import logging
from typing import Dict, Optional
from blueprints.llm_actions import LLMService
from config.product_post_caption_prompts import (
    SYSTEM_PROMPT,
    VARIATION_PROMPTS,
    get_variation_prompt
)

logger = logging.getLogger(__name__)


def generate_product_post_caption(
    product_name: str,
    product_description: str,
    product_url: str,
    variation_seed: Optional[int] = None,
    prompt_style_id: Optional[int] = None,
    model: str = 'mistral'
) -> Dict:
    """
    Generate caption for product post using LLMService with variation library.
    
    Parameters
    ----------
    product_name:
        Name of the product.
    product_description:
        Product description.
    product_url:
        URL to the product page.
    variation_seed:
        Optional seed for random variation selection (for reproducibility).
    prompt_style_id:
        Optional specific prompt style ID to use (1-30). If None, selects randomly.
    model:
        LLM model to use (default: 'mistral').
    
    Returns
    -------
    Dict with:
    {
        'caption': 'Main caption text',
        'chosen_prompt_style_id': 3,
        'variation_seed': 42,
        'model': 'mistral'
    }
    
    Raises
    ------
    Exception:
        If LLM call fails or response cannot be parsed.
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
    user_prompt = f"""Generate a Facebook caption for this product:

Product Name: {product_name}
Description: {product_description}
Product URL: {product_url}

Style: {variation['style']}
Variation Seed: {variation_seed}

{variation['prompt']}

Remember:
- Include a clear call-to-action directing people to the product URL
- Do NOT include the price
- Keep it concise but informative (2-4 sentences)
- Use 1-3 appropriate emojis
- Focus on Scottish heritage, quality, and cultural significance"""
    
    # Call LLM service
    llm_service = LLMService()
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_prompt}
    ]
    
    try:
        response = llm_service.execute_llm_request(
            provider='ollama',
            model=model,
            messages=messages
        )
        
        if not response or 'content' not in response:
            raise Exception("LLM service returned invalid response")
        
        caption = response['content'].strip()
        
        # Clean up caption (remove any JSON formatting if present)
        caption = caption.strip()
        if caption.startswith('"') and caption.endswith('"'):
            caption = caption[1:-1]
        if caption.startswith("'") and caption.endswith("'"):
            caption = caption[1:-1]
        
        return {
            'caption': caption,
            'chosen_prompt_style_id': prompt_style_id,
            'variation_seed': variation_seed,
            'model': model
        }
        
    except Exception as e:
        logger.error(f"Error generating product post caption: {e}")
        raise
