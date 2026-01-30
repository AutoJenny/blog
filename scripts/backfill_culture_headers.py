#!/usr/bin/env python3
"""
One-time backfill: add culture/heritage headers to unpublished Facebook queue rows.

Target: platform = 'facebook', content_type IN ('culture_fact', 'heritage_fact'),
        status IN ('draft', 'pending', 'ready', 'approved'), generated_content IS NOT NULL.
For each row: apply apply_culture_or_heritage_header(); if output differs from stored
generated_content, UPDATE generated_content and updated_at.
Does not touch published, failed, or cancelled rows.

Idempotency: rows whose first non-empty line is already UNDERSTANDING SCOTLAND or
SCOTTISH HERITAGE are skipped (no change). Re-run in --dry-run to confirm zero changes.

Run only once or when header rules change. Do not run on every deployment.
See docs/PREVIEW_FACEBOOK_MATCH_PUBLISH.md and docs/FACEBOOK_CULTURE_HERITAGE_FORMATTING.md.

Modes:
  --dry-run (default): print counts + sample IDs, write CSV with would-change.
  --apply: perform updates, write CSV.

Artefact: docs/BACKFILL_CULTURE_HEADERS_YYYYMMDD.csv
Columns: queue_id, content_type, status, changed (true/false)
"""

import os
import sys
import csv
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.formatting.culture_headers import apply_culture_or_heritage_header

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
TARGET_STATUSES = ("draft", "pending", "ready", "approved")
# Idempotency: do not re-apply if first non-empty line is already the correct header
EXPECTED_FIRST_LINE = {
    "culture_fact": "UNDERSTANDING SCOTLAND",
    "heritage_fact": "SCOTTISH HERITAGE",
}


def fetch_target_rows():
    with db_manager.get_cursor() as cur:
        cur.execute(
            """
            SELECT id, content_type, status, generated_content
            FROM posting_queue
            WHERE platform = 'facebook'
              AND content_type IN ('culture_fact', 'heritage_fact')
              AND status IN (%s, %s, %s, %s)
              AND generated_content IS NOT NULL
            ORDER BY id
            """,
            TARGET_STATUSES,
        )
        return [dict(r) for r in cur.fetchall()]


def main():
    apply_mode = "--apply" in sys.argv
    dry_run = not apply_mode
    today = date.today()
    date_tag = today.strftime("%Y%m%d")
    csv_path = os.path.join(DOCS_DIR, f"BACKFILL_CULTURE_HEADERS_{date_tag}.csv")

    rows = fetch_target_rows()
    if not rows:
        print("No target rows found.")
        return 0

    results = []
    to_update = []
    for r in rows:
        queue_id = r["id"]
        content_type = r["content_type"]
        status = r["status"]
        current = r["generated_content"] or ""
        # Idempotency: skip if first non-empty line is already the correct header
        first_line = next((ln.strip() for ln in current.split("\n") if ln.strip()), "")
        if first_line == EXPECTED_FIRST_LINE.get(content_type):
            results.append({"queue_id": queue_id, "content_type": content_type, "status": status, "changed": "false"})
            continue
        new_content = apply_culture_or_heritage_header(content_type, current)
        changed = new_content != current
        results.append({
            "queue_id": queue_id,
            "content_type": content_type,
            "status": status,
            "changed": "true" if changed else "false",
        })
        if changed:
            to_update.append((queue_id, new_content))

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["queue_id", "content_type", "status", "changed"])
        w.writeheader()
        w.writerows(results)

    changed_count = len(to_update)
    print(f"Target rows: {len(rows)}. Would change: {changed_count}. Wrote {csv_path}")

    if dry_run:
        if to_update:
            sample = [t[0] for t in to_update[:10]]
            print(f"[DRY-RUN] Sample IDs that would be updated: {sample}")
        return 0

    if not to_update:
        print("No rows to update.")
        return 0

    updated = 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            for queue_id, new_content in to_update:
                cur.execute(
                    """
                    UPDATE posting_queue
                    SET generated_content = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (new_content, queue_id),
                )
                updated += cur.rowcount
    print(f"Updated {updated} row(s). Artefact: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
