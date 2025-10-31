"""Link validators (200-OK checks)."""

from __future__ import annotations

from typing import List, Tuple


def validate_links(urls: List[str]) -> List[Tuple[str, bool]]:
    """Return list of (url, is_ok). Real HTTP checks added later."""
    return [(u, True) for u in urls]




