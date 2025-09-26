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
        Post content to Facebook
        """
        try:
            # Import Facebook posting functionality
            from blueprints.launchpad import post_to_facebook_page
            
            # Get Facebook credentials
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT credential_key, credential_value 
                        FROM platform_credentials 
                        WHERE credential_key IN ('page_access_token', 'page_id')
                        AND platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
                        AND is_active = true
                    """)
                    
                    creds = {row['credential_key']: row['credential_value'] for row in cursor.fetchall()}
            
            page_access_token = creds.get('page_access_token')
            page_id = creds.get('page_id')
            
            if not page_access_token or not page_id:
                return {
                    'success': False,
                    'error': 'Facebook credentials not found'
                }
            
            # Get product URL for link sharing
            product_url = None
            if post.get('product_id'):
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT url FROM clan_products WHERE id = %s
                        """, (post['product_id'],))
                        
                        result = cursor.fetchone()
                        if result:
                            product_url = result['url']
            
            # Post to Facebook with product URL as link
            result = post_to_facebook_page(page_id, page_access_token, post['generated_content'], product_url, "Facebook Page")
            
            if result.get('success'):
                return {
                    'success': True,
                    'platform_post_id': result.get('post_id'),
                    'message': 'Successfully posted to Facebook'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown Facebook posting error')
                }
                
        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def post_to_instagram(self, post: Dict) -> Dict:
        """
        Post content to Instagram (placeholder - implement Instagram API)
        """
        # TODO: Implement Instagram posting
        logger.warning("Instagram posting not yet implemented")
        return {
            'success': False,
            'error': 'Instagram posting not yet implemented'
        }
    
    def post_to_twitter(self, post: Dict) -> Dict:
        """
        Post content to Twitter (placeholder - implement Twitter API)
        """
        # TODO: Implement Twitter posting
        logger.warning("Twitter posting not yet implemented")
        return {
            'success': False,
            'error': 'Twitter posting not yet implemented'
        }
    
    def post_to_linkedin(self, post: Dict) -> Dict:
        """
        Post content to LinkedIn (placeholder - implement LinkedIn API)
        """
        # TODO: Implement LinkedIn posting
        logger.warning("LinkedIn posting not yet implemented")
        return {
            'success': False,
            'error': 'LinkedIn posting not yet implemented'
        }
    
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
        
        # Update database with result
        self.update_post_result(post_id, result)
        
        return result
    
    def update_post_result(self, post_id: int, result: Dict):
        """
        Update the database with posting result
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    if result['success']:
                        # Successful post
                        cursor.execute("""
                            UPDATE posting_queue 
                            SET status = 'published', 
                                platform_post_id = %s,
                                updated_at = %s
                            WHERE id = %s
                        """, (result.get('platform_post_id'), datetime.now(), post_id))
                        
                        logger.info(f"Post {post_id} marked as published with platform ID: {result.get('platform_post_id')}")
                    else:
                        # Failed post
                        cursor.execute("""
                            UPDATE posting_queue 
                            SET status = 'failed', 
                                error_message = %s,
                                updated_at = %s
                            WHERE id = %s
                        """, (result.get('error', 'Unknown error'), datetime.now(), post_id))
                        
                        logger.error(f"Post {post_id} marked as failed: {result.get('error')}")
                    
                    # Commit the transaction
                    conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating post result for {post_id}: {e}")
    
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
