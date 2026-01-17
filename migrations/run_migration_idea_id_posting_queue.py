#!/usr/bin/env python3
"""Run migration to add idea_id column to posting_queue"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_migration():
    """Execute the idea_id migration for posting_queue"""
    print("Running migration: Add idea_id to posting_queue...")
    
    # Read migration SQL
    migration_path = os.path.join(os.path.dirname(__file__), '20251218_add_idea_id_to_posting_queue.sql')
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute migration
                print("Adding idea_id column and index...")
                cursor.execute(migration_sql)
                conn.commit()
                print("✅ Migration executed successfully")
                
                # Verify column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'posting_queue'
                        AND column_name = 'idea_id'
                    )
                """)
                column_exists = cursor.fetchone()['exists']
                
                if column_exists:
                    print("✅ Verified: idea_id column exists")
                    
                    # Check index
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_indexes 
                            WHERE schemaname = 'public'
                            AND tablename = 'posting_queue'
                            AND indexname = 'idx_posting_queue_idea_id'
                        )
                    """)
                    index_exists = cursor.fetchone()['exists']
                    
                    if index_exists:
                        print("✅ Verified: idx_posting_queue_idea_id index exists")
                    else:
                        print("⚠️  Warning: Index not found (may already exist or creation failed)")
                    
                    print("\n✅ Migration complete!")
                    return True
                else:
                    print("❌ Error: Column not found after migration")
                    return False
                    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

