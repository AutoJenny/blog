#!/usr/bin/env python3
"""
Run migration to add content_format to post_type_channel_config
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_migration():
    """Run the migration SQL"""
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'migrations',
        '20251210_add_content_format_to_channel_config.sql'
    )
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        with db_manager.get_cursor() as cursor:
            # Execute the migration
            cursor.execute(sql)
            print("✅ Migration completed successfully")
            return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

