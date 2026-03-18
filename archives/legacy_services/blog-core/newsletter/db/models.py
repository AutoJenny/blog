"""Lightweight row models for newsletter tables.

These are simple dataclasses to represent rows; ORM is not required for now.
Keep each model concise; move helpers to dedicated modules if needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class NewsletterIssue:
    id: int
    target_week: str
    status: str
    subject: str
    preheader: str
    last_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class NewsletterBlock:
    id: int
    issue_id: int
    type: str
    enabled: bool
    position: int
    payload_json: Dict[str, Any]
    pinned_ids: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class NewsletterSendLog:
    id: int
    issue_id: int
    provider: str
    provider_id: str
    sent_at: datetime
    checksum: str
    created_at: datetime




