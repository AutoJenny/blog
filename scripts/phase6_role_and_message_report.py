#!/usr/bin/env python3
"""
Phase 6 — Report: Facebook role-less posts and message posts for a test week.

O1 Step 1: All posting_queue rows where platform='facebook', role IS NULL,
           content_type IN ('weekly_word','weekly_phrase','weekly_insult','product','message','depth_long').

O2 Step 1: All Facebook message posts for the test week (any day), with scheduled_date, role, status.

Usage:
  python3 scripts/phase6_role_and_message_report.py [--week 2026-W5] [--out path]
"""

import os
import sys
import argparse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import db_manager


def parse_iso_week(s: str):
    y, w = s.split("-W")
    return int(y), int(w)


def week_dates(year: int, week: int):
    jan4 = date(year, 1, 4)
    mon = jan4 - timedelta(days=jan4.isoweekday() - 1)
    start = mon + timedelta(weeks=week - 1)
    end = start + timedelta(days=6)
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default="2026-W5")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    year, week = parse_iso_week(args.week)
    start, end = week_dates(year, week)
    start_s, end_s = start.isoformat(), end.isoformat()

    lines = []
    def out(s=""):
        lines.append(s)

    out("=" * 60)
    out("Phase 6 — Role-less posts and message posts report")
    out("=" * 60)
    out(f"Test week: {args.week} ({start_s} .. {end_s})")
    out()

    with db_manager.get_cursor() as cursor:
        # O1 Step 1: Facebook role-less posts (relevant content types)
        out("--- O1 Step 1: Facebook posts with role IS NULL ---")
        q1 = """
        SELECT id, platform, content_type, role, status,
               scheduled_date, scheduled_time, idea_id, product_id
        FROM posting_queue
        WHERE platform = 'facebook'
          AND role IS NULL
          AND content_type IN ('weekly_word','weekly_phrase','weekly_insult','product','message','depth_long')
        ORDER BY content_type, scheduled_date, id
        """
        out("SQL:")
        out(q1.strip())
        out()
        cursor.execute(q1)
        rows = cursor.fetchall()
        out(f"Rows: {len(rows)}")
        for r in rows:
            out(str(dict(r)))
        out()

        # O2 Step 1: All Facebook message posts for the test week (any day)
        out("--- O2 Step 1: Facebook message posts for this week (any day) ---")
        q2 = """
        SELECT id, platform, content_type, role, status,
               scheduled_date, scheduled_time,
               EXTRACT(ISODOW FROM scheduled_date) as iso_weekday
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type = 'message'
          AND scheduled_date BETWEEN %s AND %s
        ORDER BY scheduled_date, id
        """
        out("SQL:")
        out(q2.strip())
        out(f"Params: ({start_s}, {end_s})")
        out()
        cursor.execute(q2, (start_s, end_s))
        msg_rows = cursor.fetchall()
        out(f"Rows: {len(msg_rows)}")
        for r in msg_rows:
            out(str(dict(r)))
        out()

    text = "\n".join(lines)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
