#!/usr/bin/env python3
"""
Check the current state of tartan tables
Shows statistics and sample data from both tables
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

def check_table_states():
    """Check the current state of both tartan tables"""
    print("=== Tartan Tables Status Check ===\n")
    
    try:
        with db_manager.get_cursor() as cursor:
            # Check tartan_designs_clan table
            print("1. tartan_designs_clan table:")
            cursor.execute("SELECT COUNT(*) FROM tartan_designs_clan")
            clan_count = cursor.fetchone()['count']
            print(f"   Total records: {clan_count}")
            
            cursor.execute("SELECT COUNT(*) FROM tartan_designs_clan WHERE register_id IS NOT NULL")
            clan_with_register = cursor.fetchone()['count']
            print(f"   Records with register_id: {clan_with_register}")
            
            # Show column structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_clan' 
                ORDER BY ordinal_position
            """)
            clan_columns = cursor.fetchall()
            print(f"   Columns ({len(clan_columns)}):")
            for col in clan_columns:
                print(f"     - {col['column_name']} ({col['data_type']})")
            
            print()
            
            # Check tartan_designs_register table
            print("2. tartan_designs_register table:")
            cursor.execute("SELECT COUNT(*) FROM tartan_designs_register")
            register_count = cursor.fetchone()['count']
            print(f"   Total records: {register_count}")
            
            cursor.execute("SELECT COUNT(*) FROM tartan_designs_register WHERE sta_ref IS NOT NULL")
            with_sta_ref = cursor.fetchone()['count']
            print(f"   Records with STA ref: {with_sta_ref}")
            
            cursor.execute("SELECT COUNT(*) FROM tartan_designs_register WHERE stwr_ref IS NOT NULL")
            with_stwr_ref = cursor.fetchone()['count']
            print(f"   Records with STWR ref: {with_stwr_ref}")
            
            # Show column structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_register' 
                ORDER BY ordinal_position
            """)
            register_columns = cursor.fetchall()
            print(f"   Columns ({len(register_columns)}):")
            for col in register_columns:
                print(f"     - {col['column_name']} ({col['data_type']})")
            
            print()
            
            # Show sample data from both tables
            print("3. Sample data from tartan_designs_clan:")
            cursor.execute("SELECT id, name, legacy_id, register_id FROM tartan_designs_clan ORDER BY id LIMIT 5")
            clan_samples = cursor.fetchall()
            for sample in clan_samples:
                print(f"   ID {sample['id']}: '{sample['name']}' (legacy_id: {sample['legacy_id']}, register_id: {sample['register_id']})")
            
            print()
            
            print("4. Sample data from tartan_designs_register:")
            cursor.execute("SELECT id, tartan_name, reference, sta_ref, stwr_ref FROM tartan_designs_register ORDER BY id LIMIT 5")
            register_samples = cursor.fetchall()
            for sample in register_samples:
                print(f"   ID {sample['id']}: '{sample['tartan_name']}' (ref: {sample['reference']}, STA: {sample['sta_ref']}, STWR: {sample['stwr_ref']})")
            
            print()
            
            # Check for potential matches
            print("5. Potential matching analysis:")
            
            # Check STA ref matches (handle both numeric and text)
            cursor.execute("""
                SELECT COUNT(*) FROM tartan_designs_register r
                WHERE r.sta_ref IS NOT NULL 
                AND r.sta_ref NOT IN ('none', 'null', '')
                AND (
                    (r.sta_ref ~ '^[0-9]+$' AND EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.legacy_id = r.sta_ref::integer
                    ))
                    OR EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.legacy_id::text = r.sta_ref
                    )
                )
            """)
            sta_matches = cursor.fetchone()['count']
            print(f"   Potential STA ref matches: {sta_matches}")
            
            # Check STWR ref matches (handle both numeric and text)
            cursor.execute("""
                SELECT COUNT(*) FROM tartan_designs_register r
                WHERE r.stwr_ref IS NOT NULL 
                AND r.stwr_ref NOT IN ('none', 'null', '')
                AND (
                    (r.stwr_ref ~ '^[0-9]+$' AND EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.legacy_id = r.stwr_ref::integer
                    ))
                    OR EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.legacy_id::text = r.stwr_ref
                    )
                )
            """)
            stwr_matches = cursor.fetchone()['count']
            print(f"   Potential STWR ref matches: {stwr_matches}")
            
            # Check reference matches (handle both numeric and text)
            cursor.execute("""
                SELECT COUNT(*) FROM tartan_designs_register r
                WHERE r.reference IS NOT NULL 
                AND (
                    (r.reference ~ '^[0-9]+$' AND EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.legacy_id = r.reference::integer
                    ))
                    OR EXISTS (
                        SELECT 1 FROM tartan_designs_clan c 
                        WHERE c.legacy_id::text = r.reference
                    )
                )
            """)
            ref_matches = cursor.fetchone()['count']
            print(f"   Potential reference matches: {ref_matches}")
            
            print()
            print("=== Status Check Complete ===")
            
    except Exception as e:
        print(f"Error checking table states: {e}")

if __name__ == "__main__":
    check_table_states()
