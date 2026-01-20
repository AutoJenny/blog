#!/usr/bin/env python3
"""
Automated Product Post Workflow Executor
Runs workflow stages for draft product posts
Executes: format → caption → hashtags → image → publish
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from blueprints.automation_execute import (
    execute_format_for_facebook,
    execute_generate_caption,
    execute_add_hashtags,
    execute_optimize_for_facebook
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/automated_product_post_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductPostWorkflowExecutor:
    def __init__(self):
        self.db_manager = db_manager
        
    def get_draft_product_posts(self) -> List[Dict]:
        """
        Get draft product posts that need workflow execution
        Only gets posts that haven't been published yet
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, product_id, content_type, platform, scheduled_date, scheduled_time
                    FROM posting_queue
                    WHERE content_type = 'product'
                    AND status = 'draft'
                    AND platform = 'facebook'
                    AND status NOT IN ('published', 'failed')  -- CRITICAL: Never reprocess published or failed posts
                    ORDER BY scheduled_date ASC, scheduled_time ASC
                    LIMIT 10
                """)
                
                posts = cursor.fetchall()
                logger.info(f"Found {len(posts)} draft product posts")
                return posts
                
        except Exception as e:
            logger.error(f"Error fetching draft posts: {e}")
            return []
    
    def execute_workflow_stages(self, queue_id: int) -> Dict[str, bool]:
        """
        Execute all workflow stages for a product post
        Returns dict with success status for each stage
        """
        results = {
            'format_for_facebook': False,
            'generate_caption': False,
            'add_hashtags': False,
            'optimize_for_facebook': False,
            'publish_to_facebook': False
        }
        
        try:
            # Stage 1: Format for Facebook
            logger.info(f"Executing format_for_facebook for queue_id {queue_id}")
            result = execute_format_for_facebook(queue_id, {})
            if isinstance(result, tuple):
                result_dict, status_code = result
            else:
                result_dict = result
                status_code = 200 if result_dict.get('success') else 500
            
            if status_code == 200 and result_dict.get('success'):
                results['format_for_facebook'] = True
                logger.info(f"✅ format_for_facebook completed")
            else:
                logger.error(f"❌ format_for_facebook failed: {result_dict}")
                return results  # Stop if first stage fails
            
            # Stage 2: Generate caption
            logger.info(f"Executing generate_caption for queue_id {queue_id}")
            result = execute_generate_caption(queue_id, {})
            if isinstance(result, tuple):
                result_dict, status_code = result
            else:
                result_dict = result
                status_code = 200 if result_dict.get('success') else 500
            
            if status_code == 200 and result_dict.get('success'):
                results['generate_caption'] = True
                logger.info(f"✅ generate_caption completed")
            else:
                logger.error(f"❌ generate_caption failed: {result_dict}")
                return results  # Stop if caption generation fails
            
            # Stage 3: Add hashtags
            logger.info(f"Executing add_hashtags for queue_id {queue_id}")
            result = execute_add_hashtags(queue_id, {})
            if isinstance(result, tuple):
                result_dict, status_code = result
            else:
                result_dict = result
                status_code = 200 if result_dict.get('success') else 500
            
            if status_code == 200 and result_dict.get('success'):
                results['add_hashtags'] = True
                logger.info(f"✅ add_hashtags completed")
            else:
                logger.warning(f"⚠️ add_hashtags failed: {result_dict}")
                # Continue even if hashtags fail
            
            # Stage 4: Optimize for Facebook (use product image)
            logger.info(f"Executing optimize_for_facebook for queue_id {queue_id}")
            result = execute_optimize_for_facebook(queue_id, {})
            if isinstance(result, tuple):
                result_dict, status_code = result
            else:
                result_dict = result
                status_code = 200 if result_dict.get('success') else 500
            
            if status_code == 200 and result_dict.get('success'):
                results['optimize_for_facebook'] = True
                logger.info(f"✅ optimize_for_facebook completed")
            else:
                logger.error(f"❌ optimize_for_facebook failed: {result_dict}")
                return results  # Stop if image optimization fails
            
            # Stage 5: Mark as ready for publishing
            # CRITICAL: Do NOT publish directly from workflow executor.
            # The centralized scheduler (scheduled_posting_executor.py) handles all publishing
            # with proper date validation. We only set status to 'ready' here.
            logger.info(f"Workflow completed for queue_id {queue_id}, setting status to 'ready' for scheduled_posting_executor")
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE posting_queue
                    SET status = 'ready', updated_at = NOW()
                    WHERE id = %s
                """, (queue_id,))
            results['publish_to_facebook'] = False  # Not published yet, will be handled by scheduled_posting_executor
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing workflow for queue_id {queue_id}: {e}")
            logger.exception("Full exception details:")
            return results
    
    def process_draft_posts(self) -> Dict[str, int]:
        """
        Process all draft product posts
        """
        stats = {
            'total_found': 0,
            'workflows_completed': 0,
            'workflows_failed': 0,
            'published': 0
        }
        
        try:
            # Get draft posts
            draft_posts = self.get_draft_product_posts()
            stats['total_found'] = len(draft_posts)
            
            if not draft_posts:
                logger.info("No draft product posts found")
                return stats
            
            # Process each post
            for post in draft_posts:
                queue_id = post['id']
                try:
                    logger.info(f"Processing queue_id {queue_id} (product_id: {post['product_id']})")
                    
                    # Execute workflow
                    results = self.execute_workflow_stages(queue_id)
                    
                    # Check if workflow completed successfully
                    if results.get('format_for_facebook') and results.get('generate_caption') and results.get('optimize_for_facebook'):
                        stats['workflows_completed'] += 1
                        if results.get('publish_to_facebook'):
                            stats['published'] += 1
                    else:
                        stats['workflows_failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing queue_id {queue_id}: {e}")
                    stats['workflows_failed'] += 1
            
            logger.info(f"Product post workflow execution complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in process_draft_posts: {e}")
            logger.exception("Full exception details:")
            return stats

def main():
    """
    Main function to run the product post workflow executor
    """
    try:
        logger.info("Starting automated product post workflow executor")
        
        executor = ProductPostWorkflowExecutor()
        
        # Process draft posts
        stats = executor.process_draft_posts()
        
        logger.info(f"Product post workflow executor complete: {stats}")
        
        # Exit with appropriate code
        if stats['workflows_failed'] > 0:
            sys.exit(1)  # Some workflows failed
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        logger.error(f"Fatal error in product post workflow executor: {e}")
        logger.exception("Full exception details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
