#!/usr/bin/env python3
"""
Clean up recipe entries that were mistakenly inserted into calendar_ideas table.
Remove them since recipes now have their own calendar_recipes table.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import db_manager

def cleanup_recipe_ideas():
    """Remove recipe entries from calendar_ideas table."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Find recipe entries (those with content_type='recipe' or tags containing 'Scottish Recipes')
                cursor.execute("""
                    SELECT id, week_number, idea_title 
                    FROM calendar_ideas 
                    WHERE content_type = 'recipe' 
                       OR tags::text LIKE '%Scottish Recipes%'
                       OR idea_title LIKE '%Cullen Skink%'
                       OR idea_title LIKE '%Haggis%'
                """)
                
                recipes_in_ideas = cursor.fetchall()
                
                if not recipes_in_ideas:
                    print("✅ No recipe entries found in calendar_ideas table")
                    return True
                
                print(f"Found {len(recipes_in_ideas)} recipe entries in calendar_ideas:")
                for row in recipes_in_ideas:
                    if isinstance(row, dict):
                        print(f"   - Week {row['week_number']}: {row['idea_title']}")
                    else:
                        print(f"   - Week {row[1]}: {row[2]}")
                
                # Delete them
                cursor.execute("""
                    DELETE FROM calendar_ideas 
                    WHERE content_type = 'recipe' 
                       OR tags::text LIKE '%Scottish Recipes%'
                """)
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"\n✅ Deleted {deleted_count} recipe entries from calendar_ideas")
                print("   Recipes are now exclusively in calendar_recipes table")
                return True
                
    except Exception as e:
        print(f"❌ Error cleaning up recipe ideas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🧹 Cleaning up recipe entries from calendar_ideas table...\n")
    
    success = cleanup_recipe_ideas()
    
    if success:
        print("\n✅ Cleanup complete!")
        sys.exit(0)
    else:
        print("\n❌ Cleanup failed!")
        sys.exit(1)

