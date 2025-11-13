"""
Fix:
1. 4 sporran flasks - these are sporrans, not containers (keep as sporran or change to sporran core_type)
2. 7 accessories - 5 should be jewellery with proper subtypes, 2 should be clothing with proper subtypes
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_sporran_flasks(dry_run=False):
    """Fix sporran flasks - they're sporrans, not containers."""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'core_type' = 'flask'
              AND name ILIKE '%sporran%'
        """)
        
        products = cursor.fetchall()
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            
            type_data['core_type'] = 'sporran'
            type_data['core_type_corrected'] = True
            type_data['core_type_corrected_from'] = 'flask'
            type_data['core_type_corrected_reason'] = 'sporran_flask_is_sporran_not_container'
            
            if 'disambiguation' not in type_data:
                type_data['disambiguation'] = {}
            type_data['disambiguation']['product_form'] = 'clothing'
            
            if not dry_run:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s
                    WHERE id = %s
                """, (json.dumps(type_data), product['id']))
            
            updates.append({
                'id': product['id'],
                'name': product['name'],
                'old_core_type': 'flask',
                'new_core_type': 'sporran'
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

def fix_accessories(dry_run=False):
    """Fix 7 accessories - determine proper core_type and form."""
    with db_manager.get_cursor() as cursor:
        # Get accessories in jewellery/clothing form
        cursor.execute("""
            SELECT id, name, product_type_data, description, short_description
            FROM clan_products
            WHERE product_type_data->>'core_type' = 'accessory'
              AND product_type_data->'disambiguation'->>'product_form' IN ('jewellery', 'clothing')
            ORDER BY product_type_data->'disambiguation'->>'product_form', name
        """)
        
        products = cursor.fetchall()
        
        # The user said 7 accessories - let me identify which ones need fixing
        # Based on the analysis, kilt pins should be brooches (jewellery)
        # But the user said only 7 need fixing, so let me check which are currently wrong
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            name = product['name'].lower()
            desc = (product.get('description') or '').lower()
            short_desc = (product.get('short_description') or '').lower()
            text = f"{name} {desc} {short_desc}"
            current_form = type_data.get('disambiguation', {}).get('product_form')
            
            # Determine what it should be
            new_core_type = None
            new_form = None
            
            if 'kilt pin' in name:
                new_core_type = 'brooch'
                new_form = 'jewellery'
            elif 'sporran' in name and 'strap' not in name:
                new_core_type = 'sporran'
                new_form = 'clothing'
            elif 'sporran strap' in name or 'chain strap' in name:
                new_core_type = 'kilt_accessory'
                new_form = 'clothing'
            elif 'scarf' in name:
                new_core_type = 'scarf'
                new_form = 'clothing'
            elif 'tie' in name:
                new_core_type = 'tie'
                new_form = 'clothing'
            elif 'cummerbund' in name:
                new_core_type = 'cummerbund'
                new_form = 'clothing'
            elif 'kilt belt' in name:
                new_core_type = 'kilt_belt'
                new_form = 'clothing'
            elif 'watch' in name or 'pocket watch' in name:
                new_core_type = 'accessory'  # Keep as accessory
                new_form = 'jewellery'
            else:
                # Skip if we can't determine
                continue
            
            # Only update if there's a change needed
            needs_update = False
            if new_core_type and type_data.get('core_type') != new_core_type:
                type_data['core_type'] = new_core_type
                type_data['core_type_corrected'] = True
                type_data['core_type_corrected_from'] = 'accessory'
                needs_update = True
            
            if new_form and current_form != new_form:
                if 'disambiguation' not in type_data:
                    type_data['disambiguation'] = {}
                type_data['disambiguation']['product_form'] = new_form
                type_data['product_form_corrected'] = True
                type_data['product_form_corrected_from'] = current_form
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
                'old_core_type': 'accessory',
                'new_core_type': new_core_type,
                'old_form': current_form,
                'new_form': new_form
            })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix sporran flasks and accessories')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("FIXING SPORRAN FLASKS AND ACCESSORIES")
        print("="*80)
        print(f"Dry run: {args.dry_run}\n")
        
        # Fix sporran flasks
        print("Fixing sporran flasks...")
        flask_updates = fix_sporran_flasks(dry_run=args.dry_run)
        print(f"✅ Fixed {len(flask_updates)} sporran flasks")
        for update in flask_updates:
            print(f"   [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']}")
        
        # Fix accessories
        print("\nFixing accessories...")
        accessory_updates = fix_accessories(dry_run=args.dry_run)
        print(f"✅ Fixed {len(accessory_updates)} accessories")
        
        # Group by form
        jewellery_updates = [u for u in accessory_updates if u['new_form'] == 'jewellery']
        clothing_updates = [u for u in accessory_updates if u['new_form'] == 'clothing']
        
        if jewellery_updates:
            print(f"\n  Jewellery ({len(jewellery_updates)} items):")
            for update in jewellery_updates:
                print(f"    [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']} ({update['new_form']})")
        
        if clothing_updates:
            print(f"\n  Clothing ({len(clothing_updates)} items):")
            for update in clothing_updates:
                print(f"    [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']} ({update['new_form']})")
        
        print(f"\n✅ All fixes complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

