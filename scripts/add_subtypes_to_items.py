"""
Add subtypes to items that need them.

For items that were just fixed from 'accessory' to proper core_types,
add appropriate subtypes where needed.
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_subtypes(dry_run=False):
    """Add subtypes to items that need them."""
    with db_manager.get_cursor() as cursor:
        updates = []
        
        # Kilt pins (brooches) - add 'kilt_pin' subtype
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' = 'brooch'
              AND product_type_data->'disambiguation'->>'product_form' = 'jewellery'
              AND (product_type_data->>'subtype' IS NULL OR product_type_data->>'subtype' = '')
              AND name ILIKE '%kilt pin%'
        """)
        
        kilt_pins = cursor.fetchall()
        for product in kilt_pins:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            type_data['subtype'] = 'kilt_pin'
            type_data['subtype_added'] = True
            
            if not dry_run:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(type_data), product['id']))
            
            updates.append({
                'id': product['id'],
                'name': product['name'],
                'core_type': 'brooch',
                'subtype': 'kilt_pin'
            })
        
        # Sporrans - add 'sporran' subtype (though core_type is already sporran, might not need subtype)
        # Actually, sporrans don't need a subtype since core_type is already sporran
        
        # Watches - add 'watch' subtype
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' = 'accessory'
              AND product_type_data->'disambiguation'->>'product_form' = 'jewellery'
              AND (product_type_data->>'subtype' IS NULL OR product_type_data->>'subtype' = '')
              AND (name ILIKE '%watch%' OR name ILIKE '%pocket watch%')
        """)
        
        watches = cursor.fetchall()
        for product in watches:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            type_data['subtype'] = 'watch'
            type_data['subtype_added'] = True
            
            if not dry_run:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(type_data), product['id']))
            
            updates.append({
                'id': product['id'],
                'name': product['name'],
                'core_type': 'accessory',
                'subtype': 'watch'
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Add subtypes to items')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("ADDING SUBTYPES TO ITEMS")
        print("="*80)
        print(f"Dry run: {args.dry_run}\n")
        
        updates = add_subtypes(dry_run=args.dry_run)
        
        print(f"✅ Added subtypes to {len(updates)} items")
        
        # Group by subtype
        from collections import Counter
        subtypes = Counter([u['subtype'] for u in updates if u.get('subtype')])
        if subtypes:
            print("\nBreakdown by subtype:")
            for subtype, count in subtypes.most_common():
                print(f"  {subtype}: {count}")
        
        # Show sample updates
        if updates:
            print("\nSample updates (first 10):")
            for update in updates[:10]:
                print(f"  [{update['id']}] {update['name']}: {update['core_type']} (subtype: {update.get('subtype', 'none')})")
        
        print(f"\n✅ Subtypes added!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

