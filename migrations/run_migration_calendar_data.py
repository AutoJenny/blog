#!/usr/bin/env python3
"""Run migration to populate calendar_week_items with existing data"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_migration():
    """Execute the calendar data migration"""
    print("Running calendar data migration (Phase 3: Data Migration)...")
    print("This will migrate existing data to calendar_week_items table.\n")
    
    # Read migration SQL
    migration_path = os.path.join(os.path.dirname(__file__), 'migrate_calendar_data_to_week_items.sql')
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check which tables exist
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('calendar_week_selection', 'calendar_week_posts', 'calendar_ideas', 'calendar_events')
                """)
                existing_tables = {row['table_name'] for row in cursor.fetchall()}
                
                # Get counts before migration
                print("Getting pre-migration counts...")
                
                # Count themes
                themes_before = 0
                if 'calendar_week_selection' in existing_tables:
                    cursor.execute("SELECT COUNT(*) as count FROM calendar_week_selection")
                    themes_before = cursor.fetchone()['count']
                else:
                    print("  Note: calendar_week_selection table does not exist, skipping theme migration")
                
                # Count recipes
                recipes_before = 0
                if 'calendar_week_posts' in existing_tables:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM calendar_week_posts cwp
                        JOIN post p ON cwp.post_id = p.id
                        WHERE p.post_type = 'recipe'
                    """)
                    recipes_before = cursor.fetchone()['count']
                else:
                    print("  Note: calendar_week_posts table does not exist, skipping recipe migration")
                
                # Count profiles
                profiles_before = 0
                if 'calendar_week_posts' in existing_tables:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM calendar_week_posts cwp
                        JOIN post p ON cwp.post_id = p.id
                        WHERE p.profile_type IS NOT NULL
                    """)
                    profiles_before = cursor.fetchone()['count']
                
                # Count ideas
                ideas_before = 0
                if 'calendar_ideas' in existing_tables:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM calendar_ideas
                        WHERE item_classification IN ('idea', 'weekly_word', 'weekly_phrase')
                    """)
                    ideas_before = cursor.fetchone()['count']
                else:
                    print("  Note: calendar_ideas table does not exist, skipping idea migration")
                
                # Count events
                events_before = 0
                if 'calendar_events' in existing_tables:
                    cursor.execute("SELECT COUNT(*) as count FROM calendar_events WHERE year IS NOT NULL")
                    events_before = cursor.fetchone()['count']
                else:
                    print("  Note: calendar_events table does not exist, skipping event migration")
                
                print(f"  Themes: {themes_before}")
                print(f"  Recipes: {recipes_before}")
                print(f"  Profiles: {profiles_before}")
                print(f"  Ideas: {ideas_before}")
                print(f"  Events: {events_before}\n")
                
                # Execute migration
                print("Executing migration...")
                cursor.execute(migration_sql)
                conn.commit()
                print("✅ Migration SQL executed\n")
                
                # Get counts after migration
                print("Getting post-migration counts...")
                
                cursor.execute("SELECT COUNT(*) as count FROM calendar_week_items WHERE item_type = 'theme'")
                themes_after = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM calendar_week_items WHERE item_type = 'recipe'")
                recipes_after = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM calendar_week_items WHERE item_type = 'profile'")
                profiles_after = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM calendar_week_items WHERE item_type IN ('idea', 'weekly_word', 'weekly_phrase')")
                ideas_after = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM calendar_week_items WHERE item_type IN ('annual_event', 'special_event')")
                events_after = cursor.fetchone()['count']
                
                print(f"  Themes: {themes_after} (expected: {themes_before})")
                print(f"  Recipes: {recipes_after} (expected: {recipes_before})")
                print(f"  Profiles: {profiles_after} (expected: {profiles_before})")
                print(f"  Ideas: {ideas_after} (expected: {ideas_before})")
                print(f"  Events: {events_after} (expected: {events_before})\n")
                
                # Verify migration
                all_good = True
                if themes_after != themes_before:
                    print(f"⚠️  Warning: Theme count mismatch ({themes_after} vs {themes_before})")
                    all_good = False
                if recipes_after != recipes_before:
                    print(f"⚠️  Warning: Recipe count mismatch ({recipes_after} vs {recipes_before})")
                    all_good = False
                if profiles_after != profiles_before:
                    print(f"⚠️  Warning: Profile count mismatch ({profiles_after} vs {profiles_before})")
                    all_good = False
                if ideas_after != ideas_before:
                    print(f"⚠️  Warning: Idea count mismatch ({ideas_after} vs {ideas_before})")
                    all_good = False
                if events_after != events_before:
                    print(f"⚠️  Warning: Event count mismatch ({events_after} vs {events_before})")
                    all_good = False
                
                if all_good:
                    print("✅ All data migrated successfully!")
                    print("\nNext step: Update API endpoints to read from calendar_week_items (Phase 4)")
                else:
                    print("⚠️  Some data may not have migrated. Please review the warnings above.")
                
                # Show sample data
                print("\nSample migrated data:")
                cursor.execute("""
                    SELECT item_type, COUNT(*) as count
                    FROM calendar_week_items
                    GROUP BY item_type
                    ORDER BY item_type
                """)
                for row in cursor.fetchall():
                    print(f"  {row['item_type']}: {row['count']} items")
                
                return all_good
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

