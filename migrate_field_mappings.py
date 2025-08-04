#!/usr/bin/env python3
"""
Migration script to convert legacy field_name mappings to modern config.outputs
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from dotenv import dotenv_values

def get_db_conn():
    """Get database connection"""
    config_path = 'blog-core/assistant_config.env'
    config = dotenv_values(config_path)
    database_url = config.get('DATABASE_URL')
    
    import re
    match = re.match(r'postgres(?:ql)?://([^:]+)(?::([^@]+))?@([^:/]+)(?::(\d+))?/([^\s]+)', database_url)
    user = match.group(1)
    password = match.group(2)
    host = match.group(3)
    port = match.group(4) or '5432'
    dbname = match.group(5)
    
    return psycopg2.connect(
        dbname=dbname, user=user, password=password, 
        host=host, port=port, cursor_factory=RealDictCursor
    )

def migrate_legacy_field_mappings():
    """Migrate legacy field_name to modern config.outputs"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔄 Phase 2: Migrating legacy field mappings...")
        print("=" * 60)
        
        # Get all steps with legacy field_name
        cursor.execute("""
            SELECT id, name, field_name 
            FROM workflow_step_entity 
            WHERE field_name IS NOT NULL
        """)
        
        legacy_steps = cursor.fetchall()
        print(f"Found {len(legacy_steps)} steps with legacy field_name")
        print("=" * 60)
        
        migrated_count = 0
        for step in legacy_steps:
            step_id = step['id']
            step_name = step['name']
            field_name = step['field_name']
            
            print(f"Processing Step {step_id} ({step_name}): {field_name}")
            
            # Check if step already has modern config
            cursor.execute("""
                SELECT config->'outputs'->'output1'->>'db_field' as existing_field
                FROM workflow_step_entity 
                WHERE id = %s
            """, (step_id,))
            existing = cursor.fetchone()
            
            if existing and existing['existing_field']:
                print(f"  ⚠️  Step {step_id} already has modern config: {existing['existing_field']}")
                continue
            
            # Create modern config structure
            new_config = {
                "outputs": {
                    "output1": {
                        "label": step_name,
                        "db_field": field_name,
                        "type": "textarea"
                    }
                }
            }
            
            # Update the step
            cursor.execute("""
                UPDATE workflow_step_entity 
                SET config = jsonb_set(
                    COALESCE(config, '{}'::jsonb),
                    '{outputs}',
                    %s::jsonb
                )
                WHERE id = %s
            """, (json.dumps(new_config["outputs"]), step_id))
            
            print(f"  ✓ Migrated Step {step_id}: {field_name}")
            migrated_count += 1
        
        conn.commit()
        print("=" * 60)
        print(f"✅ Successfully migrated {migrated_count} steps")
        
        # Verify the migration
        print("\n🔍 Verifying migration...")
        cursor.execute("""
            SELECT COUNT(*) as total_legacy
            FROM workflow_step_entity 
            WHERE field_name IS NOT NULL
        """)
        total_legacy = cursor.fetchone()['total_legacy']
        
        cursor.execute("""
            SELECT COUNT(*) as total_modern
            FROM workflow_step_entity 
            WHERE config->'outputs'->'output1'->>'db_field' IS NOT NULL
        """)
        total_modern = cursor.fetchone()['total_modern']
        
        print(f"Steps with legacy field_name: {total_legacy}")
        print(f"Steps with modern config.outputs: {total_modern}")
        
        if total_legacy == 0:
            print("✅ All legacy field_name mappings have been migrated!")
        else:
            print(f"⚠️  {total_legacy} steps still have legacy field_name")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_legacy_field_mappings()
