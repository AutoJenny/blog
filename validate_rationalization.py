#!/usr/bin/env python3
"""
Final validation script for Field Mapping System Rationalization
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

def validate_rationalization():
    """Final validation of the rationalized field mapping system"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🎯 FINAL VALIDATION: Field Mapping System Rationalization")
        print("=" * 80)
        
        # Test 1: Legacy columns removed
        print("\n1️⃣ Testing Legacy Column Removal...")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'workflow_step_entity' AND column_name IN ('field_name', 'order_index')")
        legacy_columns = cursor.fetchall()
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'llm_action' AND column_name IN ('input_field', 'output_field')")
        legacy_llm_columns = cursor.fetchall()
        
        if len(legacy_columns) == 0 and len(legacy_llm_columns) == 0:
            print("✅ Legacy columns successfully removed")
        else:
            print(f"❌ Legacy columns still exist")
        
        # Test 2: All steps have modern field mappings
        print("\n2️⃣ Testing Modern Field Mappings...")
        cursor.execute("SELECT COUNT(*) as total FROM workflow_step_entity")
        total_steps = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as mapped FROM workflow_step_entity WHERE config->'outputs'->'output1'->>'db_field' IS NOT NULL")
        mapped_steps = cursor.fetchone()['mapped']
        
        print(f"Total workflow steps: {total_steps}")
        print(f"Steps with modern field mappings: {mapped_steps}")
        
        if mapped_steps == total_steps:
            print("✅ All steps have modern field mappings")
        else:
            print(f"❌ {total_steps - mapped_steps} steps missing field mappings")
        
        # Test 3: Previously broken steps are fixed
        print("\n3️⃣ Testing Previously Broken Steps...")
        broken_steps = [(50, "Titles", "provisional_title"), (53, "Image concepts", "image_montage_concept"), (54, "Image prompts", "image_montage_prompt"), (59, "Header montage description", "image_montage_concept")]
        all_fixed = True
        
        for step_id, step_name, expected_field in broken_steps:
            cursor.execute("SELECT config->'outputs'->'output1'->>'db_field' as output_field FROM workflow_step_entity WHERE id = %s", (step_id,))
            result = cursor.fetchone()
            
            if result and result['output_field'] == expected_field:
                print(f"✅ Step {step_id} ({step_name}): {expected_field}")
            else:
                print(f"❌ Step {step_id} ({step_name}): Expected {expected_field}, got {result['output_field'] if result else 'None'}")
                all_fixed = False
        
        if all_fixed:
            print("✅ All previously broken steps are now fixed")
        
        # Test 4: Database structure integrity
        print("\n4️⃣ Testing Database Structure Integrity...")
        cursor.execute("SELECT table_name, COUNT(*) as column_count FROM information_schema.columns WHERE table_name IN ('workflow_step_entity', 'llm_action') GROUP BY table_name")
        table_structure = cursor.fetchall()
        
        for table in table_structure:
            print(f"✅ {table['table_name']}: {table['column_count']} columns")
        
        # Test 5: No orphaned references
        print("\n5️⃣ Testing for Orphaned References...")
        cursor.execute("SELECT COUNT(*) as orphaned FROM workflow_step_entity wse LEFT JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id WHERE wsse.id IS NULL")
        orphaned_steps = cursor.fetchone()['orphaned']
        
        if orphaned_steps == 0:
            print("✅ No orphaned workflow steps found")
        else:
            print(f"❌ Found {orphaned_steps} orphaned workflow steps")
        
        # Test 6: No empty field names
        print("\n6️⃣ Testing for Empty Field Names...")
        cursor.execute("SELECT COUNT(*) as empty FROM workflow_step_entity WHERE config->'outputs'->'output1'->>'db_field' = ''")
        empty_field_names = cursor.fetchone()['empty']
        
        if empty_field_names == 0:
            print("✅ No empty field names found")
        else:
            print(f"❌ Found {empty_field_names} steps with empty field names")
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 80)
        
        # Count successes
        success_count = 0
        total_tests = 6
        
        if len(legacy_columns) == 0 and len(legacy_llm_columns) == 0:
            success_count += 1
        if mapped_steps == total_steps:
            success_count += 1
        if all_fixed:
            success_count += 1
        if len(table_structure) == 2:
            success_count += 1
        if orphaned_steps == 0:
            success_count += 1
        if empty_field_names == 0:
            success_count += 1
        
        print(f"Tests passed: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("🎉 ALL VALIDATION TESTS PASSED!")
            print("✅ Field Mapping System Rationalization is complete and successful!")
        else:
            print("⚠️  Some validation tests failed. Please review the issues above.")
        
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    validate_rationalization()
