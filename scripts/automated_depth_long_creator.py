#!/usr/bin/env python3
"""
Automated Depth-Long Creator (Phase P1.1)

Batch-creates posting_queue entries for Sunday DEPTH_LONG (depth_long) from KB rota.
Phase P1: One slot = one row per platform. Insert skeleton if missing; regenerate in place if failed/empty/placeholder; skip if valid.
- Approach A: orchestrator selects once per Sunday (topic_id, source_page_id); creator(platform, selection) creates both.
- CLI: --weeks-ahead (default 12), --dry-run, --force, --week (optional ISO week). Legacy ensure_depth_long_slot targets facebook only.
"""

import os
import sys
import logging
import json
from datetime import date, datetime, timedelta, time
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.content_roles.depth_long_generator import DepthLongGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs",
                "automated_depth_long_creator.log",
            )
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PLATFORM = "facebook"
ROLE = "DEPTH_LONG"
CONTENT_TYPE = "depth_long"
CHANNEL_TYPE = "feed_post"
SUNDAY_TIME = "15:00"
VALID_STATUSES = ("ready", "approved", "scheduled", "published", "generated")


def _row_is_valid(row: dict) -> bool:
    content = (row.get("generated_content") or "").strip()
    if not content:
        return False
    if "placeholder" in content.lower():
        return False
    status = (row.get("status") or "").strip()
    return status in VALID_STATUSES


def _get_rota_for_week(sunday: date):
    """Get rota entry (topic_id) for the ISO week containing Sunday."""
    year, week, _ = sunday.isocalendar()
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT r.id as rota_id, r.topic_id, r.scheduled_year, r.scheduled_week
                FROM kb_topic_rota r
                WHERE r.scheduled_year = %s AND r.scheduled_week = %s
                """,
                (year, week),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "topic_id": row["topic_id"],
            "year": row["scheduled_year"],
            "week": row["scheduled_week"],
        }
    except Exception as e:
        logger.error("Error getting rota for Sunday %s: %s", sunday, e)
        return None


def _get_source_page_id_for_topic(topic_id: int) -> int | None:
    """First try kb_topic_content source_article_ids, then kb_topics.article_ids, then first clan_kb_articles."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT source_article_ids FROM kb_topic_content
                WHERE topic_id = %s ORDER BY word_count DESC LIMIT 1
                """,
                (topic_id,),
            )
            row = cursor.fetchone()
        if row and row.get("source_article_ids"):
            ids = row["source_article_ids"]
            if isinstance(ids, list) and ids:
                return ids[0]
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT article_ids FROM kb_topics WHERE id = %s AND is_active = TRUE",
                (topic_id,),
            )
            row = cursor.fetchone()
        if row and row.get("article_ids"):
            ids = row["article_ids"]
            if isinstance(ids, list) and ids:
                return ids[0]
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM clan_kb_articles WHERE is_active = TRUE ORDER BY id ASC LIMIT 1"
            )
            row = cursor.fetchone()
        if row:
            return row["id"]
    except Exception as e:
        logger.error("Error getting source_page_id for topic %s: %s", topic_id, e)
    return None


def get_upcoming_sundays(weeks_ahead: int, from_date: date | None = None):
    if from_date is None:
        from_date = date.today()
    sundays = []
    # First Sunday at or after from_date
    days_until_sunday = (7 - from_date.isoweekday()) % 7
    if days_until_sunday == 0 and from_date.isoweekday() == 7:
        current = from_date
    else:
        current = from_date + timedelta(days=days_until_sunday if days_until_sunday else 7)
    for _ in range(weeks_ahead):
        if current >= from_date:
            sundays.append(current)
        current += timedelta(days=7)
    return sundays


def iter_sunday_dates(weeks_ahead: int, from_date: date):
    """Yield (target_date, weekday) for each Sunday in the next weeks_ahead weeks, >= from_date."""
    days_until_sunday = (7 - from_date.isoweekday()) % 7
    if days_until_sunday == 0 and from_date.isoweekday() == 7:
        current = from_date
    else:
        current = from_date + timedelta(days=days_until_sunday if days_until_sunday else 7)
    for _ in range(weeks_ahead):
        if current >= from_date:
            yield current, 7  # ISO Sunday
        current += timedelta(days=7)


def get_slot_dates(weeks_ahead: int, from_date: date) -> List[Tuple[date, int]]:
    """Return list of (scheduled_date, weekday) for Sundays in range. For orchestrator."""
    return list(iter_sunday_dates(weeks_ahead, from_date))


def select_for_slot(
    target_date: date,
    weekday: int,
    year: int,
    week_number: int,
) -> Optional[Dict[str, Any]]:
    """
    Select once per slot (Approach A). Returns shared selection object for both platforms.
    Keys: topic_id, source_page_id, scheduled_date, scheduled_time, rota_year, rota_week.
    """
    rota = _get_rota_for_week(target_date)
    if not rota:
        return None
    topic_id = rota["topic_id"]
    source_page_id = _get_source_page_id_for_topic(topic_id)
    if not source_page_id:
        return None
    return {
        "topic_id": topic_id,
        "source_page_id": source_page_id,
        "scheduled_date": target_date,
        "scheduled_time": SUNDAY_TIME,
        "rota_year": rota["year"],
        "rota_week": rota["week"],
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
    selection: from select_for_slot (topic_id, source_page_id, scheduled_date, scheduled_time, rota_year, rota_week).
    Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    target_date = slot_key["scheduled_date"]
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    scheduled_time = datetime.strptime(SUNDAY_TIME, "%H:%M").time()
    scheduled_dt = datetime.combine(target_date, scheduled_time)
    topic_id = selection["topic_id"]
    source_page_id = selection["source_page_id"]
    rota_year = selection["rota_year"]
    rota_week = selection["rota_week"]

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND content_type = %s AND scheduled_date = %s
                LIMIT 1
                """,
                (platform, CONTENT_TYPE, target_date),
            )
            row = cursor.fetchone()
            existed_before = False

            if row:
                existed_before = True
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                row_dict = dict(row) if hasattr(row, "keys") else {"generated_content": row[1], "status": row[2]}
                if not force and _row_is_valid(row_dict):
                    logger.info("Depth_long slot %s %s valid, skip queue_id=%s", platform, target_date, queue_id)
                    return "skipped"
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate depth_long %s queue_id=%s date=%s", platform, queue_id, target_date)
                    return "regenerated"
            else:
                if dry_run:
                    logger.info("[DRY-RUN] Would create depth_long %s date=%s", platform, target_date)
                    return "created"
                cursor.execute(
                    """
                    INSERT INTO posting_queue (
                        role, platform, channel_type, content_type,
                        generated_content, scheduled_date, scheduled_time, scheduled_timestamp,
                        status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, '', %s, %s, %s, 'draft', NOW(), NOW())
                    RETURNING id
                    """,
                    (ROLE, platform, CHANNEL_TYPE, CONTENT_TYPE, target_date, SUNDAY_TIME, scheduled_dt),
                )
                r = cursor.fetchone()
                queue_id = (r["id"] if r and isinstance(r, dict) else (r[0] if r else None))
                conn.commit()
                if not queue_id:
                    return "failed"
                row = {"id": queue_id}
                logger.info("Created depth_long skeleton %s queue_id=%s date=%s", platform, queue_id, target_date)

            queue_id = row["id"] if isinstance(row, dict) else row[0]
            generator = DepthLongGenerator()
            result = generator.generate(
                topic_id,
                source_page_id,
                rota_year,
                rota_week,
                angle_id=None,
            )
            if not result.get("success"):
                cursor.execute(
                    """
                    UPDATE posting_queue
                    SET status = 'failed', validation_report_json = COALESCE(%s, validation_report_json), updated_at = NOW()
                    WHERE id = %s
                    """,
                    (json.dumps({"error": result.get("error")}), queue_id),
                )
                conn.commit()
                return "failed"

            content = result.get("content", "")
            validation_report = {"valid": True, "role": ROLE, "validation_issues": result.get("validation_issues") or []}
            cursor.execute(
                """
                UPDATE posting_queue
                SET generated_content = %s, topic_id = %s, source_page_id = %s,
                    rota_year = %s, rota_week = %s, validation_report_json = %s,
                    status = 'generated', updated_at = NOW()
                WHERE id = %s
                """,
                (
                    content,
                    topic_id,
                    source_page_id,
                    rota_year,
                    rota_week,
                    json.dumps(validation_report),
                    queue_id,
                ),
            )
            conn.commit()
            logger.info("Generated depth_long %s queue_id=%s date=%s", platform, queue_id, target_date)
            return "regenerated" if existed_before else "created"
    return "failed"


def ensure_depth_long_slot(
    sunday: date,
    dry_run: bool,
    force: bool,
) -> str:
    """
    One slot = one row. Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    scheduled_time = datetime.strptime(SUNDAY_TIME, "%H:%M").time()
    scheduled_dt = datetime.combine(sunday, scheduled_time)
    rota = _get_rota_for_week(sunday)
    if not rota:
        logger.error("No rota for Sunday %s", sunday)
        return "failed"
    topic_id = rota["topic_id"]
    rota_year = rota["year"]
    rota_week = rota["week"]
    source_page_id = _get_source_page_id_for_topic(topic_id)
    if not source_page_id:
        logger.error("No source_page_id for topic %s (Sunday %s)", topic_id, sunday)
        return "failed"

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND content_type = %s AND scheduled_date = %s
                LIMIT 1
                """,
                (PLATFORM, CONTENT_TYPE, sunday),
            )
            row = cursor.fetchone()

            was_existing = False
            if row:
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                row_dict = dict(row) if hasattr(row, "keys") else {"generated_content": row[1], "status": row[2]}
                if not force and _row_is_valid(row_dict):
                    logger.info("Depth_long slot %s valid, skip queue_id=%s", sunday, queue_id)
                    return "skipped"
                was_existing = True
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate depth_long queue_id=%s date=%s", queue_id, sunday)
                    return "regenerated"
            else:
                if dry_run:
                    logger.info("[DRY-RUN] Would create depth_long date=%s", sunday)
                    return "created"
                # Insert skeleton
                cursor.execute(
                    """
                    INSERT INTO posting_queue (
                        role, platform, channel_type, content_type,
                        generated_content, scheduled_date, scheduled_time, scheduled_timestamp,
                        status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, '', %s, %s, %s, 'draft', NOW(), NOW())
                    RETURNING id
                    """,
                    (ROLE, PLATFORM, CHANNEL_TYPE, CONTENT_TYPE, sunday, SUNDAY_TIME, scheduled_dt),
                )
                r = cursor.fetchone()
                queue_id = (r["id"] if r and isinstance(r, dict) else (r[0] if r else None))
                if not queue_id:
                    return "failed"
                conn.commit()
                logger.info("Created depth_long skeleton queue_id=%s date=%s", queue_id, sunday)

            queue_id = row["id"] if isinstance(row, dict) else row[0] if row else queue_id
            generator = DepthLongGenerator()
            result = generator.generate(
                topic_id,
                source_page_id,
                rota_year,
                rota_week,
                angle_id=None,
            )
            if not result.get("success"):
                logger.error(
                    "Depth_long generation failed for queue_id=%s date=%s: %s",
                    queue_id,
                    sunday,
                    result.get("error"),
                )
                with db_manager.get_connection() as conn2:
                    with conn2.cursor() as c2:
                        c2.execute(
                            """
                            UPDATE posting_queue
                            SET status = 'failed', validation_report_json = COALESCE(%s, validation_report_json), updated_at = NOW()
                            WHERE id = %s
                            """,
                            (json.dumps({"error": result.get("error")}), queue_id),
                        )
                        conn2.commit()
                return "failed"

            content = result.get("content", "")
            validation = result.get("validation_issues") or []
            validation_report = {"valid": len(validation) == 0, "role": ROLE, "validation_issues": validation}

            with db_manager.get_connection() as conn2:
                with conn2.cursor() as c2:
                    c2.execute(
                        """
                        UPDATE posting_queue
                        SET generated_content = %s, topic_id = %s, source_page_id = %s,
                            rota_year = %s, rota_week = %s, validation_report_json = %s,
                            status = 'generated', updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            content,
                            topic_id,
                            source_page_id,
                            rota_year,
                            rota_week,
                            json.dumps(validation_report),
                            queue_id,
                        ),
                    )
                    conn2.commit()
            logger.info(
                "Generated depth_long queue_id=%s date=%s status=generated",
                queue_id,
                sunday,
            )
            return "regenerated" if was_existing else "created"
    return "failed"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sunday depth_long (P1.1): one slot = one row; batch from KB rota.")
    parser.add_argument("--weeks-ahead", type=int, default=12, help="Weeks to look ahead (default 12)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--force", action="store_true", help="Regenerate even if slot is valid")
    parser.add_argument("--week", type=str, default=None, help="Target ISO week e.g. 2026-W5 (optional)")
    args = parser.parse_args()

    if args.week:
        try:
            y, w = args.week.split("-W")
            y, w = int(y), int(w)
            jan4 = date(y, 1, 4)
            week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
            sunday = week1_monday + timedelta(days=6)
            sundays = [sunday]
        except Exception:
            logger.error("Invalid --week %s", args.week)
            sys.exit(1)
    else:
        sundays = get_upcoming_sundays(args.weeks_ahead)

    stats = {"created": 0, "regenerated": 0, "skipped": 0, "failed": 0}
    for s in sundays:
        outcome = ensure_depth_long_slot(s, dry_run=args.dry_run, force=args.force)
        stats[outcome] = stats.get(outcome, 0) + 1

    logger.info("Automated depth_long creator complete: %s", stats)
    print("\nDepth_long Creator Results:")
    print(f"  Created: {stats['created']}")
    print(f"  Regenerated: {stats['regenerated']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    sys.exit(0 if stats["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
