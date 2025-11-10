#!/usr/bin/env python3
"""
Diagnostic script to check image style setup for a post.
Checks if migrations have run and if taxonomy is configured correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import json

def check_column_exists():
    """Check if default_image_style column exists"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'taxonomy_item' 
                AND column_name = 'default_image_style'
            """)
            result = cursor.fetchone()
            if result:
                print(f"✅ Column exists: {result['column_name']} ({result['data_type']})")
                return True
            else:
                print("❌ Column 'default_image_style' does not exist in taxonomy_item table")
                print("   Run: psql -d blog_db -f migrations/add_default_image_style_to_taxonomy.sql")
                return False
    except Exception as e:
        print(f"❌ Error checking column: {e}")
        return False

def check_post_taxonomy(post_id):
    """Check post's taxonomy configuration"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.content_type_id,
                       ti.id as taxonomy_id, ti.display_name, ti.slug,
                       ti.default_image_style
                FROM post p
                LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                WHERE p.id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ Post {post_id} not found")
                return False
            
            print(f"\n📋 Post {post_id}: {result['title']}")
            print(f"   content_type_id: {result['content_type_id']}")
            
            if not result['content_type_id']:
                print("   ⚠️  Post has no content_type_id set!")
                return False
            
            if not result['taxonomy_id']:
                print(f"   ⚠️  Taxonomy item {result['content_type_id']} not found!")
                return False
            
            print(f"   Taxonomy: {result['display_name']} (slug: {result['slug']})")
            
            if result['default_image_style']:
                style = result['default_image_style']
                if isinstance(style, str):
                    style = json.loads(style)
                print(f"   ✅ Default image style: {style.get('name', 'Unknown')}")
                return True
            else:
                print(f"   ⚠️  No default_image_style set for this taxonomy item")
                print(f"   Run: psql -d blog_db -f migrations/populate_landscape_image_style.sql")
                return False
                
    except Exception as e:
        print(f"❌ Error checking post: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    post_id = 81
    
    print("🔍 Checking image style setup for post 81...\n")
    
    # Check if column exists
    if not check_column_exists():
        print("\n❌ Migration not run. Please run the migration first.")
        return
    
    # Check post configuration
    if not check_post_taxonomy(post_id):
        print("\n❌ Post taxonomy not configured correctly.")
        return
    
    print("\n✅ Setup looks correct!")

if __name__ == '__main__':
    main()

