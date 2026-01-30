#!/usr/bin/env python3
"""
Validate daily cap invariant: for Facebook, non-Saturday dates must have at most 1 publishable row.

Uses same predicate as executor: utils.publishable_predicate (ready/pending, scheduled <= now).
Fails (exit 1) if any non-Saturday date in the next N weeks has >1 publishable row.

Usage:
  python scripts/validate_daily_cap_invariant.py --weeks 12 --platform facebook
"""

import os
import sys
from datetime import date, timedelta, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.publishable_predicate import PUBLISHABLE_STATUSES


def get_publishable_facebook_in_range(start_date: date, end_date: date):
    """Same predicate as executor and cleanup."""
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
    import argparse
    parser = argparse.ArgumentParser(description="Validate daily cap invariant (max 1 publishable per non-Saturday date)")
    parser.add_argument("--weeks", type=int, default=12, help="Weeks ahead to check (default 12)")
    parser.add_argument("--platform", type=str, default="facebook", help="Platform (default facebook)")
    args = parser.parse_args()
    if args.platform != "facebook":
        print("Only facebook is validated; other platforms skipped.", file=sys.stderr)
    today = date.today()
    end_date = today + timedelta(weeks=args.weeks)
    posts = get_publishable_facebook_in_range(today, end_date)
    by_date = defaultdict(list)
    for p in posts:
        sd = p.get("scheduled_date")
        if sd:
            if isinstance(sd, str):
                sd = date.fromisoformat(sd)
            by_date[sd].append(p)
    violations = []
    for scheduled_date, group in sorted(by_date.items()):
        weekday = scheduled_date.isoweekday()
        if weekday == 6:
            # Saturday: multiple product rows allowed; non-product is surplus
            non_products = [p for p in group if (p.get("content_type") or "").strip() != "product"]
            if non_products:
                violations.append((scheduled_date, "Saturday has non-product publishable", non_products))
        else:
            if len(group) > 1:
                violations.append((scheduled_date, f"Non-Saturday has {len(group)} publishable (max 1)", group))
    if violations:
        print("Daily cap invariant VIOLATED:", file=sys.stderr)
        for d, msg, rows in violations:
            print(f"  {d}: {msg} ids={[r['id'] for r in rows]}", file=sys.stderr)
        sys.exit(1)
    print(f"Daily cap invariant OK: {len(by_date)} dates checked, max 1 publishable per non-Saturday date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
