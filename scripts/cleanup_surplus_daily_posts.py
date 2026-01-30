#!/usr/bin/env python3
"""
Cleanup surplus daily posts for Facebook: one post per day (except Saturday multiple products).

Scans forward N weeks (default 12), finds days where there is >1 publishable row for Facebook,
keeps one per date (deterministic: Matrix priority then lowest id), cancels the rest with a reason.
Outputs docs/CLEANUP_SURPLUS_POSTS_YYYYMMDD.csv.

Usage:
  python scripts/cleanup_surplus_daily_posts.py              # run, 12 weeks
  python scripts/cleanup_surplus_daily_posts.py --weeks 4   # 4 weeks ahead
  python scripts/cleanup_surplus_daily_posts.py --dry-run   # report only, no updates
"""

import os
import sys
import csv
from datetime import date, timedelta, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


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
        p = 7
    else:
        p = 99
    return (p, post.get("id") or 0)


def get_publishable_facebook_in_range(start_date: date, end_date: date):
    """Return list of post dicts (facebook, publishable) in [start_date, end_date]. Same predicate as executor: utils.publishable_predicate."""
    from utils.publishable_predicate import PUBLISHABLE_STATUSES
    now = datetime.now()
    with db_manager.get_cursor() as cur:
        cur.execute(
            """
            SELECT id, platform, role, content_type, scheduled_date, scheduled_time, status
            FROM posting_queue
            WHERE platform = 'facebook'
              AND scheduled_date >= %s AND scheduled_date <= %s
              AND status IN (%s, %s)
              AND (
                  (scheduled_timestamp IS NOT NULL AND scheduled_timestamp <= %s)
                  OR (scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL
                      AND (scheduled_date::date + scheduled_time::time)::timestamp <= %s)
              )
            ORDER BY scheduled_date, id
            """,
            (start_date, end_date, PUBLISHABLE_STATUSES[0], PUBLISHABLE_STATUSES[1], now, now),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def main():
    dry_run = "--dry-run" in sys.argv
    weeks = 12
    if "--weeks" in sys.argv:
        i = sys.argv.index("--weeks")
        if i + 1 < len(sys.argv):
            weeks = int(sys.argv[i + 1])
    today = date.today()
    end_date = today + timedelta(weeks=weeks)
    date_tag = today.strftime("%Y%m%d")
    csv_path = os.path.join(DOCS_DIR, f"CLEANUP_SURPLUS_POSTS_{date_tag}.csv")

    posts = get_publishable_facebook_in_range(today, end_date)
    by_date = defaultdict(list)
    for p in posts:
        sd = p.get("scheduled_date")
        if sd:
            if isinstance(sd, str):
                sd = date.fromisoformat(sd)
            by_date[sd].append(p)

    to_cancel = []  # list of (id, scheduled_date, role, content_type, status, error_message, kept_id)
    for scheduled_date, group in sorted(by_date.items()):
        if len(group) <= 1:
            continue
        weekday = scheduled_date.isoweekday()
        if weekday == 6:
            # Saturday: keep all product rows, cancel non-product
            products = [p for p in group if (p.get("content_type") or "").strip() == "product"]
            non_products = [p for p in group if (p.get("content_type") or "").strip() != "product"]
            for p in non_products:
                to_cancel.append((p["id"], scheduled_date, p.get("role"), p.get("content_type"), p.get("status"),
                                  f"Cleanup: cancelled non-product for Saturday {scheduled_date}; only product posts allowed", None))
        else:
            # Non-Saturday: keep one by priority
            sorted_posts = sorted(group, key=_priority_key)
            keep = sorted_posts[0]
            for p in sorted_posts[1:]:
                to_cancel.append((p["id"], scheduled_date, p.get("role"), p.get("content_type"), p.get("status"),
                                  f"Cleanup: cancelled surplus for date {scheduled_date}; kept queue_id={keep['id']}", keep["id"]))

    if not to_cancel:
        print(f"No surplus rows in [{today}, {end_date}]. Nothing to cancel.")
        return 0

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "scheduled_date", "role", "content_type", "status_before", "error_message", "kept_queue_id"])
        for row in to_cancel:
            w.writerow([row[0], row[1], row[2], row[3], row[4], row[5], row[6]])
    n = len(to_cancel)
    print(f"Wrote {csv_path} ({n} row{'s' if n != 1 else ''} to cancel)")

    if dry_run:
        print(f"[DRY-RUN] Would cancel {len(to_cancel)} row(s). IDs: {[r[0] for r in to_cancel]}")
        return 0

    cancelled = 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            for (queue_id, _sd, _role, _ct, _status, error_message, _kept_id) in to_cancel:
                cur.execute("""
                    UPDATE posting_queue
                    SET status = 'cancelled', error_message = %s, updated_at = NOW()
                    WHERE id = %s
                """, (error_message, queue_id))
                cancelled += cur.rowcount
    print(f"Cancelled {cancelled} row(s). Artefact: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
