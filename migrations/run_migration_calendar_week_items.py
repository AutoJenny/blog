#!/usr/bin/env python3
"""Run migration to create calendar_week_items table and compatibility views"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_migration():
    """Execute the calendar_week_items migration"""
    print("Running calendar_week_items migration (Phase 1: Foundation)...")
    
    # Read table creation migration
    table_migration_path = os.path.join(os.path.dirname(__file__), 'create_calendar_week_items_table.sql')
    with open(table_migration_path, 'r') as f:
        table_sql = f.read()
    
    # Read views creation migration
    views_migration_path = os.path.join(os.path.dirname(__file__), 'create_calendar_week_items_views.sql')
    with open(views_migration_path, 'r') as f:
        views_sql = f.read()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute table creation
                print("Creating calendar_week_items table...")
                cursor.execute(table_sql)
                conn.commit()
                print("✅ Table created successfully")
                
                # Execute views creation
                print("Creating compatibility views...")
                cursor.execute(views_sql)
                conn.commit()
                print("✅ Views created successfully")
                
                # Verify table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'calendar_week_items'
                    )
                """)
                table_exists = cursor.fetchone()['exists']
                
                if table_exists:
                    # Check indexes
                    cursor.execute("""
                        SELECT COUNT(*) as index_count
                        FROM pg_indexes 
                        WHERE tablename = 'calendar_week_items'
                    """)
                    index_count = cursor.fetchone()['index_count']
                    print(f"✅ Table verified: {index_count} indexes created")
                    
                    # Check views
                    cursor.execute("""
                        SELECT COUNT(*) as view_count
                        FROM information_schema.views 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('calendar_week_selection_v2', 'calendar_week_posts_v2', 'calendar_week_items_summary')
                    """)
                    view_count = cursor.fetchone()['view_count']
                    print(f"✅ Views verified: {view_count} views created")
                    
                    print("\n✅ Migration complete! calendar_week_items table is ready for use.")
                    print("   Next step: Implement dual-write pattern (Phase 2)")
                    return True
                else:
                    print("❌ Table verification failed")
                    return False
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

