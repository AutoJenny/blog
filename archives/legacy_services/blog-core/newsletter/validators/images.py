"""Image validators (presence and ratio)."""

from __future__ import annotations

from typing import Dict, List, Tuple


def validate_image_cards(cards: List[Dict[str, str]]) -> List[Tuple[str, bool]]:
    """Check each card dict for required image fields; return (id_or_url, ok)."""
    out: List[Tuple[str, bool]] = []
    for c in cards:
        url = c.get("image_url", "")
        ok = bool(url)
        out.append((url, ok))
    return out




