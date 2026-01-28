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
from datetime import date, datetime, timedelta, time as time_type

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

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
    def __init__(self, days_ahead: int = 28):
        self.db_manager = db_manager
        self.days_ahead = days_ahead
        # Friday in ISO: 5 (Mon=1..Sun=7)
        self.iso_weekday_target = 5
        self.publication_time = "15:00"  # 3 PM UK time, consistent with Sunday rail

    def get_upcoming_fridays(self):
        """Return list of upcoming Friday dates within days_ahead."""
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
        Insert a minimal AUTHORITY_SHORT post for Facebook on the given Friday.
        """
        scheduled_time = datetime.strptime(self.publication_time, "%H:%M").time()
        scheduled_dt = datetime.combine(target_date, scheduled_time)

        placeholder = (
            "AUTHORITY_SHORT placeholder: short factual context about clan, tartan "
            "or provenance, scheduled for Friday per Matrix v1."
        )

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
                %s,
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
                placeholder,
                target_date,
                scheduled_time,
                scheduled_dt,
            ),
        )
        row = cursor.fetchone()
        queue_id = row["id"] if isinstance(row, dict) else row[0]
        logger.info("Created AUTHORITY_SHORT post: id=%s date=%s", queue_id, target_date)
        return queue_id

    def run(self):
        """Main entry: ensure upcoming Fridays have an AUTHORITY_SHORT post."""
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
                        if self.friday_has_authority_short(target_date, cursor):
                            logger.info(
                                "Skipping %s - AUTHORITY_SHORT already exists", target_date
                            )
                            stats["skipped_existing"] += 1
                            continue

                            # fall-through: create post if none exists
                        try:
                            self.create_authority_short_post(target_date, cursor)
                            stats["created"] += 1
                        except Exception as e:
                            logger.error(
                                "Error creating AUTHORITY_SHORT for %s: %s",
                                target_date,
                                e,
                            )
                            stats["errors"] += 1

        except Exception as e:
            logger.error("Error in AuthorityShortCreator.run(): %s", e, exc_info=True)

        logger.info("AuthorityShortCreator stats: %s", stats)
        return stats


def main():
    creator = AuthorityShortCreator(days_ahead=28)
    stats = creator.run()
    print("AUTHORITY_SHORT creation results:")
    print(f"  Created: {stats['created']}")
    print(f"  Skipped (existing): {stats['skipped_existing']}")
    print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    main()

