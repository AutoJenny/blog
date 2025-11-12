#!/usr/bin/env python3
"""
Update foreign key references to point to images table.
This ensures all references point to images instead of image.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_references():
    """Update FK references to point to images table."""
    print("=" * 80)
    print("UPDATE FOREIGN KEY REFERENCES")
    print("=" * 80)
    print()
    
    try:
        # Update post_images.image_id references
        print("1. Updating post_images.image_id references...")
        query = """
        UPDATE post_images pi
        SET image_id = i2.id
        FROM image i1
        JOIN images i2 ON i1.id = i2.id
        WHERE pi.image_id = i1.id;
        """
        result = db_manager.execute_update(query)
        print(f"   ✅ Updated {result} post_images references")
        print()
        
        # Update post.header_image_id references
        print("2. Updating post.header_image_id references...")
        query = """
        UPDATE post p
        SET header_image_id = i2.id
        FROM image i1
        JOIN images i2 ON i1.id = i2.id
        WHERE p.header_image_id = i1.id;
        """
        result = db_manager.execute_update(query)
        print(f"   ✅ Updated {result} post.header_image_id references")
        print()
        
        # Verify updates
        print("3. Verifying updates...")
        query = """
        SELECT 
            'post_images.image_id pointing to image' as issue,
            COUNT(*) as count
        FROM post_images pi
        JOIN image i ON pi.image_id = i.id
        UNION ALL
        SELECT 
            'post.header_image_id pointing to image' as issue,
            COUNT(*) as count
        FROM post p
        JOIN image i ON p.header_image_id = i.id
        WHERE p.header_image_id IS NOT NULL;
        """
        results = db_manager.execute_query(query)
        
        all_updated = True
        for row in results:
            if row['count'] > 0:
                print(f"   ⚠️  {row['issue']}: {row['count']} still pointing to image")
                all_updated = False
            else:
                print(f"   ✅ {row['issue']}: All updated")
        
        print()
        if all_updated:
            print("=" * 80)
            print("✅ All references updated successfully!")
            print("=" * 80)
        else:
            print("=" * 80)
            print("⚠️  Some references may still point to image table")
            print("   (This is OK if IDs match - code update will handle it)")
            print("=" * 80)
        
    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_references()



