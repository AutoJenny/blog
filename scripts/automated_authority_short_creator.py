#!/usr/bin/env python3
"""
Automated Authority-Short Creator (Phase 7)

Purpose:
- Create minimal AUTHORITY_SHORT posts for Facebook on Fridays so that
  Matrix v1 has a structurally complete Friday slot.

Behaviour:
- For upcoming Fridays (configurable window), if there is no existing
  posting_queue row for:
    platform = 'facebook'
    role = 'AUTHORITY_SHORT'
    scheduled_date = that Friday
  then insert a simple placeholder post:
    role = 'AUTHORITY_SHORT'
    platform = 'facebook'
    channel_type = 'feed_post'
    content_type = 'authority_short'
    generated_content = short factual/placeholder text
    scheduled_date = Friday
    scheduled_time = 15:00 (UK)
    scheduled_timestamp = Friday 15:00
    status = 'draft'

Scope:
- Facebook only.
- No backfill of historical weeks (script looks forward).
"""

import os
import sys
import logging
import argparse
import json
from datetime import date, datetime, timedelta, time as time_type

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.content_roles.authority_short_generator import AuthorityShortGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'logs',
                'automated_authority_short_creator.log'
            )
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AuthorityShortCreator:
    def __init__(self, days_ahead: int = 28, dry_run: bool = False, force: bool = False, target_week: str | None = None):
        self.db_manager = db_manager
        self.days_ahead = days_ahead
        self.dry_run = dry_run
        self.force = force
        self.target_week = target_week
        # Friday in ISO: 5 (Mon=1..Sun=7)
        self.iso_weekday_target = 5
        self.publication_time = "15:00"  # 3 PM UK time, consistent with Sunday rail
        self.generator = AuthorityShortGenerator()

    def get_upcoming_fridays(self):
        """Return list of upcoming Friday dates within days_ahead, or a specific ISO week if provided."""
        if self.target_week:
            year_str, week_str = self.target_week.split("-W")
            y, w = int(year_str), int(week_str)
            # Find Monday of that ISO week
            # ISO week 1 is the week with Jan 4; reuse same logic as calendar schedule
            from datetime import timedelta as td
            jan4 = date(y, 1, 4)
            jan4_day = (jan4.isoweekday() + 6) % 7  # Monday = 0
            week_monday = jan4 + td(days=(w - 1) * 7 - jan4_day)
            friday = week_monday + td(days=4)  # Monday+4 = Friday
            return [friday]

        today = date.today()
        fridays = []

        # Python weekday(): Mon=0..Sun=6; Friday=4
        weekday_target = 4
        days_until = (weekday_target - today.weekday()) % 7

        # If today is Friday but time has passed, skip to next week
        now_time = datetime.now().time()
        pub_time = datetime.strptime(self.publication_time, "%H:%M").time()
        if days_until == 0 and now_time < pub_time:
            next_friday = today
        else:
            if days_until == 0:
                days_until = 7
            next_friday = today + timedelta(days=days_until)

        current = next_friday
        while (current - today).days <= self.days_ahead:
            fridays.append(current)
            current += timedelta(days=7)

        logger.info("Upcoming Fridays: %s", fridays)
        return fridays

    def friday_has_authority_short(self, target_date, cursor) -> bool:
        """Check if an AUTHORITY_SHORT post already exists for this Friday."""
        cursor.execute(
            """
            SELECT 1
            FROM posting_queue
            WHERE platform = 'facebook'
              AND role = 'AUTHORITY_SHORT'
              AND scheduled_date = %s
              AND status != 'failed'
            LIMIT 1
            """,
            (target_date,),
        )
        return cursor.fetchone() is not None

    def create_authority_short_post(self, target_date, cursor):
        """
        Insert or update AUTHORITY_SHORT post for Facebook on the given Friday.
        """
        scheduled_time = datetime.strptime(self.publication_time, "%H:%M").time()
        scheduled_dt = datetime.combine(target_date, scheduled_time)
        # Step 1: ensure a posting_queue row exists
        cursor.execute(
            """
            SELECT id, generated_content, status
            FROM posting_queue
            WHERE platform = 'facebook'
              AND role = 'AUTHORITY_SHORT'
              AND scheduled_date = %s
              AND content_type = 'authority_short'
            ORDER BY id ASC
            LIMIT 1
            """,
            (target_date,),
        )
        row = cursor.fetchone()
        if row:
            queue_id = row["id"] if isinstance(row, dict) else row[0]
            existing_content = row["generated_content"] if isinstance(row, dict) else None
            existing_status = row["status"] if isinstance(row, dict) else None
            # Detect placeholder
            is_placeholder = bool(
                existing_content and str(existing_content).startswith("AUTHORITY_SHORT placeholder")
            )
            if not self.force and not is_placeholder and existing_status in ("generated", "ready", "approved", "scheduled"):
                logger.info("Existing AUTHORITY_SHORT %s for %s retained (status=%s)", queue_id, target_date, existing_status)
                return queue_id
        else:
            # Create skeleton row
            cursor.execute(
                """
                INSERT INTO posting_queue (
                    role,
                    platform,
                    channel_type,
                    content_type,
                    generated_content,
                    scheduled_date,
                    scheduled_time,
                    scheduled_timestamp,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (
                    'AUTHORITY_SHORT',
                    'facebook',
                    'feed_post',
                    'authority_short',
                    '',
                    %s,
                    %s,
                    %s,
                    'draft',
                    NOW(),
                    NOW()
                )
                RETURNING id
                """,
                (
                    target_date,
                    scheduled_time,
                    scheduled_dt,
                ),
            )
            created_row = cursor.fetchone()
            queue_id = created_row["id"] if isinstance(created_row, dict) else created_row[0]
            logger.info("Created AUTHORITY_SHORT skeleton post: id=%s date=%s", queue_id, target_date)

        if self.dry_run:
            logger.info("Dry-run: would generate AUTHORITY_SHORT content for id=%s date=%s", queue_id, target_date)
            return queue_id

        # Step 2: generate real content using generator
        result = self.generator.generate_for_friday(target_date, queue_id)
        if not result.get("success"):
            logger.error(
                "AUTHORITY_SHORT generation failed for id=%s date=%s: %s",
                queue_id,
                target_date,
                result.get("error"),
            )
            # Persist validation_report_json on failure for audit (attempts, failed_rules, source_used)
            fail_report = result.get("validation_report_json")
            cursor.execute(
                """
                UPDATE posting_queue
                SET status = 'failed',
                    validation_report_json = COALESCE(%s, validation_report_json),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (json.dumps(fail_report) if fail_report else None, queue_id),
            )
            return queue_id

        content = result["content"]
        validation_report = result.get("validation_report_json", {"valid": True, "role": "AUTHORITY_SHORT"})
        topic_id = result.get("topic_id")
        source_page_id = result.get("source_page_id")

        cursor.execute(
            """
            UPDATE posting_queue
            SET generated_content = %s,
                status = 'ready',
                topic_id = COALESCE(%s, topic_id),
                source_page_id = COALESCE(%s, source_page_id),
                rota_year = COALESCE(%s, rota_year),
                rota_week = COALESCE(%s, rota_week),
                validation_report_json = COALESCE(%s, validation_report_json),
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                content,
                topic_id,
                source_page_id,
                result.get("rota_year"),
                result.get("rota_week"),
                json.dumps(validation_report),
                queue_id,
            ),
        )

        failed_rules = (validation_report or {}).get("failed_rules") or []
        logger.info(
            "Generated AUTHORITY_SHORT for id=%s date=%s status=ready chars=%s source_type=%s topic_id=%s source_page_id=%s failed_rules_count=%s",
            queue_id,
            target_date,
            result.get("char_count"),
            result.get("source_type"),
            topic_id,
            source_page_id,
            len(failed_rules),
        )
        return queue_id

    def run(self):
        """Main entry: ensure upcoming Fridays have an AUTHORITY_SHORT post with real content."""
        fridays = self.get_upcoming_fridays()
        stats = {
            "created": 0,
            "skipped_existing": 0,
            "errors": 0,
        }

        if not fridays:
            logger.info("No upcoming Fridays in window; nothing to do.")
            return stats

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for target_date in fridays:
                        try:
                            if self.friday_has_authority_short(target_date, cursor) and not (self.force or self.dry_run):
                                logger.info(
                                    "AUTHORITY_SHORT exists for %s and force/dry-run not set; skipping create() but may regenerate",
                                    target_date,
                                )
                            pq_id = self.create_authority_short_post(target_date, cursor)
                            if self.dry_run:
                                stats["skipped_existing"] += 1
                            else:
                                stats["created"] += 1
                        except Exception as e:
                            logger.error(
                                "Error creating/regenerating AUTHORITY_SHORT for %s: %s",
                                target_date,
                                e,
                            )
                            stats["errors"] += 1

        except Exception as e:
            logger.error("Error in AuthorityShortCreator.run(): %s", e, exc_info=True)

        logger.info("AuthorityShortCreator stats: %s", stats)
        return stats


def main():
    parser = argparse.ArgumentParser(description="Automated AUTHORITY_SHORT creator for Facebook Fridays")
    parser.add_argument("--days-ahead", type=int, default=28, help="Number of days ahead to scan for Fridays")
    parser.add_argument("--dry-run", action="store_true", help="Log actions but do not write to database")
    parser.add_argument("--force", action="store_true", help="Regenerate even if an AUTHORITY_SHORT exists")
    parser.add_argument("--week", type=str, default=None, help="Target a specific ISO week, e.g. 2026-W5")
    args = parser.parse_args()

    creator = AuthorityShortCreator(
        days_ahead=args.days_ahead,
        dry_run=args.dry_run,
        force=args.force,
        target_week=args.week,
    )
    stats = creator.run()
    print("AUTHORITY_SHORT creation results:")
    print(f"  Created: {stats['created']}")
    print(f"  Skipped (existing): {stats['skipped_existing']}")
    print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    main()

