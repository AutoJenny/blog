#!/usr/bin/env python3
"""
Fix the 4 broken steps by adding proper field mappings
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

def fix_broken_steps():
    """Add field mappings to the 4 broken steps"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Define the broken steps and their field mappings
    broken_steps = [
        (50, "Titles", "provisional_title"),
        (53, "Image concepts", "image_montage_concept"),
        (54, "Image prompts", "image_montage_prompt"),
        (59, "Header montage description", "image_montage_concept")
    ]
    
    try:
        print("🔧 Phase 1: Fixing 4 broken steps...")
        print("=" * 60)
        
        for step_id, step_name, field_name in broken_steps:
            print(f"Processing Step {step_id} ({step_name})...")
            
            # Check if step exists
            cursor.execute("SELECT id, name, config FROM workflow_step_entity WHERE id = %s", (step_id,))
            step = cursor.fetchone()
            
            if not step:
                print(f"❌ Step {step_id} not found!")
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
            
            print(f"✓ Fixed Step {step_id} ({step_name}): {field_name}")
        
        conn.commit()
        print("=" * 60)
        print(f"✅ Successfully fixed {len(broken_steps)} steps")
        
        # Verify the fixes
        print("\n🔍 Verifying fixes...")
        for step_id, step_name, field_name in broken_steps:
            cursor.execute("""
                SELECT config->'outputs'->'output1'->>'db_field' as output_field
                FROM workflow_step_entity 
                WHERE id = %s
            """, (step_id,))
            result = cursor.fetchone()
            
            if result and result['output_field'] == field_name:
                print(f"✓ Verified Step {step_id}: {field_name}")
            else:
                print(f"❌ Verification failed for Step {step_id}")
        
    except Exception as e:
        print(f"❌ Error during fix: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_broken_steps()
