"""Suggestion service: generates top suggestions, validates links, templates text."""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from newsletter.db.queries_sources import get_cached_items, check_repeat_cooldown
from newsletter.services.scoring import score_items, apply_diversity_rules


def validate_link(url: str, timeout: int = 5) -> bool:
    """Check if URL returns HTTP 200 (or acceptable redirect).
    
    Returns True if link appears valid.
    """
    if not url or url == '':
        return False
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0)'}
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return 200 <= resp.status_code < 400
    except Exception:
        return False


def generate_suggestions(*, block_type: str, target_week: str, count: int = 3, reference_date: datetime | None = None) -> List[Dict[str, Any]]:
    """Generate top-scored suggestions for a block type and target week.
    
    For intro/snapshot: fetches from cached source items, applies scoring,
    diversity rules, and link validation.
    
    Args:
        block_type: Type of block (intro, snapshot, etc.)
        target_week: Target week string (e.g., "2025W44")
        count: Number of suggestions to return
        reference_date: Date to use for freshness scoring (defaults to today)
    
    Returns:
        List of suggestion dicts with scores, attribution info
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    # Parse target week to get ISO week number (for future week-based filtering)
    week_number = 0
    if 'W' in target_week:
        try:
            week_number = int(target_week.split('W')[1])
        except Exception:
            pass
    
    # Get cached items (last 14 days)
    all_items = get_cached_items(days_back=14, limit=200)
    
    if not all_items:
        return []
    
    # Re-score items with current reference date
    scored = score_items(all_items, reference_date=reference_date)
    
    # Apply diversity rules (prefer mix of categories)
    if block_type in ('intro', 'snapshot'):
        # For intro: prefer one weather, one event, one community
        diverse = apply_diversity_rules(scored, max_per_category=1)
    else:
        diverse = scored
    
    # Validate links (filter out broken URLs)
    validated = []
    for item in diverse[:count * 3]:  # Check more than needed
        if validate_link(item.get('url', '')):
            validated.append(item)
        if len(validated) >= count:
            break
    
    # Format as suggestions with metadata
    suggestions = []
    for item in validated[:count]:
        suggestions.append({
            'id': item.get('id'),
            'source_name': item.get('source_name'),
            'title': item.get('title'),
            'url': item.get('url'),
            'category': item.get('category'),
            'location': item.get('location'),
            'published_at': item.get('published_at'),
            'event_date': item.get('event_date'),
            'signal_score': item.get('signal_score', 0.0),
            'freshness_score': item.get('freshness_score', 0.0),
            'combined_score': item.get('combined_score', 0.0),
            'raw_data': item.get('raw_data', {}),
        })
    
    return suggestions


def select_default(suggestions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pick the top suggestion (highest combined score)."""
    if not suggestions:
        return None
    return suggestions[0] if suggestions else None


def template_intro_text(weather_item: Dict[str, Any] | None = None, 
                        event_item: Dict[str, Any] | None = None,
                        community_item: Dict[str, Any] | None = None) -> str:
    """Generate 2-3 sentence intro text from selected items.
    
    Tone: warm, observational, with inline attribution.
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


def template_snapshot_text(item: Dict[str, Any]) -> str:
    """Generate single-item snapshot text with attribution."""
    source = item.get('source_name', '')
    title = item.get('title', '')
    
    # Attribution phrasing
    if 'bbc' in source.lower():
        return f"BBC Scotland reports: {title}"
    elif 'reddit' in source.lower():
        return f"A fun discussion on {source}: {title}"
    elif 'met office' in source.lower():
        return f"The Met Office reports: {title}"
    else:
        return f"{source}: {title}"

