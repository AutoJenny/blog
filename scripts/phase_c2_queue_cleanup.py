#!/usr/bin/env python3
"""
Phase C2 queue cleanup — export affected IDs to CSV, then cancel rows.

1. Export IDs for non-Tuesday language (ready/pending) to docs/PHASE_C2_AFFECTED_IDS_LANGUAGE_<date>.csv
2. Export IDs for duplicate product rows (to cancel) to docs/PHASE_C2_AFFECTED_IDS_PRODUCT_<date>.csv
3. UPDATE posting_queue: set status='cancelled', error_message='...' for those IDs

Run: PYTHONPATH=. python3 scripts/phase_c2_queue_cleanup.py
Dry-run (export only, no updates): PYTHONPATH=. python3 scripts/phase_c2_queue_cleanup.py --dry-run
"""
import os
import sys
import csv
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
DATE_TAG = date.today().strftime("%Y%m%d")
LANG_CSV = os.path.join(DOCS_DIR, f"PHASE_C2_AFFECTED_IDS_LANGUAGE_{DATE_TAG}.csv")
PRODUCT_CSV = os.path.join(DOCS_DIR, f"PHASE_C2_AFFECTED_IDS_PRODUCT_{DATE_TAG}.csv")

LANG_MSG = "Phase C2: non-Tuesday language row neutralised"
PRODUCT_MSG = "Phase C2: duplicate product row neutralised"


def run_query(sql, params=None):
    with db_manager.get_cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def run_update(sql, params=None):
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            # autocommit is True on connection
            return cur.rowcount


def export_language_ids():
    rows = run_query("""
        SELECT id, content_type, idea_id, scheduled_date, status
        FROM posting_queue
        WHERE platform = 'facebook'
          AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
          AND scheduled_date IS NOT NULL
          AND EXTRACT(ISODOW FROM scheduled_date) != 2
          AND status IN ('ready', 'pending')
        ORDER BY id
    """)
    ids = [r["id"] for r in rows]
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(LANG_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "content_type", "idea_id", "scheduled_date", "status"])
        for r in rows:
            w.writerow([r["id"], r["content_type"], r["idea_id"], r["scheduled_date"], r["status"]])
    return ids


def export_product_ids():
    # All ids in duplicate groups except min(id) per group
    rows = run_query("""
        WITH dup AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY platform, content_type, product_id, scheduled_date ORDER BY id) AS rn
            FROM posting_queue
            WHERE platform = 'facebook'
              AND content_type = 'product'
              AND product_id IS NOT NULL
              AND scheduled_date IS NOT NULL
        )
        SELECT pq.id, pq.product_id, pq.scheduled_date, pq.status
        FROM posting_queue pq
        JOIN dup ON dup.id = pq.id
        WHERE dup.rn > 1
        ORDER BY pq.id
    """)
    ids = [r["id"] for r in rows]
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(PRODUCT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "product_id", "scheduled_date", "status"])
        for r in rows:
            w.writerow([r["id"], r["product_id"], r["scheduled_date"], r["status"]])
    return ids


def cancel_language(ids):
    if not ids:
        return 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE posting_queue
                SET status = 'cancelled', error_message = %s
                WHERE id = ANY(%s)
            """, (LANG_MSG, ids))
            n = cur.rowcount
    return n


def cancel_product(ids):
    if not ids:
        return 0
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE posting_queue
                SET status = 'cancelled', error_message = %s
                WHERE id = ANY(%s)
            """, (PRODUCT_MSG, ids))
            n = cur.rowcount
    return n


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("Phase C2 cleanup — DRY RUN (export only, no updates)\n")
    else:
        print("Phase C2 cleanup — export IDs then cancel\n")

    # Export language IDs
    lang_ids = export_language_ids()
    print(f"Exported {len(lang_ids)} non-Tuesday language IDs to {LANG_CSV}")

    # Export product IDs (duplicates to cancel)
    product_ids = export_product_ids()
    print(f"Exported {len(product_ids)} duplicate product IDs to {PRODUCT_CSV}")

    if dry_run:
        print("\nDry run: no updates performed.")
        return 0

    if not lang_ids and not product_ids:
        print("\nNo rows to cancel.")
        return 0

    # Execute cancellations
    lang_updated = cancel_language(lang_ids)
    product_updated = cancel_product(product_ids)
    print(f"\nCancelled non-Tuesday language rows: {lang_updated}")
    print(f"Cancelled duplicate product rows: {product_updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
