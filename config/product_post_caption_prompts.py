"""
Product Post Caption Generation Prompts
System prompt and variation library for product post caption generation
"""

# System Prompt (always used)
SYSTEM_PROMPT = """You are a social media marketing expert for CLAN.com, a Scottish heritage and culture e-commerce site.

Your task is to generate engaging Facebook captions for product promotion posts.

RULES (ALWAYS FOLLOW):
- Warm, professional Scottish tone that reflects heritage and craftsmanship
- Highlight product's key features and benefits
- Include a clear call-to-action directing people to the product URL
- Use appropriate emojis (1-3 max) to enhance engagement
- Do NOT include the price in the post
- Keep it concise but informative (2-4 sentences)
- Focus on Scottish heritage, quality, and cultural significance
- Make it feel personal and authentic, not overly salesy

OUTPUT FORMAT:
Return ONLY the caption text, no JSON, no additional formatting.
The caption should be ready to post directly to Facebook."""

# Variation Library (20-30 style prompts for product posts)
VARIATION_PROMPTS = [
    {
        'id': 1,
        'style': 'heritage',
        'prompt': 'Emphasize the Scottish heritage and traditional craftsmanship of this product.'
    },
    {
        'id': 2,
        'style': 'quality',
        'prompt': 'Highlight the quality and attention to detail in this product.'
    },
    {
        'id': 3,
        'style': 'gift',
        'prompt': 'Position this as a perfect gift for someone who loves Scottish culture.'
    },
    {
        'id': 4,
        'style': 'storytelling',
        'prompt': 'Tell a brief story about how this product connects to Scottish traditions.'
    },
    {
        'id': 5,
        'style': 'practical',
        'prompt': 'Focus on the practical uses and benefits of this product.'
    },
    {
        'id': 6,
        'style': 'celebration',
        'prompt': 'Celebrate Scottish culture and identity through this product.'
    },
    {
        'id': 7,
        'style': 'connection',
        'prompt': 'Emphasize how this product helps people connect with their Scottish roots.'
    },
    {
        'id': 8,
        'style': 'craftsmanship',
        'prompt': 'Highlight the skilled craftsmanship and traditional techniques used.'
    },
    {
        'id': 9,
        'style': 'collection',
        'prompt': 'Suggest this as a great addition to a Scottish heritage collection.'
    },
    {
        'id': 10,
        'style': 'occasion',
        'prompt': 'Position this for a specific Scottish occasion or celebration.'
    },
    {
        'id': 11,
        'style': 'authenticity',
        'prompt': 'Emphasize the authentic Scottish design and cultural significance.'
    },
    {
        'id': 12,
        'style': 'timeless',
        'prompt': 'Highlight how this product represents timeless Scottish style.'
    },
    {
        'id': 13,
        'style': 'family',
        'prompt': 'Appeal to families wanting to pass down Scottish traditions.'
    },
    {
        'id': 14,
        'style': 'pride',
        'prompt': 'Celebrate Scottish pride and identity through this product.'
    },
    {
        'id': 15,
        'style': 'versatility',
        'prompt': 'Show how versatile this product is for different uses.'
    },
    {
        'id': 16,
        'style': 'tradition',
        'prompt': 'Connect this product to long-standing Scottish traditions.'
    },
    {
        'id': 17,
        'style': 'modern',
        'prompt': 'Show how this product brings Scottish heritage into modern life.'
    },
    {
        'id': 18,
        'style': 'detail',
        'prompt': 'Focus on the intricate details and design elements.'
    },
    {
        'id': 19,
        'style': 'community',
        'prompt': 'Appeal to the Scottish community and shared cultural values.'
    },
    {
        'id': 20,
        'style': 'exclusivity',
        'prompt': 'Position this as a special, unique piece for Scottish heritage enthusiasts.'
    },
    {
        'id': 21,
        'style': 'history',
        'prompt': 'Connect this product to Scottish history and cultural evolution.'
    },
    {
        'id': 22,
        'style': 'elegance',
        'prompt': 'Emphasize the elegance and sophistication of this product.'
    },
    {
        'id': 23,
        'style': 'durability',
        'prompt': 'Highlight the durability and lasting quality of this product.'
    },
    {
        'id': 24,
        'style': 'personalization',
        'prompt': 'Show how this product can be personalized or made special.'
    },
    {
        'id': 25,
        'style': 'ceremony',
        'prompt': 'Position this for formal Scottish ceremonies or events.'
    },
    {
        'id': 26,
        'style': 'everyday',
        'prompt': 'Show how this product fits into everyday Scottish life.'
    },
    {
        'id': 27,
        'style': 'artisan',
        'prompt': 'Emphasize the artisan-made quality and traditional methods.'
    },
    {
        'id': 28,
        'style': 'symbolism',
        'prompt': 'Explain the symbolic meaning and cultural significance.'
    },
    {
        'id': 29,
        'style': 'treasure',
        'prompt': 'Position this as a treasured piece for Scottish heritage lovers.'
    },
    {
        'id': 30,
        'style': 'legacy',
        'prompt': 'Connect this product to preserving Scottish legacy for future generations.'
    }
]


def get_variation_prompt(style_id: int) -> dict:
    """
    Get variation prompt by ID.
    
    Parameters
    ----------
    style_id:
        ID of the variation prompt (1-30).
    
    Returns
    -------
    Dict with 'id', 'style', and 'prompt' keys.
    """
    return next(
        (p for p in VARIATION_PROMPTS if p['id'] == style_id),
        VARIATION_PROMPTS[0]  # Default to first if not found
    )
