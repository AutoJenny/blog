"""Draft builder service.

Composes the weekly issue by invoking selectors and assembling blocks.
"""

from __future__ import annotations

from typing import Dict, List
from datetime import date
from newsletter.db.queries_issue import create_issue, upsert_block
from newsletter.selectors.blog_feature import select_feature_article
from newsletter.selectors.snapshot import select_snapshot, fallback_snapshot
from newsletter.selectors.products import select_new_products, select_spotlight_product, group_variants
from newsletter.selectors.category import select_category_feature
from newsletter.selectors.evergreen import select_evergreen


def build_weekly_issue(*, target_week: str | None = None) -> Dict:
    """Create an issue and populate initial blocks (placeholders allowed)."""
    if not target_week:
        iso_year, iso_week, _ = date.today().isocalendar()
        target_week = f"{iso_year}W{iso_week:02d}"

    subject = f"This week in Scotland — {target_week}"
    preheader = "A quick wander through culture & craft."
    issue_id = create_issue(target_week=target_week, subject=subject, preheader=preheader)

    position = 0

    # Feature Article
    feature = select_feature_article()
    upsert_block(issue_id=issue_id, block_type="feature", position=position, enabled=True, payload=feature or {})
    position += 1

    # Snapshot
    snap = select_snapshot() or fallback_snapshot()
    upsert_block(issue_id=issue_id, block_type="snapshot", position=position, enabled=True, payload=snap)
    position += 1

    # New Products or Spotlight (placeholder selection)
    new_items = select_new_products(since_iso_timestamp=f"{date.today().isoformat()}T00:00:00Z")
    if new_items:
        grouped, _ = group_variants(new_items)
        upsert_block(issue_id=issue_id, block_type="new_products", position=position, enabled=True, payload={"items": grouped[:6]})
    else:
        spotlight = select_spotlight_product()
        upsert_block(issue_id=issue_id, block_type="spotlight", position=position, enabled=True, payload=spotlight or {})
    position += 1

    # Category Feature
    category = select_category_feature()
    upsert_block(issue_id=issue_id, block_type="category", position=position, enabled=True, payload=category or {})
    position += 1

    # Evergreen
    evergreen = select_evergreen()
    upsert_block(issue_id=issue_id, block_type="evergreen", position=position, enabled=True, payload=evergreen or {})
    position += 1

    # Closing placeholder
    upsert_block(issue_id=issue_id, block_type="closing", position=position, enabled=True, payload={"text": "Warmly, from Scotland"})

    return {"issue_id": issue_id, "target_week": target_week}


