"""Category feature rotation with cooldown."""

from __future__ import annotations

from typing import Any, Dict, Optional
from newsletter.db.queries_libraries import list_category_features


def select_category_feature() -> Optional[Dict[str, Any]]:
    """Pick the least recently used approved category feature."""
    items = list_category_features(limit=50)
    if not items:
        return None
    it = items[0]
    return {
        "id": it["id"],
        "title": it["title"],
        "body_html": it["body_html"],
        "topic": it["topic"],
    }



