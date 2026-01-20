#!/usr/bin/env python3
"""
Automated Weekly Content Creator
Creates posting_queue entries for weekly content items 1 week in advance
Runs daily to check for upcoming weekly content and create draft posts
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.calendar_resolver import resolve_item_for_week
from utils.posting_queue_helpers import create_weekly_social_post

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('/Users/autojenny/Documents/projects/blog/logs/automated_weekly_content_creator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeeklyContentCreator:
    def __init__(self):
        self.db_manager = db_manager
        # Default publication day and time for weekly content (can be configured)
        self.default_publication_day = 1  # Monday (1=Monday, 7=Sunday)
        self.default_publication_time = "09:00"  # 9 AM
        
    def get_upcoming_weeks(self, days_ahead: int = 7) -> List[tuple]:
        """
        Get list of (year, week_number) tuples for upcoming weeks
        """
        today = datetime.now()
        weeks = []
        
        for i in range(days_ahead):
            target_date = today + timedelta(days=i)
            year, week_number, _ = target_date.isocalendar()
            if (year, week_number) not in weeks:
                weeks.append((year, week_number))
        
        return weeks
    
    def check_existing_post(self, idea_id: int, content_type: str, platform: str, scheduled_date: str) -> bool:
        """
        Check if a posting_queue entry already exists for this idea/platform/date
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM posting_queue
                    WHERE idea_id = %s
                    AND content_type = %s
                    AND platform = %s
                    AND scheduled_date = %s
                """, (idea_id, content_type, platform, scheduled_date))
                
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking existing post: {e}")
            return False
    
    def get_publication_date_for_week(self, year: int, week_number: int, content_type: str = None) -> Optional[str]:
        """
        Get the publication date for a week based on content type
        - weekly_word: Monday (day 1)
        - weekly_phrase: Wednesday (day 3)
        - weekly_insult: Friday (day 5)
        Defaults to Monday if content_type not specified
        
        Uses ISO week calculation: finds Thursday of the target week (always in correct ISO week),
        then calculates Monday from there.
        """
        try:
            # ISO week calculation: January 4 is always in ISO week 1
            # Find Thursday of week 1 (more reliable than Monday due to year boundaries)
            jan4 = datetime(year, 1, 4)
            jan4_iso_year, jan4_iso_week, jan4_iso_weekday = jan4.isocalendar()
            
            # Calculate days to Thursday from Jan 4
            # ISO weekday: 1=Monday, 4=Thursday, 7=Sunday
            days_to_thursday = 4 - jan4_iso_weekday
            week1_thursday = jan4 + timedelta(days=days_to_thursday)
            
            # Verify week1_thursday is actually in week 1
            thursday_iso_year, thursday_iso_week, thursday_iso_weekday = week1_thursday.isocalendar()
            if thursday_iso_week != 1 or thursday_iso_year != year:
                # Adjust: if Jan 4 is in previous year's week 53, week 1 starts later
                # Find the first Thursday that's in week 1 of the target year
                # Try a few days around Jan 4
                for day_offset in range(-3, 4):
                    test_date = jan4 + timedelta(days=day_offset)
                    test_iso_year, test_iso_week, test_iso_weekday = test_date.isocalendar()
                    if test_iso_week == 1 and test_iso_year == year and test_iso_weekday == 4:
                        week1_thursday = test_date
                        break
            
            # Calculate Thursday of target week
            weeks_from_week1 = week_number - 1
            target_thursday = week1_thursday + timedelta(weeks=weeks_from_week1)
            
            # Go back to Monday (3 days before Thursday)
            target_monday = target_thursday - timedelta(days=3)
            
            # Verify we got the right week
            monday_iso_year, monday_iso_week, monday_iso_weekday = target_monday.isocalendar()
            if monday_iso_week != week_number or monday_iso_year != year:
                logger.error(f"ISO week calculation error: expected {year}-W{week_number:02d}, got {monday_iso_year}-W{monday_iso_week:02d}")
                # Fallback: brute force - find a date in the correct week
                # Start from January 1 and search forward
                test_date = datetime(year, 1, 1)
                for _ in range(365):
                    test_iso_year, test_iso_week, test_iso_weekday = test_date.isocalendar()
                    if test_iso_week == week_number and test_iso_year == year and test_iso_weekday == 1:
                        target_monday = test_date
                        break
                    test_date += timedelta(days=1)
            
            # Determine day offset based on content type
            day_offset = 0  # Default: Monday
            if content_type == 'weekly_word':
                day_offset = 0  # Monday
            elif content_type == 'weekly_phrase':
                day_offset = 2  # Wednesday
            elif content_type == 'weekly_insult':
                day_offset = 4  # Friday
            
            # Calculate target date
            target_date = target_monday + timedelta(days=day_offset)
            
            # Final verification and logging
            final_iso_year, final_iso_week, final_iso_weekday = target_date.isocalendar()
            logger.info(f"Calculated publication date for {year}-W{week_number:02d} {content_type}: {target_date.date()} (ISO: {final_iso_year}-W{final_iso_week:02d}-{final_iso_weekday}, day_offset={day_offset})")
            
            return target_date.date().isoformat()
        except Exception as e:
            logger.error(f"Error calculating publication date for {year}-W{week_number:02d} {content_type}: {e}")
            logger.exception("Full exception details:")
            return None
    
    def create_weekly_content_posts(self, days_ahead: int = 7) -> Dict[str, int]:
        """
        Create posting_queue entries for weekly content items in upcoming weeks
        """
        stats = {
            'weeks_checked': 0,
            'items_found': 0,
            'posts_created': 0,
            'posts_skipped': 0,
            'errors': 0
        }
        
        try:
            # Get upcoming weeks
            upcoming_weeks = self.get_upcoming_weeks(days_ahead)
            stats['weeks_checked'] = len(upcoming_weeks)
            
            logger.info(f"Checking {len(upcoming_weeks)} upcoming weeks for weekly content")
            
            # Weekly content types to check
            content_types = ['weekly_word', 'weekly_phrase', 'weekly_insult']
            platform = 'facebook'  # Default platform (can be extended)
            
            for year, week_number in upcoming_weeks:
                logger.info(f"Processing week {year}-W{week_number:02d}")
                
                for content_type in content_types:
                    try:
                        # Resolve item for this week
                        item = resolve_item_for_week(
                            content_type, 
                            year, 
                            week_number,
                            classification=content_type
                        )
                        
                        if not item:
                            continue
                        
                        stats['items_found'] += 1
                        idea_id = item.get('id')
                        idea_title = item.get('idea_title', '')
                        idea_description = item.get('idea_description', '')
                        
                        if not idea_id:
                            logger.warning(f"No idea_id found for {content_type} in week {year}-W{week_number:02d}")
                            continue
                        
                        # Get publication date (with correct day based on content type)
                        scheduled_date = self.get_publication_date_for_week(year, week_number, content_type)
                        if not scheduled_date:
                            logger.warning(f"Could not calculate publication date for week {year}-W{week_number:02d}")
                            continue
                        
                        # Check if post already exists (with better error handling)
                        try:
                            if self.check_existing_post(idea_id, content_type, platform, scheduled_date):
                                logger.info(f"Post already exists for {content_type} ID {idea_id} on {scheduled_date}")
                                stats['posts_skipped'] += 1
                                continue
                        except Exception as e:
                            # If check fails, assume post exists (safer - prevents duplicates)
                            logger.error(f"Error checking existing post for {content_type} ID {idea_id}: {e}. Skipping to prevent duplicates.")
                            stats['posts_skipped'] += 1
                            continue
                        
                        # Create posting_queue entry
                        logger.info(f"Creating post for {content_type} ID {idea_id} ({idea_title}) on {scheduled_date}")
                        
                        generated_content = f"{idea_title}\n\n{idea_description}".strip() if idea_description else idea_title
                        
                        try:
                            queue_id = create_weekly_social_post(
                                idea_id=idea_id,
                                content_type=content_type,
                                platform=platform,
                                generated_content=generated_content,
                                status='draft',
                                scheduled_date=scheduled_date,
                                scheduled_time=self.default_publication_time
                            )
                            
                            if queue_id:
                                logger.info(f"Created posting_queue entry: ID {queue_id}")
                                stats['posts_created'] += 1
                            else:
                                # create_weekly_social_post returns None on duplicate (database constraint)
                                logger.warning(f"Post creation skipped (likely duplicate): {content_type} ID {idea_id} on {scheduled_date}")
                                stats['posts_skipped'] += 1
                        except Exception as e:
                            # Handle database constraint violations (duplicate key)
                            if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                                logger.warning(f"Duplicate post prevented by database constraint: {content_type} ID {idea_id} on {scheduled_date}")
                                stats['posts_skipped'] += 1
                            else:
                                logger.error(f"Error creating post for {content_type} ID {idea_id}: {e}")
                                stats['errors'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing {content_type} for week {year}-W{week_number:02d}: {e}")
                        stats['errors'] += 1
                        continue
            
            logger.info(f"Weekly content creation complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in create_weekly_content_posts: {e}")
            logger.exception("Full exception details:")
            return stats

def main():
    """
    Main function to run the weekly content creator
    """
    try:
        logger.info("Starting automated weekly content creator")
        
        creator = WeeklyContentCreator()
        
        # Create posts for next 7 days (1 week ahead)
        stats = creator.create_weekly_content_posts(days_ahead=7)
        
        logger.info(f"Weekly content creator complete: {stats}")
        
        # Exit with appropriate code
        if stats['errors'] > 0:
            sys.exit(1)  # Some errors occurred
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        logger.error(f"Fatal error in weekly content creator: {e}")
        logger.exception("Full exception details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
