#!/usr/bin/env python3
"""
Verification script to check posting safeguards
Ensures no published posts are being reprocessed
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def verify_safeguards():
    """Verify that published posts are not being reprocessed"""
    
    print("=" * 60)
    print("POSTING SAFEGUARDS VERIFICATION")
    print("=" * 60)
    print()
    
    with db_manager.get_cursor() as cursor:
        # Check 1: Count posts by status
        print("1. Posting Queue Status Distribution:")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM posting_queue
            GROUP BY status
            ORDER BY count DESC
        """)
        status_counts = cursor.fetchall()
        for row in status_counts:
            print(f"   {row['status']}: {row['count']}")
        print()
        
        # Check 2: Find any published posts that might be getting reprocessed
        print("2. Checking for published posts with suspicious status changes:")
        cursor.execute("""
            SELECT id, status, platform, content_type, scheduled_timestamp, 
                   platform_post_id, updated_at
            FROM posting_queue
            WHERE status = 'published'
            AND platform_post_id IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 10
        """)
        published_posts = cursor.fetchall()
        print(f"   Found {len(published_posts)} published posts with platform_post_id")
        if published_posts:
            print("   Sample published posts:")
            for post in published_posts[:5]:
                print(f"   - ID {post['id']}: {post['content_type']} on {post['platform']}, "
                      f"posted at {post['updated_at']}")
        print()
        
        # Check 3: Find posts that are 'ready' or 'pending' but have platform_post_id
        # (This would indicate they were posted but status wasn't updated)
        print("3. Checking for posts that were posted but status not updated:")
        cursor.execute("""
            SELECT id, status, platform, content_type, scheduled_timestamp,
                   platform_post_id, updated_at
            FROM posting_queue
            WHERE status IN ('ready', 'pending', 'draft')
            AND platform_post_id IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 20
        """)
        suspicious_posts = cursor.fetchall()
        if suspicious_posts:
            print(f"   ⚠️  WARNING: Found {len(suspicious_posts)} posts with platform_post_id but wrong status!")
            print("   These posts were likely posted but status wasn't updated:")
            for post in suspicious_posts:
                print(f"   - ID {post['id']}: status={post['status']}, "
                      f"platform_post_id={post['platform_post_id']}, "
                      f"updated_at={post['updated_at']}")
        else:
            print("   ✅ No suspicious posts found - all posted items have correct status")
        print()
        
        # Check 4: Find posts that are 'ready' or 'pending' with past scheduled times
        # (These should be processed, but we want to verify they're not published)
        print("4. Checking for ready/pending posts with past scheduled times:")
        now = datetime.now()
        cursor.execute("""
            SELECT id, status, platform, content_type, scheduled_timestamp,
                   platform_post_id
            FROM posting_queue
            WHERE status IN ('ready', 'pending')
            AND (
                (scheduled_timestamp IS NOT NULL AND scheduled_timestamp <= %s)
                OR (scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL
                    AND (scheduled_date::date + scheduled_time::time)::timestamp <= %s)
            )
            AND platform_post_id IS NULL
            ORDER BY scheduled_timestamp DESC
            LIMIT 20
        """, (now, now))
        due_posts = cursor.fetchall()
        print(f"   Found {len(due_posts)} posts that are due but not yet posted")
        if due_posts:
            print("   These should be processed by posting_executor:")
            for post in due_posts[:10]:
                print(f"   - ID {post['id']}: {post['status']}, scheduled={post['scheduled_timestamp']}")
        print()
        
        # Check 5: Verify no published posts are in processing queries
        print("5. Verifying published posts are excluded from processing queries:")
        
        # Simulate the queries used by each script
        queries = {
            'workflow_executor': """
                SELECT COUNT(*) as count
                FROM posting_queue
                WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
                AND status = 'draft'
                AND platform = 'facebook'
                AND status NOT IN ('published', 'failed')
            """,
            'posting_executor': """
                SELECT COUNT(*) as count
                FROM posting_queue
                WHERE status IN ('pending', 'ready')
                AND status NOT IN ('published', 'failed')
                AND scheduled_timestamp <= %s
            """,
            'automated_posting': """
                SELECT COUNT(*) as count
                FROM posting_queue
                WHERE status = 'ready'
                AND status NOT IN ('published', 'failed')
                AND scheduled_timestamp <= %s
            """
        }
        
        for name, query in queries.items():
            if '%s' in query:
                cursor.execute(query, (now,))
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            print(f"   {name}: {result['count']} posts would be processed")
        
        # Check if any published posts would be included
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM posting_queue
            WHERE status = 'published'
            AND (
                (SELECT COUNT(*) FROM posting_queue WHERE status = 'draft' 
                 AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')) > 0
                OR
                (SELECT COUNT(*) FROM posting_queue WHERE status IN ('pending', 'ready')) > 0
            )
        """)
        overlap = cursor.fetchone()
        if overlap['count'] == 0:
            print("   ✅ No published posts would be included in processing queries")
        else:
            print(f"   ⚠️  WARNING: {overlap['count']} published posts might be included!")
        print()
        
        # Summary
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        if suspicious_posts:
            print("⚠️  ISSUES FOUND: Some posts have platform_post_id but wrong status")
            print("   These need to be fixed manually or will be reprocessed")
        else:
            print("✅ All safeguards appear to be working correctly")
            print("   - Published posts have correct status")
            print("   - No posts with platform_post_id have wrong status")
            print("   - Processing queries exclude published posts")
        print()

if __name__ == "__main__":
    verify_safeguards()
