"""Intro text generation: combines weather/event/community items into 2-3 sentences."""

from __future__ import annotations

from typing import Any, Dict, Optional


def generate_intro_text(
    weather_item: Dict[str, Any] | None = None,
    event_item: Dict[str, Any] | None = None,
    community_item: Dict[str, Any] | None = None
) -> str:
    """Generate 2-3 sentence intro text from selected items.
    
    Tone: warm, observational, with inline attribution.
    
    Args:
        weather_item: Dict with source_name, title, url (optional)
        event_item: Dict with source_name, title, url, location (optional)
        community_item: Dict with source_name, title, url (optional)
    
    Returns:
        Generated intro text (2-3 sentences)
    """
    sentences = []
    
    # Weather sentence (if available)
    if weather_item:
        source = weather_item.get('source_name', '')
        title = weather_item.get('title', '')
        # Simple phrasing: "The Met Office reports..." or "Weather warnings are in effect..."
        if 'met office' in source.lower():
            sentences.append(f"The Met Office reports: {title}")
        else:
            sentences.append(f"{source} reports: {title}")
    
    # Event/community sentence
    if event_item:
        source = event_item.get('source_name', '')
        title = event_item.get('title', '')
        location = event_item.get('location', '')
        if location:
            sentences.append(f"{source} has announced: {title} in {location}.")
        else:
            sentences.append(f"{source} has announced: {title}.")
    elif community_item:
        source = community_item.get('source_name', '')
        title = community_item.get('title', '')
        if 'reddit' in source.lower():
            sentences.append(f"A fun discussion on {source}: {title}")
        else:
            sentences.append(f"{source}: {title}")
    
    # Fallback if nothing available
    if not sentences:
        return "A quick wander through culture & craft from Scotland this week."
    
    # Join with soft segue
    text = ". ".join(sentences)
    if len(sentences) > 1:
        text += " If you're nearby, it's worth a look."
    
    return text

