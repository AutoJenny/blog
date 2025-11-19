"""Service for generating intro paragraph for New Products Spotlight block."""

from __future__ import annotations

from typing import Any, Dict, List
from blueprints.header.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)


def generate_products_intro(products: List[Dict[str, Any]]) -> str:
    """Generate a brief intro paragraph for the New Products Spotlight.
    
    Reviews the three selected products and writes a short paragraph from the
    newsletter editor's perspective, mentioning they're recently added.
    
    Args:
        products: List of 3 product dicts with: name, short_description, sku
    
    Returns:
        Brief intro paragraph (2-3 sentences, ~50-75 words)
    """
    if not products or len(products) == 0:
        return ""
    
    if len(products) > 3:
        products = products[:3]
    
    # Build product descriptions for LLM
    product_descriptions = []
    for i, p in enumerate(products, 1):
        name = p.get('name', 'Unknown Product')
        desc = p.get('short_description', '') or p.get('description', '')
        product_descriptions.append(f"{i}. {name}" + (f" - {desc}" if desc else ""))
    
    products_text = "\n".join(product_descriptions)
    
    llm_service = LLMService()
    
    system_prompt = """You are writing a brief intro paragraph for a "New Products Spotlight" section in a Scottish heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, conversational tone - like the newsletter editor sharing something new they've discovered.

REQUIREMENTS:
- Write ONE brief paragraph (2-3 sentences, maximum 75 words total)
- Mention that these products are recently added to the website, so readers may not be aware of them yet
- Comment briefly on the products based on their descriptions
- Keep it light and engaging - this is just a quick intro, not a detailed review
- Natural, conversational language
- Don't list product names explicitly - weave them naturally into the commentary
- Focus on what's interesting or appealing about these products as a group
- Your response should be a complete paragraph, not just punctuation or fragments"""
    
    user_prompt = f"""Write a brief intro paragraph (2-3 sentences, max 75 words) for these three recently added products:

{products_text}

The paragraph should:
1. Mention that these products are recently added to the website, so readers may not be aware of them yet
2. Comment briefly on what's interesting or appealing about these products based on their descriptions
3. Keep it conversational and engaging

Write a complete paragraph - do not just respond with punctuation or fragments."""
    
    try:
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        # Use Ollama by default (local, fast)
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in result:
            logger.error(f"LLM error generating products intro: {result['error']}")
            # Fallback
            product_names = [p.get('name', 'product') for p in products]
            return f"We've recently added some new products to the website that you might not have seen yet, including {', '.join(product_names[:2])} and more. These are worth a look if you're interested in Scottish heritage items."
        
        intro = result.get('content', '').strip()
        
        # Clean up the response
        intro = intro.strip('"\'')
        intro = intro.strip()
        
        # Check if intro is valid (not just punctuation)
        if not intro or len(intro) < 10 or intro in ['.', '...', '?', '!']:
            # Fallback - create a simple intro
            product_names = [p.get('name', 'product') for p in products]
            if len(product_names) >= 2:
                return f"We've recently added some new products to the website that you might not have seen yet, including {product_names[0]} and {product_names[1]}. These are worth a look if you're interested in Scottish heritage items."
            else:
                return f"We've recently added some new products to the website that you might not have seen yet. These are worth a look if you're interested in Scottish heritage items."
        
        # Ensure it's a reasonable length (enforce max 75 words)
        words = intro.split()
        if len(words) > 75:
            # Truncate at sentence boundary if possible
            sentences = [s.strip() for s in intro.split('. ') if s.strip()]
            truncated = []
            word_count = 0
            for sentence in sentences:
                sentence_words = sentence.split()
                if word_count + len(sentence_words) <= 75:
                    truncated.append(sentence)
                    word_count += len(sentence_words)
                else:
                    break
            intro = '. '.join(truncated)
            if not intro.endswith('.'):
                intro += '.'
        
        return intro
    
    except Exception as e:
        logger.error(f"Error generating products intro: {e}", exc_info=True)
        # Fallback
        product_names = [p.get('name', 'product') for p in products]
        return f"We've recently added some new products to the website that you might not have seen yet, including {', '.join(product_names[:2])} and more. These are worth a look if you're interested in Scottish heritage items."

