"""
Normalize all drinking vessels to a single core_type.

Drinking vessels include:
- mugs
- glasses
- drinkware
- drinking_horn
- tankard
- cup
- flask (drinking flask, not hip flask)
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target core_type for all drinking vessels
TARGET_CORE_TYPE = 'drinkware'

# Core types that are drinking vessels
DRINKING_VESSEL_TYPES = {
    'mug',
    'glass',
    'drinkware',
    'drinking_horn',
    'tankard',
    'cup',
    'quaich',  # Quaichs are traditional Scottish drinking vessels
}

def normalize_drinking_vessels(dry_run=False):
    """Normalize all drinking vessels to 'drinkware'."""
    with db_manager.get_cursor() as cursor:
        # Find all products that are drinking vessels
        # 1. By core_type
        placeholders = ','.join(['%s'] * len(DRINKING_VESSEL_TYPES))
        cursor.execute(f"""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' IN ({placeholders})
        """, tuple(DRINKING_VESSEL_TYPES))
        
        products_by_type = cursor.fetchall()
        
        # 2. By name patterns (but exclude non-drinking items)
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE (
                name ILIKE '%drinking%'
                OR name ILIKE '%mug%'
                OR (name ILIKE '%glass%' AND name NOT ILIKE '%sunglass%' AND name NOT ILIKE '%picture glass%' AND name NOT ILIKE '%photo glass%')
                OR name ILIKE '%tankard%'
                OR (name ILIKE '%cup%' AND name NOT ILIKE '%measuring cup%' AND name NOT ILIKE '%measuring%')
            )
            AND product_type_data->'disambiguation'->>'product_form' = 'homeware'
            AND (
                product_type_data->>'core_type' IS NULL
                OR product_type_data->>'core_type' NOT IN ('flask', 'bottle', 'decanter')
            )
        """)
        
        products_by_name = cursor.fetchall()
        
        # Combine and deduplicate, excluding non-drinking items
        all_products = {}
        for product in products_by_type + products_by_name:
            name = product['name'].lower()
            # Exclude chopping boards, picture frames, etc.
            if 'chopping' in name or 'cutting board' in name:
                continue
            all_products[product['id']] = product
        
        products = list(all_products.values())
        
        logger.info(f"Found {len(products)} drinking vessels to normalize")
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            current_core_type = type_data.get('core_type')
            name = product['name'].lower()
            
            # Skip if already correct (has drinkware AND subtype)
            if current_core_type == TARGET_CORE_TYPE and type_data.get('subtype'):
                continue
            
            # Special handling for flasks - only drinking flasks, not hip flasks
            if current_core_type == 'flask':
                if 'hip' in name:
                    # Hip flasks stay as flask (they're not drinking vessels)
                    continue
            
            # Exclude chopping boards
            if 'chopping' in name or 'cutting board' in name:
                continue
            
            # Exclude non-drinking items that might have been misclassified
            if 'sporran' in name:
                # Sporrans are not drinking vessels
                continue
            
            # Determine subtype from current core_type or name
            subtype = None
            if current_core_type and current_core_type != TARGET_CORE_TYPE:
                # Use the old core_type as the subtype
                subtype = current_core_type
            elif 'quaich' in name:
                subtype = 'quaich'
            elif 'mug' in name:
                subtype = 'mug'
            elif 'glass' in name or 'tumbler' in name:
                subtype = 'glass'
            elif 'tankard' in name:
                subtype = 'tankard'
            elif 'drinking horn' in name or 'horn' in name:
                subtype = 'drinking_horn'
            elif 'cup' in name:
                subtype = 'cup'
            
            # Update to drinkware with subtype
            needs_update = False
            if current_core_type != TARGET_CORE_TYPE:
                type_data['core_type'] = TARGET_CORE_TYPE
                type_data['core_type_normalized'] = True
                if current_core_type:
                    type_data['core_type_normalized_from'] = current_core_type
                else:
                    type_data['core_type_normalized_from'] = 'null'
                type_data['core_type_normalized_reason'] = 'drinking_vessel_consolidation'
                needs_update = True
            
            if subtype and type_data.get('subtype') != subtype:
                type_data['subtype'] = subtype
                type_data['subtype_added'] = True
                needs_update = True
            
            if not needs_update:
                continue
            
            if not dry_run:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(type_data), product['id']))
            
            updates.append({
                'id': product['id'],
                'name': product['name'],
                'old_core_type': current_core_type or 'null',
                'new_core_type': TARGET_CORE_TYPE
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize all drinking vessels to drinkware')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("NORMALIZING DRINKING VESSELS")
        print("="*80)
        print(f"Target core_type: {TARGET_CORE_TYPE}")
        print(f"Dry run: {args.dry_run}\n")
        
        updates = normalize_drinking_vessels(dry_run=args.dry_run)
        
        print(f"✅ Normalized {len(updates)} drinking vessels to '{TARGET_CORE_TYPE}'")
        
        # Show breakdown by old type
        from collections import Counter
        old_types = Counter([u['old_core_type'] for u in updates])
        print("\nBreakdown by old core_type:")
        for old_type, count in old_types.most_common():
            print(f"  {old_type}: {count}")
        
        # Show sample updates
        if updates:
            print("\nSample updates (first 10):")
            for update in updates[:10]:
                print(f"  [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']}")
        
        print(f"\n✅ Normalization complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

