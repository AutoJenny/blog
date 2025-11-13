"""
Normalize all containers to a single core_type with subtypes.

Containers include:
- flask (hip flasks)
- bottle (water bottles, etc.)
- decanter
- water_bottle
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target core_type for all containers
TARGET_CORE_TYPE = 'container'

# Container types that should be subtypes
CONTAINER_TYPES = {
    'flask',
    'bottle',
    'decanter',
    'water_bottle',
    'hip_flask',
}

def normalize_containers(dry_run=False):
    """Normalize all containers to 'container' core_type with subtypes."""
    with db_manager.get_cursor() as cursor:
        # Find containers by core_type
        placeholders = ','.join(['%s'] * len(CONTAINER_TYPES))
        cursor.execute(f"""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' IN ({placeholders})
        """, tuple(CONTAINER_TYPES))
        
        products_by_type = cursor.fetchall()
        
        # Find containers by name patterns (but exclude non-container items)
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE (
                (name ILIKE '%flask%' AND name NOT ILIKE '%sporran%')
                OR name ILIKE '%bottle%'
                OR name ILIKE '%decanter%'
            )
            AND product_type_data->'disambiguation'->>'product_form' IN ('homeware', 'haberdashery')
            AND product_type_data->>'core_type' NOT IN ('flask', 'bottle', 'decanter', 'water_bottle', 'container')
        """)
        
        products_by_name = cursor.fetchall()
        
        # Combine and deduplicate, excluding non-containers
        all_products = {}
        for product in products_by_type + products_by_name:
            name = product['name'].lower()
            current_core_type = product['product_type_data'].get('core_type') if product['product_type_data'] else None
            
            # Exclude non-container items
            if 'sporran' in name:
                continue
            if current_core_type == 'bottle_opener':
                # Bottle openers are tools, not containers
                continue
            if current_core_type == 'magnet':
                # Magnets are not containers
                continue
            if current_core_type == 'bag' and 'purse flask' in name:
                # Purse flasks are bags, not containers
                continue
            
            all_products[product['id']] = product
        
        products = list(all_products.values())
        
        logger.info(f"Found {len(products)} containers to normalize")
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            current_core_type = type_data.get('core_type')
            name = product['name'].lower()
            
            # Skip if already correct (has container AND subtype)
            if current_core_type == TARGET_CORE_TYPE and type_data.get('subtype'):
                continue
            
            # Determine subtype from current core_type or name
            subtype = None
            if current_core_type and current_core_type in CONTAINER_TYPES and current_core_type != TARGET_CORE_TYPE:
                # Use the old core_type as the subtype
                if current_core_type == 'hip_flask':
                    subtype = 'flask'
                elif current_core_type == 'water_bottle':
                    subtype = 'bottle'
                else:
                    subtype = current_core_type
            elif current_core_type == 'drinkware' and 'flask' in name:
                # Flasks that were misclassified as drinkware
                subtype = 'flask'
            elif 'flask' in name:
                subtype = 'flask'
            elif 'bottle' in name:
                subtype = 'bottle'
            elif 'decanter' in name:
                subtype = 'decanter'
            
            # Update to container with subtype
            needs_update = False
            if current_core_type != TARGET_CORE_TYPE:
                type_data['core_type'] = TARGET_CORE_TYPE
                type_data['core_type_normalized'] = True
                if current_core_type:
                    type_data['core_type_normalized_from'] = current_core_type
                else:
                    type_data['core_type_normalized_from'] = 'null'
                type_data['core_type_normalized_reason'] = 'container_consolidation'
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
                'new_core_type': TARGET_CORE_TYPE,
                'subtype': subtype
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize all containers to container core_type')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("NORMALIZING CONTAINERS")
        print("="*80)
        print(f"Target core_type: {TARGET_CORE_TYPE}")
        print(f"Dry run: {args.dry_run}\n")
        
        updates = normalize_containers(dry_run=args.dry_run)
        
        print(f"✅ Normalized {len(updates)} containers to '{TARGET_CORE_TYPE}'")
        
        # Show breakdown by old type
        from collections import Counter
        old_types = Counter([u['old_core_type'] for u in updates])
        if old_types:
            print("\nBreakdown by old core_type:")
            for old_type, count in old_types.most_common():
                print(f"  {old_type}: {count}")
        
        # Show breakdown by subtype
        subtypes = Counter([u['subtype'] for u in updates if u.get('subtype')])
        if subtypes:
            print("\nBreakdown by subtype:")
            for subtype, count in subtypes.most_common():
                print(f"  {subtype}: {count}")
        
        # Show sample updates
        if updates:
            print("\nSample updates (first 10):")
            for update in updates[:10]:
                print(f"  [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']} (subtype: {update.get('subtype', 'none')})")
        
        print(f"\n✅ Normalization complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

