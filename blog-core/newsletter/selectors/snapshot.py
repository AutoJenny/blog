"""Select a Scottish Snapshot item from approved sources with fallback."""

from __future__ import annotations

from typing import Any, Dict, Optional
from newsletter.db.queries_libraries import list_snapshot_sources


def select_snapshot() -> Optional[Dict[str, Any]]:
    """Return a simple snapshot seeded from an approved source list.

    For MVP, we do not scrape; we surface a placeholder using the source name.
    """
    sources = list_snapshot_sources(enabled_only=True)
    if not sources:
        return None
    s = sources[0]
    return {
        "title": f"From {s['name']}",
        "publisher": s["name"],
        "url": s["base_url"],
        "comment": "A wee highlight worth a look.",
    }


def fallback_snapshot() -> Dict[str, Any]:
    return {
        "title": "This week in Scotland",
        "publisher": "In-house",
        "url": "",
        "comment": "A wee cultural moment while we fetch fresh headlines.",
    }



