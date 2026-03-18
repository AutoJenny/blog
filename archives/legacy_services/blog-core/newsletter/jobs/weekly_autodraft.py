"""Scheduled job entrypoint for weekly auto-draft creation."""

from __future__ import annotations

from newsletter.services.draft_service import build_weekly_issue


def run() -> dict:
    """Create an auto-draft for the current ISO week and return summary."""
    result = build_weekly_issue()
    return {"created": True, **result}



