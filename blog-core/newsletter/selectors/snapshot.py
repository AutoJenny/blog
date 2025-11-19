"""Select a Scottish Snapshot item using new suggestion system."""

from __future__ import annotations

from typing import Any, Dict, Optional
from newsletter.services.suggestion_service import generate_suggestions, select_default
from newsletter.rendering.snapshot_text import generate_snapshot_text


def select_snapshot(*, target_week: str) -> Optional[Dict[str, Any]]:
    """Return snapshot content using suggestion system.
    
    Fetches top-scored suggestions, selects default, generates text with attribution.
    """
    # Skip validation for cached items - they were validated on fetch
    suggestions = generate_suggestions(block_type='snapshot', target_week=target_week, count=3, skip_validation=True)
    
    if not suggestions:
        return fallback_snapshot()
    
    selected = select_default(suggestions)
    if not selected:
        return fallback_snapshot()
    
    text = generate_snapshot_text(selected)
    
    return {
        "title": selected.get('title', ''),
        "publisher": selected.get('source_name', ''),
        "url": selected.get('url', ''),
        "comment": text,
        "suggestions": suggestions,  # Include all suggestions for UI
        "selected_id": selected.get('id'),
    }


def fallback_snapshot() -> Dict[str, Any]:
    """Return fallback snapshot when no suggestions available."""
    return {
        "title": "This week in Scotland",
        "publisher": "In-house",
        "url": "",
        "comment": "A wee cultural moment while we fetch fresh headlines.",
        "suggestions": [],
        "selected_id": None,
    }



