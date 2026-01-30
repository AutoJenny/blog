#!/usr/bin/env python3
"""
Automated Product Post Creator (Phase P1.1 normalised)

Creates posting_queue entries for Saturday COMMERCE (product) from daily_posts_schedule + clan_products.
Phase P1: One slot = one row per platform. Slot key = (scheduled_date, scheduled_time, role, content_type).
- Approach A: orchestrator selects product once per slot (date+time), passes selection; creator(platform, selection) creates both.
- CLI: --days-ahead (default 28), --dry-run, --force. Legacy ensure_product_slot targets facebook only.
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional, Any, Tuple

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
                "automated_product_post_creator.log",
            )
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PLATFORM = "facebook"
CONTENT_TYPE = "product"
ROLE = "COMMERCE"
SATURDAY_TIME = time(15, 0)
SATURDAY_TIME_STR = "15:00"
VALID_STATUSES = ("ready", "approved", "scheduled", "published")


def _row_is_valid(row: Dict[str, Any]) -> bool:
    content = (row.get("generated_content") or "").strip()
    if not content:
        return False
    if "placeholder" in (content or "").lower():
        return False
    status = (row.get("status") or "").strip()
    return status in VALID_STATUSES


def get_active_schedules(platform: str = "facebook") -> List[Dict]:
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, time, timezone, days, is_active
                FROM daily_posts_schedule
                WHERE is_active = true AND platform = %s AND content_type = 'product'
                ORDER BY time ASC
            """, (platform,))
            schedules = cursor.fetchall()
        if platform == "facebook" and schedules:
            for s in schedules:
                s["days"] = [6]  # Saturday only
        return list(schedules) if schedules else []
    except Exception as e:
        logger.error("Error fetching active schedules: %s", e)
        return []


def get_upcoming_saturday_slots(days_ahead: int) -> List[Dict]:
    today = date.today()
    slots = []
    for day_offset in range(days_ahead):
        check_date = today + timedelta(days=day_offset)
        if check_date.isoweekday() != 6:
            continue
        if check_date <= today:
            continue
        schedule_time = time(15, 0)
        slots.append({
            "date": check_date,
            "time": schedule_time,
            "datetime": datetime.combine(check_date, schedule_time),
            "schedule_id": 0,
            "schedule_name": "Matrix Saturday",
        })
    return slots


def get_products_pool(limit: int = 50, days_back: int = 30, exclude_product_id: Optional[int] = None) -> List[Dict]:
    cutoff = date.today() - timedelta(days=days_back)
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT cp.id, cp.name, cp.sku, cp.image_url, cp.url
                FROM clan_products cp
                WHERE cp.image_url IS NOT NULL AND cp.image_url != ''
                AND cp.id NOT IN (
                    SELECT DISTINCT product_id FROM posting_queue
                    WHERE product_id IS NOT NULL AND content_type = 'product'
                    AND (scheduled_date >= %s OR status = 'published')
                )
                ORDER BY cp.id DESC
                LIMIT %s
            """, (cutoff, limit))
            rows = cursor.fetchall()
        products = [dict(r) for r in rows] if rows else []
        if exclude_product_id is not None:
            products = [p for p in products if p.get("id") != exclude_product_id]
        return products
    except Exception as e:
        logger.error("Error fetching products: %s", e)
        return []


def iter_saturday_slot_dates(weeks_ahead: int, from_date: date):
    """Yield (scheduled_date, scheduled_time_str) for each Saturday in the next weeks_ahead weeks, >= from_date."""
    year, week_number, _ = from_date.isocalendar()
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    monday = week1_monday + timedelta(weeks=week_number - 1)
    if monday > from_date:
        monday -= timedelta(days=7)
    for _ in range(weeks_ahead):
        saturday = monday + timedelta(days=5)
        if saturday >= from_date:
            yield saturday, SATURDAY_TIME_STR
        monday += timedelta(days=7)


def get_slot_dates(weeks_ahead: int, from_date: date) -> List[Tuple[date, str]]:
    """Return list of (scheduled_date, scheduled_time_str) for Saturday slots in range. For orchestrator."""
    return list(iter_saturday_slot_dates(weeks_ahead, from_date))


def select_for_slot(
    target_date: date,
    scheduled_time_str: str,
    year: int,
    week_number: int,
) -> Optional[Dict[str, Any]]:
    """
    Select once per slot (Approach A). Returns shared selection object for both platforms.
    Keys: product_id, scheduled_date, scheduled_time.
    """
    products = get_products_pool(limit=50)
    if not products:
        return None
    index = (year * 53 + week_number) % len(products)
    product = products[index]
    return {
        "product_id": product["id"],
        "scheduled_date": target_date,
        "scheduled_time": scheduled_time_str,
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
    slot_key for Saturday: {scheduled_date, scheduled_time, role, content_type}.
    selection: from select_for_slot (product_id, scheduled_date, scheduled_time).
    Returns: 'created' | 'regenerated' | 'skipped' | 'failed'
    """
    target_date = slot_key["scheduled_date"]
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    scheduled_time_str = slot_key.get("scheduled_time") or selection.get("scheduled_time") or SATURDAY_TIME_STR
    scheduled_time_obj = datetime.strptime(scheduled_time_str, "%H:%M").time()
    scheduled_datetime = datetime.combine(target_date, scheduled_time_obj)
    schedule_name = "Matrix Saturday"

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, product_id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND content_type = %s AND scheduled_date = %s AND scheduled_time = %s
                LIMIT 1
                """,
                (platform, CONTENT_TYPE, target_date, scheduled_time_str),
            )
            row = cursor.fetchone()

            if row:
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                row_dict = dict(row) if hasattr(row, "keys") else {"generated_content": row[2], "status": row[3]}
                if not force and _row_is_valid(row_dict):
                    logger.info("Product slot %s %s valid, skip queue_id=%s", platform, target_date, queue_id)
                    return "skipped"
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate product %s queue_id=%s date=%s", platform, queue_id, target_date)
                    return "regenerated"
                cursor.execute(
                    """
                    UPDATE posting_queue
                    SET product_id = %s, status = 'draft', generated_content = NULL, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (selection["product_id"], queue_id),
                )
                conn.commit()
                logger.info("Regenerated product %s queue_id=%s date=%s", platform, queue_id, target_date)
                return "regenerated"
            else:
                if dry_run:
                    logger.info("[DRY-RUN] Would create product %s date=%s", platform, target_date)
                    return "created"
                cursor.execute(
                    """
                    INSERT INTO posting_queue (
                        product_id, content_type, platform, status, role,
                        scheduled_date, scheduled_time, scheduled_timestamp,
                        schedule_name, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, 'draft', %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                    """,
                    (
                        selection["product_id"],
                        CONTENT_TYPE,
                        platform,
                        ROLE,
                        target_date,
                        scheduled_time_str,
                        scheduled_datetime,
                        schedule_name,
                    ),
                )
                r = cursor.fetchone()
                qid = r["id"] if r and isinstance(r, dict) else (r[0] if r else None)
                conn.commit()
                if qid:
                    logger.info("Created product %s queue_id=%s date=%s", platform, qid, target_date)
                    return "created"
                return "failed"
    return "failed"


def ensure_product_slot(
    slot: Dict,
    products_pool: List[Dict],
    product_index: int,
    dry_run: bool,
    force: bool,
) -> tuple:
    """
    One slot = one row. Regenerate = re-pick product (do not retry same product_id), UPDATE row.
    Returns: (outcome, used_pool_index) where outcome in 'created'|'regenerated'|'skipped'|'failed',
    and used_pool_index is the index consumed from pool (-1 if none).
    """
    scheduled_date = slot["date"]
    scheduled_time = slot["time"]
    scheduled_datetime = slot["datetime"]
    schedule_name = slot.get("schedule_name", "Matrix Saturday")

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, product_id, generated_content, status
                FROM posting_queue
                WHERE platform = %s AND content_type = 'product'
                AND scheduled_date = %s AND scheduled_time = %s
                LIMIT 1
            """, (PLATFORM, scheduled_date, scheduled_time))
            row = cursor.fetchone()

            if row:
                queue_id = row["id"] if isinstance(row, dict) else row[0]
                current_product_id = row["product_id"] if isinstance(row, dict) else row[1]
                row_dict = (
                    dict(row)
                    if hasattr(row, "keys")
                    else {"generated_content": row[2], "status": row[3]}
                )
                if not force and _row_is_valid(row_dict):
                    logger.info("Product slot %s valid, skip queue_id=%s", scheduled_date, queue_id)
                    return ("skipped", -1)
                # Regenerate: pick first product in pool that is not current_product_id
                used_idx = -1
                for i in range(len(products_pool)):
                    idx = (product_index + i) % len(products_pool)
                    if products_pool[idx].get("id") != current_product_id:
                        used_idx = idx
                        break
                if used_idx < 0:
                    logger.warning("No alternate product for slot %s (pool exhausted)", scheduled_date)
                    return ("failed", -1)
                new_product_id = products_pool[used_idx]["id"]
                if dry_run:
                    logger.info("[DRY-RUN] Would regenerate product queue_id=%s date=%s new_product_id=%s", queue_id, scheduled_date, new_product_id)
                    return ("regenerated", used_idx)
                cursor.execute("""
                    UPDATE posting_queue
                    SET product_id = %s, status = 'draft', generated_content = NULL, updated_at = NOW()
                    WHERE id = %s
                """, (new_product_id, queue_id))
                conn.commit()
                logger.info("Regenerated product queue_id=%s date=%s product_id=%s", queue_id, scheduled_date, new_product_id)
                return ("regenerated", used_idx)
            else:
                if product_index >= len(products_pool):
                    logger.warning("No product available for slot %s", scheduled_date)
                    return ("failed", -1)
                product = products_pool[product_index]
                product_id = product["id"]
                if dry_run:
                    logger.info("[DRY-RUN] Would create product post date=%s product_id=%s", scheduled_date, product_id)
                    return ("created", product_index)
                cursor.execute("""
                    INSERT INTO posting_queue (
                        product_id, content_type, platform, status, role,
                        scheduled_date, scheduled_time, scheduled_timestamp,
                        schedule_name, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, 'draft', %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (product_id, CONTENT_TYPE, PLATFORM, ROLE, scheduled_date, scheduled_time, scheduled_datetime, schedule_name))
                r = cursor.fetchone()
                qid = r["id"] if r and isinstance(r, dict) else (r[0] if r else None)
                conn.commit()
                if qid:
                    logger.info("Created product queue_id=%s date=%s product_id=%s", qid, scheduled_date, product_id)
                    return ("created", product_index)
                return ("failed", -1)
    return ("failed", -1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Saturday product (P1.1): one slot = one row; regenerate = re-pick product.")
    parser.add_argument("--days-ahead", type=int, default=28, help="Days ahead (default 28)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--force", action="store_true", help="Regenerate even if slot is valid")
    args = parser.parse_args()

    slots = get_upcoming_saturday_slots(args.days_ahead)
    if not slots:
        logger.info("No upcoming Saturday slots in window")
        sys.exit(0)

    products = get_products_pool(limit=max(len(slots) * 2, 20))
    if not products:
        logger.warning("No products available for posting")
        sys.exit(1)

    stats = {"created": 0, "regenerated": 0, "skipped": 0, "failed": 0}
    product_index = 0
    for slot in slots:
        outcome, used_idx = ensure_product_slot(slot, products, product_index, dry_run=args.dry_run, force=args.force)
        stats[outcome] = stats.get(outcome, 0) + 1
        if outcome in ("created", "regenerated") and used_idx >= 0:
            product_index = used_idx + 1
        if product_index >= len(products):
            product_index = 0

    logger.info("Product post creation complete: %s", stats)
    print("\nProduct Post Creation Results:")
    print(f"  Created: {stats['created']}")
    print(f"  Regenerated: {stats['regenerated']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    sys.exit(0 if stats["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
