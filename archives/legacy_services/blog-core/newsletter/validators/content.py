"""Content validators (lengths, alt text, thresholds)."""

from __future__ import annotations

from typing import Dict, Tuple


def validate_lengths(block: Dict, *, min_words: int, max_words: int) -> Tuple[int, bool]:
    words = len(str(block.get("text", "")).split())
    return words, min_words <= words <= max_words


def has_alt_text(img: Dict[str, str]) -> bool:
    return bool(img.get("alt"))




