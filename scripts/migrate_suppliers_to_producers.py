#!/usr/bin/env python3
"""
Migration script: Populate producers table from clan_products.supplier_name

This script extracts unique supplier names from clan_products and creates
corresponding records in the producers table, then links products back to
producers via producer_id.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.database import db_manager

def migrate_suppliers_to_producers():
    """Extract suppliers from clan_products and create producer records"""
    
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        # Step 1: Get unique suppliers with their descriptions
        print("Step 1: Extracting unique suppliers from clan_products...")
        cur.execute("""
            SELECT DISTINCT 
                supplier_name,
                (SELECT supplier_description 
                 FROM clan_products cp2 
                 WHERE cp2.supplier_name = cp1.supplier_name 
                   AND cp2.supplier_description IS NOT NULL 
                 LIMIT 1) as supplier_description
            FROM clan_products cp1
            WHERE supplier_name IS NOT NULL 
              AND supplier_name != ''
            ORDER BY supplier_name
        """)
        
        suppliers = cur.fetchall()
        print(f"Found {len(suppliers)} unique suppliers")
        
        # Step 2: Insert suppliers into producers table
        print("Step 2: Creating producer records...")
        producers_created = 0
        producers_skipped = 0
        
        for supplier in suppliers:
            try:
                # Handle both dict_row and tuple results
                if isinstance(supplier, dict):
                    supplier_name = supplier['supplier_name']
                    supplier_desc = supplier.get('supplier_description')
                else:
                    supplier_name = supplier[0]
                    supplier_desc = supplier[1] if len(supplier) > 1 else None
                
                cur.execute("""
                    INSERT INTO producers (name, description, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE SET
                        description = COALESCE(EXCLUDED.description, producers.description),
                        updated_at = NOW()
                    RETURNING id
                """, (supplier_name, supplier_desc))
                
                result = cur.fetchone()
                if result:
                    producers_created += 1
                    print(f"  Created/updated: {supplier_name}")
            except Exception as e:
                if isinstance(supplier, dict):
                    supplier_name = supplier.get('supplier_name', 'Unknown')
                else:
                    supplier_name = supplier[0] if len(supplier) > 0 else 'Unknown'
                print(f"  Error creating producer {supplier_name}: {e}")
                producers_skipped += 1
                continue
        
        conn.commit()
        print(f"Created/updated {producers_created} producers, skipped {producers_skipped}")
        
        # Step 3: Link products to producers
        print("Step 3: Linking products to producers...")
        cur.execute("""
            UPDATE clan_products p
            SET producer_id = pr.id
            FROM producers pr
            WHERE p.supplier_name = pr.name
              AND p.producer_id IS NULL
        """)
        
        products_linked = cur.rowcount
        conn.commit()
        print(f"Linked {products_linked} products to producers")
        
        # Step 4: Verify results
        print("\nStep 4: Verifying migration...")
        cur.execute("SELECT COUNT(*) as count FROM producers")
        result = cur.fetchone()
        producer_count = result[0] if isinstance(result, tuple) else result['count']
        
        cur.execute("SELECT COUNT(*) as count FROM clan_products WHERE producer_id IS NOT NULL")
        result = cur.fetchone()
        linked_count = result[0] if isinstance(result, tuple) else result['count']
        
        cur.execute("SELECT COUNT(*) as count FROM clan_products WHERE supplier_name IS NOT NULL AND supplier_name != ''")
        result = cur.fetchone()
        total_with_supplier = result[0] if isinstance(result, tuple) else result['count']
        
        print(f"\nMigration Summary:")
        print(f"  Producers in database: {producer_count}")
        print(f"  Products linked to producers: {linked_count}")
        print(f"  Products with supplier_name: {total_with_supplier}")
        print(f"  Coverage: {linked_count/total_with_supplier*100:.1f}%" if total_with_supplier > 0 else "  Coverage: N/A")
        
        cur.close()
        conn.close()
        
        print("\nMigration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Starting supplier to producer migration...")
    success = migrate_suppliers_to_producers()
    sys.exit(0 if success else 1)

