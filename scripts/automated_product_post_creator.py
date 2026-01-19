#!/usr/bin/env python3
"""
Automated Product Post Creator
Creates posting_queue entries for product posts 1 week in advance
Runs daily to check for upcoming schedule slots and create draft posts
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/automated_product_post_creator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductPostCreator:
    def __init__(self):
        self.db_manager = db_manager
        self.days_ahead = 7  # Create posts 1 week in advance
        
    def get_active_schedules(self, platform: str = 'facebook') -> List[Dict]:
        """
        Get active schedules for product posts
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, time, timezone, days, is_active
                    FROM daily_posts_schedule
                    WHERE is_active = true
                    AND platform = %s
                    AND content_type = 'product'
                    ORDER BY time ASC
                """, (platform,))
                
                schedules = cursor.fetchall()
                logger.info(f"Found {len(schedules)} active schedules for product posts")
                return schedules
                
        except Exception as e:
            logger.error(f"Error fetching active schedules: {e}")
            return []
    
    def get_upcoming_slots(self, schedules: List[Dict], days_ahead: int = 7) -> List[Dict]:
        """
        Calculate upcoming posting slots based on schedules
        Returns list of {date, time, schedule_id, schedule_name} dicts
        """
        slots = []
        today = date.today()
        
        for schedule in schedules:
            schedule_time = schedule['time']
            schedule_days = schedule['days']  # Array of day numbers (1=Monday, 7=Sunday)
            schedule_id = schedule['id']
            schedule_name = schedule.get('name', f"Schedule {schedule_id}")
            
            # Parse schedule_time if it's a string
            if isinstance(schedule_time, str):
                time_parts = schedule_time.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                schedule_time_obj = time(hour, minute)
            else:
                schedule_time_obj = schedule_time
            
            # Check each day in the lookahead period
            for day_offset in range(days_ahead):
                check_date = today + timedelta(days=day_offset)
                weekday = check_date.weekday() + 1  # 1=Monday, 7=Sunday
                
                # Check if this day matches the schedule
                if schedule_days and weekday in schedule_days:
                    slots.append({
                        'date': check_date,
                        'time': schedule_time_obj,
                        'schedule_id': schedule_id,
                        'schedule_name': schedule_name,
                        'datetime': datetime.combine(check_date, schedule_time_obj)
                    })
        
        # Sort by datetime
        slots.sort(key=lambda x: x['datetime'])
        logger.info(f"Found {len(slots)} upcoming posting slots")
        return slots
    
    def check_existing_post(self, scheduled_date: date, scheduled_time: time, platform: str = 'facebook', product_id: int = None) -> bool:
        """
        Check if a posting_queue entry already exists for this date/time/platform/product
        If product_id is provided, checks for that specific product. Otherwise checks for any product.
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                if product_id:
                    # Check for specific product at this time slot
                    cursor.execute("""
                        SELECT id FROM posting_queue
                        WHERE content_type = 'product'
                        AND platform = %s
                        AND scheduled_date = %s
                        AND scheduled_time = %s
                        AND product_id = %s
                        AND status NOT IN ('published', 'failed')
                    """, (platform, scheduled_date, scheduled_time, product_id))
                else:
                    # Check for any product at this time slot (prevent multiple products at same time)
                    cursor.execute("""
                        SELECT id FROM posting_queue
                        WHERE content_type = 'product'
                        AND platform = %s
                        AND scheduled_date = %s
                        AND scheduled_time = %s
                        AND status NOT IN ('published', 'failed')
                    """, (platform, scheduled_date, scheduled_time))
                
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking existing post: {e}")
            return False
    
    def get_products_not_posted_recently(self, limit: int = 10, days_back: int = 30) -> List[Dict]:
        """
        Get products that haven't been posted recently
        Prioritizes products with images
        """
        try:
            cutoff_date = date.today() - timedelta(days=days_back)
            
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT cp.id, cp.name, cp.sku, cp.image_url, cp.url
                    FROM clan_products cp
                    WHERE cp.image_url IS NOT NULL
                    AND cp.image_url != ''
                    AND cp.id NOT IN (
                        SELECT DISTINCT product_id
                        FROM posting_queue
                        WHERE product_id IS NOT NULL
                        AND content_type = 'product'
                        AND (
                            scheduled_date >= %s
                            OR status = 'published'
                        )
                    )
                    ORDER BY cp.id DESC
                    LIMIT %s
                """, (cutoff_date, limit))
                
                products = cursor.fetchall()
                logger.info(f"Found {len(products)} products not posted recently")
                return products
                
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    def create_product_post(self, product_id: int, scheduled_date: date, scheduled_time: time, 
                           schedule_id: int, schedule_name: str, platform: str = 'facebook') -> Optional[int]:
        """
        Create a draft product post in posting_queue
        Returns queue_id if successful, None otherwise
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                # Get product details
                cursor.execute("""
                    SELECT id, name, sku, description, image_url, url, price
                    FROM clan_products
                    WHERE id = %s
                """, (product_id,))
                
                product = cursor.fetchone()
                if not product:
                    logger.error(f"Product {product_id} not found")
                    return None
                
                # Create scheduled_timestamp
                scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
                
                # Insert into posting_queue
                cursor.execute("""
                    INSERT INTO posting_queue (
                        product_id, content_type, platform, status,
                        scheduled_date, scheduled_time, scheduled_timestamp,
                        schedule_name, created_at, updated_at
                    )
                    VALUES (%s, 'product', %s, 'draft', %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (
                    product_id, platform, scheduled_date, scheduled_time,
                    scheduled_datetime, schedule_name
                ))
                
                result = cursor.fetchone()
                queue_id = result['id'] if isinstance(result, dict) else result[0]
                
                logger.info(f"Created product post: queue_id={queue_id}, product={product['name']}, scheduled={scheduled_date} {scheduled_time}")
                return queue_id
                
        except Exception as e:
            logger.error(f"Error creating product post: {e}")
            return None
    
    def create_product_posts(self, days_ahead: int = 7) -> Dict[str, int]:
        """
        Create posting_queue entries for product posts in upcoming slots
        """
        stats = {
            'schedules_found': 0,
            'slots_found': 0,
            'slots_skipped': 0,
            'posts_created': 0,
            'errors': 0
        }
        
        try:
            # Get active schedules
            schedules = self.get_active_schedules()
            stats['schedules_found'] = len(schedules)
            
            if not schedules:
                logger.warning("No active schedules found for product posts")
                return stats
            
            # Get upcoming slots
            slots = self.get_upcoming_slots(schedules, days_ahead)
            stats['slots_found'] = len(slots)
            
            if not slots:
                logger.info("No upcoming posting slots found")
                return stats
            
            # Get products that haven't been posted recently
            products = self.get_products_not_posted_recently(limit=len(slots) * 2)  # Get extra in case some are skipped
            
            if not products:
                logger.warning("No products available for posting")
                return stats
            
            product_index = 0
            
            # Create posts for each slot
            for slot in slots:
                scheduled_date = slot['date']
                scheduled_time = slot['time']
                
                # Check if any post already exists for this slot (prevent duplicates)
                if self.check_existing_post(scheduled_date, scheduled_time):
                    logger.info(f"Post already exists for {scheduled_date} {scheduled_time}, skipping")
                    stats['slots_skipped'] += 1
                    continue
                
                # Get next available product
                if product_index >= len(products):
                    logger.warning(f"Ran out of products, only created {stats['posts_created']} posts")
                    break
                
                product = products[product_index]
                product_id = product['id']
                
                # Double-check this specific product isn't already scheduled for this slot
                if self.check_existing_post(scheduled_date, scheduled_time, product_id=product_id):
                    logger.info(f"Product {product_id} already scheduled for {scheduled_date} {scheduled_time}, trying next product")
                    # Try next product instead
                    product_index += 1
                    if product_index >= len(products):
                        logger.warning(f"Ran out of products")
                        break
                    product = products[product_index]
                    product_id = product['id']
                
                # Create post
                queue_id = self.create_product_post(
                    product_id=product_id,
                    scheduled_date=scheduled_date,
                    scheduled_time=scheduled_time,
                    schedule_id=slot['schedule_id'],
                    schedule_name=slot['schedule_name']
                )
                
                if queue_id:
                    stats['posts_created'] += 1
                    product_index += 1
                else:
                    stats['errors'] += 1
            
            logger.info(f"Product post creation complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in create_product_posts: {e}")
            logger.exception("Full exception details:")
            return stats

def main():
    """
    Main function to run the product post creator
    """
    try:
        logger.info("Starting automated product post creator")
        
        creator = ProductPostCreator()
        
        # Create posts for next 7 days (1 week ahead)
        stats = creator.create_product_posts(days_ahead=7)
        
        logger.info(f"Product post creator complete: {stats}")
        
        # Exit with appropriate code
        if stats['errors'] > 0:
            sys.exit(1)  # Some errors occurred
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        logger.error(f"Fatal error in product post creator: {e}")
        logger.exception("Full exception details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
