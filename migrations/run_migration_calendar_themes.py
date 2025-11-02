#!/usr/bin/env python3
"""Run migration to create calendar_themes table and migrate data"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_migration():
    """Execute the calendar_themes migration"""
    print("Running calendar_themes migration...")
    
    with open(os.path.join(os.path.dirname(__file__), 'create_calendar_themes_table.sql'), 'r') as f:
        sql = f.read()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute migration
                cursor.execute(sql)
                conn.commit()
                
                # Verify migration
                cursor.execute("SELECT COUNT(*) FROM calendar_themes")
                theme_count = cursor.fetchone()['count']
                print(f"✅ Migration complete: {theme_count} themes migrated")
                
                cursor.execute("SELECT COUNT(*) FROM calendar_schedule WHERE theme_id IS NOT NULL")
                schedule_count = cursor.fetchone()['count']
                print(f"✅ Schedule entries updated: {schedule_count} entries now reference calendar_themes")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

