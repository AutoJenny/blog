"""
Normalize all table linens to a single core_type with subtypes.

Table linens include:
- place_mat
- napkins
- table_runner
- tablecloth
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target core_type for all table linens
TARGET_CORE_TYPE = 'table_linen'

# Table linen types that should be subtypes
TABLE_LINEN_TYPES = {
    'place_mat',
    'napkins',
    'napkin',
    'table_runner',
    'tablecloth',
    'table_cloth',
}

def normalize_table_linens(dry_run=False):
    """Normalize all table linens to 'table_linen' core_type with subtypes."""
    with db_manager.get_cursor() as cursor:
        # Find table linens by core_type
        placeholders = ','.join(['%s'] * len(TABLE_LINEN_TYPES))
        cursor.execute(f"""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' IN ({placeholders})
        """, tuple(TABLE_LINEN_TYPES))
        
        products_by_type = cursor.fetchall()
        
        # Find table linens by name patterns
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE (
                name ILIKE '%place mat%'
                OR name ILIKE '%napkin%'
                OR name ILIKE '%table runner%'
                OR name ILIKE '%tablecloth%'
                OR name ILIKE '%table cloth%'
            )
            AND product_type_data->'disambiguation'->>'product_form' = 'homeware'
            AND product_type_data->>'core_type' NOT IN ('place_mat', 'napkins', 'napkin', 'table_runner', 'tablecloth', 'table_cloth', 'table_linen')
        """)
        
        products_by_name = cursor.fetchall()
        
        # Combine and deduplicate, excluding non-table-linen items
        all_products = {}
        for product in products_by_type + products_by_name:
            name = product['name'].lower()
            # Exclude napkin rings (they're accessories, not table linens)
            if 'napkin ring' in name or 'ring' in name and 'napkin' in name:
                continue
            all_products[product['id']] = product
        
        products = list(all_products.values())
        
        logger.info(f"Found {len(products)} table linens to normalize")
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            current_core_type = type_data.get('core_type')
            name = product['name'].lower()
            
            # Skip if already correct (has table_linen AND subtype)
            if current_core_type == TARGET_CORE_TYPE and type_data.get('subtype'):
                continue
            
            # Determine subtype from current core_type or name
            subtype = None
            if current_core_type and current_core_type in TABLE_LINEN_TYPES and current_core_type != TARGET_CORE_TYPE:
                # Normalize plural/singular
                if current_core_type == 'napkins':
                    subtype = 'napkin'
                elif current_core_type == 'table_cloth':
                    subtype = 'tablecloth'
                else:
                    subtype = current_core_type
            elif 'place mat' in name:
                subtype = 'place_mat'
            elif 'napkin' in name:
                subtype = 'napkin'
            elif 'table runner' in name:
                subtype = 'table_runner'
            elif 'tablecloth' in name or 'table cloth' in name:
                subtype = 'tablecloth'
            
            # Update to table_linen with subtype
            needs_update = False
            if current_core_type != TARGET_CORE_TYPE:
                type_data['core_type'] = TARGET_CORE_TYPE
                type_data['core_type_normalized'] = True
                if current_core_type:
                    type_data['core_type_normalized_from'] = current_core_type
                else:
                    type_data['core_type_normalized_from'] = 'null'
                type_data['core_type_normalized_reason'] = 'table_linen_consolidation'
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
    
    parser = argparse.ArgumentParser(description='Normalize all table linens to table_linen core_type')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("NORMALIZING TABLE LINENS")
        print("="*80)
        print(f"Target core_type: {TARGET_CORE_TYPE}")
        print(f"Dry run: {args.dry_run}\n")
        
        updates = normalize_table_linens(dry_run=args.dry_run)
        
        print(f"✅ Normalized {len(updates)} table linens to '{TARGET_CORE_TYPE}'")
        
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

