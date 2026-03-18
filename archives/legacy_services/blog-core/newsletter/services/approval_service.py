"""Approval and send workflow service."""

from __future__ import annotations

from typing import Dict
from newsletter.db.queries_metrics import insert_send_log
from newsletter.db.queries_issue import list_blocks_by_issue
from newsletter.rendering.to_html import render_html
from newsletter.rendering.to_text import render_text
from newsletter.rendering.layout import compose_layout
from newsletter.adapters.preview import send_preview


def approve_issue(*, issue_id: int) -> None:
    # Minimal stub: in future mark status in DB
    return None


def send_issue(*, issue_id: int, adapter: str) -> Dict:
    # Render content
    blocks = list_blocks_by_issue(issue_id=issue_id)
    layout = compose_layout(blocks)
    html = render_html(layout)
    text = render_text(layout)

    # Dispatch via selected adapter (preview only for now)
    if adapter == "preview":
        provider_id = send_preview(subject=f"Newsletter Issue {issue_id}", html=html, text=text, recipients=["preview@local"])  # type: ignore[arg-type]
    else:
        provider_id = send_preview(subject=f"Newsletter Issue {issue_id}", html=html, text=text, recipients=["preview@local"])  # safe default

    # Log send
    insert_send_log(issue_id=issue_id, provider=adapter, provider_id=provider_id, checksum="")
    return {"issue_id": issue_id, "status": "sent", "adapter": adapter, "provider_id": provider_id}



