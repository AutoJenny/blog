"""Snapshot text generation: single-item phrasing with attribution."""

from __future__ import annotations

from typing import Any, Dict


def generate_snapshot_text(item: Dict[str, Any]) -> str:
    """Generate single-item snapshot text with attribution.
    
    Tone: concise, with source attribution inline.
    
    Args:
        item: Dict with source_name, title, url (optional)
    
    Returns:
        Generated snapshot text with attribution
    """
    source = item.get('source_name', '')
    title = item.get('title', '')
    
    # Attribution phrasing based on source
    if 'bbc' in source.lower():
        return f"BBC Scotland reports: {title}"
    elif 'reddit' in source.lower():
        return f"A fun discussion on {source}: {title}"
    elif 'met office' in source.lower():
        return f"The Met Office reports: {title}"
    else:
        return f"{source}: {title}"

