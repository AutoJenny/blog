#!/usr/bin/env python3
"""
Backfill a single ISO week to Matrix v1 alignment (Facebook).

For a given week this script:
- Moves message posts from Saturday → Wednesday (and sets role=REASSURANCE).
- Moves product posts from Tue/Thu (or any non-Saturday) → Saturday (and sets role=COMMERCE).
  If multiple products land on the same Saturday, all are moved to that Saturday (first-come
  keeps earliest time; extras keep distinct times or same slot per product—no dedupe here).
- Ensures Wednesday has a message (if none, skip or copy from Sat→Wed move).
- Does not create Fri authority posts (no authority_short creator in scope); see docs.
- Updates post_type_channel_config: message publication_day = 3 for facebook.

Usage:
  python3 scripts/backfill_matrix_v1_week.py --week 2026-W5 [--dry-run]

Deliverable D: script path scripts/backfill_matrix_v1_week.py
  Command for 2026-W5: python3 scripts/backfill_matrix_v1_week.py --week 2026-W5
  Before/after: run the same query as Step 1 (posting_queue for that week) before and after.
"""

import os
import sys
import argparse
from datetime import date, timedelta, time, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager


def parse_iso_week(s: str):
    """e.g. '2026-W5' -> (2026, 5)."""
    y, w = s.split("-W")
    return int(y), int(w)


def week_to_monday_sunday(year: int, week: int):
    """Return (week_monday, week_sunday) for ISO week."""
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    week_monday = week1_monday + timedelta(days=(week - 1) * 7)
    week_sunday = week_monday + timedelta(days=6)
    return week_monday, week_sunday


def run_backfill(year: int, week: int, dry_run: bool):
    week_monday, week_sunday = week_to_monday_sunday(year, week)
    wednesday = week_monday + timedelta(days=2)
    saturday = week_monday + timedelta(days=5)
    start_s = week_monday.isoformat()
    end_s = week_sunday.isoformat()

    updates = []

    with db_manager.get_cursor() as cursor:
        # 1) Messages on Saturday → move to Wednesday, set role=REASSURANCE
        cursor.execute("""
            SELECT id, scheduled_date, scheduled_time, scheduled_timestamp, generated_content
            FROM posting_queue
            WHERE platform = 'facebook' AND content_type = 'message'
              AND scheduled_date BETWEEN %s AND %s
              AND EXTRACT(ISODOW FROM scheduled_date) = 6
        """, (start_s, end_s))
        sat_messages = cursor.fetchall()
        for row in sat_messages:
            new_ts = datetime.combine(wednesday, row['scheduled_time'] or time(14, 30))
            updates.append(('message', row['id'], 'scheduled_date', row['scheduled_date'], wednesday))
            updates.append(('message', row['id'], 'scheduled_timestamp', None, new_ts))
            updates.append(('message', row['id'], 'role', None, 'REASSURANCE'))
            if not dry_run:
                cursor.execute("""
                    UPDATE posting_queue
                    SET scheduled_date = %s, scheduled_timestamp = %s, role = 'REASSURANCE', updated_at = NOW()
                    WHERE id = %s
                """, (wednesday, new_ts, row['id']))

        # 2) Products not on Saturday → move to Saturday, set role=COMMERCE
        cursor.execute("""
            SELECT id, scheduled_date, scheduled_time, scheduled_timestamp, product_id
            FROM posting_queue
            WHERE platform = 'facebook' AND content_type = 'product'
              AND scheduled_date BETWEEN %s AND %s
              AND EXTRACT(ISODOW FROM scheduled_date) != 6
        """, (start_s, end_s))
        non_sat_products = cursor.fetchall()
        default_time = time(17, 0)
        for i, row in enumerate(non_sat_products):
            t = row['scheduled_time'] or default_time
            new_ts = datetime.combine(saturday, t)
            updates.append(('product', row['id'], 'scheduled_date', row['scheduled_date'], saturday))
            updates.append(('product', row['id'], 'scheduled_timestamp', None, new_ts))
            updates.append(('product', row['id'], 'role', None, 'COMMERCE'))
            if not dry_run:
                cursor.execute("""
                    UPDATE posting_queue
                    SET scheduled_date = %s, scheduled_time = %s, scheduled_timestamp = %s, role = 'COMMERCE', updated_at = NOW()
                    WHERE id = %s
                """, (saturday, t, new_ts, row['id']))

        # 3) Update post_type_channel_config: message publication_day = 3 for facebook
        if not dry_run:
            cursor.execute("""
                UPDATE post_type_channel_config
                SET publication_day = 3
                WHERE channel = 'facebook' AND post_type = 'message'
            """)
            rc = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            updates.append(('config', 0, 'post_type_channel_config message', 6, 3))

    return updates


def main():
    ap = argparse.ArgumentParser(description="Backfill one ISO week to Matrix v1 (Facebook)")
    ap.add_argument("--week", default="2026-W5", help="ISO week e.g. 2026-W5")
    ap.add_argument("--dry-run", action="store_true", help="Print planned updates only")
    args = ap.parse_args()
    year, week = parse_iso_week(args.week)
    week_monday, week_sunday = week_to_monday_sunday(year, week)
    print(f"Backfill Matrix v1 week {args.week} ({week_monday} .. {week_sunday})" + (" [DRY-RUN]" if args.dry_run else ""))
    updates = run_backfill(year, week, args.dry_run)
    for u in updates:
        print(f"  {u}")
    print("Done. Run Step 1 SQL to verify before/after.")


if __name__ == "__main__":
    main()
