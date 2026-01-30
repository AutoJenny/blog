#!/usr/bin/env python3
"""One-off: query posting_queue for the 5-post incident date to build correlation table.
Usage: python3 scripts/correlation_query_5post_incident.py [SCHEDULED_DATE]
Default SCHEDULED_DATE: 2026-01-29 (5 posts ~17h ago from 2026-01-30).
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    scheduled_date = "2026-01-29"
    if len(sys.argv) > 1:
        scheduled_date = sys.argv[1]

    from config.database import db_manager

    with db_manager.get_cursor() as cur:
        cur.execute("""
            SELECT id, role, content_type, status, scheduled_date, scheduled_time,
                   platform_post_id, error_message, updated_at
            FROM posting_queue
            WHERE platform = 'facebook'
              AND scheduled_date = %s
            ORDER BY id
        """, (scheduled_date,))
        rows = cur.fetchall()

    print(f"Facebook posting_queue rows for scheduled_date = {scheduled_date}")
    print("Columns: id, role, content_type, status, scheduled_date, scheduled_time, platform_post_id, error_message, updated_at")
    print("-" * 80)
    for r in rows:
        print(r)
    print("-" * 80)
    print(f"Total rows: {len(rows)}")
    published = [r for r in rows if r.get("status") == "published"]
    print(f"Published: {len(published)}")
    if published:
        print("\nMapping (platform_post_id -> posting_queue.id):")
        for r in published:
            pid = r.get("platform_post_id") or "(null)"
            print(f"  {pid} -> {r['id']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
