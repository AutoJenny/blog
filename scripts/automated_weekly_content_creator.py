#!/usr/bin/env python3
"""
Automated Weekly Content Creator — CULTURE v1.1 (Phase P1.1 normalised)

Exactly one posting_queue row per Tuesday (Facebook CULTURE language).
Phase P1: One slot = one row. Insert if missing; regenerate in place if failed/empty/placeholder; skip if valid.
- Rotation: weekly_word → weekly_phrase → weekly_insult by (week_number - 1) % 3.
- 90-day repeat avoidance; scheduled_time 15:00.
- CLI: --weeks-ahead (default 12).
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Set, Tuple, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.calendar_resolver import resolve_item_for_week
from utils.posting_queue_helpers import create_weekly_social_post

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs",
                "automated_weekly_content_creator.log",
            )
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PLATFORM = "facebook"
TUESDAY_SCHEDULED_TIME = "15:00"
REPEAT_DAYS = 90
LANGUAGE_TYPES = ["weekly_word", "weekly_phrase", "weekly_insult"]
VALID_STATUSES = ("ready", "approved", "scheduled", "published")


def _row_is_valid(row: Dict[str, Any]) -> bool:
    content = (row.get("generated_content") or "").strip()
    if not content:
        return False
    if "placeholder" in content.lower():
        return False
    status = (row.get("status") or "").strip()
    return status in VALID_STATUSES


def get_upcoming_weeks_by_weeks_ahead(weeks_ahead: int) -> List[Tuple[int, int]]:
    today = date.today()
    weeks = []
    for i in range(weeks_ahead):
        d = today + timedelta(weeks=i)
        y, w, _ = d.isocalendar()
        if (y, w) not in weeks:
            weeks.append((y, w))
    return weeks


def get_tuesday_date_for_week(year: int, week_number: int) -> Optional[date]:
    try:
        jan4 = date(year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
        monday = week1_monday + timedelta(weeks=week_number - 1)
        tuesday = monday + timedelta(days=1)
        if tuesday.isocalendar()[0] != year or tuesday.isocalendar()[1] != week_number:
            return None
        return tuesday
    except Exception as e:
        logger.error("Error computing Tuesday for %s-W%s: %s", year, week_number, e)
        return None


def get_idea_ids_used_in_last_90_days(target_date: date) -> Set[int]:
    cutoff = target_date - timedelta(days=REPEAT_DAYS)
    try:
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
    except Exception as e:
        logger.error("Error fetching idea_ids in 90-day window: %s", e)
        return set()


def pick_idea_for_tuesday(
    content_type: str,
    year: int,
    week_number: int,
    exclude_idea_ids: Set[int],
) -> Optional[Dict]:
    item = resolve_item_for_week(content_type, year, week_number, classification=content_type)
    if item and item.get("id") and item["id"] not in exclude_idea_ids:
        return item
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, idea_title, idea_description, position
                FROM calendar_ideas
                WHERE item_classification = %s
                ORDER BY id
                """,
                (content_type,),
            )
            rows = cursor.fetchall()
        if not rows:
            return None
        eligible = [r for r in rows if r["id"] not in exclude_idea_ids]
        if not eligible:
            return None
        seed = year * 53 + week_number
        chosen = eligible[seed % len(eligible)]
        return dict(chosen)
    except Exception as e:
        logger.error("Error picking eligible idea for %s: %s", content_type, e)
        return None


def ensure_tuesday_slot(
    tuesday_date: date,
    year: int,
    week_number: int,
    dry_run: bool,
    force: bool,
) -> str:
    """
    One slot = one row. Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    content_type = LANGUAGE_TYPES[(week_number - 1) % 3]
    exclude_idea_ids = get_idea_ids_used_in_last_90_days(tuesday_date)
    item = pick_idea_for_tuesday(content_type, year, week_number, exclude_idea_ids)
    if not item:
        logger.warning("No eligible idea for %s-W%s %s", year, week_number, content_type)
        return "failed"

    idea_id = item.get("id")
    idea_title = item.get("idea_title", "")
    idea_description = item.get("idea_description", "")
    generated_content = (
        f"{idea_title}\n\n{idea_description}".strip() if idea_description else idea_title
    )
    scheduled_date_str = tuesday_date.isoformat()

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND scheduled_date = %s
                AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
                LIMIT 1
                """,
                (PLATFORM, tuesday_date),
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
                    logger.info("Tuesday slot %s valid, skip queue_id=%s", tuesday_date, queue_id)
                    return "skipped"
                # Regenerate in place
                if dry_run:
                    logger.info(
                        "[DRY-RUN] Would regenerate Tuesday queue_id=%s date=%s",
                        queue_id,
                        tuesday_date,
                    )
                    return "regenerated"
                cursor.execute(
                    """
                    UPDATE posting_queue
                    SET idea_id = %s, content_type = %s, generated_content = %s, role = 'CULTURE',
                        status = 'ready', updated_at = NOW()
                    WHERE id = %s
                    """,
                    (idea_id, content_type, generated_content, queue_id),
                )
                conn.commit()
                logger.info(
                    "Regenerated Tuesday language queue_id=%s %s idea_id=%s date=%s",
                    queue_id,
                    content_type,
                    idea_id,
                    tuesday_date,
                )
                return "regenerated"
            else:
                # Insert (one row per slot)
                if dry_run:
                    logger.info("[DRY-RUN] Would create Tuesday language date=%s", tuesday_date)
                    return "created"
                try:
                    queue_id = create_weekly_social_post(
                        idea_id=idea_id,
                        content_type=content_type,
                        platform=PLATFORM,
                        generated_content=generated_content,
                        status="ready",
                        scheduled_date=scheduled_date_str,
                        scheduled_time=TUESDAY_SCHEDULED_TIME,
                        cursor=cursor,
                    )
                    conn.commit()
                    if queue_id:
                        logger.info(
                            "Created Tuesday language queue_id=%s %s idea_id=%s date=%s",
                            queue_id,
                            content_type,
                            idea_id,
                            tuesday_date,
                        )
                        return "created"
                except Exception as e:
                    if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                        logger.info("Tuesday slot %s already exists (race?), treat as skipped", tuesday_date)
                        return "skipped"
                    logger.error("Error creating Tuesday post for %s: %s", tuesday_date, e)
                    return "failed"
    return "failed"


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Tuesday language (P1.1): one slot = one row. weekly_word/phrase/insult."
    )
    parser.add_argument("--weeks-ahead", type=int, default=12, help="Weeks to look ahead (default 12)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--force", action="store_true", help="Regenerate even if slot is valid")
    args = parser.parse_args()
    today = date.today()
    stats = {"created": 0, "regenerated": 0, "skipped": 0, "failed": 0}
    try:
        weeks = get_upcoming_weeks_by_weeks_ahead(args.weeks_ahead)
        for year, week_number in weeks:
            tuesday_date = get_tuesday_date_for_week(year, week_number)
            if not tuesday_date or tuesday_date <= today:
                continue
            outcome = ensure_tuesday_slot(
                tuesday_date, year, week_number,
                dry_run=args.dry_run,
                force=args.force,
            )
            stats[outcome] = stats.get(outcome, 0) + 1
        logger.info("Weekly content creator complete: %s", stats)
        sys.exit(0 if stats["failed"] == 0 else 1)
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
