#!/usr/bin/env python3
"""
Automated Message Post Creator (Phase P1.1 normalised)

Creates posting_queue entries for Wednesday REASSURANCE (message) from facebook_messages.csv.
Phase P1: One slot = one row. Insert if missing; regenerate in place with NEXT message in rotation if failed/empty/placeholder; skip if valid.
- CLI: --days-ahead (default 28), --dry-run, --force.
"""

import os
import sys
import csv
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs",
                "automated_message_post_creator.log",
            )
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PLATFORM = "facebook"
CONTENT_TYPE = "message"
ROLE = "REASSURANCE"
PUBLICATION_DAY = 3  # Wednesday
PUBLICATION_TIME = "14:30"
VALID_STATUSES = ("ready", "approved", "scheduled", "published")


def _csv_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "facebook_messages.csv",
    )


def load_messages() -> List[str]:
    messages = []
    try:
        with open(_csv_path(), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                msg = (row.get("message") or "").strip()
                if msg:
                    messages.append(msg)
        return messages
    except Exception as e:
        logger.error("Error loading messages from CSV: %s", e)
        return []


def _row_is_valid(row: Dict[str, Any]) -> bool:
    content = (row.get("generated_content") or "").strip()
    if not content:
        return False
    if "placeholder" in content.lower():
        return False
    status = (row.get("status") or "").strip()
    return status in VALID_STATUSES


def get_last_published_message_index(cursor) -> int:
    """Index of the most recently published message (for rotation). Returns -1 if none."""
    cursor.execute("""
        SELECT generated_content
        FROM posting_queue
        WHERE content_type = 'message' AND platform = 'facebook' AND status = 'published'
        ORDER BY scheduled_timestamp DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if not row:
        return -1
    content = (row["generated_content"] if isinstance(row, dict) else row[0]) or ""
    messages = load_messages()
    if not messages:
        return -1
    content_n = content.replace("\\n", "\n").strip()
    for idx, msg in enumerate(messages):
        if (msg.replace("\\n", "\n").strip() == content_n):
            return idx
    return -1


def get_message_index_from_content(cursor, content: str, messages: List[str]) -> int:
    """Find index of content in messages list; if not found return 0."""
    if not content or not messages:
        return 0
    content_n = (content or "").replace("\\n", "\n").strip()
    for idx, msg in enumerate(messages):
        if msg.replace("\\n", "\n").strip() == content_n:
            return idx
    return 0


def get_upcoming_wednesdays(days_ahead: int) -> List[date]:
    today = date.today()
    weekday_target = (PUBLICATION_DAY - 1) % 7  # Wed = 2
    days_until = (weekday_target - today.weekday()) % 7
    if days_until == 0 and datetime.now().time() < datetime.strptime(PUBLICATION_TIME, "%H:%M").time():
        next_date = today
    else:
        if days_until == 0:
            days_until = 7
        next_date = today + timedelta(days=days_until)
    out = []
    current = next_date
    while (current - today).days <= days_ahead:
        if current > today:
            out.append(current)
        current += timedelta(days=7)
    return out


def ensure_message_slot(
    scheduled_date: date,
    messages: List[str],
    next_message_index: int,
    dry_run: bool,
    force: bool,
    cursor,
) -> str:
    """
    One slot = one row. Regenerate = next message in rotation (never retry same).
    Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    if not messages:
        return "failed"
    message_index = next_message_index % len(messages)
    message = messages[message_index].replace("\\n", "\n")
    scheduled_time_obj = datetime.strptime(PUBLICATION_TIME, "%H:%M").time()
    scheduled_timestamp = datetime.combine(scheduled_date, scheduled_time_obj)

    cursor.execute("""
        SELECT id, generated_content, status
        FROM posting_queue
        WHERE platform = %s AND content_type = %s AND scheduled_date = %s
        LIMIT 1
    """, (PLATFORM, CONTENT_TYPE, scheduled_date))
    row = cursor.fetchone()

    if row:
        queue_id = row["id"] if isinstance(row, dict) else row[0]
        row_dict = (
            dict(row)
            if hasattr(row, "keys")
            else {"generated_content": row[1], "status": row[2]}
        )
        if not force and _row_is_valid(row_dict):
            logger.info("Message slot %s valid, skip queue_id=%s", scheduled_date, queue_id)
            return "skipped"
        # Regenerate: advance to next message (do not retry same)
        if dry_run:
            logger.info("[DRY-RUN] Would regenerate message queue_id=%s date=%s", queue_id, scheduled_date)
            return "regenerated"
        cursor.execute("""
            UPDATE posting_queue
            SET generated_content = %s, status = 'ready', updated_at = NOW()
            WHERE id = %s
        """, (message, queue_id))
        logger.info("Regenerated message queue_id=%s date=%s (next in rotation)", queue_id, scheduled_date)
        return "regenerated"
    else:
        if dry_run:
            logger.info("[DRY-RUN] Would create message date=%s", scheduled_date)
            return "created"
        cursor.execute("""
            INSERT INTO posting_queue (
                content_type, platform, status, role,
                generated_content,
                scheduled_date, scheduled_time, scheduled_timestamp,
                created_at, updated_at
            )
            VALUES (%s, %s, 'ready', %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, (
            CONTENT_TYPE,
            PLATFORM,
            ROLE,
            message,
            scheduled_date,
            PUBLICATION_TIME,
            scheduled_timestamp,
        ))
        r = cursor.fetchone()
        qid = r["id"] if r and isinstance(r, dict) else (r[0] if r else None)
        if qid:
            logger.info("Created message queue_id=%s date=%s index=%s", qid, scheduled_date, message_index)
            return "created"
        return "failed"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wednesday message (P1.1): one slot = one row; regenerate = next in rotation.")
    parser.add_argument("--days-ahead", type=int, default=28, help="Days ahead (default 28)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--force", action="store_true", help="Regenerate even if slot is valid")
    args = parser.parse_args()

    messages = load_messages()
    if not messages:
        logger.error("No messages loaded from CSV")
        sys.exit(1)

    wednesdays = get_upcoming_wednesdays(args.days_ahead)
    stats = {"created": 0, "regenerated": 0, "skipped": 0, "failed": 0}

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                last_pub = get_last_published_message_index(cursor)
                next_index = (last_pub + 1) % len(messages) if last_pub >= 0 else 0
                for i, pub_date in enumerate(wednesdays):
                    outcome = ensure_message_slot(
                        pub_date,
                        messages,
                        next_index + i,
                        dry_run=args.dry_run,
                        force=args.force,
                        cursor=cursor,
                    )
                    stats[outcome] = stats.get(outcome, 0) + 1
            conn.commit()
        logger.info("Message post creation complete: %s", stats)
        print("\nMessage Post Creation Results:")
        print(f"  Created: {stats['created']}")
        print(f"  Regenerated: {stats['regenerated']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")
        sys.exit(0 if stats["failed"] == 0 else 1)
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
