"""
Fix product_form classifications:
- sgian_dubh should be in jewellery form
- buckles, headwear, garters should be in clothing form
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Items that should be in jewellery form
JEWELLERY_ITEMS = {
    'sgian_dubh',
}

# Items that should be in clothing form
CLOTHING_ITEMS = {
    'belt_buckle',
    'buckle',
    'headwear',
    'garter',
}

def fix_forms(dry_run=False):
    """Fix product_form for specific items."""
    with db_manager.get_cursor() as cursor:
        updates = []
        
        # Fix jewellery items
        for core_type in JEWELLERY_ITEMS:
            cursor.execute("""
                SELECT id, name, product_type_data
                FROM clan_products
                WHERE product_type_data->>'core_type' = %s
                  AND product_type_data->'disambiguation'->>'product_form' != 'jewellery'
            """, (core_type,))
            
            products = cursor.fetchall()
            for product in products:
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_form = type_data.get('disambiguation', {}).get('product_form')
                
                if 'disambiguation' not in type_data:
                    type_data['disambiguation'] = {}
                
                type_data['disambiguation']['product_form'] = 'jewellery'
                type_data['product_form_corrected'] = True
                type_data['product_form_corrected_from'] = current_form
                type_data['product_form_corrected_reason'] = f'{core_type}_should_be_jewellery'
                
                if not dry_run:
                    cursor.execute("""
                        UPDATE clan_products
                        SET product_type_data = %s
                        WHERE id = %s
                    """, (json.dumps(type_data), product['id']))
                
                updates.append({
                    'id': product['id'],
                    'name': product['name'],
                    'core_type': core_type,
                    'old_form': current_form,
                    'new_form': 'jewellery'
                })
        
        # Fix clothing items
        for core_type in CLOTHING_ITEMS:
            cursor.execute("""
                SELECT id, name, product_type_data
                FROM clan_products
                WHERE product_type_data->>'core_type' = %s
                  AND product_type_data->'disambiguation'->>'product_form' != 'clothing'
            """, (core_type,))
            
            products = cursor.fetchall()
            for product in products:
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_form = type_data.get('disambiguation', {}).get('product_form')
                
                if 'disambiguation' not in type_data:
                    type_data['disambiguation'] = {}
                
                type_data['disambiguation']['product_form'] = 'clothing'
                type_data['product_form_corrected'] = True
                type_data['product_form_corrected_from'] = current_form
                type_data['product_form_corrected_reason'] = f'{core_type}_should_be_clothing'
                
                if not dry_run:
                    cursor.execute("""
                        UPDATE clan_products
                        SET product_type_data = %s
                        WHERE id = %s
                    """, (json.dumps(type_data), product['id']))
                
                updates.append({
                    'id': product['id'],
                    'name': product['name'],
                    'core_type': core_type,
                    'old_form': current_form,
                    'new_form': 'clothing'
                })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix product_form for specific items')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("FIXING PRODUCT FORMS")
        print("="*80)
        print(f"Dry run: {args.dry_run}\n")
        
        updates = fix_forms(dry_run=args.dry_run)
        
        # Group by new form
        jewellery_updates = [u for u in updates if u['new_form'] == 'jewellery']
        clothing_updates = [u for u in updates if u['new_form'] == 'clothing']
        
        if jewellery_updates:
            print(f"✅ Fixed {len(jewellery_updates)} items to jewellery form:")
            for update in jewellery_updates:
                print(f"   [{update['id']}] {update['name']}: {update['old_form']} → {update['new_form']}")
        
        if clothing_updates:
            print(f"\n✅ Fixed {len(clothing_updates)} items to clothing form:")
            for update in clothing_updates:
                print(f"   [{update['id']}] {update['name']}: {update['old_form']} → {update['new_form']}")
        
        print(f"\n✅ All fixes complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

