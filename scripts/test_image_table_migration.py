#!/usr/bin/env python3
"""
Test script to verify image table migration works correctly.
Tests key functionality after migration to images table.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_header_image_finder():
    """Test that header_image_finder can load images from images table."""
    print("=" * 80)
    print("TEST 1: Header Image Finder")
    print("=" * 80)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blog-launchpad'))
        from publish.header_image_finder import get_header_image
        
        # Find a post with a header image
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title
                FROM post p
                JOIN post_images pi ON pi.post_id = p.id
                JOIN images i ON pi.image_id = i.id
                WHERE pi.image_type LIKE 'header%%'
                LIMIT 1
            """)
            post = cursor.fetchone()
            
            if not post:
                print("⚠️  No posts with header images found for testing")
                return False
            
            print(f"Testing with post {post['id']}: {post['title']}")
            header_image = get_header_image(post['id'])
            
            if header_image:
                print(f"✅ Header image found: {header_image.get('path')}")
                print(f"   Alt text: {header_image.get('alt_text')}")
                print(f"   Caption: {header_image.get('caption')}")
                return True
            else:
                print("❌ No header image found")
                return False
                
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False

def test_database_queries():
    """Test that database queries work with images table."""
    print("\n" + "=" * 80)
    print("TEST 2: Database Queries")
    print("=" * 80)
    
    try:
        with db_manager.get_cursor() as cursor:
            # Test 1: Query header images via post_images
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM post_images pi
                JOIN images i ON pi.image_id = i.id
                WHERE pi.image_type LIKE 'header%%'
            """)
            result = cursor.fetchone()
            header_count = result['count']
            print(f"✅ Header images via post_images: {header_count} records")
            
            # Test 2: Query section images
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM post_images pi
                JOIN images i ON pi.image_id = i.id
                WHERE pi.image_type = 'section_optimized'
            """)
            result = cursor.fetchone()
            section_count = result['count']
            print(f"✅ Section images via post_images: {section_count} records")
            
            # Test 3: Verify file_path column exists and has data
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM images
                WHERE file_path IS NOT NULL
            """)
            result = cursor.fetchone()
            path_count = result['count']
            print(f"✅ Images with file_path: {path_count} records")
            
            # Test 4: Verify width/height columns exist
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM images
                WHERE width IS NOT NULL OR height IS NOT NULL
            """)
            result = cursor.fetchone()
            dim_count = result['count']
            print(f"✅ Images with dimensions: {dim_count} records")
            
            return True
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False

def test_foreign_keys():
    """Test that foreign key references are valid."""
    print("\n" + "=" * 80)
    print("TEST 3: Foreign Key References")
    print("=" * 80)
    
    try:
        with db_manager.get_cursor() as cursor:
            # Test 1: Check for orphaned post_images.image_id
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM post_images pi
                LEFT JOIN images i ON pi.image_id = i.id
                WHERE i.id IS NULL
            """)
            result = cursor.fetchone()
            orphaned_pi = result['count']
            
            if orphaned_pi == 0:
                print(f"✅ No orphaned post_images.image_id references: {orphaned_pi}")
            else:
                print(f"⚠️  Orphaned post_images.image_id references: {orphaned_pi}")
            
            # Test 2: Check for orphaned post.header_image_id
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM post p
                LEFT JOIN images i ON p.header_image_id = i.id
                WHERE p.header_image_id IS NOT NULL AND i.id IS NULL
            """)
            result = cursor.fetchone()
            orphaned_post = result['count']
            
            if orphaned_post == 0:
                print(f"✅ No orphaned post.header_image_id references: {orphaned_post}")
            else:
                print(f"⚠️  Orphaned post.header_image_id references: {orphaned_post}")
            
            return orphaned_pi == 0 and orphaned_post == 0
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("IMAGE TABLE MIGRATION TESTS")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Header image finder
    results.append(("Header Image Finder", test_header_image_finder()))
    
    # Test 2: Database queries
    results.append(("Database Queries", test_database_queries()))
    
    # Test 3: Foreign keys
    results.append(("Foreign Key References", test_foreign_keys()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All tests passed! Migration is working correctly.")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

