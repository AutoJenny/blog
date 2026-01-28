#!/usr/bin/env python3
"""
Step 1 — Establish Ground Truth (DB-first) for Facebook Matrix v1 drift fix.

Runs the exact SQL from the briefing to produce:
  (1) posting_queue rows for the calendar week (Facebook, date range)
  (2) Weekly language streams (calendar_ideas / calendar_category_cycles for 2026-W5)
  (3) Product scheduling source (post_type_channel_config + daily_posts_schedule)
  (4) Message/reassurance scheduling source (post_type_channel_config + code reference)

Output: printed to stdout; redirect to docs/DELIVERABLE_A_MATRIX_GROUND_TRUTH.md if desired.

Usage:
  python scripts/step1_matrix_ground_truth.py [--week 2026-W5] [--out path]
  Default week: 2026-W5. Default date range: 2026-01-26 to 2026-02-01 (Mon–Sun).
"""

import os
import sys
import argparse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager


def parse_iso_week(s: str):
    """e.g. '2026-W5' -> (2026, 5). Week 1 is first week with Thursday."""
    y, w = s.split("-W")
    return int(y), int(w)


def week_to_monday_sunday(year: int, week: int):
    """Return (week_monday, week_sunday) for ISO week."""
    jan4 = date(year, 1, 4)
    # Monday of week 1
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    week_monday = week1_monday + timedelta(days=(week - 1) * 7)
    week_sunday = week_monday + timedelta(days=6)
    return week_monday, week_sunday


def main():
    ap = argparse.ArgumentParser(description="Step 1 Matrix ground truth SQL")
    ap.add_argument("--week", default="2026-W5", help="ISO week e.g. 2026-W5")
    ap.add_argument("--out", default=None, help="Write output to file")
    args = ap.parse_args()
    year, week = parse_iso_week(args.week)
    start_date, end_date = week_to_monday_sunday(year, week)
    start_s = start_date.isoformat()
    end_s = end_date.isoformat()

    out_lines = []
    def w(s=""):
        out_lines.append(s)

    w("=" * 80)
    w("DELIVERABLE A — Step 1 Ground Truth (Facebook Matrix v1)")
    w("=" * 80)
    w(f"Week: {args.week}  |  Date range: {start_s} .. {end_s}")
    w("")

    with db_manager.get_cursor() as cursor:
        # (1) posting_queue – exact columns from briefing (omit channel_type if not in schema)
        w("--- 1. posting_queue (Facebook, Social Posts row) ---")
        q1 = """
SELECT id, platform, role, content_type, status,
       scheduled_date, scheduled_time, rota_year, rota_week,
       topic_id, angle_id
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date BETWEEN %s AND %s
ORDER BY scheduled_date, scheduled_time, id;
"""
        w("SQL:")
        w(q1.strip())
        w("")
        try:
            cursor.execute(q1, (start_s, end_s))
            rows = cursor.fetchall()
            w(f"Output ({len(rows)} rows):")
            for r in rows:
                w(str(dict(r)))
        except Exception as e:
            w(f"Error: {e}")
            # fallback without rota_year/rota_week/topic_id/angle_id if needed
            try:
                q1b = """
SELECT id, platform, role, content_type, status,
       scheduled_date, scheduled_time
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date BETWEEN %s AND %s
ORDER BY scheduled_date, scheduled_time, id;
"""
                cursor.execute(q1b, (start_s, end_s))
                rows = cursor.fetchall()
                w("(Fallback query without rota_year/rota_week/topic_id/angle_id):")
                for r in rows:
                    w(str(dict(r)))
            except Exception as e2:
                w(f"Fallback error: {e2}")
        w("")

        # (2) Weekly language streams – tables that drive word/phrase/insult
        w("--- 2. Weekly language streams (word/phrase/insult) ---")
        w("Source: calendar_ideas (item_classification), calendar_category_cycles (cycle).")
        q_cycles = """
SELECT category, cycle_start_week
FROM calendar_category_cycles
WHERE category IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
ORDER BY category;
"""
        w("SQL (calendar_category_cycles):")
        w(q_cycles.strip())
        w("")
        cursor.execute(q_cycles)
        for r in cursor.fetchall():
            w(str(dict(r)))
        q_ideas = """
SELECT id, item_classification, idea_title, position, created_at
FROM calendar_ideas
WHERE item_classification IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
ORDER BY item_classification, position
LIMIT 50;
"""
        w("")
        w("SQL (calendar_ideas — language items):")
        w(q_ideas.strip())
        w("")
        cursor.execute(q_ideas)
        for r in cursor.fetchall():
            w(str(dict(r)))
        w("")

        # (3) Product scheduling source
        w("--- 3. Product scheduling source ---")
        q_ptcc = """
SELECT post_type, channel, publication_day, publication_time, is_active
FROM post_type_channel_config
WHERE channel = 'facebook' AND post_type = 'product' AND is_active = TRUE;
"""
        w("SQL (post_type_channel_config — product):")
        w(q_ptcc.strip())
        w("")
        cursor.execute(q_ptcc)
        for r in cursor.fetchall():
            w(str(dict(r)))
        q_dps = """
SELECT id, name, platform, content_type, days, time, is_active
FROM daily_posts_schedule
WHERE is_active = TRUE AND platform = 'facebook' AND content_type = 'product';
"""
        w("")
        w("SQL (daily_posts_schedule — product weekdays):")
        w(q_dps.strip())
        w("")
        cursor.execute(q_dps)
        for r in cursor.fetchall():
            w(str(dict(r)))
        w("")

        # (4) Message/reassurance scheduling source
        w("--- 4. Message/reassurance scheduling source ---")
        q_msg_cfg = """
SELECT post_type, channel, publication_day, publication_time, is_active
FROM post_type_channel_config
WHERE channel = 'facebook' AND post_type = 'message' AND is_active = TRUE;
"""
        w("SQL (post_type_channel_config — message):")
        w(q_msg_cfg.strip())
        w("")
        cursor.execute(q_msg_cfg)
        for r in cursor.fetchall():
            w(str(dict(r)))
        w("")
        w("Code reference: scripts/automated_message_post_creator.py")
        w("  self.publication_day = 6  # Saturday (1=Monday, 7=Sunday)")
        w("  self.publication_time = '14:30'")
        w("(Matrix v1 target: Wednesday = 3)")
        w("")

    out_text = "\n".join(out_lines)
    if args.out:
        with open(args.out, "w") as f:
            f.write(out_text)
        print(f"Wrote {args.out}")
    else:
        print(out_text)


if __name__ == "__main__":
    main()
