#!/usr/bin/env python3
"""
Validate daily cap invariant per platform: for each platform (facebook, instagram),
non-Saturday dates must have at most 1 publishable row; Saturday allows multiple product rows,
non-product on Saturday is a violation per platform.

Uses same predicate as executor: utils.publishable_predicate (ready/pending, scheduled <= now).
Fails (exit 1) if any platform has a violation. FB and IG may both have one row per date;
the invariant is per-platform, not cross-platform.

Usage:
  python scripts/validate_daily_cap_invariant.py --weeks 12
  python scripts/validate_daily_cap_invariant.py --weeks 3 --platforms facebook instagram
"""

import os
import sys
from datetime import date, timedelta, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.publishable_predicate import PUBLISHABLE_STATUSES

DEFAULT_PLATFORMS = ["facebook", "instagram"]


def get_publishable_in_range(platform: str, start_date: date, end_date: date):
    """Same predicate as executor and cleanup; for given platform."""
    now = datetime.now()
    with db_manager.get_cursor() as cur:
        cur.execute(
            """
            SELECT id, platform, role, content_type, scheduled_date, scheduled_time, status
            FROM posting_queue
            WHERE platform = %s
              AND scheduled_date >= %s AND scheduled_date <= %s
              AND status IN (%s, %s)
              AND (
                  (scheduled_timestamp IS NOT NULL AND scheduled_timestamp <= %s)
                  OR (scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL
                      AND (scheduled_date::date + scheduled_time::time)::timestamp <= %s)
              )
            ORDER BY scheduled_date, scheduled_time, id
            """,
            (platform, start_date, end_date, PUBLISHABLE_STATUSES[0], PUBLISHABLE_STATUSES[1], now, now),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def check_platform(platform: str, start_date: date, end_date: date):
    """
    Check one platform. Returns list of (scheduled_date, platform, rule, row_ids).
    """
    posts = get_publishable_in_range(platform, start_date, end_date)
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
            non_products = [p for p in group if (p.get("content_type") or "").strip() != "product"]
            if non_products:
                violations.append((
                    scheduled_date,
                    platform,
                    "Saturday has non-product publishable (max product only)",
                    [r["id"] for r in non_products],
                ))
        else:
            if len(group) > 1:
                violations.append((
                    scheduled_date,
                    platform,
                    f"Non-Saturday has {len(group)} publishable (max 1)",
                    [r["id"] for r in group],
                ))
    return violations


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate daily cap invariant per platform (max 1 publishable per non-Saturday date per platform)"
    )
    parser.add_argument("--weeks", type=int, default=12, help="Weeks ahead to check (default 12)")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=DEFAULT_PLATFORMS,
        help="Platforms to validate (default: facebook instagram)",
    )
    args = parser.parse_args()
    today = date.today()
    end_date = today + timedelta(weeks=args.weeks)
    all_violations = []
    for platform in args.platforms:
        violations = check_platform(platform, today, end_date)
        for v in violations:
            all_violations.append(v)
    if all_violations:
        print("Daily cap invariant VIOLATED:", file=sys.stderr)
        for d, platform, rule, row_ids in all_violations:
            print(f"  {d} {platform}: {rule} ids={row_ids}", file=sys.stderr)
        sys.exit(1)
    print(
        f"Daily cap invariant OK: platforms={args.platforms}, range {today}..{end_date}, "
        "max 1 publishable per non-Saturday date per platform."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
