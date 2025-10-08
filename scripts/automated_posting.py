#!/usr/bin/env python3
"""
Automated Social Media Posting System
Checks for due posts and schedules them with random delays for natural distribution
"""

import os
import sys
import random
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from blueprints.llm_actions import LLMService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/automated_posting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedPostingSystem:
    def __init__(self):
        self.db_manager = db_manager
        self.llm_service = LLMService()
        
    def get_due_posts(self, check_window_minutes: int = 30) -> List[Dict]:
        """
        Get posts that are due to be published within the next check_window_minutes
        """
        logger.debug(f"get_due_posts called with check_window_minutes={check_window_minutes}")
        
        try:
            with self.db_manager.get_cursor() as cursor:
                # Calculate the time window
                now = datetime.now()
                window_end = now + timedelta(minutes=check_window_minutes)
                
                logger.debug(f"Current time: {now}")
                logger.debug(f"Window end: {window_end}")
                
                cursor.execute("""
                    SELECT pq.id, pq.platform, pq.channel_type, pq.content_type,
                           pq.generated_content, pq.status, pq.product_id, pq.section_id,
                           pq.scheduled_timestamp, pq.schedule_name, pq.timezone,
                           cp.name as product_name, cp.sku, cp.image_url as product_image,
                           ps.section_heading as section_title
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    LEFT JOIN post_section ps ON pq.section_id = ps.id
                    WHERE pq.status = 'ready'
                    AND pq.scheduled_timestamp IS NOT NULL
                    AND pq.scheduled_timestamp <= %s
                    ORDER BY pq.scheduled_timestamp ASC
                """, (window_end,))
                
                posts = cursor.fetchall()
                logger.info(f"Found {len(posts)} posts due for publishing in next {check_window_minutes} minutes")
                
                # Log details of each post found
                for post in posts:
                    logger.debug(f"Due post: ID={post['id']}, scheduled={post['scheduled_timestamp']}, status={post['status']}, platform={post['platform']}")
                
                # Also log all 'ready' posts to see what's available
                cursor.execute("""
                    SELECT id, status, scheduled_timestamp, platform, content_type
                    FROM posting_queue 
                    WHERE status = 'ready'
                    ORDER BY scheduled_timestamp ASC
                    LIMIT 10
                """)
                all_ready_posts = cursor.fetchall()
                logger.debug(f"All ready posts in queue: {len(all_ready_posts)}")
                for post in all_ready_posts:
                    logger.debug(f"Ready post: ID={post['id']}, scheduled={post['scheduled_timestamp']}, platform={post['platform']}")
                
                return posts
                
        except Exception as e:
            logger.error(f"Error fetching due posts: {e}")
            logger.exception("Full exception details:")
            return []
    
    def calculate_staggered_time(self, scheduled_time: datetime, 
                                min_delay: int = 1, max_delay: int = 29) -> datetime:
        """
        Calculate a random staggered time for posting
        """
        # Generate random delay in minutes
        delay_minutes = random.randint(min_delay, max_delay)
        
        # Add delay to scheduled time
        staggered_time = scheduled_time + timedelta(minutes=delay_minutes)
        
        # Ensure we don't go too far into the future (max 2 hours ahead)
        max_future = datetime.now() + timedelta(hours=2)
        if staggered_time > max_future:
            staggered_time = max_future
            
        return staggered_time
    
    def is_optimal_posting_time(self, post_time: datetime, platform: str, content_type: str) -> bool:
        """
        Check if the posting time is optimal for the platform and content type
        """
        hour = post_time.hour
        
        # Avoid very early morning and very late night
        if hour < 6 or hour > 23:
            return False
            
        # Platform-specific optimal times
        if platform == 'facebook':
            # Facebook: Avoid 8-9 AM and 5-6 PM (rush hours)
            if hour in [8, 9, 17, 18]:
                return False
        elif platform == 'instagram':
            # Instagram: Prefer 11 AM - 1 PM and 5-7 PM
            if not (11 <= hour <= 13 or 17 <= hour <= 19):
                return False
        elif platform == 'twitter':
            # Twitter: More flexible, but avoid 8-9 AM and 5-6 PM
            if hour in [8, 9, 17, 18]:
                return False
                
        # Content type considerations
        if content_type == 'blog_post':
            # Blog posts: Prefer 10 AM - 2 PM and 7-9 PM
            if not (10 <= hour <= 14 or 19 <= hour <= 21):
                return False
        elif content_type == 'product':
            # Product posts: Prefer 11 AM - 1 PM and 6-8 PM
            if not (11 <= hour <= 13 or 18 <= hour <= 20):
                return False
                
        return True
    
    def schedule_post(self, post: Dict) -> bool:
        """
        Schedule a post for publishing with staggered timing
        """
        logger.debug(f"schedule_post called for post ID={post.get('id', 'unknown')}")
        
        try:
            post_id = post['id']
            scheduled_time = post['scheduled_timestamp']
            platform = post['platform']
            content_type = post['content_type']
            
            logger.debug(f"Post {post_id}: original scheduled_time={scheduled_time}, platform={platform}, content_type={content_type}")
            
            # Calculate staggered time
            now = datetime.now()
            if scheduled_time <= now:
                # If post is overdue, schedule for immediate posting (within 5 minutes)
                staggered_time = now + timedelta(minutes=1)
                logger.debug(f"Post {post_id}: overdue, scheduling for immediate posting at {staggered_time}")
            else:
                # If post is in the future, use normal staggering
                staggered_time = self.calculate_staggered_time(scheduled_time)
                logger.debug(f"Post {post_id}: future post, staggered_time={staggered_time}")
                
                # Check if the staggered time is optimal
                if not self.is_optimal_posting_time(staggered_time, platform, content_type):
                    logger.debug(f"Post {post_id}: staggered time not optimal, trying alternatives")
                    # If not optimal, try a different random time within the next 2 hours
                    for attempt in range(3):  # Try up to 3 times
                        staggered_time = self.calculate_staggered_time(scheduled_time, 1, 119)
                        logger.debug(f"Post {post_id}: attempt {attempt+1}, staggered_time={staggered_time}")
                        if self.is_optimal_posting_time(staggered_time, platform, content_type):
                            logger.debug(f"Post {post_id}: found optimal time on attempt {attempt+1}")
                            break
                    else:
                        logger.warning(f"Post {post_id}: could not find optimal posting time, using last attempt")
            
            # Update the post with staggered time
            logger.debug(f"Post {post_id}: updating database with staggered_time={staggered_time}")
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE posting_queue 
                        SET scheduled_timestamp = %s, status = 'pending'
                        WHERE id = %s
                    """, (staggered_time, post_id))
                    
                    conn.commit()
                    logger.info(f"Scheduled post {post_id} for {staggered_time} (originally {scheduled_time})")
                    return True
                
        except Exception as e:
            logger.error(f"Error scheduling post {post.get('id', 'unknown')}: {e}")
            logger.exception("Full exception details:")
            return False
    
    def process_due_posts(self, check_window_minutes: int = 30) -> Dict[str, int]:
        """
        Process all due posts and schedule them with staggered timing
        """
        stats = {
            'total_found': 0,
            'successfully_scheduled': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            logger.debug(f"process_due_posts: starting with check_window_minutes={check_window_minutes}")
            
            # Get due posts
            due_posts = self.get_due_posts(check_window_minutes)
            stats['total_found'] = len(due_posts)
            
            logger.info(f"Found {len(due_posts)} posts due for processing")
            
            if not due_posts:
                logger.info("No posts due for publishing")
                return stats
            
            # Process each post
            for i, post in enumerate(due_posts):
                post_id = post.get('id', 'unknown')
                logger.debug(f"Processing post {i+1}/{len(due_posts)}: ID={post_id}")
                
                try:
                    # Check if post is still valid for scheduling
                    if post['status'] != 'ready':
                        logger.warning(f"Post {post_id}: status is '{post['status']}', not 'ready', skipping")
                        stats['skipped'] += 1
                        continue
                    
                    logger.debug(f"Post {post_id}: status is 'ready', proceeding with scheduling")
                    
                    # Schedule the post
                    if self.schedule_post(post):
                        stats['successfully_scheduled'] += 1
                        logger.info(f"Post {post_id}: successfully scheduled")
                    else:
                        stats['failed'] += 1
                        logger.error(f"Post {post_id}: failed to schedule")
                        
                except Exception as e:
                    logger.error(f"Error processing post {post_id}: {e}")
                    logger.exception("Full exception details:")
                    stats['failed'] += 1
            
            logger.info(f"Processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in process_due_posts: {e}")
            return stats

def main():
    """
    Main function to run the automated posting system
    """
    try:
        logger.info("Starting automated posting system")
        logger.debug("Creating AutomatedPostingSystem instance")
        
        # Create posting system
        posting_system = AutomatedPostingSystem()
        logger.debug("AutomatedPostingSystem created successfully")
        
        # Process due posts (30-minute window)
        logger.debug("Starting process_due_posts with 30-minute window")
        stats = posting_system.process_due_posts(check_window_minutes=30)
        
        logger.info(f"Automated posting complete: {stats}")
        
        # Exit with appropriate code
        if stats['failed'] > 0:
            sys.exit(1)  # Some posts failed
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        logger.error(f"Fatal error in automated posting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
