#!/usr/bin/env python3
"""
Posting Executor - Actually posts content to social media platforms
Runs every few minutes to execute pending posts
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/posting_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PostingExecutor:
    def __init__(self):
        self.db_manager = db_manager
        
    def get_pending_posts(self) -> List[Dict]:
        """
        Get posts that are due to be published now (status = 'pending')
        """
        logger.debug("get_pending_posts called")
        
        try:
            with self.db_manager.get_cursor() as cursor:
                now = datetime.now()
                logger.debug(f"Current time: {now}")
                
                cursor.execute("""
                    SELECT pq.id, pq.platform, pq.channel_type, pq.content_type,
                           pq.generated_content, pq.status, pq.product_id, pq.section_id,
                           pq.scheduled_timestamp, pq.schedule_name, pq.timezone,
                           pq.scheduled_date, pq.scheduled_time,
                           cp.name as product_name, cp.sku, cp.image_url as product_image,
                           ps.section_heading as section_title
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    LEFT JOIN post_section ps ON pq.section_id = ps.id
                    WHERE pq.status IN ('pending', 'ready')
                    AND pq.status NOT IN ('published', 'failed')  -- CRITICAL: Never reprocess published posts
                    AND (
                        (pq.scheduled_timestamp IS NOT NULL AND pq.scheduled_timestamp <= %s)
                        OR (pq.scheduled_date IS NOT NULL AND pq.scheduled_time IS NOT NULL
                            AND (pq.scheduled_date::date + pq.scheduled_time::time)::timestamp <= %s)
                    )
                    ORDER BY COALESCE(pq.scheduled_timestamp, (pq.scheduled_date::date + pq.scheduled_time::time)::timestamp) ASC
                """, (now, now))
                
                posts = cursor.fetchall()
                logger.info(f"Found {len(posts)} pending posts ready for publishing")
                
                # Log details of each pending post
                for post in posts:
                    logger.debug(f"Pending post: ID={post['id']}, scheduled={post['scheduled_timestamp']}, platform={post['platform']}")
                
                # Also log all 'pending' posts to see what's available
                cursor.execute("""
                    SELECT id, status, scheduled_timestamp, platform, content_type
                    FROM posting_queue 
                    WHERE status = 'pending'
                    ORDER BY scheduled_timestamp ASC
                    LIMIT 10
                """)
                all_pending_posts = cursor.fetchall()
                logger.debug(f"All pending posts in queue: {len(all_pending_posts)}")
                for post in all_pending_posts:
                    logger.debug(f"Pending post: ID={post['id']}, scheduled={post['scheduled_timestamp']}, platform={post['platform']}")
                
                return posts
                
        except Exception as e:
            logger.error(f"Error fetching pending posts: {e}")
            logger.exception("Full exception details:")
            return []
    
    def post_to_facebook(self, post: Dict) -> Dict:
        """
        Post content to Facebook using the appropriate posting function
        Handles both product posts and weekly content posts
        
        ⚠️ DISABLED - Facebook posting has been disabled to prevent unwanted posts.
        """
        logger.error(f"BLOCKED: post_to_facebook called for post_id={post.get('id')} - Facebook posting is DISABLED")
        return {'success': False, 'error': 'Facebook posting has been disabled'}
        try:
            content_type = post.get('content_type', '').lower()
            queue_id = post['id']
            
            # Check if this is weekly content
            if content_type in ('weekly_word', 'weekly_phrase', 'weekly_insult'):
                # Use weekly content workflow
                logger.info(f"Using weekly content workflow for {content_type}")
                from blueprints.automation_execute import execute_publish_to_facebook
                
                result = execute_publish_to_facebook(queue_id, {})
                
                # Handle tuple return (result, status_code) or dict return
                if isinstance(result, tuple):
                    result_dict, status_code = result
                else:
                    result_dict = result
                    status_code = 200 if result_dict.get('success') else 500
                
                if status_code == 200 and result_dict.get('success'):
                    # Extract platform_post_id from results
                    platform_post_ids = result_dict.get('platform_post_ids', [])
                    platform_post_id = platform_post_ids[0] if platform_post_ids else None
                    
                    return {
                        'success': True,
                        'platform_post_id': platform_post_id,
                        'message': result_dict.get('message', 'Published successfully')
                    }
                else:
                    return {
                        'success': False,
                        'error': result_dict.get('error', 'Unknown error')
                    }
            else:
                # Use product post workflow (existing logic)
                from blueprints.launchpad import execute_facebook_post
                
                result = execute_facebook_post(queue_id)
                
                if result['success']:
                    return {
                        'success': True,
                        'platform_post_id': result.get('platform_post_ids', [None])[0] if result.get('platform_post_ids') else None,
                        'message': result['message']
                    }
                else:
                    return {
                        'success': False,
                        'error': result['message']
                    }
                
        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            logger.exception("Full exception details:")
            return {'success': False, 'error': str(e)}
    def execute_post(self, post: Dict) -> Dict:
        """
        Execute a single post to the appropriate platform
        """
        platform = post['platform'].lower()
        post_id = post['id']
        
        logger.info(f"Executing post {post_id} to {platform}")
        
        # Route to appropriate platform handler
        if platform == 'facebook':
            result = self.post_to_facebook(post)
        elif platform == 'instagram':
            result = self.post_to_instagram(post)
        elif platform == 'twitter':
            result = self.post_to_twitter(post)
        elif platform == 'linkedin':
            result = self.post_to_linkedin(post)
        else:
            result = {
                'success': False,
                'error': f'Unknown platform: {platform}'
            }
        
        return result
    
    def post_to_instagram(self, post: Dict) -> Dict:
        """
        Post content to Instagram
        Currently not implemented - returns error
        """
        logger.warning(f"Instagram posting not yet implemented for post {post['id']}")
        return {
            'success': False,
            'error': 'Instagram posting is not yet implemented'
        }
    
    def post_to_twitter(self, post: Dict) -> Dict:
        """
        Post content to Twitter
        Currently not implemented - returns error
        """
        logger.warning(f"Twitter posting not yet implemented for post {post['id']}")
        return {
            'success': False,
            'error': 'Twitter posting is not yet implemented'
        }
    
    def post_to_linkedin(self, post: Dict) -> Dict:
        """
        Post content to LinkedIn
        Currently not implemented - returns error
        """
        logger.warning(f"LinkedIn posting not yet implemented for post {post['id']}")
        return {
            'success': False,
            'error': 'LinkedIn posting is not yet implemented'
        }
        
    def process_pending_posts(self) -> Dict[str, int]:
        """
        Process all pending posts that are due for publishing
        """
        stats = {
            'total_found': 0,
            'successfully_published': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            # Get pending posts
            pending_posts = self.get_pending_posts()
            stats['total_found'] = len(pending_posts)
            
            if not pending_posts:
                logger.info("No pending posts ready for publishing")
                return stats
            
            # Process each post
            for post in pending_posts:
                try:
                    # CRITICAL SAFEGUARD: Re-check status and platform_post_id before posting
                    # This prevents race conditions where status might have changed
                    with self.db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT status, platform_post_id
                            FROM posting_queue
                            WHERE id = %s
                        """, (post['id'],))
                        current_state = cursor.fetchone()
                        
                        if not current_state:
                            logger.warning(f"Post {post['id']} no longer exists, skipping")
                            stats['skipped'] += 1
                            continue
                        
                        # If already published, skip (shouldn't happen but defense in depth)
                        if current_state['status'] == 'published':
                            logger.warning(f"Post {post['id']} already published (status={current_state['status']}), skipping")
                            stats['skipped'] += 1
                            continue
                        
                        # If has platform_post_id, it was already posted - skip
                        if current_state['platform_post_id']:
                            logger.warning(f"Post {post['id']} already has platform_post_id={current_state['platform_post_id']}, skipping to prevent duplicate")
                            # Update status to published if it's not already
                            if current_state['status'] != 'published':
                                cursor.execute("""
                                    UPDATE posting_queue
                                    SET status = 'published'
                                    WHERE id = %s
                                """, (post['id'],))
                            stats['skipped'] += 1
                            continue
                        
                        # Check if post is still pending or ready
                        if current_state['status'] not in ('pending', 'ready'):
                            logger.debug(f"Post {post['id']} status changed to {current_state['status']}, skipping")
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
                            """, (post['id'],))
                            row = cursor.fetchone()
                            
                            if not row or not row.get('image_path') or not row.get('generated_caption'):
                                logger.warning(f"Weekly content post {post['id']} missing image or caption, skipping")
                                stats['skipped'] += 1
                                continue
                    
                    # Execute the post
                    result = self.execute_post(post)
                    
                    if result['success']:
                        stats['successfully_published'] += 1
                        
                        # Update status to 'published'
                        with self.db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                UPDATE posting_queue
                                SET status = 'published',
                                    platform_post_id = %s,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (result.get('platform_post_id'), post['id']))
                    else:
                        # Check if error is due to posting being disabled
                        error_msg = result.get('error', 'Unknown error')
                        if 'disabled' in str(error_msg).lower() or 'blocked' in str(error_msg).lower():
                            # Don't mark as failed - keep as 'ready' so it can be retried when posting is re-enabled
                            logger.info(f"Posting disabled for queue_id {post['id']}, keeping status as 'ready' (not marking as failed)")
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
                                """, (error_msg, post['id']))
                        
                except Exception as e:
                    logger.error(f"Error processing post {post.get('id', 'unknown')}: {e}")
                    logger.exception("Full exception details:")
                    stats['failed'] += 1
            
            logger.info(f"Posting execution complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in process_pending_posts: {e}")
            return stats

def main():
    """
    Main function to run the posting executor
    """
    try:
        logger.info("Starting posting executor")
        
        # Create posting executor
        executor = PostingExecutor()
        
        # Process pending posts
        stats = executor.process_pending_posts()
        
        logger.info(f"Posting executor complete: {stats}")
        
        # Exit with appropriate code
        if stats['failed'] > 0:
            sys.exit(1)  # Some posts failed
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        logger.error(f"Fatal error in posting executor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
