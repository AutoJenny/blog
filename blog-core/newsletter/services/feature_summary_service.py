"""Service for generating chatty feature block summaries from post content."""

from __future__ import annotations

from typing import Any, Dict, Optional
from blueprints.header.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)


def generate_feature_summary(title: str, expanded_idea: str) -> str:
    """Generate a chatty, conversational summary for a featured blog post.
    
    Uses the post title and expanded idea to create a newsletter-style summary
    that sounds like the newsletter writer sharing what they found interesting.
    
    Args:
        title: Post title
        expanded_idea: Post expanded idea/content outline
    
        Returns:
        Chatty summary (exactly 2 short paragraphs, 100-120 words total)
    """
    if not title:
        return ""
    
    if not expanded_idea:
        # Fallback if no expanded idea
        return f"This week's theme and our latest blog post feature is {title}.\n\nIt's a fascinating topic that we think you'll find interesting."
    
    llm_service = LLMService()
    
    system_prompt = """You are writing a chatty summary/commentary of a blog post for a Scottish heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, observational tone - like you're sharing something interesting you've discovered with a friend.
This is NOT a summary of the post - it's the newsletter writer's voice sharing what they found interesting about the topic.

IMPORTANT CONTEXT:
- This post is the theme of the week and our latest blog post feature
- Mention this near the start of your commentary (in the first paragraph)
- DO NOT repeat the post title in your text - it's already displayed above

REQUIREMENTS:
- Write EXACTLY 2 short paragraphs (no more, no less)
- Each paragraph should be 3-4 sentences
- Aim for 100-120 words TOTAL (not per paragraph - TOTAL)
- Keep it engaging and informative - this is a teaser that should give readers a good sense of what the post covers
- Focus on what's interesting or notable about this topic
- Natural, conversational language - not formal or academic
- Avoid just repeating the expanded idea - use it as information to create your own commentary
- Keep enthusiasm moderate - avoid being overly hyperbolic or overenthusiastic

Tone: Warm, chatty, like talking to a friend about something interesting you discovered. Moderate enthusiasm - not overly excited."""
    
    user_prompt = f"""Post Title: {title}

Expanded Idea/Content Outline:
{expanded_idea}

This post is our theme of the week and latest blog post feature. Write EXACTLY 2 paragraphs (each 3-4 sentences, 100-120 words TOTAL) in a chatty, conversational style.
IMPORTANT: Do NOT repeat the post title in your text - it's already shown above.
In the first paragraph, mention that this is our theme of the week and latest blog post feature.
Share what's interesting about this topic from the newsletter writer's perspective.
Don't just summarize - comment on what makes it notable or engaging.
Write naturally, like you're chatting with a friend about something you've learned.
Keep it informative and engaging - this is a teaser that should give readers a good sense of what the post covers.
Keep your tone moderate - avoid being overly enthusiastic or hyperbolic.

Your response should be EXACTLY 2 paragraphs separated by a blank line, nothing else.
Aim for 100-120 words total."""
    
    try:
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        # Use Ollama by default (local, fast)
        result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
        
        if 'error' in result:
            logger.error(f"LLM error generating feature summary: {result['error']}")
            # Fallback: simple summary (2 short paragraphs, 100-120 words)
            if expanded_idea:
                # Split expanded idea into 2 parts for 2 paragraphs
                words = expanded_idea.split()[:60]  # First 60 words for first para
                first_para = ' '.join(words)
                return f"This week's theme and our latest blog post feature is {title}. It's a fascinating topic that we're excited to share with you.\n\n{first_para}..."
            return f"This week's theme and our latest blog post feature is {title}.\n\nIt's a fascinating topic that we think you'll find interesting."
        
        summary = result.get('content', '').strip()
        # Clean up the response
        summary = summary.strip('"\'')
        summary = summary.strip()
        
        # Split into paragraphs (handle both \n\n and single \n)
        paragraphs = [p.strip() for p in summary.split('\n\n') if p.strip()]
        if not paragraphs:
            # Try single line breaks
            paragraphs = [p.strip() for p in summary.split('\n') if p.strip()]
        if not paragraphs:
            # No line breaks - split by sentences
            paragraphs = [summary]
        
        # If more than 2 paragraphs, take first 2
        if len(paragraphs) > 2:
            paragraphs = paragraphs[:2]
        
        # If only 1 paragraph, split at sentence boundary
        if len(paragraphs) == 1:
            sentences = [s.strip() for s in paragraphs[0].split('. ') if s.strip()]
            if len(sentences) >= 2:
                mid = len(sentences) // 2
                paragraphs = [
                    '. '.join(sentences[:mid]).strip() + '.',
                    '. '.join(sentences[mid:]).strip()
                ]
            else:
                # Single sentence - split at comma or just duplicate
                if ',' in paragraphs[0]:
                    parts = paragraphs[0].split(',', 1)
                    paragraphs = [parts[0].strip() + '.', parts[1].strip()]
                else:
                    # Can't split meaningfully - create 2 short sentences
                    words = paragraphs[0].split()[:12]
                    paragraphs = [' '.join(words) + '.', 'It\'s a fascinating topic.']
        
        # Enforce word limit (120 words max total) - but respect sentence boundaries
        all_words = []
        for para in paragraphs:
            all_words.extend(para.split())
        
        if len(all_words) > 120:
            # Rebuild paragraphs by taking complete sentences that fit within limit
            # First, collect all sentences from both paragraphs
            all_sentences = []
            for para in paragraphs:
                # Split by sentence endings
                sentences = []
                current = para
                for punct in ['. ', '! ', '? ']:
                    parts = current.split(punct)
                    for i, part in enumerate(parts[:-1]):
                        sentences.append(part.strip() + punct[0])
                    current = parts[-1]
                if current.strip():
                    sentences.append(current.strip())
                all_sentences.extend([s for s in sentences if s.strip()])
            
            # Take sentences that fit within 120 word limit
            word_count = 0
            kept_sentences = []
            for sent in all_sentences:
                sent_words = sent.split()
                if word_count + len(sent_words) <= 120:
                    kept_sentences.append(sent)
                    word_count += len(sent_words)
                else:
                    break
            
            if len(kept_sentences) >= 2:
                # Split sentences between 2 paragraphs
                mid = len(kept_sentences) // 2
                para1_sentences = kept_sentences[:mid]
                para2_sentences = kept_sentences[mid:]
                paragraphs = [
                    ' '.join(para1_sentences).strip(),
                    ' '.join(para2_sentences).strip()
                ]
            elif kept_sentences:
                # Only one sentence - duplicate or split
                paragraphs = [
                    ' '.join(kept_sentences).strip(),
                    'It\'s a fascinating topic that we think you\'ll find interesting.'
                ]
            else:
                # Fallback if no sentences fit
                paragraphs = [
                    'We\'re exploring this topic this week.',
                    'It\'s a fascinating topic that we think you\'ll find interesting.'
                ]
        
        # Ensure exactly 2 paragraphs
        while len(paragraphs) < 2:
            paragraphs.append('It\'s a fascinating topic.')
        paragraphs = paragraphs[:2]
        
        summary = '\n\n'.join(paragraphs)
        
        # Fallback if LLM returned empty
        if not summary:
            if expanded_idea:
                words = expanded_idea.split()[:60]
                first_para = ' '.join(words)
                return f"This week's theme and our latest blog post feature is {title}. It's a fascinating topic that we're excited to share with you.\n\n{first_para}..."
            return f"This week's theme and our latest blog post feature is {title}.\n\nIt's a fascinating topic that we think you'll find interesting."
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating feature summary: {e}", exc_info=True)
        # Fallback: simple summary (2 short paragraphs, 100-120 words)
        if expanded_idea:
            words = expanded_idea.split()[:60]
            first_para = ' '.join(words)
            return f"This week's theme and our latest blog post feature is {title}. It's a fascinating topic that we're excited to share with you.\n\n{first_para}..."
        return f"This week's theme and our latest blog post feature is {title}.\n\nIt's a fascinating topic that we think you'll find interesting."

