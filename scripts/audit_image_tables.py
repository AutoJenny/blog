#!/usr/bin/env python3
"""
Audit script for image/images table migration.
Runs pre-migration queries to understand current state.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_audit():
    """Run audit queries and display results."""
    print("=" * 80)
    print("IMAGE/IMAGES TABLE MIGRATION AUDIT")
    print("=" * 80)
    print()
    
    try:
        # Query 1: Count records in each table
        print("1. RECORD COUNTS")
        print("-" * 80)
        query = """
        SELECT 'image table' as table_name, COUNT(*) as record_count FROM image
        UNION ALL
        SELECT 'images table' as table_name, COUNT(*) as record_count FROM images;
        """
        results = db_manager.execute_query(query)
        for row in results:
            print(f"   {row['table_name']}: {row['record_count']} records")
        print()
        
        # Query 2: Check for ID conflicts
        print("2. ID CONFLICTS")
        print("-" * 80)
        query = """
        SELECT COUNT(*) as conflict_count
        FROM image i1
        JOIN images i2 ON i1.id = i2.id;
        """
        results = db_manager.execute_query(query)
        conflict_count = results[0]['conflict_count']
        print(f"   ID conflicts: {conflict_count}")
        if conflict_count > 0:
            print("   ⚠️  WARNING: ID conflicts detected! This needs resolution before migration.")
            # Show the conflicts
            query = """
            SELECT i1.id, i1.filename, i1.path, i2.filename, i2.file_path
            FROM image i1
            JOIN images i2 ON i1.id = i2.id
            LIMIT 10;
            """
            conflicts = db_manager.execute_query(query)
            print("   Sample conflicts:")
            for row in conflicts:
                print(f"      ID {row['id']}: image.path='{row['path']}' vs images.file_path='{row['file_path']}'")
        else:
            print("   ✅ No ID conflicts")
        print()
        
        # Query 3: Check post_images references
        print("3. POST_IMAGES REFERENCES")
        print("-" * 80)
        query = """
        SELECT 
            'post_images pointing to image' as source,
            COUNT(*) as count
        FROM post_images pi
        JOIN image i ON pi.image_id = i.id
        UNION ALL
        SELECT 
            'post_images pointing to images' as source,
            COUNT(*) as count
        FROM post_images pi
        JOIN images i ON pi.image_id = i.id;
        """
        results = db_manager.execute_query(query)
        for row in results:
            print(f"   {row['source']}: {row['count']} references")
        print()
        
        # Query 4: Check post.header_image_id references
        print("4. POST.HEADER_IMAGE_ID REFERENCES")
        print("-" * 80)
        query = """
        SELECT 
            'post.header_image_id pointing to image' as source,
            COUNT(*) as count
        FROM post p
        JOIN image i ON p.header_image_id = i.id
        UNION ALL
        SELECT 
            'post.header_image_id pointing to images' as source,
            COUNT(*) as count
        FROM post p
        JOIN images i ON p.header_image_id = i.id;
        """
        results = db_manager.execute_query(query)
        for row in results:
            print(f"   {row['source']}: {row['count']} references")
        print()
        
        # Query 5: Check for orphaned references
        print("5. ORPHANED REFERENCES CHECK")
        print("-" * 80)
        query = """
        SELECT 
            'post_images.image_id not in image or images' as issue,
            COUNT(*) as count
        FROM post_images pi
        LEFT JOIN image i1 ON pi.image_id = i1.id
        LEFT JOIN images i2 ON pi.image_id = i2.id
        WHERE i1.id IS NULL AND i2.id IS NULL
        UNION ALL
        SELECT 
            'post.header_image_id not in image or images' as issue,
            COUNT(*) as count
        FROM post p
        LEFT JOIN image i1 ON p.header_image_id = i1.id
        LEFT JOIN images i2 ON p.header_image_id = i2.id
        WHERE p.header_image_id IS NOT NULL 
          AND i1.id IS NULL AND i2.id IS NULL;
        """
        results = db_manager.execute_query(query)
        orphaned_found = False
        for row in results:
            if row['count'] > 0:
                print(f"   ⚠️  {row['issue']}: {row['count']} orphaned references")
                orphaned_found = True
        if not orphaned_found:
            print("   ✅ No orphaned references found")
        print()
        
        # Summary
        print("=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        if conflict_count > 0:
            print("⚠️  ACTION REQUIRED: ID conflicts detected. Resolve before migration.")
        else:
            print("✅ Ready for migration (no ID conflicts)")
        print()
        
    except Exception as e:
        logger.error(f"Audit failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_audit()




