"""
Weekly Content Caption Generation Prompts
System prompt and variation library for Ollama caption generation
"""

# System Prompt (always used)
SYSTEM_PROMPT = """You are a social media content specialist for a Scottish culture blog.

Your task is to generate engaging Facebook captions for weekly Scots language content.

RULES (ALWAYS FOLLOW):
- Write in clear, ordinary English (avoid Scots dialect or overly colloquial language)
- Tone should be engaging and appeal to Scottish identity and sentiment, but straightforward and natural
- Include the Scots phrase + translation
- Exactly 1 question only
- No hashtags (or at most 1)
- No obscenity
- No targeting protected traits
- Never invent "provenance" unless provided (you can say "often heard in…" only if you have notes)

OUTPUT FORMAT (STRICT JSON):
{
    "caption": "Main caption text (1 question, includes phrase + translation)",
    "pinned_comment": "Optional pinned comment",
    "alt_caption_1": "Alternative caption option 1",
    "alt_caption_2": "Alternative caption option 2"
}

Return ONLY valid JSON, no other text."""

# Variation Library (20-30 style prompts)
VARIATION_PROMPTS = [
    {
        'id': 1,
        'style': 'nostalgia',
        'prompt': 'Write in a nostalgic tone asking if their grandmother used this phrase.'
    },
    {
        'id': 2,
        'style': 'locality',
        'prompt': 'Ask where in Scotland they hear this phrase most often.'
    },
    {
        'id': 3,
        'style': 'playful',
        'prompt': 'Write playfully asking if they would dare use this phrase.'
    },
    {
        'id': 4,
        'style': 'education',
        'prompt': 'Write as an educational moment introducing a new word for their week.'
    },
    {
        'id': 5,
        'style': 'memory',
        'prompt': 'Ask what memories this phrase brings back for them.'
    },
    {
        'id': 6,
        'style': 'connection',
        'prompt': 'Ask if this phrase connects them to their Scottish heritage.'
    },
    {
        'style': 'humor',
        'id': 7,
        'prompt': 'Write with gentle humor about when this phrase might come in handy.'
    },
    {
        'id': 8,
        'style': 'curiosity',
        'prompt': 'Ask if they knew this phrase before and where they learned it.'
    },
    {
        'id': 9,
        'style': 'family',
        'prompt': 'Ask if anyone in their family uses this phrase regularly.'
    },
    {
        'id': 10,
        'style': 'regional',
        'prompt': 'Ask which part of Scotland this phrase reminds them of.'
    },
    {
        'id': 11,
        'style': 'tradition',
        'prompt': 'Write about keeping Scots language traditions alive through phrases like this.'
    },
    {
        'id': 12,
        'style': 'everyday',
        'prompt': 'Ask if they could see themselves using this phrase in everyday conversation.'
    },
    {
        'id': 13,
        'style': 'celebration',
        'prompt': 'Write about the richness of Scots language shown in this phrase.'
    },
    {
        'id': 14,
        'style': 'reflection',
        'prompt': 'Ask what this phrase tells us about Scottish culture and identity.'
    },
    {
        'id': 15,
        'style': 'sharing',
        'prompt': 'Ask if they would share this phrase with someone learning about Scottish culture.'
    },
    {
        'id': 16,
        'style': 'history',
        'prompt': 'Write about the historical roots of this phrase in Scottish language.'
    },
    {
        'id': 17,
        'style': 'modern',
        'prompt': 'Ask if this phrase still feels relevant in modern Scottish life.'
    },
    {
        'id': 18,
        'style': 'emotion',
        'prompt': 'Write about the emotional connection Scots speakers have to phrases like this.'
    },
    {
        'id': 19,
        'style': 'community',
        'prompt': 'Ask if this phrase helps them feel part of the Scottish community.'
    },
    {
        'id': 20,
        'style': 'discovery',
        'prompt': 'Write about discovering new aspects of Scots language through this phrase.'
    },
    {
        'id': 21,
        'style': 'pride',
        'prompt': 'Ask if phrases like this make them proud of their Scottish heritage.'
    },
    {
        'id': 22,
        'style': 'learning',
        'prompt': 'Write as a learning moment for those exploring Scots language.'
    },
    {
        'id': 23,
        'style': 'conversation',
        'prompt': 'Ask if they would use this phrase to start a conversation about Scottish culture.'
    },
    {
        'id': 24,
        'style': 'preservation',
        'prompt': 'Write about the importance of preserving phrases like this for future generations.'
    },
    {
        'id': 25,
        'style': 'identity',
        'prompt': 'Ask how phrases like this shape Scottish identity and culture.'
    },
    {
        'id': 26,
        'style': 'warmth',
        'prompt': 'Write about the familiarity and comfort of this Scots phrase.'
    },
    {
        'id': 27,
        'style': 'exploration',
        'prompt': 'Ask if they enjoy exploring the nuances of Scots language through phrases like this.'
    },
    {
        'id': 28,
        'style': 'connection',
        'prompt': 'Write about how this phrase connects Scots speakers across generations.'
    },
    {
        'id': 29,
        'style': 'appreciation',
        'prompt': 'Ask if they appreciate the unique character of Scots language shown in this phrase.'
    },
    {
        'id': 30,
        'style': 'celebration',
        'prompt': 'Write about the beauty and expressiveness of Scots language shown in this phrase.'
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
