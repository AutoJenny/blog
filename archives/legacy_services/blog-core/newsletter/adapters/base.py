"""EmailDelivery interface."""

from __future__ import annotations

from typing import Protocol, Sequence


class EmailDelivery(Protocol):
    def send(self, *, subject: str, html: str, text: str, recipients: Sequence[str], headers: dict | None = None) -> str:  # returns provider id
        ...




