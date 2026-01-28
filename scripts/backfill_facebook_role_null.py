#!/usr/bin/env python3
"""
Phase 6 — Backfill: Assign role to Facebook posting_queue rows where role IS NULL.

Canonical mapping (Matrix v1):
  weekly_word / weekly_phrase / weekly_insult → CULTURE
  message → REASSURANCE
  product → COMMERCE
  depth_long → DEPTH_LONG

Logs every change (before/after). Dry-run mode required for safety.

Usage:
  python3 scripts/backfill_facebook_role_null.py [--dry-run]
  python3 scripts/backfill_facebook_role_null.py --dry-run   # preview only
  python3 scripts/backfill_facebook_role_null.py            # apply updates
"""

import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import db_manager

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

CONTENT_TYPE_TO_ROLE = {
    "weekly_word": "CULTURE",
    "weekly_phrase": "CULTURE",
    "weekly_insult": "CULTURE",
    "message": "REASSURANCE",
    "product": "COMMERCE",
    "depth_long": "DEPTH_LONG",
}


def run(dry_run: bool):
    updates = []
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, content_type, role, scheduled_date, status
            FROM posting_queue
            WHERE platform = 'facebook'
              AND role IS NULL
              AND content_type IN ('weekly_word','weekly_phrase','weekly_insult','product','message','depth_long')
            ORDER BY content_type, scheduled_date, id
        """)
        rows = cursor.fetchall()
        for row in rows:
            ct = row["content_type"]
            role = CONTENT_TYPE_TO_ROLE.get(ct)
            if not role:
                continue
            updates.append((row["id"], ct, role, row["scheduled_date"], row["status"]))
            if not dry_run:
                cursor.execute(
                    "UPDATE posting_queue SET role = %s, updated_at = NOW() WHERE id = %s",
                    (role, row["id"]),
                )
    return updates


def main():
    ap = argparse.ArgumentParser(description="Backfill Facebook posting_queue.role where NULL")
    ap.add_argument("--dry-run", action="store_true", help="Log changes only, do not write")
    args = ap.parse_args()
    mode = "dry-run" if args.dry_run else "apply"
    logger.info("Phase 6 role backfill — %s", mode)
    updates = run(args.dry_run)
    for uid, ct, role, sd, st in updates:
        logger.info("  id=%s content_type=%s → role=%s (scheduled_date=%s status=%s)", uid, ct, role, sd, st)
    logger.info("Total: %s rows %s", len(updates), "would be updated" if args.dry_run else "updated")
    if not args.dry_run and updates:
        logger.info("Run phase6_role_and_message_report or Step 1 SQL to verify zero role IS NULL for relevant types.")


if __name__ == "__main__":
    main()
