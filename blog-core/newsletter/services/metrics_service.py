"""Post-send metrics helpers."""

from __future__ import annotations

from typing import Dict


def record_send(db, *, issue_id: int, provider: str, provider_id: str) -> None:
    return None


def summarize_issue(db, *, issue_id: int) -> Dict:
    return {"issue_id": issue_id, "clicks": 0}




