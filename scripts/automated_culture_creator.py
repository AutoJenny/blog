#!/usr/bin/env python3
"""
Automated Culture Creator — CULTURE v1.1 (Phase P1.1 normalised)

Creates posting_queue entries for Monday CULTURE (culture_fact) from culture_library.
Phase P1: One slot = one row. Insert skeleton if missing; regenerate in place if failed/empty/placeholder; skip if valid.
- 90-day repeat avoidance; deterministic pick; scheduled_time 15:00.
- CLI: --weeks-ahead, --start-date, --dry-run, --force.
"""

import argparse
import logging
import sys
from datetime import date, timedelta, time, datetime
from typing import Optional, Dict, Any

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.content_roles.culture_generator import (
    pick_culture_for_slot,
    CULTURE_SCHEDULED_TIME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs",
                "automated_culture_creator.log",
            )
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PLATFORM = "facebook"
CONTENT_TYPE = "culture_fact"
ROLE = "CULTURE"
VALID_STATUSES = ("ready", "approved", "scheduled", "published")


def _row_is_valid(row: Dict[str, Any]) -> bool:
    """Valid = non-empty generated_content, not placeholder, status in valid set."""
    content = (row.get("generated_content") or "").strip()
    if not content:
        return False
    if "placeholder" in content.lower():
        return False
    status = (row.get("status") or "").strip()
    return status in VALID_STATUSES


def get_monday_of_week(year: int, week_number: int) -> date:
    """Return Monday of the given ISO (year, week_number)."""
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    return week1_monday + timedelta(weeks=week_number - 1)


def iter_monday_dates(weeks_ahead: int, from_date: date):
    """Yield (d, weekday) for each Monday in the next weeks_ahead weeks, >= from_date."""
    year, week_number, _ = from_date.isocalendar()
    monday = get_monday_of_week(year, week_number)
    if monday > from_date:
        monday -= timedelta(days=7)
    for _ in range(weeks_ahead):
        d = monday
        if d >= from_date:
            yield d, d.isoweekday()
        monday += timedelta(days=7)


def ensure_culture_slot(
    target_date: date,
    weekday: int,
    dry_run: bool,
    force: bool,
) -> str:
    """
    One slot = one row. Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    scheduled_time_str = CULTURE_SCHEDULED_TIME
    scheduled_time_obj = time(15, 0)
    scheduled_timestamp = datetime.combine(target_date, scheduled_time_obj)
    year, week_number, _ = target_date.isocalendar()

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND content_type = %s AND scheduled_date = %s
                LIMIT 1
                """,
                (PLATFORM, CONTENT_TYPE, target_date),
            )
            row = cursor.fetchone()

            if row:
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                row_dict = dict(row) if hasattr(row, "keys") else {"generated_content": row[1], "status": row[2]}
                if not force and _row_is_valid(row_dict):
                    logger.info("Culture slot %s valid, skip queue_id=%s", target_date, queue_id)
                    return "skipped"
                # Regenerate in place
                payload = pick_culture_for_slot(target_date, weekday, year, week_number)
                if not payload:
                    logger.error("No culture payload for %s", target_date)
                    return "failed"
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate culture queue_id=%s date=%s", queue_id, target_date)
                    return "regenerated"
                cursor.execute(
                    """
                    UPDATE posting_queue
                    SET culture_library_id = %s, generated_content = %s, status = 'ready',
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (payload["culture_library_id"], payload["generated_content"], queue_id),
                )
                conn.commit()
                logger.info("Regenerated culture_fact queue_id=%s date=%s", queue_id, target_date)
                return "regenerated"
            else:
                # Insert skeleton then fill
                payload = pick_culture_for_slot(target_date, weekday, year, week_number)
                if not payload:
                    logger.error("No culture payload for %s", target_date)
                    return "failed"
                if dry_run:
                    logger.info("[DRY-RUN] Would create culture_fact date=%s", target_date)
                    return "created"
                cursor.execute(
                    """
                    INSERT INTO posting_queue (
                        platform, role, content_type, culture_library_id,
                        generated_content, status,
                        scheduled_date, scheduled_time, scheduled_timestamp,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, 'ready', %s, %s, %s, NOW(), NOW()
                    )
                    RETURNING id
                    """,
                    (
                        PLATFORM,
                        ROLE,
                        CONTENT_TYPE,
                        payload["culture_library_id"],
                        payload["generated_content"],
                        target_date,
                        scheduled_time_str,
                        scheduled_timestamp,
                    ),
                )
                r = cursor.fetchone()
                qid = r["id"] if r and isinstance(r, dict) else (r[0] if r else None)
                conn.commit()
                if qid:
                    logger.info("Created culture_fact queue_id=%s date=%s", qid, target_date)
                    return "created"
                return "failed"
    return "failed"


def main():
    parser = argparse.ArgumentParser(description="CULTURE v1.1 (P1.1): Monday culture_fact — one slot = one row.")
    parser.add_argument("--weeks-ahead", type=int, default=12, help="Weeks to look ahead (default 12)")
    parser.add_argument("--start-date", type=str, default=None, help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--force", action="store_true", help="Regenerate even if slot is valid")
    args = parser.parse_args()
    today = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else date.today()
    stats = {"slots": 0, "created": 0, "regenerated": 0, "skipped": 0, "failed": 0}
    try:
        for d, weekday in iter_monday_dates(args.weeks_ahead, today):
            stats["slots"] += 1
            outcome = ensure_culture_slot(d, weekday, dry_run=args.dry_run, force=args.force)
            stats[outcome] = stats.get(outcome, 0) + 1
        logger.info("Automated culture creator complete: %s", stats)
        sys.exit(0 if stats["failed"] == 0 else 1)
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
