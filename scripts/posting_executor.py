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
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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
        try:
            with self.db_manager.get_cursor() as cursor:
                now = datetime.now()
                
                cursor.execute("""
                    SELECT pq.id, pq.platform, pq.channel_type, pq.content_type,
                           pq.generated_content, pq.status, pq.product_id, pq.section_id,
                           pq.scheduled_timestamp, pq.schedule_name, pq.timezone,
                           cp.name as product_name, cp.sku, cp.image_url as product_image,
                           ps.section_heading as section_title
                    FROM posting_queue pq
                    LEFT JOIN clan_products cp ON pq.product_id = cp.id
                    LEFT JOIN post_section ps ON pq.section_id = ps.id
                    WHERE pq.status = 'pending'
                    AND pq.scheduled_timestamp IS NOT NULL
                    AND pq.scheduled_timestamp <= %s
                    ORDER BY pq.scheduled_timestamp ASC
                """, (now,))
                
                posts = cursor.fetchall()
                logger.info(f"Found {len(posts)} pending posts ready for publishing")
                return posts
                
        except Exception as e:
            logger.error(f"Error fetching pending posts: {e}")
            return []
    
    def post_to_facebook(self, post: Dict) -> Dict:
        """
        Post content to Facebook using the shared posting function
        """
        try:
            # Import the shared posting function
            from blueprints.launchpad import execute_facebook_post
            
            # Use the shared function which handles both pages and proper image URLs
            result = execute_facebook_post(post['id'])
            
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
                    # Check if post is still pending
                    if post['status'] != 'pending':
                        stats['skipped'] += 1
                        continue
                    
                    # Execute the post
                    result = self.execute_post(post)
                    
                    if result['success']:
                        stats['successfully_published'] += 1
                    else:
                        stats['failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing post {post.get('id', 'unknown')}: {e}")
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
