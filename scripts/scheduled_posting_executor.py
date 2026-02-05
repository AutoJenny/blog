#!/usr/bin/env python3
"""
Scheduled Posting Executor - Centralized Date-Sensitive Scheduler
------------------------------------------------------------------

This is the SINGLE SOURCE OF TRUTH for date validation and publishing.
All calendar-based posts (weekly_word, weekly_phrase, weekly_insult, product, etc.)
go through this centralized scheduler.

Responsibilities:
- Query posting_queue for posts where scheduled_date + scheduled_time <= now
- Failsafe validation: Double-check dates in Python (not just SQL) before publishing
- Route to appropriate platform publisher based on platform field
- Update status to 'published' or 'failed' after publishing

Platform-specific publishing logic is in utils/platform_publishers.py
"""

import os
import sys
import logging
from datetime import datetime, date, time
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.platform_publishers import (
    publish_to_facebook,
    publish_to_instagram,
    publish_to_twitter,
    publish_to_linkedin
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/scheduled_posting_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScheduledPostingExecutor:
    def __init__(self):
        self.db_manager = db_manager
        self._bypass_switch = False  # Set to True to bypass automated_posting_enabled check
        self._dry_run = False  # Set to True to log only, no DB updates or publishing
    
    def is_automated_posting_enabled(self) -> bool:
        """
        Check if automated posting is enabled in system_config.
        
        Returns
        -------
        bool: True if enabled, False if disabled.
              Defaults to True if config not found (safer - allows posting).
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT config_value
                    FROM system_config
                    WHERE config_key = 'automated_posting_enabled'
                """)
                result = cursor.fetchone()
                
                if result:
                    value = result.get('config_value', 'true').lower()
                    return value == 'true' or value == '1'
                
                # Default to enabled if not found
                return True
        except Exception as e:
            logger.error(f"Error checking automated posting config: {e}")
            # Default to enabled on error (safer - allows posting)
            return True
    
    def validate_scheduled_date(self, post: Dict) -> bool:
        """
        Failsafe: Ensure scheduled date/time has actually passed.
        
        This is a CRITICAL safety check that validates dates in Python,
        not just relying on SQL queries. This prevents future-dated posts
        from being published even if there's a bug in the SQL query.
        
        Parameters
        ----------
        post:
            Post dict with scheduled_date, scheduled_time, or scheduled_timestamp.
        
        Returns
        -------
        True if scheduled time has passed, False otherwise.
        """
        now = datetime.now()
        
        # Check scheduled_timestamp if available
        if post.get('scheduled_timestamp'):
            scheduled = post['scheduled_timestamp']
            if isinstance(scheduled, str):
                # Parse ISO format
                if 'Z' in scheduled:
                    scheduled = datetime.fromisoformat(scheduled.replace('Z', '+00:00')).replace(tzinfo=None)
                elif '+' in scheduled or (scheduled.count('-') > 2 and 'T' in scheduled):
                    scheduled = datetime.fromisoformat(scheduled).replace(tzinfo=None)
                else:
                    scheduled = datetime.fromisoformat(scheduled)
            elif isinstance(scheduled, datetime):
                scheduled = scheduled.replace(tzinfo=None) if scheduled.tzinfo else scheduled
            
            if scheduled > now:
                logger.error(f"BLOCKED: Post {post['id']} scheduled_timestamp {scheduled} is in the future (now: {now})")
                return False
            return True
        
        # Check scheduled_date + scheduled_time
        scheduled_date = post.get('scheduled_date')
        scheduled_time = post.get('scheduled_time')
        
        if not scheduled_date or not scheduled_time:
            logger.warning(f"Post {post['id']} missing scheduled_date or scheduled_time")
            return False
        
        # Parse and combine
        if isinstance(scheduled_date, str):
            scheduled_date = date.fromisoformat(scheduled_date)
        elif isinstance(scheduled_date, date):
            pass  # Already a date object
        else:
            logger.error(f"Post {post['id']} has invalid scheduled_date type: {type(scheduled_date)}")
            return False
        
        if isinstance(scheduled_time, str):
            time_parts = scheduled_time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            scheduled_time = time(hour, minute)
        elif isinstance(scheduled_time, time):
            pass  # Already a time object
        else:
            logger.error(f"Post {post['id']} has invalid scheduled_time type: {type(scheduled_time)}")
            return False
        
        scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
        
        # Failsafe: Only publish if scheduled time has passed
        if scheduled_datetime > now:
            logger.error(f"BLOCKED: Post {post['id']} scheduled for {scheduled_datetime} is in the future (now: {now})")
            return False
        
        return True
    
    # Matrix v1.1 (Phase C1/H1): content_type -> allowed weekdays (ISO 1=Mon .. 7=Sun)
    _CONTENT_WEEKDAY_MATRIX = {
        'weekly_word': (2,),      # Tuesday only
        'weekly_phrase': (2,),    # Tuesday only
        'weekly_insult': (2,),    # Tuesday only
        'culture_fact': (1,),     # Monday only (Thursday = HERITAGE)
        'heritage_fact': (4,),    # Thursday only
        'message': (3,),          # Wednesday
        'authority_short': (5,),  # Friday
        'product': (6,),          # Saturday
        'depth_long': (7,),       # Sunday
    }
    _LANGUAGE_TYPES = ('weekly_word', 'weekly_phrase', 'weekly_insult')

    def validate_content_schedule(self, post: Dict) -> bool:
        """
        Validate that post follows Matrix v1.1 weekday rules (Phase C1).
        - Language (weekly_word/phrase/insult): Tuesday only; one language post per week.
        - culture_fact: Monday only. heritage_fact: Thursday only.
        - message: Wednesday. authority_short: Friday. product: Saturday. depth_long: Sunday.
        - If content_type not in matrix, allow (no restriction).
        - Legacy language on any day other than Tuesday is hard-blocked.
        """
        content_type = post.get('content_type', '').lower()
        if not content_type or content_type not in self._CONTENT_WEEKDAY_MATRIX:
            return True  # Not in matrix, skip validation

        scheduled_date = post.get('scheduled_date')
        if not scheduled_date:
            logger.warning(f"Post {post['id']} ({content_type}) missing scheduled_date, cannot validate weekday")
            return False

        if isinstance(scheduled_date, str):
            scheduled_date = date.fromisoformat(scheduled_date)

        weekday = scheduled_date.isoweekday()  # 1=Monday, 7=Sunday
        allowed = self._CONTENT_WEEKDAY_MATRIX[content_type]

        if weekday not in allowed:
            logger.error(
                "BLOCKED: Post %s (%s) scheduled for weekday %s (allowed: %s)",
                post['id'], content_type, weekday, allowed,
            )
            return False

        # Language only: at most one language post (any type) per week already published
        if content_type in self._LANGUAGE_TYPES:
            year, week_number, _ = scheduled_date.isocalendar()
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM posting_queue
                    WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
                    AND status = 'published'
                    AND scheduled_date IS NOT NULL
                    AND EXTRACT(YEAR FROM scheduled_date) = %s
                    AND EXTRACT(WEEK FROM scheduled_date) = %s
                    AND id != %s
                """, (year, week_number, post['id']))
                existing = cursor.fetchone()
                if existing:
                    logger.error(
                        "BLOCKED: Post %s (%s) - another language post already published in week %s-W%02d",
                        post['id'], content_type, year, week_number,
                    )
                    return False

        return True
    
    def get_due_posts(self) -> List[Dict]:
        """
        Get posts that are due to be published now.
        
        Uses SQL query to find posts, then validates each one with
        failsafe date checking before returning.
        
        Returns
        -------
        List of post dicts that have passed both SQL and Python date validation.
        """
        logger.debug("get_due_posts called")
        
        try:
            with self.db_manager.get_cursor() as cursor:
                now = datetime.now()
                logger.debug(f"Current time: {now}")
                
                # SQL query to find posts that appear to be due (include role for daily-cap priority).
                # Predicate must match utils.publishable_predicate (PUBLISHABLE_STATUSES + SCHEDULED_DUE_FRAGMENT).
                cursor.execute("""
                    SELECT pq.id, pq.platform, pq.role, pq.channel_type, pq.content_type,
                           pq.post_id, pq.generated_content, pq.status, pq.product_id, pq.section_id,
                           pq.scheduled_timestamp, pq.schedule_name, pq.timezone,
                           pq.scheduled_date, pq.scheduled_time,
                           cp.name as product_name, cp.sku, cp.image_url as product_image,
                           ps.section_heading as section_title
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    LEFT JOIN post_section ps ON pq.section_id = ps.id
                    WHERE pq.status IN ('pending', 'ready')
                    AND pq.status NOT IN ('published', 'failed')
                    AND (
                        (pq.scheduled_timestamp IS NOT NULL AND pq.scheduled_timestamp <= %s)
                        OR (pq.scheduled_date IS NOT NULL AND pq.scheduled_time IS NOT NULL
                            AND (pq.scheduled_date::date + pq.scheduled_time::time)::timestamp <= %s)
                    )
                    ORDER BY COALESCE(pq.scheduled_timestamp, (pq.scheduled_date::date + pq.scheduled_time::time)::timestamp) ASC
                """, (now, now))
                
                candidate_posts = cursor.fetchall()
                logger.info(f"Found {len(candidate_posts)} candidate posts from SQL query")
                
                # Failsafe: Validate each post with Python date checking AND Matrix v1.1 content schedule
                valid_posts = []
                for post in candidate_posts:
                    # First check: date validation
                    if not self.validate_scheduled_date(post):
                        logger.warning(f"BLOCKED post {post['id']} - failed failsafe date validation")
                        continue

                    # Second check: Matrix v1.1 content schedule (language Tuesday only; culture_fact Mon/Thu; etc.)
                    if not self.validate_content_schedule(post):
                        logger.warning(f"BLOCKED post {post['id']} - failed content schedule validation")
                        continue

                    # Phase H-5.1: For blog_post, publish only the run marked current in workbench
                    ct = (post.get('content_type') or '').strip().lower()
                    if ct == 'blog_post' and post.get('post_id') is not None:
                        try:
                            from blueprints.launchpad_utils import resolve_current_posting_queue_id
                            resolved_id = resolve_current_posting_queue_id(
                                post['post_id'],
                                post.get('platform') or 'facebook',
                                post.get('channel_type') or 'blog_post',
                                'primary',
                            )
                            if resolved_id is None:
                                logger.warning(
                                    "BLOCKED post %s (blog_post) - no current output set for (post_id=%s, platform=%s); skip",
                                    post['id'], post['post_id'], post.get('platform'),
                                )
                                continue
                            if resolved_id != post['id']:
                                logger.warning(
                                    "BLOCKED post %s (blog_post) - queue row is not the current output (current=%s); skip",
                                    post['id'], resolved_id,
                                )
                                continue
                        except Exception as e:
                            logger.warning(f"BLOCKED post {post['id']} - resolver error: {e}; skip")
                            continue

                    scheduled_str = post.get('scheduled_timestamp') or f"{post.get('scheduled_date')} {post.get('scheduled_time')}"
                    valid_posts.append(post)
                    logger.debug(f"Validated post: ID={post['id']}, scheduled={scheduled_str}, platform={post['platform']}")
                
                logger.info(f"After failsafe validation: {len(valid_posts)} posts ready for publishing")
                return valid_posts
                
        except Exception as e:
            logger.error(f"Error fetching due posts: {e}")
            logger.exception("Full exception details:")
            return []

    # Daily cap: Matrix priority for deterministic selection (highest first)
    _PRIORITY_BY_ROLE_OR_TYPE = {
        'AUTHORITY_SHORT': 1,
        'DEPTH_LONG': 2,
        'HERITAGE': 3,
        'CULTURE': 4,
        'message': 5,
        'weekly_word': 6,
        'weekly_phrase': 6,
        'weekly_insult': 6,
        'product': 7,
    }

    def _priority_sort_key(self, post: Dict) -> tuple:
        role = (post.get('role') or '').strip()
        ct = (post.get('content_type') or '').strip()
        if role == 'AUTHORITY_SHORT':
            p = 1
        elif ct == 'depth_long':
            p = 2
        elif role == 'HERITAGE' or ct == 'heritage_fact':
            p = 3
        elif ct == 'culture_fact':
            p = 4
        elif ct == 'message':
            p = 5
        elif ct in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
            p = 6
        elif ct == 'product':
            p = 7
        else:
            p = 99
        return (p, post.get('id') or 0)

    def apply_daily_cap(self, valid_posts: List[Dict]) -> tuple:
        """
        Enforce one post per day for Facebook (except Saturday: multiple product posts allowed).
        Returns (posts_to_publish, list of (id, error_message) to cancel).
        """
        to_publish = []
        to_cancel = []  # list of (id, error_message)
        if not valid_posts:
            return (to_publish, to_cancel)

        from collections import defaultdict
        by_platform_date = defaultdict(list)
        for p in valid_posts:
            platform = (p.get('platform') or '').strip().lower()
            sd = p.get('scheduled_date')
            if not sd:
                continue
            if isinstance(sd, str):
                sd = date.fromisoformat(sd)
            by_platform_date[(platform, sd)].append(p)

        for (platform, scheduled_date), posts in by_platform_date.items():
            if platform != 'facebook':
                to_publish.extend(posts)
                continue
            weekday = scheduled_date.isoweekday()  # 1=Mon .. 7=Sun
            if weekday == 6:  # Saturday: keep all product rows, cancel non-product
                products = [p for p in posts if (p.get('content_type') or '').strip() == 'product']
                non_products = [p for p in posts if (p.get('content_type') or '').strip() != 'product']
                to_publish.extend(products)
                for p in non_products:
                    to_cancel.append((
                        p['id'],
                        f"Executor cap: cancelled non-product post for Saturday {scheduled_date}; only product posts publish on Saturday",
                    ))
                if non_products:
                    logger.info(
                        "Executor daily cap (Saturday): kept %s product(s), cancelled %s non-product for %s",
                        len(products), len(non_products), scheduled_date,
                    )
            else:
                # Non-Saturday: exactly one per date
                sorted_posts = sorted(posts, key=self._priority_sort_key)
                keep = sorted_posts[0]
                to_publish.append(keep)
                for p in sorted_posts[1:]:
                    to_cancel.append((
                        p['id'],
                        f"Executor cap: cancelled surplus eligible post for date {scheduled_date}; kept queue_id={keep['id']}",
                    ))
                if len(sorted_posts) > 1:
                    logger.info(
                        "Executor daily cap: date %s had %s eligible, kept id=%s (priority), cancelling %s surplus",
                        scheduled_date, len(sorted_posts), keep['id'], len(sorted_posts) - 1,
                    )
        return (to_publish, to_cancel)

    def route_to_platform_publisher(self, post: Dict) -> Dict:
        """
        Route post to appropriate platform publisher.
        
        Parameters
        ----------
        post:
            Post dict with platform field.
        
        Returns
        -------
        Dict with success status and platform_post_id.
        """
        platform = post.get('platform', '').lower()
        queue_id = post['id']
        
        logger.info(f"Routing post {queue_id} to platform: {platform}")
        
        if platform == 'facebook':
            result = publish_to_facebook(queue_id)
        elif platform == 'instagram':
            result = publish_to_instagram(queue_id)
        elif platform == 'twitter':
            result = publish_to_twitter(queue_id)
        elif platform == 'linkedin':
            result = publish_to_linkedin(queue_id)
        else:
            result = {
                'success': False,
                'error': f'Unknown platform: {platform}'
            }
        
        return result
    
    def process_due_posts(self) -> Dict[str, int]:
        """
        Process all posts that are due for publishing.
        
        CRITICAL: Checks automated_posting_enabled switch before publishing.
        If disabled, logs and returns without publishing.
        
        Returns
        -------
        Dict with stats: total_found, successfully_published, failed, skipped
        """
        stats = {
            'eligible_after_validation': 0,
            'total_found': 0,
            'successfully_published': 0,
            'failed': 0,
            'skipped': 0,
            'cancelled_surplus': 0,
            'blocked_wrong_day': 0,
        }
        
        try:
            # CRITICAL: Check if automated posting is enabled (unless bypassed)
            if not self._bypass_switch and not self.is_automated_posting_enabled():
                logger.info("Automated posting is DISABLED - skipping all publishing")
                due_posts = self.get_due_posts()
                stats['eligible_after_validation'] = len(due_posts)
                stats['total_found'] = len(due_posts)
                stats['skipped'] = len(due_posts)
                return stats
            
            # Get due posts (already validated by get_due_posts)
            due_posts = self.get_due_posts()
            stats['eligible_after_validation'] = len(due_posts)
            stats['total_found'] = len(due_posts)
            
            if not due_posts:
                logger.info("No posts due for publishing")
                return stats
            
            # Daily cap: at most one per day for Facebook (except Saturday products); cancel surplus
            posts_to_publish, cancel_list = self.apply_daily_cap(due_posts)
            if cancel_list:
                stats['cancelled_surplus'] = len(cancel_list)
                if self._dry_run:
                    for queue_id, error_message in cancel_list:
                        logger.info("DRY-RUN would cancel id=%s: %s", queue_id, error_message[:80])
                else:
                    with self.db_manager.get_connection() as conn:
                        with conn.cursor() as cursor:
                            for queue_id, error_message in cancel_list:
                                cursor.execute("""
                                    UPDATE posting_queue
                                    SET status = 'cancelled', error_message = %s, updated_at = NOW()
                                    WHERE id = %s
                                """, (error_message, queue_id))
                    logger.info("Executor cap: cancelled %s surplus eligible row(s)", len(cancel_list))
            
            if self._dry_run:
                for post in posts_to_publish:
                    logger.info("DRY-RUN would publish id=%s platform=%s content_type=%s scheduled_date=%s",
                                post.get('id'), post.get('platform'), post.get('content_type'), post.get('scheduled_date'))
                logger.info("DRY-RUN complete: would publish %s, would cancel %s", len(posts_to_publish), len(cancel_list))
                return stats
            
            # Process each post (only those that passed the daily cap)
            for post in posts_to_publish:
                try:
                    queue_id = post['id']
                    
                    # CRITICAL SAFEGUARD: Re-check status and platform_post_id before posting
                    # This prevents race conditions where status might have changed
                    with self.db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT status, platform_post_id
                            FROM posting_queue
                            WHERE id = %s
                        """, (queue_id,))
                        current_state = cursor.fetchone()
                        
                        if not current_state:
                            logger.warning(f"Post {queue_id} no longer exists, skipping")
                            stats['skipped'] += 1
                            continue
                        
                        # If already published, skip (shouldn't happen but defense in depth)
                        if current_state['status'] == 'published':
                            logger.warning(f"Post {queue_id} already published (status={current_state['status']}), skipping")
                            stats['skipped'] += 1
                            continue
                        
                        # If has platform_post_id, it was already posted - skip
                        if current_state['platform_post_id']:
                            logger.warning(f"Post {queue_id} already has platform_post_id={current_state['platform_post_id']}, skipping to prevent duplicate")
                            # Update status to published if it's not already
                            if current_state['status'] != 'published':
                                cursor.execute("""
                                    UPDATE posting_queue
                                    SET status = 'published'
                                    WHERE id = %s
                                """, (queue_id,))
                            stats['skipped'] += 1
                            continue
                        
                        # Check if post is still pending or ready
                        if current_state['status'] not in ('pending', 'ready'):
                            logger.debug(f"Post {queue_id} status changed to {current_state['status']}, skipping")
                            stats['skipped'] += 1
                            continue
                    
                    # For weekly content, ensure workflow has been run
                    content_type = post.get('content_type', '').lower()
                    if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                        # Check if image and caption exist
                        with self.db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                SELECT image_path, generated_caption
                                FROM posting_queue
                                WHERE id = %s
                            """, (queue_id,))
                            row = cursor.fetchone()
                            
                            if not row or not row.get('image_path') or not row.get('generated_caption'):
                                logger.warning(f"Weekly content post {queue_id} missing image or caption, skipping")
                                stats['skipped'] += 1
                                continue
                    
                    # Atomic claim: prevent two processes publishing the same row (only one winner)
                    # Claim only if still eligible: status in ready/pending AND platform_post_id IS NULL
                    with self.db_manager.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE posting_queue
                                SET status = 'publishing', updated_at = NOW()
                                WHERE id = %s AND status IN ('ready', 'pending')
                                  AND (platform_post_id IS NULL OR platform_post_id = '')
                            """, (queue_id,))
                            if cursor.rowcount != 1:
                                logger.warning(
                                    "Post %s not claimed (rowcount=%s); already claimed/published by another process, skipping",
                                    queue_id, cursor.rowcount,
                                )
                                stats['skipped'] += 1
                                continue
                    
                    # Route to platform publisher
                    result = self.route_to_platform_publisher(post)
                    
                    if result.get('success'):
                        stats['successfully_published'] += 1
                        
                        # Update status to 'published'
                        platform_post_id = result.get('platform_post_id')
                        with self.db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                UPDATE posting_queue
                                SET status = 'published',
                                    platform_post_id = %s,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (platform_post_id, queue_id))
                        
                        logger.info(f"Successfully published post {queue_id} to {post.get('platform')}")
                    else:
                        # Check if error is due to posting being disabled
                        error_msg = result.get('error', 'Unknown error')
                        if 'disabled' in str(error_msg).lower() or 'blocked' in str(error_msg).lower():
                            # Don't mark as failed - keep as 'ready' so it can be retried when posting is re-enabled
                            logger.info(f"Posting disabled for queue_id {queue_id}, keeping status as 'ready' (not marking as failed)")
                            stats['skipped'] += 1
                        else:
                            # Real error - mark as failed
                            stats['failed'] += 1
                            with self.db_manager.get_cursor() as cursor:
                                cursor.execute("""
                                    UPDATE posting_queue
                                    SET status = 'failed',
                                        error_message = %s,
                                        updated_at = NOW()
                                    WHERE id = %s
                                """, (error_msg, queue_id))
                            
                            logger.error(f"Failed to publish post {queue_id}: {error_msg}")
                        
                except Exception as e:
                    logger.error(f"Error processing post {post.get('id', 'unknown')}: {e}")
                    logger.exception("Full exception details:")
                    stats['failed'] += 1
            
            logger.info(
                "Scheduled posting execution complete: eligible=%s published=%s failed=%s skipped=%s cancelled_surplus=%s",
                stats['eligible_after_validation'], stats['successfully_published'], stats['failed'],
                stats['skipped'], stats['cancelled_surplus'],
            )
            return stats
            
        except Exception as e:
            logger.error(f"Error in process_due_posts: {e}")
            logger.exception("Full exception details:")
            return stats


def main():
    """
    Main function to run the scheduled posting executor

    Command-line arguments:
    --bypass-switch: Bypass the automated_posting_enabled check (for manual triggers)
    --dry-run: Log due posts, daily cap, and cancellations only; no DB updates or publishing
    """
    try:
        import argparse
        parser = argparse.ArgumentParser(description='Scheduled Posting Executor')
        parser.add_argument('--bypass-switch', action='store_true',
                          help='Bypass automated_posting_enabled check (for manual triggers)')
        parser.add_argument('--dry-run', action='store_true',
                          help='Log due posts, daily cap selection, and cancellations only; do not update DB or publish')
        args = parser.parse_args()

        logger.info("Starting scheduled posting executor")
        try:
            from config.unified_config import get_database_target_for_logging
            logger.info("DB target: %s", get_database_target_for_logging())
        except Exception:
            logger.info("DB target: (config unavailable)")
        logger.info("Executor daily cap enabled (max 1 per day except Saturday products)")
        if args.bypass_switch:
            logger.info("BYPASS MODE: Ignoring automated_posting_enabled switch (manual trigger)")
        if args.dry_run:
            logger.info("DRY-RUN: No DB updates or publishing")

        # Create executor
        executor = ScheduledPostingExecutor()
        executor._bypass_switch = args.bypass_switch
        executor._dry_run = getattr(args, 'dry_run', False)

        # Process due posts
        stats = executor.process_due_posts()

        logger.info("Scheduled posting executor complete: %s", stats)

        # Exit with appropriate code
        if stats['failed'] > 0:
            sys.exit(1)  # Some posts failed
        else:
            sys.exit(0)  # Success

    except Exception as e:
        logger.error("Fatal error in scheduled posting executor: %s", e)
        logger.exception("Full exception details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
