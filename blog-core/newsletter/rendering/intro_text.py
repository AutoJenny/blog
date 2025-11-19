"""Intro text generation: combines weather/event/community items into conversational paragraph.

New approach: Weather is now a conversational summary (one sentence), and elements
are combined in varying order to create natural, chatty intro paragraphs.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional, List


def generate_intro_text(
    weather_item: Dict[str, Any] | None = None,
    event_item: Dict[str, Any] | None = None,
    community_item: Dict[str, Any] | None = None
) -> str:
    """Generate conversational intro text from selected items.
    
    New approach:
    - Weather: One conversational sentence about weekly weather patterns
    - Event: One sentence about a local event
    - Community: One sentence about community discussion
    - Order varies to keep it natural
    
    Tone: warm, chatty, conversational, like talking to a friend.
    
    Args:
        weather_item: Dict with summary_text (conversational weather summary)
        event_item: Dict with source_name, title, url, location (optional)
        community_item: Dict with source_name, title, url (optional)
    
    Returns:
        Generated intro text (2-3 sentences, naturally combined)
    """
    sentences: List[str] = []
    
    # Weather sentence (new format: already a conversational summary)
    if weather_item:
        # Check if it's the new format (has summary_text) or old format (has title)
        if 'summary_text' in weather_item:
            # New format: use the pre-generated conversational summary
            weather_sentence = weather_item.get('summary_text', '')
            if weather_sentence:
                sentences.append(weather_sentence)
        else:
            # Old format fallback: convert to conversational
            source = weather_item.get('source_name', '')
            title = weather_item.get('title', '')
            if title:
                sentences.append(f"Weather-wise, {title.lower()}")
    
    # Event sentence
    if event_item:
        source = event_item.get('source_name', '')
        title = event_item.get('title', '')
        location = event_item.get('location', '')
        if location:
            sentences.append(f"Meanwhile, {source} has announced {title} in {location}.")
        else:
            sentences.append(f"Meanwhile, {source} has announced {title}.")
    
    # Community sentence
    if community_item:
        source = community_item.get('source_name', '')
        title = community_item.get('title', '')
        if 'reddit' in source.lower():
            sentences.append(f"Over on {source}, there's been discussion about {title}.")
        else:
            sentences.append(f"From {source}, we've heard about {title}.")
    
    # Fallback if nothing available
    if not sentences:
        return "A quick wander through culture & craft from Scotland this week."
    
    # Vary the order for natural flow
    # Randomize order but keep it readable
    if len(sentences) > 1:
        # Shuffle but ensure weather doesn't always come first
        random.shuffle(sentences)
    
    # Join sentences naturally
    if len(sentences) == 1:
        text = sentences[0]
    elif len(sentences) == 2:
        # Two sentences: join with period and space
        text = sentences[0] + " " + sentences[1]
    else:
        # Three sentences: join first two, then add third
        text = sentences[0] + " " + sentences[1] + " " + sentences[2]
    
    return text

