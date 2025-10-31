"""Preview adapter: stores rendered HTML for QA without sending."""

from __future__ import annotations

from typing import Sequence


_STORE: list[str] = []


def send_preview(*, subject: str, html: str, text: str, recipients: Sequence[str], headers: dict | None = None) -> str:
    _STORE.append(html)
    return f"preview:{len(_STORE)}"


def latest_preview_html() -> str | None:
    return _STORE[-1] if _STORE else None




