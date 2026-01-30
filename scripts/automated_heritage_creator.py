#!/usr/bin/env python3
"""
Automated Heritage Creator — Phase H1 (Phase P1.1 normalised)

Creates posting_queue entries for Thursday HERITAGE (heritage_fact) from heritage_library.
Phase P1: One slot = one row per platform. Insert skeleton if missing; regenerate in place if failed/empty/placeholder; skip if valid.
- Approach A: orchestrator selects once per slot, calls generate_for_slot(platform, slot_key, selection) for both platforms.
- CLI: --weeks-ahead, --dry-run, --force. Legacy ensure_heritage_slot targets facebook only.
"""

import argparse
import logging
import sys
from datetime import date, timedelta, time, datetime
from typing import Optional, Dict, Any, List, Tuple

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.content_roles.heritage_generator import (
    pick_heritage_for_thursday,
    HERITAGE_SCHEDULED_TIME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs",
                "automated_heritage_creator.log",
            )
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PLATFORM = "facebook"
ROLE = "HERITAGE"
CONTENT_TYPE = "heritage_fact"
VALID_STATUSES = ("ready", "approved", "scheduled", "published")


def _row_is_valid(row: Dict[str, Any]) -> bool:
    content = (row.get("generated_content") or "").strip()
    if not content:
        return False
    if "placeholder" in content.lower():
        return False
    status = (row.get("status") or "").strip()
    return status in VALID_STATUSES


def get_monday_of_week(year: int, week_number: int) -> date:
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    return week1_monday + timedelta(weeks=week_number - 1)


def iter_thursday_dates(weeks_ahead: int, from_date: date):
    year, week_number, _ = from_date.isocalendar()
    monday = get_monday_of_week(year, week_number)
    if monday > from_date:
        monday -= timedelta(days=7)
    for _ in range(weeks_ahead):
        d = monday + timedelta(days=3)
        if d >= from_date:
            yield d, d.isoweekday()
        monday += timedelta(days=7)


def get_slot_dates(weeks_ahead: int, from_date: date) -> List[Tuple[date, int]]:
    """Return list of (scheduled_date, weekday) for Thursdays in range. For orchestrator."""
    return list(iter_thursday_dates(weeks_ahead, from_date))


def select_for_slot(
    target_date: date,
    weekday: int,
    year: int,
    week_number: int,
) -> Optional[Dict[str, Any]]:
    """
    Select once per slot (Approach A). Returns shared selection object for both platforms.
    Keys: heritage_library_id, scheduled_date, scheduled_time, generated_content.
    """
    payload = pick_heritage_for_thursday(target_date, year, week_number)
    if not payload:
        return None
    return {
        "heritage_library_id": payload["heritage_library_id"],
        "scheduled_date": target_date,
        "scheduled_time": HERITAGE_SCHEDULED_TIME,
        "generated_content": payload.get("generated_content", ""),
    }


def generate_for_slot(
    platform: str,
    slot_key: Dict[str, Any],
    selection: Dict[str, Any],
    dry_run: bool,
    force: bool,
) -> str:
    """
    Create or update one row for (platform, slot_key). Idempotent.
    slot_key: {scheduled_date, role, content_type}.
    selection: from select_for_slot (heritage_library_id, scheduled_date, scheduled_time, generated_content).
    Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    target_date = slot_key["scheduled_date"]
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    scheduled_time_str = selection.get("scheduled_time") or HERITAGE_SCHEDULED_TIME
    scheduled_time_obj = time(15, 0)
    scheduled_timestamp = datetime.combine(target_date, scheduled_time_obj)

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND role = %s AND content_type = %s AND scheduled_date = %s
                LIMIT 1
                """,
                (platform, ROLE, CONTENT_TYPE, target_date),
            )
            row = cursor.fetchone()

            if row:
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                row_dict = dict(row) if hasattr(row, "keys") else {"generated_content": row[1], "status": row[2]}
                if not force and _row_is_valid(row_dict):
                    logger.info("Heritage slot %s %s valid, skip queue_id=%s", platform, target_date, queue_id)
                    return "skipped"
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate heritage %s queue_id=%s date=%s", platform, queue_id, target_date)
                    return "regenerated"
                cursor.execute(
                    """
                    UPDATE posting_queue
                    SET heritage_library_id = %s, generated_content = %s, status = 'ready', updated_at = NOW()
                    WHERE id = %s
                    """,
                    (selection["heritage_library_id"], selection["generated_content"], queue_id),
                )
                conn.commit()
                logger.info("Regenerated heritage_fact %s queue_id=%s date=%s", platform, queue_id, target_date)
                return "regenerated"
            else:
                if dry_run:
                    logger.info("[DRY-RUN] Would create heritage_fact %s date=%s", platform, target_date)
                    return "created"
                cursor.execute(
                    """
                    INSERT INTO posting_queue (
                        platform, role, content_type, heritage_library_id,
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
                        platform,
                        ROLE,
                        CONTENT_TYPE,
                        selection["heritage_library_id"],
                        selection["generated_content"],
                        target_date,
                        scheduled_time_str,
                        scheduled_timestamp,
                    ),
                )
                r = cursor.fetchone()
                qid = r["id"] if r and isinstance(r, dict) else (r[0] if r else None)
                conn.commit()
                if qid:
                    logger.info("Created heritage_fact %s queue_id=%s date=%s", platform, qid, target_date)
                    return "created"
                return "failed"
    return "failed"


def ensure_heritage_slot(
    target_date: date,
    year: int,
    week_number: int,
    dry_run: bool,
    force: bool,
) -> str:
    """
    One slot = one row. Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    scheduled_time_str = HERITAGE_SCHEDULED_TIME
    scheduled_time_obj = time(15, 0)
    scheduled_timestamp = datetime.combine(target_date, scheduled_time_obj)

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND role = %s AND scheduled_date = %s
                LIMIT 1
                """,
                (PLATFORM, ROLE, target_date),
            )
            row = cursor.fetchone()

            if row:
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                row_dict = (
                    dict(row)
                    if hasattr(row, "keys")
                    else {"generated_content": row[1], "status": row[2]}
                )
                if not force and _row_is_valid(row_dict):
                    logger.info("Heritage slot %s valid, skip queue_id=%s", target_date, queue_id)
                    return "skipped"
                payload = pick_heritage_for_thursday(target_date, year, week_number)
                if not payload:
                    logger.error("No heritage payload for %s", target_date)
                    return "failed"
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate heritage queue_id=%s date=%s", queue_id, target_date)
                    return "regenerated"
                cursor.execute(
                    """
                    UPDATE posting_queue
                    SET heritage_library_id = %s, generated_content = %s, status = 'ready',
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (payload["heritage_library_id"], payload["generated_content"], queue_id),
                )
                conn.commit()
                logger.info("Regenerated heritage_fact queue_id=%s date=%s", queue_id, target_date)
                return "regenerated"
            else:
                payload = pick_heritage_for_thursday(target_date, year, week_number)
                if not payload:
                    logger.error("No heritage payload for %s", target_date)
                    return "failed"
                if dry_run:
                    logger.info("[DRY-RUN] Would create heritage_fact date=%s", target_date)
                    return "created"
                cursor.execute(
                    """
                    INSERT INTO posting_queue (
                        platform, role, content_type, heritage_library_id,
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
                        payload["heritage_library_id"],
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
                    logger.info("Created heritage_fact queue_id=%s date=%s", qid, target_date)
                    return "created"
                return "failed"
    return "failed"


def main():
    parser = argparse.ArgumentParser(description="Thursday heritage_fact (P1.1): one slot = one row.")
    parser.add_argument("--weeks-ahead", type=int, default=12, help="Weeks to look ahead (default 12)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--force", action="store_true", help="Regenerate even if slot is valid")
    args = parser.parse_args()
    today = date.today()
    stats = {"created": 0, "regenerated": 0, "skipped": 0, "failed": 0}
    try:
        for d, weekday in iter_thursday_dates(args.weeks_ahead, today):
            year, week_number, _ = d.isocalendar()
            outcome = ensure_heritage_slot(d, year, week_number, dry_run=args.dry_run, force=args.force)
            stats[outcome] = stats.get(outcome, 0) + 1
        logger.info("Automated heritage creator complete: %s", stats)
        sys.exit(0 if stats["failed"] == 0 else 1)
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
