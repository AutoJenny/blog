"""Evergreen snippet rotation with weighting and cooldown."""

from __future__ import annotations

from typing import Any, Dict, Optional
from newsletter.db.queries_libraries import list_evergreen


def select_evergreen() -> Optional[Dict[str, Any]]:
    items = list_evergreen(limit=100)
    if not items:
        return None
    it = items[0]
    return {
        "id": it["id"],
        "topic": it["topic"],
        "text": it["text"],
        "length": it.get("length", 0),
        "season": it.get("season"),
        "region_tags": it.get("region_tags"),
    }



