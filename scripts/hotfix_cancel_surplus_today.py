#!/usr/bin/env python3
"""
Hotfix: Cancel surplus Facebook rows for TODAY to enforce one-post-per-day.

1. Find all Facebook rows for today that are publishable (status in ready/pending, scheduled <= now).
2. Keep exactly one (deterministic: Matrix priority then lowest id).
3. Cancel the rest: status='cancelled', error_message='Hotfix: cancelled to enforce one-post-per-day cap (date=YYYY-MM-DD)'.
4. Write docs/HOTFIX_CANCELLED_IDS_YYYYMMDD.csv: id, role, content_type, scheduled_date, scheduled_time, status_before, status_after.

Usage:
  python scripts/hotfix_cancel_surplus_today.py           # run
  python scripts/hotfix_cancel_surplus_today.py --dry-run  # report only, no updates
"""

import os
import sys
import csv
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

# Matrix priority (highest first): 1=AUTHORITY_SHORT, 2=DEPTH_LONG, 3=HERITAGE, 4=CULTURE, 5=message, 6=language
_PRIORITY_ORDER = {
    "AUTHORITY_SHORT": 1,
    "DEPTH_LONG": 2,
    "HERITAGE": 3,
    "CULTURE": 4,
    "message": 5,
    "weekly_word": 6,
    "weekly_phrase": 6,
    "weekly_insult": 6,
}


def _priority_key(post):
    role = (post.get("role") or "").strip()
    ct = (post.get("content_type") or "").strip()
    if role == "AUTHORITY_SHORT":
        p = 1
    elif ct == "depth_long":
        p = 2
    elif role == "HERITAGE" or ct == "heritage_fact":
        p = 3
    elif ct == "culture_fact":
        p = 4
    elif ct == "message":
        p = 5
    elif ct in ("weekly_word", "weekly_phrase", "weekly_insult"):
        p = 6
    elif ct == "product":
        p = 7  # Saturday: keep all products; for same-day cap we still pick one if mixed
    else:
        p = 99
    return (p, post.get("id") or 0)


def get_publishable_today(platform="facebook"):
    """Return list of post dicts for today that are publishable (same predicate as executor: utils.publishable_predicate)."""
    from utils.publishable_predicate import PUBLISHABLE_STATUSES
    today = date.today()
    now = datetime.now()
    with db_manager.get_cursor() as cur:
        cur.execute(
            """
            SELECT id, platform, role, content_type, scheduled_date, scheduled_time, status
            FROM posting_queue
            WHERE platform = %s
              AND scheduled_date = %s
              AND status IN (%s, %s)
              AND (
                  (scheduled_timestamp IS NOT NULL AND scheduled_timestamp <= %s)
                  OR (scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL
                      AND (scheduled_date::date + scheduled_time::time)::timestamp <= %s)
              )
            ORDER BY id
            """,
            (platform, today, PUBLISHABLE_STATUSES[0], PUBLISHABLE_STATUSES[1], now, now),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def choose_keep_id(posts):
    """Pick one to keep: Saturday can have multiple products; for same-day cap we keep one by priority then lowest id."""
    if not posts:
        return None
    # For hotfix "today" we enforce one per day: pick single best by priority then id
    sorted_posts = sorted(posts, key=_priority_key)
    return sorted_posts[0]["id"]


def main():
    dry_run = "--dry-run" in sys.argv
    today = date.today()
    date_str = today.isoformat()
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    csv_path = os.path.join(docs_dir, f"HOTFIX_CANCELLED_IDS_{today.strftime('%Y%m%d')}.csv")

    posts = get_publishable_today()
    if not posts:
        print(f"No publishable Facebook rows for today ({date_str}). Nothing to do.")
        return 0

    keep_id = choose_keep_id(posts)
    to_cancel = [p for p in posts if p["id"] != keep_id]
    cancelled_count = len(to_cancel)
    error_msg = f"Hotfix: cancelled to enforce one-post-per-day cap (date={date_str})"

    # Build CSV rows: id, role, content_type, scheduled_date, scheduled_time, status_before, status_after
    csv_rows = []
    for p in posts:
        status_after = "kept" if p["id"] == keep_id else "cancelled"
        csv_rows.append({
            "id": p["id"],
            "role": p.get("role") or "",
            "content_type": p.get("content_type") or "",
            "scheduled_date": p.get("scheduled_date"),
            "scheduled_time": str(p.get("scheduled_time") or ""),
            "status_before": p.get("status") or "",
            "status_after": status_after,
        })

    os.makedirs(docs_dir, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "role", "content_type", "scheduled_date", "scheduled_time", "status_before", "status_after"])
        w.writeheader()
        w.writerows(csv_rows)
    print(f"Wrote {csv_path} ({len(csv_rows)} rows)")

    if dry_run:
        print(f"[DRY-RUN] Would keep id={keep_id}, cancel {cancelled_count} row(s): {[p['id'] for p in to_cancel]}")
        return 0

    if to_cancel:
        ids = [p["id"] for p in to_cancel]
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE posting_queue
                    SET status = 'cancelled', error_message = %s, updated_at = NOW()
                    WHERE id = ANY(%s)
                    """,
                    (error_msg, ids),
                )
                n = cur.rowcount
        print(f"Cancelled {n} row(s). Kept id={keep_id}.")
    else:
        print(f"Only one publishable row for today (id={keep_id}). No cancellations.")

    print(f"Counts: found={len(posts)}, kept=1, cancelled={cancelled_count}")
    print(f"Artefact: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
