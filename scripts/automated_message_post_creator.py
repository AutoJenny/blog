#!/usr/bin/env python3
"""
Automated Message Post Creator
Creates posting_queue entries for Facebook Messages posts from CSV file
Posts sequentially, looping back to start when finished
Runs daily to check for upcoming Saturdays and create draft posts
"""

import os
import sys
import csv
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/automated_message_post_creator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MessagePostCreator:
    def __init__(self):
        self.db_manager = db_manager
        self.csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'facebook_messages.csv'
        )
        self.publication_day = 6  # Saturday (1=Monday, 7=Sunday)
        self.publication_time = "14:30"  # 2:30 PM UK time
        
    def load_messages_from_csv(self) -> List[str]:
        """
        Load messages from CSV file.
        Returns list of message strings with \n\n preserved.
        """
        messages = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    message = row.get('message', '').strip()
                    if message:
                        messages.append(message)
            
            logger.info(f"Loaded {len(messages)} messages from CSV")
            return messages
        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading messages from CSV: {e}")
            return []
    
    def get_last_used_message_index(self, cursor) -> int:
        """
        Get the index of the last message that was used.
        Returns -1 if no messages have been posted yet.
        
        We track this by storing the message index in generated_content
        with a special prefix, or by checking the order of published posts.
        """
        # Get all published message posts in order
        cursor.execute("""
            SELECT generated_content, scheduled_timestamp
            FROM posting_queue
            WHERE content_type = 'message'
            AND platform = 'facebook'
            AND status = 'published'
            ORDER BY scheduled_timestamp DESC
        """)
        
        published_posts = cursor.fetchall()
        if not published_posts:
            return -1
        
        # Load all messages to match against
        messages = self.load_messages_from_csv()
        if not messages:
            return -1
        
        # Find the most recent published message in our list
        # and return its index
        for post in published_posts:
            post_content = post['generated_content'] or ''
            # Try to find matching message (normalize line breaks)
            for idx, msg in enumerate(messages):
                # Normalize both for comparison
                msg_normalized = msg.replace('\\n', '\n')
                if post_content.strip() == msg_normalized.strip():
                    return idx
        
        # If we can't match, assume we need to start from beginning
        # Count how many have been published and use that as index
        return len(published_posts) % len(messages) - 1
    
    def get_next_saturdays(self, days_ahead: int = 14) -> List[date]:
        """
        Get list of upcoming Saturday dates.
        """
        today = date.today()
        saturdays = []
        
        # Find next Saturday
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and datetime.now().time() < datetime.strptime(self.publication_time, "%H:%M").time():
            # Today is Saturday and publication time hasn't passed
            next_saturday = today
        else:
            if days_until_saturday == 0:
                days_until_saturday = 7  # Next Saturday
            next_saturday = today + timedelta(days=days_until_saturday)
        
        # Collect Saturdays up to days_ahead
        current = next_saturday
        while (current - today).days <= days_ahead:
            saturdays.append(current)
            current += timedelta(days=7)
        
        logger.info(f"Found {len(saturdays)} upcoming Saturdays: {saturdays}")
        return saturdays
    
    def create_message_post(self, message: str, message_index: int, scheduled_date: date, 
                           scheduled_time: str, cursor) -> Optional[int]:
        """
        Create a message post in posting_queue.
        Returns queue_id if successful, None otherwise.
        """
        try:
            # Convert \n\n to actual newlines for storage
            # We'll convert back when posting
            formatted_message = message.replace('\\n', '\n')
            
            # Create scheduled_timestamp
            scheduled_datetime = datetime.combine(scheduled_date, datetime.strptime(scheduled_time, "%H:%M").time())
            
            # Insert into posting_queue
            # Store message text in generated_content (line breaks preserved)
            cursor.execute("""
                INSERT INTO posting_queue (
                    content_type, platform, status,
                    generated_content,
                    scheduled_date, scheduled_time, scheduled_timestamp,
                    created_at, updated_at
                )
                VALUES (%s, 'facebook', 'draft', %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (
                'message',
                formatted_message,
                scheduled_date,
                scheduled_time,
                scheduled_datetime
            ))
            
            result = cursor.fetchone()
            queue_id = result['id'] if isinstance(result, dict) else result[0]
            
            logger.info(f"Created message post: queue_id={queue_id}, index={message_index}, scheduled={scheduled_date} {scheduled_time}")
            return queue_id
                
        except Exception as e:
            logger.error(f"Error creating message post: {e}")
            return None
    
    def create_message_posts(self, days_ahead: int = 14) -> Dict[str, int]:
        """
        Create message posts for upcoming Saturdays.
        Posts sequentially, looping back to start when finished.
        """
        stats = {
            'posts_created': 0,
            'posts_skipped': 0,
            'errors': 0
        }
        
        messages = self.load_messages_from_csv()
        if not messages:
            logger.error("No messages loaded from CSV")
            return stats
        
        saturdays = self.get_next_saturdays(days_ahead)
        if not saturdays:
            logger.info("No upcoming Saturdays found")
            return stats
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get last used message index
                    last_index = self.get_last_used_message_index(cursor)
                    next_index = (last_index + 1) % len(messages)
                    
                    logger.info(f"Starting from message index {next_index} (last used: {last_index})")
                    
                    # Check which Saturdays already have posts
                    if saturdays:
                        placeholders = ','.join(['%s'] * len(saturdays))
                        cursor.execute(f"""
                            SELECT scheduled_date
                            FROM posting_queue
                            WHERE content_type = 'message'
                            AND platform = 'facebook'
                            AND scheduled_date IN ({placeholders})
                            AND status != 'failed'
                        """, saturdays)
                        
                        existing_dates = {row['scheduled_date'] for row in cursor.fetchall()}
                    else:
                        existing_dates = set()
                    
                    # Create posts for Saturdays that don't have them
                    for saturday in saturdays:
                        if saturday in existing_dates:
                            logger.info(f"Skipping {saturday} - post already exists")
                            stats['posts_skipped'] += 1
                            continue
                        
                        # Skip if date is today or in the past
                        if saturday <= date.today():
                            logger.info(f"Skipping {saturday} - date is today or in the past")
                            stats['posts_skipped'] += 1
                            continue
                        
                        # Get message for this Saturday (sequential, looping)
                        message = messages[next_index]
                        
                        # Create post
                        queue_id = self.create_message_post(
                            message=message,
                            message_index=next_index,
                            scheduled_date=saturday,
                            scheduled_time=self.publication_time,
                            cursor=cursor
                        )
                        
                        if queue_id:
                            stats['posts_created'] += 1
                            # Move to next message (loop back to 0 when reaching end)
                            next_index = (next_index + 1) % len(messages)
                        else:
                            stats['errors'] += 1
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error creating message posts: {e}", exc_info=True)
            stats['errors'] += 1
        
        logger.info(f"Message post creation complete: {stats}")
        return stats


def main():
    """Main entry point for script"""
    creator = MessagePostCreator()
    stats = creator.create_message_posts(days_ahead=14)
    
    print(f"\nMessage Post Creation Results:")
    print(f"  Posts created: {stats['posts_created']}")
    print(f"  Posts skipped: {stats['posts_skipped']}")
    print(f"  Errors: {stats['errors']}")


if __name__ == '__main__':
    main()
