#!/usr/bin/env python3
"""
Test Weekly Content Facebook Post
----------------------------------
Creates a test Facebook post for last week's word-of-the-week.
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.posting_queue_helpers import create_weekly_social_post, get_posting_queue_row
from blueprints.automation_execute import (
    execute_format_for_facebook,
    execute_generate_caption,
    execute_add_hashtags,
    execute_optimize_for_facebook,
    execute_publish_to_facebook
)

def find_last_week_word():
    """Find last week's word-of-the-week from calendar_ideas."""
    today = datetime.now()
    last_week = today - timedelta(days=7)
    year, week_number, _ = last_week.isocalendar()
    
    print(f"Looking for weekly_word from year {year}, week {week_number}...")
    
    with db_manager.get_cursor() as cursor:
        # Try item_classification first, fallback to content_type
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'calendar_ideas' AND column_name = 'item_classification'
        """)
        has_classification = cursor.fetchone() is not None
        
        if has_classification:
            cursor.execute("""
                SELECT id, idea_title, idea_description, week_number
                FROM calendar_ideas
                WHERE week_number = %s
                AND item_classification = 'weekly_word'
                ORDER BY id DESC
                LIMIT 1
            """, (week_number,))
        else:
            cursor.execute("""
                SELECT id, idea_title, idea_description, week_number
                FROM calendar_ideas
                WHERE week_number = %s
                AND content_type = 'weekly_word'
                ORDER BY id DESC
                LIMIT 1
            """, (week_number,))
        
        word = cursor.fetchone()
        
        if not word:
            print(f"❌ No weekly_word found for week {week_number}")
            return None
        
        print(f"✅ Found: {word['idea_title']} (ID: {word['id']})")
        return word

def main():
    print("=" * 60)
    print("Testing Weekly Content Facebook Post")
    print("=" * 60)
    print()
    
    # Step 1: Find last week's word
    word = find_last_week_word()
    if not word:
        print("❌ Cannot proceed without a word-of-the-week")
        return 1
    
    idea_id = word['id']
    print()
    
    # Step 2: Create posting_queue entry
    print("Step 1: Creating posting_queue entry...")
    try:
        queue_id = create_weekly_social_post(
            idea_id=idea_id,
            content_type='weekly_word',
            platform='facebook',
            generated_content='Test post for weekly word',
            status='draft'
        )
        print(f"✅ Created posting_queue entry: ID {queue_id}")
    except Exception as e:
        print(f"❌ Error creating posting_queue entry: {e}")
        return 1
    
    print()
    
    # Step 3: Execute workflow stages
    print("Step 2: Executing workflow stages...")
    print()
    
    stages = [
        ("format_for_facebook", execute_format_for_facebook),
        ("generate_caption", execute_generate_caption),
        ("add_hashtags", execute_add_hashtags),
        ("optimize_for_facebook", execute_optimize_for_facebook),
        ("publish_to_facebook", execute_publish_to_facebook),
    ]
    
    for stage_name, stage_func in stages:
        print(f"  → Executing {stage_name}...")
        try:
            result = stage_func(queue_id, {})
            
            # Handle both (dict, status_code) tuple and dict-only returns
            if isinstance(result, tuple):
                result_dict, status_code = result
            else:
                result_dict = result
                status_code = 200 if result_dict.get('success') else 500
            
            if status_code == 200 and result_dict.get('success'):
                print(f"    ✅ {stage_name} completed successfully")
                if 'message' in result_dict:
                    print(f"       {result_dict['message']}")
            else:
                print(f"    ⚠️  {stage_name} returned: {result_dict}")
                if status_code != 200:
                    print(f"       Status code: {status_code}")
        except Exception as e:
            print(f"    ❌ Error in {stage_name}: {e}")
            import traceback
            traceback.print_exc()
            return 1
        print()
    
    # Step 4: Check final status
    print("Step 3: Checking final status...")
    queue_row = get_posting_queue_row(queue_id)
    if queue_row:
        print(f"✅ Final status: {queue_row.get('status')}")
        print(f"   Platform post ID: {queue_row.get('platform_post_id')}")
        print(f"   Image path: {queue_row.get('image_path')}")
        print(f"   Generated caption: {queue_row.get('generated_caption', '')[:100]}...")
    else:
        print("❌ Could not retrieve posting_queue row")
        return 1
    
    print()
    print("=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
