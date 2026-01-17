#!/usr/bin/env python3
"""Run migration to add weekly content metadata columns to posting_queue"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def run_migration():
    """Execute the weekly content metadata migration for posting_queue"""
    print("Running migration: Add weekly content metadata columns to posting_queue...")
    print("\nThis migration adds:")
    print("  - generated_caption (TEXT) - AI-generated caption text")
    print("  - pinned_comment (TEXT) - Optional pinned comment")
    print("  - chosen_prompt_style_id (INTEGER) - Prompt variation ID used")
    print("  - image_path (TEXT) - Path to generated square image")
    print("  - ollama_model (VARCHAR(100)) - Ollama model used")
    print("  - generation_timestamp (TIMESTAMPTZ) - When caption/image were generated")
    print("  - 2 indexes for efficient querying")
    print()
    
    # Read migration SQL
    migration_path = os.path.join(os.path.dirname(__file__), '20260117_add_weekly_content_metadata_to_posting_queue.sql')
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute migration
                print("Executing migration SQL...")
                cursor.execute(migration_sql)
                conn.commit()
                print("✅ Migration executed successfully")
                
                # Verify columns exist
                expected_columns = [
                    'generated_caption',
                    'pinned_comment',
                    'chosen_prompt_style_id',
                    'image_path',
                    'ollama_model',
                    'generation_timestamp'
                ]
                
                print("\nVerifying columns...")
                all_exist = True
                for col_name in expected_columns:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'posting_queue'
                            AND column_name = %s
                        )
                    """, (col_name,))
                    exists = cursor.fetchone()['exists']
                    if exists:
                        print(f"  ✅ {col_name}")
                    else:
                        print(f"  ❌ {col_name} - NOT FOUND")
                        all_exist = False
                
                if not all_exist:
                    print("\n❌ Error: Some columns not found after migration")
                    return False
                
                # Check indexes
                print("\nVerifying indexes...")
                expected_indexes = [
                    'idx_posting_queue_generation_timestamp',
                    'idx_posting_queue_prompt_style_id'
                ]
                
                for index_name in expected_indexes:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_indexes 
                            WHERE schemaname = 'public'
                            AND tablename = 'posting_queue'
                            AND indexname = %s
                        )
                    """, (index_name,))
                    exists = cursor.fetchone()['exists']
                    if exists:
                        print(f"  ✅ {index_name}")
                    else:
                        print(f"  ⚠️  {index_name} - not found (may already exist or creation failed)")
                
                print("\n✅ Migration complete! All columns added successfully.")
                return True
                    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
