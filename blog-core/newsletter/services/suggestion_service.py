"""Suggestion service: generates top suggestions, validates links, templates text."""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from newsletter.db.queries_sources import get_cached_items, check_repeat_cooldown
from newsletter.services.scoring import score_items, apply_diversity_rules
from newsletter.rendering.intro_text import generate_intro_text
from newsletter.rendering.snapshot_text import generate_snapshot_text


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


def generate_suggestions(*, block_type: str, target_week: str, count: int = 3, reference_date: datetime | None = None, skip_validation: bool = False) -> List[Dict[str, Any]]:
    """Generate top-scored suggestions for a block type and target week.
    
    For intro/snapshot: fetches from cached source items, applies scoring,
    diversity rules, and optional link validation.
    
    Args:
        block_type: Type of block (intro, snapshot, etc.)
        target_week: Target week string (e.g., "2025W44")
        count: Number of suggestions to return
        reference_date: Date to use for freshness scoring (defaults to today)
        skip_validation: If True, skip link validation (faster, for cached items)
    
    Returns:
        List of suggestion dicts with scores, attribution info
    """
    import logging
    logger = logging.getLogger(__name__)
    
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
        logger.debug(f"No cached items found for {block_type} block")
        return []
    
    logger.debug(f"Found {len(all_items)} cached items for {block_type} block")
    
    # Re-score items with current reference date
    scored = score_items(all_items, reference_date=reference_date)
    
    if not scored:
        logger.debug(f"No items passed scoring for {block_type} block")
        return []
    
    logger.debug(f"After scoring: {len(scored)} items, top score: {scored[0].get('combined_score', 0) if scored else 0}")
    
    # Apply diversity rules (prefer mix of categories)
    if block_type in ('intro', 'snapshot'):
        # For intro: prefer one weather, one event, one community
        diverse = apply_diversity_rules(scored, max_per_category=1)
    else:
        diverse = scored
    
    logger.debug(f"After diversity rules: {len(diverse)} items")
    
    # Validate links (filter out broken URLs) - but be lenient
    # For cached items, we can skip validation since they were validated on fetch
    validated = []
    unvalidated = []
    
    if skip_validation:
        # Skip validation for performance - cached items are already validated
        validated = diverse[:count]
        logger.debug(f"Skipping link validation, using top {len(validated)} items")
    else:
        # Try to validate, but don't be too strict
        validation_attempts = min(count * 5, len(diverse))  # Check more items
        for item in diverse[:validation_attempts]:
            url = item.get('url', '')
            if not url:
                continue  # Skip items without URLs
            
            # Quick validation - if it fails, still keep it but mark as unvalidated
            if validate_link(url):
                validated.append(item)
            else:
                unvalidated.append(item)
            
            if len(validated) >= count:
                break
        
        # Fallback: if validation filtered everything, use unvalidated items
        if not validated and unvalidated:
            logger.warning(f"Link validation filtered all items, using unvalidated items as fallback")
            validated = unvalidated[:count]
        elif len(validated) < count and unvalidated:
            # Fill remaining slots with unvalidated items
            needed = count - len(validated)
            validated.extend(unvalidated[:needed])
    
    logger.debug(f"Final validated items: {len(validated)}")
    
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
    
    Delegates to rendering module.
    """
    return generate_intro_text(weather_item, event_item, community_item)


def template_snapshot_text(item: Dict[str, Any]) -> str:
    """Generate single-item snapshot text with attribution.
    
    Delegates to rendering module.
    """
    return generate_snapshot_text(item)

