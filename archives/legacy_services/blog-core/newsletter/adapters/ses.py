"""Amazon SES adapter (stub)."""

from __future__ import annotations

from typing import Sequence


def send_ses(*, subject: str, html: str, text: str, recipients: Sequence[str], headers: dict | None = None) -> str:
    # Placeholder; wire to SES later
    return "ses:pending"




