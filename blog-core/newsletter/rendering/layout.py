"""Compose newsletter blocks into a renderable structure."""

from __future__ import annotations

from typing import Dict, List


def compose_layout(blocks: List[Dict]) -> Dict:
    return {"blocks": blocks}




