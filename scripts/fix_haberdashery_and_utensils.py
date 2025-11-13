"""
Fix haberdashery items and normalize utensils.

1. Move buttons and swatches to haberdashery form
2. Group all utensils under core_type 'utensil' with subtypes (spoon, fork, etc.)
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target core_type for utensils
UTENSIL_CORE_TYPE = 'utensil'

# Utensil types that should be subtypes
UTENSIL_TYPES = {
    'spoon',
    'fork',
    'knife',
    'utensil',
}

def fix_haberdashery_items(dry_run=False):
    """Move buttons and swatches to haberdashery form."""
    with db_manager.get_cursor() as cursor:
        # Find buttons and swatches (including antler_button)
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE (
                product_type_data->>'core_type' IN ('button', 'swatch', 'antler_button')
                OR (name ILIKE '%button%' AND name ILIKE '%set%')
                OR name ILIKE '%swatch%'
            )
        """)
        
        products = cursor.fetchall()
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            current_form = type_data.get('disambiguation', {}).get('product_form')
            current_core_type = type_data.get('core_type')
            name = product['name'].lower()
            
            # Check if it's actually a button or swatch (exclude false matches)
            # Exclude clothing items (vests, jackets, etc.) that just mention buttons
            is_button = (
                current_core_type == 'button' or 
                (current_core_type == 'antler_button') or
                ('button' in name and 'set' in name and ('vest' not in name and 'jacket' not in name and 'waistcoat' not in name))
            )
            is_swatch = current_core_type == 'swatch' or ('swatch' in name and 'fabric' not in current_core_type)
            
            if not (is_button or is_swatch):
                continue
            
            needs_update = False
            
            # Normalize antler_button to button
            if current_core_type == 'antler_button':
                type_data['core_type'] = 'button'
                type_data['core_type_normalized'] = True
                type_data['core_type_normalized_from'] = 'antler_button'
                needs_update = True
            
            if 'disambiguation' not in type_data:
                type_data['disambiguation'] = {}
            
            # Only update form if it's not already haberdashery
            if current_form != 'haberdashery':
                type_data['disambiguation']['product_form'] = 'haberdashery'
                type_data['product_form_corrected'] = True
                type_data['product_form_corrected_from'] = current_form
                type_data['product_form_corrected_reason'] = 'haberdashery_item'
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
                'old_form': current_form,
                'new_form': 'haberdashery'
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

def normalize_utensils(dry_run=False):
    """Normalize all utensils to 'utensil' core_type with subtypes."""
    with db_manager.get_cursor() as cursor:
        # Find utensils by core_type
        placeholders = ','.join(['%s'] * len(UTENSIL_TYPES))
        cursor.execute(f"""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' IN ({placeholders})
        """, tuple(UTENSIL_TYPES))
        
        products_by_type = cursor.fetchall()
        
        # Find utensils by name patterns
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE (
                name ILIKE '%spoon%'
                OR name ILIKE '%fork%'
                OR name ILIKE '%utensil%'
            )
            AND product_type_data->'disambiguation'->>'product_form' = 'homeware'
            AND product_type_data->>'core_type' NOT IN ('spoon', 'fork', 'utensil', 'knife')
        """)
        
        products_by_name = cursor.fetchall()
        
        # Combine and deduplicate
        all_products = {}
        for product in products_by_type + products_by_name:
            all_products[product['id']] = product
        
        products = list(all_products.values())
        
        logger.info(f"Found {len(products)} utensils to normalize")
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            current_core_type = type_data.get('core_type')
            name = product['name'].lower()
            
            # Skip if already correct (has utensil AND subtype)
            if current_core_type == UTENSIL_CORE_TYPE and type_data.get('subtype'):
                continue
            
            # Determine subtype from current core_type or name
            subtype = None
            if current_core_type and current_core_type in UTENSIL_TYPES and current_core_type != UTENSIL_CORE_TYPE:
                subtype = current_core_type
            elif 'spoon' in name:
                subtype = 'spoon'
            elif 'fork' in name:
                subtype = 'fork'
            elif 'knife' in name and 'sgian' not in name:
                subtype = 'knife'
            elif 'utensil' in name:
                # Try to determine from context
                if 'spoon' in name:
                    subtype = 'spoon'
                elif 'fork' in name:
                    subtype = 'fork'
                else:
                    subtype = 'utensil'
            
            # Update to utensil with subtype
            needs_update = False
            if current_core_type != UTENSIL_CORE_TYPE:
                type_data['core_type'] = UTENSIL_CORE_TYPE
                type_data['core_type_normalized'] = True
                if current_core_type:
                    type_data['core_type_normalized_from'] = current_core_type
                else:
                    type_data['core_type_normalized_from'] = 'null'
                type_data['core_type_normalized_reason'] = 'utensil_consolidation'
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
                'new_core_type': UTENSIL_CORE_TYPE,
                'subtype': subtype
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix haberdashery items and normalize utensils')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("FIXING HABERDASHERY ITEMS AND NORMALIZING UTENSILS")
        print("="*80)
        print(f"Dry run: {args.dry_run}\n")
        
        # Fix haberdashery items
        print("Fixing buttons and swatches...")
        haberdashery_updates = fix_haberdashery_items(dry_run=args.dry_run)
        print(f"✅ Fixed {len(haberdashery_updates)} haberdashery items")
        for update in haberdashery_updates:
            print(f"   [{update['id']}] {update['name']}: {update['old_form']} → {update['new_form']}")
        
        # Normalize utensils
        print("\nNormalizing utensils...")
        utensil_updates = normalize_utensils(dry_run=args.dry_run)
        print(f"✅ Normalized {len(utensil_updates)} utensils to '{UTENSIL_CORE_TYPE}'")
        
        # Show breakdown by subtype
        from collections import Counter
        subtypes = Counter([u['subtype'] for u in utensil_updates if u.get('subtype')])
        if subtypes:
            print("\nBreakdown by subtype:")
            for subtype, count in subtypes.most_common():
                print(f"  {subtype}: {count}")
        
        # Show sample updates
        if utensil_updates:
            print("\nSample updates (first 10):")
            for update in utensil_updates[:10]:
                print(f"   [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']} (subtype: {update.get('subtype', 'none')})")
        
        print(f"\n✅ All fixes complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

