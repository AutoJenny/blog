"""
Facebook Matrix v1 – single source of truth for day → role (+ fixed angle hints).

Scope: Facebook only.

This module encodes the authoritative weekly matrix for Facebook, using the
Topic → Angle → Role → Channel → Post hierarchy as agreed in Phase 5.

Notes:
- Angles here are *hints* for expected variants (e.g. WORD / PHRASE / INSULT)
  inside CULTURE slots. They are fixed for Matrix v1 (no rotation/pooling).
- This file is intentionally simple and importable from both backend logic
  and reporting/diagnostic scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class FacebookDayConfig:
    """Configuration for a single Facebook day in Matrix v1."""

    role: str
    angle_hint: Optional[str] = None
    topic_source_hint: Optional[str] = None


# ISO weekday: 1 = Monday, 7 = Sunday
FACEBOOK_MATRIX_V1: Dict[int, FacebookDayConfig] = {
    1: FacebookDayConfig(
        role="CULTURE",
        angle_hint="LANGUAGE: WORD",
        topic_source_hint="Weekly language pool (word); CULTURE slot",
    ),
    2: FacebookDayConfig(
        role="CULTURE",
        angle_hint="LANGUAGE: PHRASE",
        topic_source_hint="Weekly language pool (phrase); CULTURE slot",
    ),
    3: FacebookDayConfig(
        role="REASSURANCE",
        angle_hint=None,
        topic_source_hint="Service principles / reassurance prompts",
    ),
    4: FacebookDayConfig(
        role="CULTURE",
        angle_hint="LANGUAGE: INSULT",
        topic_source_hint="Weekly language pool (insult); CULTURE slot",
    ),
    5: FacebookDayConfig(
        role="AUTHORITY_SHORT",
        angle_hint=None,
        topic_source_hint="Authority / provenance assertions (short context)",
    ),
    6: FacebookDayConfig(
        role="COMMERCE",
        angle_hint="PRODUCT SPOTLIGHT",
        topic_source_hint="Product catalogue; soft commerce",
    ),
    7: FacebookDayConfig(
        role="DEPTH_LONG",
        angle_hint="DEEP DIVE",
        topic_source_hint="KB topic rota (rota-authoritative)",
    ),
}


def get_facebook_day_config(iso_weekday: int) -> FacebookDayConfig:
    """
    Return the Matrix v1 configuration for the given ISO weekday (1–7).

    Falls back to Sunday (DEPTH_LONG) if an out-of-range value is provided,
    but callers should generally pass a valid ISO weekday.
    """

    return FACEBOOK_MATRIX_V1.get(iso_weekday, FACEBOOK_MATRIX_V1[7])

