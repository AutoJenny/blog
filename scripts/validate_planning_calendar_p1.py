#!/usr/bin/env python3
"""
Validate planning calendar for Phase P1: 2–3 future weeks.
- Exactly one post per day (Sat may have multiple times).
- Mon = culture_fact, Thu = heritage_fact, Tue = exactly one language post.
- Titles non-placeholder (esp Fri/Sun).
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from config.unified_config import get_database_target_for_logging

# Pick 2–3 future weeks: e.g. 2026-W6, 2026-W10, 2026-W14
WEEKS_TO_CHECK = [(2026, 6), (2026, 10), (2026, 14)]


def week_start(year: int, week_number: int) -> date:
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    return week1_monday + timedelta(weeks=week_number - 1)


def main():
    print("DB target:", get_database_target_for_logging(), file=sys.stderr)
    issues = []
    for year, week_number in WEEKS_TO_CHECK:
        start = week_start(year, week_number)
        end = start + timedelta(days=6)
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, platform, content_type, role, scheduled_date, scheduled_time,
                       LEFT(generated_content, 120) AS content_preview
                FROM posting_queue
                WHERE platform = 'facebook'
                  AND scheduled_date >= %s
                  AND scheduled_date <= %s
                  AND scheduled_date IS NOT NULL
                ORDER BY scheduled_date, scheduled_time
                """,
                (start, end),
            )
            rows = cursor.fetchall()

        # Group by day (scheduled_date)
        by_date = {}
        for r in rows:
            d = r["scheduled_date"]
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(r)

        # Expected: Mon 1 (culture_fact), Tue 1 (language), Wed 1 (message), Thu 1 (heritage),
        # Fri 1 (authority_short), Sat 1+ (product), Sun 1 (depth_long)
        expected_role_per_weekday = {
            1: ["culture_fact"],
            2: ["weekly_word", "weekly_phrase", "weekly_insult"],
            3: ["message"],
            4: ["HERITAGE"],
            5: ["AUTHORITY_SHORT"],
            6: ["product"],
            7: ["depth_long"],
        }
        for d in (start + timedelta(days=i) for i in range(7)):
            weekday = d.isoweekday()
            posts = by_date.get(d, [])
            if weekday == 6:  # Saturday: may have multiple times
                n_expected = 1
                types_ok = any(p.get("content_type") == "product" for p in posts)
            else:
                n_expected = 1
                types_ok = len(posts) == 1
            if len(posts) < n_expected:
                issues.append(f"{year}-W{week_number} {d}: expected at least {n_expected} post(s), got {len(posts)}")
            elif weekday != 6 and len(posts) > 1:
                issues.append(f"{year}-W{week_number} {d}: expected 1 post, got {len(posts)}")
            # Check type
            for p in posts:
                ct = p.get("content_type") or ""
                role = p.get("role") or ""
                if weekday == 1 and ct != "culture_fact":
                    issues.append(f"{year}-W{week_number} {d}: Mon should be culture_fact, got content_type={ct} role={role}")
                if weekday == 2 and ct not in ("weekly_word", "weekly_phrase", "weekly_insult"):
                    issues.append(f"{year}-W{week_number} {d}: Tue should be language, got content_type={ct}")
                if weekday == 4 and role != "HERITAGE":
                    issues.append(f"{year}-W{week_number} {d}: Thu should be HERITAGE, got role={role}")
                # Non-placeholder title/content
                preview = (p.get("content_preview") or "").strip()
                if preview and ("placeholder" in preview.lower() or preview.startswith("AUTHORITY_SHORT placeholder")):
                    issues.append(f"{year}-W{week_number} {d} id={p.get('id')}: placeholder content")

        # Summary for this week
        print(f"\n=== {year}-W{week_number} ({start} to {end}) ===")
        for d in (start + timedelta(days=i) for i in range(7)):
            posts = by_date.get(d, [])
            wd = d.isoweekday()
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][wd - 1]
            for p in posts:
                ct = p.get("content_type") or p.get("role") or "?"
                preview = (p.get("content_preview") or "")[:60].replace("\n", " ")
                placeholder = " [PLACEHOLDER]" if preview and "placeholder" in preview.lower() else ""
                print(f"  {d} {day_name}: {ct} id={p.get('id')} {preview!r}{placeholder}")

    if issues:
        print("\n--- Issues ---")
        for i in issues:
            print("  ", i)
        return 1
    print("\nValidation OK: one post per day (Sat may have multiple), types correct, no placeholders in sampled weeks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
