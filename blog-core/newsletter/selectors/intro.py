"""Intro block selector: aggregates weather/event/community suggestions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from newsletter.services.suggestion_service import generate_suggestions
from newsletter.rendering.intro_text import generate_intro_text
from newsletter.services.scoring import apply_diversity_rules


def select_intro_content(*, target_week: str) -> Dict[str, Any]:
    """Generate intro block content from aggregated suggestions.
    
    Fetches suggestions across weather, event, and community categories,
    applies diversity rules, and generates 2-3 sentence text with attribution.
    
    Returns dict with:
    - suggestions: List of 3 scored options
    - selected: Auto-selected item (top suggestion)
    - text: Generated intro text
    - items_by_category: Dict mapping category to selected item
    """
    # Get suggestions for intro (we want diverse mix)
    all_suggestions = generate_suggestions(block_type='intro', target_week=target_week, count=9)
    
    if not all_suggestions:
        return {
            'suggestions': [],
            'selected': None,
            'text': "A quick wander through culture & craft from Scotland this week.",
            'items_by_category': {},
        }
    
    # Group by category and apply diversity
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for item in all_suggestions:
        cat = item.get('category', 'other')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    # Select one top item per category
    weather_item = None
    event_item = None
    community_item = None
    
    if 'weather' in by_category:
        weather_item = by_category['weather'][0]  # Top scored
    if 'event' in by_category:
        event_item = by_category['event'][0]
    if 'community' in by_category:
        community_item = by_category['community'][0]
    
    # Fallback: if no category-specific, use top items regardless
    if not weather_item and not event_item and not community_item:
        if all_suggestions:
            # Use top 3 as fallback
            for i, item in enumerate(all_suggestions[:3]):
                cat = item.get('category', 'other')
                if cat == 'weather' and not weather_item:
                    weather_item = item
                elif cat == 'event' and not event_item:
                    event_item = item
                elif cat == 'community' and not community_item:
                    community_item = item
                elif not weather_item:
                    weather_item = item
                elif not event_item:
                    event_item = item
                elif not community_item:
                    community_item = item
    
    # Generate text from selected items
    text = generate_intro_text(weather_item, event_item, community_item)
    
    # Build top 3 suggestions for UI
    top_suggestions = []
    items_by_category = {}
    
    if weather_item:
        top_suggestions.append(weather_item)
        items_by_category['weather'] = weather_item
    if event_item:
        top_suggestions.append(event_item)
        items_by_category['event'] = event_item
    if community_item:
        top_suggestions.append(community_item)
        items_by_category['community'] = community_item
    
    # Fill remaining slots with other top-scored items
    seen_ids = {item.get('id') for item in top_suggestions}
    for item in all_suggestions:
        if len(top_suggestions) >= 3:
            break
        if item.get('id') not in seen_ids:
            top_suggestions.append(item)
            seen_ids.add(item.get('id'))
    
    # Auto-select top suggestion (weather preferred, then event, then community)
    selected = weather_item or event_item or community_item
    if not selected and top_suggestions:
        selected = top_suggestions[0]
    
    return {
        'suggestions': top_suggestions[:3],
        'selected': selected,
        'text': text,
        'items_by_category': items_by_category,
    }

