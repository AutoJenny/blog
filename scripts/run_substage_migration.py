#!/usr/bin/env python3
"""
Run substage configuration migration
1. Creates database tables
2. Migrates data from config files
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_sql_migration():
    """Run the SQL schema migration"""
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'migrations',
        '20251216_create_substage_config_tables.sql'
    )
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        with db_manager.get_cursor() as cursor:
            # Execute the migration
            cursor.execute(sql)
            print("✅ SQL migration completed successfully")
            return True
    except Exception as e:
        print(f"❌ SQL migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_data_migration():
    """Run the data migration"""
    try:
        from migrations.run_migration_substage_config import main as migrate_data
        return migrate_data() == 0
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Substage Configuration Migration")
    print("=" * 60)
    
    # Step 1: Create tables
    if not run_sql_migration():
        sys.exit(1)
    
    # Step 2: Migrate data
    if not run_data_migration():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All migrations completed successfully!")
    print("=" * 60)
    sys.exit(0)

