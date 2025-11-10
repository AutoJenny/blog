#!/usr/bin/env python3
"""
Check what styles are actually being returned for a post.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.taxonomy_helpers import get_default_image_style
import json

def check_post_styles(post_id):
    """Check what styles are stored and what should be returned"""
    try:
        with db_manager.get_cursor() as cursor:
            # Check extra_settings
            cursor.execute("""
                SELECT extra_settings
                FROM post
                WHERE id = %s
            """, (post_id,))
            result = cursor.fetchone()
            
            extra_settings = result['extra_settings'] if result and result.get('extra_settings') else {}
            if isinstance(extra_settings, str):
                extra_settings = json.loads(extra_settings)
            
            imaging = extra_settings.get('imaging', {})
            saved_styles = imaging.get('styles', [])
            active_index = imaging.get('activeIndex', 0)
            
            print(f"📋 Post {post_id} styles check:")
            print(f"   Saved styles in extra_settings: {len(saved_styles)}")
            if saved_styles:
                for i, style in enumerate(saved_styles):
                    print(f"      [{i}] {style.get('name', 'Unknown')}")
            else:
                print("      (none - will use taxonomy default)")
            
            # Check taxonomy default
            taxonomy_style = get_default_image_style(post_id)
            if taxonomy_style:
                print(f"   ✅ Taxonomy default: {taxonomy_style.get('name', 'Unknown')}")
            else:
                print(f"   ⚠️  No taxonomy default found")
            
            # What will actually be returned?
            if saved_styles:
                print(f"\n   ⚠️  ISSUE: Post has saved styles, so taxonomy default will NOT be used!")
                print(f"   Solution: Clear the styles array in extra_settings to use taxonomy default")
            else:
                print(f"\n   ✅ Will use taxonomy default: {taxonomy_style.get('name') if taxonomy_style else 'Watercolour (fallback)'}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_post_styles(81)

