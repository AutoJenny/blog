#!/usr/bin/env python3
"""
Tuesday eligibility report for Phase P1.
- Count eligible calendar_ideas per classification (weekly_word, weekly_phrase, weekly_insult).
- For next N weeks, show how many ideas the 90-day exclusion blocks vs available.
- Identify weeks with 0 eligible (pre-generation failure risk).
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

REPEAT_DAYS = 90
LANGUAGE_TYPES = ["weekly_word", "weekly_phrase", "weekly_insult"]


def get_tuesday_date_for_week(year: int, week_number: int) -> date | None:
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    monday = week1_monday + timedelta(weeks=week_number - 1)
    tuesday = monday + timedelta(days=1)
    if tuesday.isocalendar()[0] != year or tuesday.isocalendar()[1] != week_number:
        return None
    return tuesday


def get_idea_ids_used_in_last_90_days(target_date: date) -> set:
    cutoff = target_date - timedelta(days=REPEAT_DAYS)
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT idea_id FROM posting_queue
            WHERE idea_id IS NOT NULL
            AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
            AND scheduled_date >= %s
            """,
            (cutoff,),
        )
        rows = cursor.fetchall()
    return {r["idea_id"] for r in rows if r.get("idea_id")}


def main():
    weeks_ahead = int(os.environ.get("WEEKS_AHEAD", "12"))

    # 1) Count calendar_ideas per classification
    print("=== calendar_ideas counts per classification ===")
    with db_manager.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT item_classification, count(*) AS n
            FROM calendar_ideas
            WHERE item_classification IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
            GROUP BY item_classification
            ORDER BY item_classification
            """
        )
        rows = cursor.fetchall()
    pool = {r["item_classification"]: r["n"] for r in rows}
    for ct in LANGUAGE_TYPES:
        print(f"  {ct}: {pool.get(ct, 0)}")
    total = sum(pool.get(ct, 0) for ct in LANGUAGE_TYPES)
    print(f"  total (all three): {total}")

    # 2) Upcoming weeks: for each Tuesday, content_type and eligible count
    print("\n=== 90-day exclusion: blocked vs available per Tuesday (next %s weeks) ===" % weeks_ahead)
    today = date.today()
    failures = []
    for i in range(weeks_ahead):
        d = today + timedelta(weeks=i)
        y, w, _ = d.isocalendar()
        tuesday = get_tuesday_date_for_week(y, w)
        if not tuesday:
            continue
        content_type = LANGUAGE_TYPES[(w - 1) % 3]
        exclude = get_idea_ids_used_in_last_90_days(tuesday)
        pool_size = pool.get(content_type, 0)
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM calendar_ideas
                WHERE item_classification = %s
                """,
                (content_type,),
            )
            all_ids = {r["id"] for r in cursor.fetchall()}
        eligible_ids = all_ids - exclude
        eligible_count = len(eligible_ids)
        blocked = len(all_ids & exclude)
        print(f"  {tuesday} (W{w}) {content_type}: pool={pool_size} blocked_in_window={blocked} eligible={eligible_count}")
        if eligible_count == 0:
            failures.append((tuesday, w, content_type))

    if failures:
        print("\n=== Weeks with NO eligible idea (pre-generation will fail) ===")
        for tuesday, w, ct in failures:
            print(f"  {tuesday} W{w} {ct}")
        print("\n=== Proposed fixes ===")
        print("  1. Increase Tuesday pool: add more calendar_ideas for each classification (weekly_word, weekly_phrase, weekly_insult).")
        print("  2. Adjust 90-day exclusion: reduce REPEAT_DAYS in automated_weekly_content_creator.py (e.g. 60) so more ideas are eligible.")
        print("  3. Fallback policy: when eligible=0, allow re-use of least-recently-used idea (requires code change).")
    else:
        print("\nNo failures: all %s Tuesdays have at least one eligible idea." % (weeks_ahead,))

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
