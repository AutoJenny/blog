"""Mailchimp adapter (stub uses pre-rendered HTML)."""

from __future__ import annotations

from typing import Sequence


def send_mailchimp(*, subject: str, html: str, text: str, recipients: Sequence[str], headers: dict | None = None) -> str:
    # Placeholder; wire to Mailchimp API later
    return "mailchimp:pending"




