#!/usr/bin/env python3
"""
Phase C2 — Queue hygiene analysis (READ-ONLY).
Runs SQL to quantify duplicates and non-Tuesday language rows.
No data is modified. Output is for REPORT_PHASE_C2_QUEUE_HYGIENE.md.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run(qname: str, sql: str, params=None):
    with db_manager.get_cursor() as cur:
        cur.execute(sql, params or ())
        rows = cur.fetchall()
    return rows

def main():
    print("=== Phase C2 queue hygiene analysis (read-only) ===\n")

    # 1) Duplicate language rows: (platform, content_type, idea_id, scheduled_date) with COUNT > 1
    dup_lang = run("dup_lang", """
        SELECT platform, content_type, idea_id, scheduled_date,
               COUNT(*) AS cnt,
               array_agg(id ORDER BY id) AS queue_ids
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
          AND idea_id IS NOT NULL
          AND scheduled_date IS NOT NULL
        GROUP BY platform, content_type, idea_id, scheduled_date
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    """)
    print("1) Duplicate language rows (same platform, content_type, idea_id, scheduled_date):")
    print(f"   Groups with duplicates: {len(dup_lang)}")
    if dup_lang:
        total_dup_rows = sum(r['cnt'] - 1 for r in dup_lang)  # extra rows per group
        print(f"   Total duplicate rows (to neutralise): {total_dup_rows}")
        for r in dup_lang[:10]:
            print(f"   - {r['content_type']} idea_id={r['idea_id']} date={r['scheduled_date']} cnt={r['cnt']} ids={r['queue_ids'][:5]}...")
        if len(dup_lang) > 10:
            print(f"   ... and {len(dup_lang) - 10} more groups")
    print()

    # 2) Non-Tuesday language rows (any status)
    non_tue = run("non_tue", """
        SELECT content_type, status, scheduled_date, COUNT(*) AS cnt
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
          AND scheduled_date IS NOT NULL
          AND EXTRACT(ISODOW FROM scheduled_date) != 2
        GROUP BY content_type, status, scheduled_date
        ORDER BY scheduled_date, content_type, status
    """)
    print("2) Non-Tuesday language rows (EXTRACT(ISODOW FROM scheduled_date) != 2):")
    total_non_tue = sum(r['cnt'] for r in non_tue)
    print(f"   Total rows: {total_non_tue}")
    if non_tue:
        for r in non_tue[:15]:
            print(f"   - {r['content_type']} {r['status']} {r['scheduled_date']} cnt={r['cnt']}")
        if len(non_tue) > 15:
            print(f"   ... and {len(non_tue) - 15} more (content_type, status, date) groups")
    print()

    # 3) Count by content_type and status for language (all time, for context)
    lang_summary = run("lang_summary", """
        SELECT content_type, status, COUNT(*) AS cnt
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
        GROUP BY content_type, status
        ORDER BY content_type, status
    """)
    print("3) Language rows by content_type and status (all dates):")
    for r in lang_summary:
        print(f"   - {r['content_type']} {r['status']}: {r['cnt']}")
    print()

    # 4) Risky: language rows that are ready/pending and scheduled in the past (could be picked if time check bug)
    past_ready = run("past_ready", """
        SELECT COUNT(*) AS cnt
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
          AND status IN ('ready', 'pending')
          AND scheduled_date IS NOT NULL
          AND scheduled_time IS NOT NULL
          AND (scheduled_date::date + scheduled_time::time)::timestamp < NOW()
    """)
    print("4) Language rows ready/pending with scheduled time in the past (could be due):")
    print(f"   Count: {past_ready[0]['cnt'] if past_ready else 0}")
    print()

    # 5) Product duplicates (same platform, content_type, product_id, scheduled_date)
    dup_product = run("dup_product", """
        SELECT platform, content_type, product_id, scheduled_date,
               COUNT(*) AS cnt, array_agg(id ORDER BY id) AS queue_ids
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type = 'product'
          AND product_id IS NOT NULL
          AND scheduled_date IS NOT NULL
        GROUP BY platform, content_type, product_id, scheduled_date
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    """)
    print("5) Duplicate product rows (same platform, content_type, product_id, scheduled_date):")
    print(f"   Groups with duplicates: {len(dup_product)}")
    if dup_product:
        print(f"   Total duplicate product rows: {sum(r['cnt'] - 1 for r in dup_product)}")
    print()

    # 6) CULTURE / authority / depth counts (do not touch)
    culture = run("culture", """
        SELECT content_type, role, status, COUNT(*) AS cnt
        FROM posting_queue
        WHERE platform = 'facebook'
          AND (content_type = 'culture_fact' OR role IN ('AUTHORITY_SHORT', 'DEPTH_LONG'))
        GROUP BY content_type, role, status
        ORDER BY content_type, role, status
    """)
    print("6) Rows explicitly out of scope (do not touch): culture_fact, AUTHORITY_SHORT, DEPTH_LONG:")
    for r in culture:
        print(f"   - {r['content_type']} {r['role']} {r['status']}: {r['cnt']}")

    print("\n=== End of read-only analysis ===")

if __name__ == "__main__":
    main()
