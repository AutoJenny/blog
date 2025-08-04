#!/usr/bin/env python3
"""
Fix remaining issues found in validation
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

def fix_remaining_issues():
    """Fix the remaining issues found in validation"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔧 Fixing Remaining Issues...")
        print("=" * 60)
        
        # Fix 1: Remove orphaned step (Step 52)
        print("\n1️⃣ Removing orphaned step...")
        cursor.execute("DELETE FROM workflow_step_entity WHERE id = 52")
        print("✅ Removed orphaned Step 52 (Unassigned)")
        
        # Fix 2: Add field mappings to missing steps
        print("\n2️⃣ Adding field mappings to missing steps...")
        
        # Define field mappings for missing steps based on their names
        missing_steps = [
            (49, "FIX language", "draft"),  # Language fix likely goes to draft
            (42, "Test New Step", "draft"),  # Test step goes to draft
            (51, "Summary", "summary"),  # Summary goes to summary field
            (56, "Watermark & optimise", "generated_image_url"),  # Image optimization
            (57, "Header montage", "image_montage_concept")  # Header montage
        ]
        
        for step_id, step_name, field_name in missing_steps:
            print(f"Processing Step {step_id} ({step_name})...")
            
            # Check if step exists
            cursor.execute("SELECT id, name FROM workflow_step_entity WHERE id = %s", (step_id,))
            step = cursor.fetchone()
            
            if not step:
                print(f"  ⚠️  Step {step_id} not found!")
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
            
            print(f"  ✓ Fixed Step {step_id}: {field_name}")
        
        conn.commit()
        print("=" * 60)
        print("✅ Successfully fixed remaining issues")
        
        # Verify the fixes
        print("\n🔍 Verifying fixes...")
        
        # Check for orphaned steps
        cursor.execute("""
            SELECT COUNT(*) as orphaned_steps
            FROM workflow_step_entity wse
            LEFT JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
            WHERE wsse.id IS NULL
        """)
        orphaned_steps = cursor.fetchone()['orphaned_steps']
        
        if orphaned_steps == 0:
            print("✅ No orphaned workflow steps found")
        else:
            print(f"❌ Found {orphaned_steps} orphaned workflow steps")
        
        # Check for missing field mappings
        cursor.execute("""
            SELECT COUNT(*) as missing_mappings
            FROM workflow_step_entity
            WHERE config->'outputs'->'output1'->>'db_field' IS NULL
        """)
        missing_mappings = cursor.fetchone()['missing_mappings']
        
        if missing_mappings == 0:
            print("✅ All steps have field mappings")
        else:
            print(f"❌ {missing_mappings} steps still missing field mappings")
        
    except Exception as e:
        print(f"❌ Error during fix: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_remaining_issues()
