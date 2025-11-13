"""
Fix specific misclassifications identified by user.

1. Kilts, tops, sporrans in homeware → should be clothing
2. Accessories in jewellery form → should have proper core_type
"""

import sys
sys.path.insert(0, '.')
import json
import logging
from config.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_clothing_in_homeware(dry_run=False):
    """Fix clothing items (kilts, tops, sporrans) that are in homeware form."""
    with db_manager.get_cursor() as cursor:
        # Find items in homeware that need fixing
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->'disambiguation'->>'product_form' = 'homeware'
              AND (
                  product_type_data->>'core_type' IN ('kilt', 'top', 'sporran', 'kilt_accessory')
                  OR name ILIKE '%kilt%'
                  OR name ILIKE '%fly plaid%'
              )
        """)
        
        products = cursor.fetchall()
        
        updates = []
        for product in products:
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            current_form = type_data.get('disambiguation', {}).get('product_form')
            core_type = type_data.get('core_type')
            name = product['name'].lower()
            
            # Determine correct core_type and form based on name
            new_core_type = core_type
            new_form = 'clothing'
            
            # Fix specific misclassifications
            if 'buckle' in name:
                new_core_type = 'belt_buckle'
                new_form = 'clothing'  # Belt buckles are clothing accessories
            elif 'sgian dubh' in name or 'sgian_dubh' in name:
                new_core_type = 'sgian_dubh'
                new_form = 'clothing'
            elif 'flash' in name or 'flashes' in name:
                new_core_type = 'kilt_flash'
                new_form = 'clothing'
            elif 'lace' in name or 'tassel' in name:
                new_core_type = 'kilt_accessory'
                new_form = 'clothing'
            elif 'hanger' in name:
                new_core_type = 'kilt_accessory'
                new_form = 'haberdashery'  # Hangers are haberdashery
            elif 'sporran flask' in name or 'flask' in name:
                new_core_type = 'flask'
                new_form = 'homeware'  # Flask is homeware, not clothing
            elif 'kilt' in name and 'fly plaid' in name:
                new_core_type = 'fly_plaid'
                new_form = 'clothing'
            elif core_type == 'kilt':
                new_form = 'clothing'  # Actual kilts should be clothing
            elif core_type == 'sporran':
                new_form = 'clothing'  # Actual sporrans should be clothing
            elif core_type == 'top':
                # Check if it's actually a top or something else
                if 'sgian' in name or 'dubh' in name:
                    new_core_type = 'sgian_dubh'
                    new_form = 'clothing'
                else:
                    new_form = 'clothing'
            
            # Update if needed
            if new_core_type != core_type or new_form != current_form:
                if 'disambiguation' not in type_data:
                    type_data['disambiguation'] = {}
                type_data['disambiguation']['product_form'] = new_form
                type_data['core_type'] = new_core_type
                type_data['core_type_corrected'] = (new_core_type != core_type)
                type_data['product_form_corrected'] = (new_form != current_form)
                if new_core_type != core_type:
                    type_data['core_type_corrected_from'] = core_type
                if new_form != current_form:
                    type_data['product_form_corrected_from'] = current_form
                
                if not dry_run:
                    cursor.execute("""
                        UPDATE clan_products
                        SET product_type_data = %s
                        WHERE id = %s
                    """, (json.dumps(type_data), product['id']))
                
                updates.append({
                    'id': product['id'],
                    'name': product['name'],
                    'old_core_type': core_type,
                    'new_core_type': new_core_type,
                    'old_form': current_form,
                    'new_form': new_form
                })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

def fix_accessories_in_jewellery(dry_run=False):
    """Fix accessories in jewellery form - need to determine proper core_type."""
    with db_manager.get_cursor() as cursor:
        # Find accessories or NULL core_type in jewellery form
        cursor.execute("""
            SELECT id, name, product_type_data, description, short_description
            FROM clan_products
            WHERE product_type_data->'disambiguation'->>'product_form' = 'jewellery'
              AND (
                  product_type_data->>'core_type' = 'accessory'
                  OR product_type_data->>'core_type' IS NULL
                  OR product_type_data->>'core_type' = ''
              )
        """)
        
        products = cursor.fetchall()
        
        # Try to determine proper core_type from name/description
        updates = []
        for product in products:
            name = product['name'].lower()
            description = (product.get('description') or '').lower()
            short_desc = (product.get('short_description') or '').lower()
            text = f"{name} {description} {short_desc}"
            
            type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
            
            # Try to identify the actual type - check in order of specificity
            new_core_type = None
            if any(word in text for word in ['sgian dubh', 'sgian_dubh']):
                new_core_type = 'sgian_dubh'
            elif any(word in text for word in ['ring']) and 'earring' not in text and 'brooch' not in text:
                new_core_type = 'ring'
            elif any(word in text for word in ['buckle', 'belt buckle']) and 'charm' not in text:
                new_core_type = 'belt_buckle'
            elif any(word in text for word in ['earring', 'stud']):
                new_core_type = 'earrings'
            elif any(word in text for word in ['pendant', 'necklace']):
                new_core_type = 'pendant'
            elif any(word in text for word in ['bracelet', 'bangle']):
                new_core_type = 'bracelet'
            elif any(word in text for word in ['charm']) and 'buckle' not in text:
                new_core_type = 'charm'
            elif any(word in text for word in ['cufflink', 'cuff link']):
                new_core_type = 'cufflinks'
            elif any(word in text for word in ['brooch', 'pin', 'badge', 'plaid brooch']) and 'charm' not in text:
                new_core_type = 'brooch'
            elif any(word in text for word in ['watch', 'pocket watch']):
                new_core_type = 'accessory'  # Keep as accessory - watches are accessories
                type_data['needs_review'] = True
                type_data['needs_review_reason'] = 'watch_in_jewellery_form'
            elif any(word in text for word in ['tie pin', 'lapel pin']):
                new_core_type = 'brooch'
            else:
                # If we can't determine, keep as accessory but note it
                new_core_type = 'accessory'
                type_data['needs_review'] = True
                type_data['needs_review_reason'] = 'accessory_in_jewellery_form_unclear_type'
            
            if new_core_type and new_core_type != 'accessory':
                type_data['core_type'] = new_core_type
                type_data['core_type_corrected'] = True
                type_data['core_type_corrected_from'] = 'accessory'
                type_data['core_type_corrected_reason'] = 'accessory_in_jewellery_form'
                
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
                    'new_core_type': new_core_type
                })
        
        if not dry_run:
            db_manager.get_connection().commit()
        
        return updates

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix specific misclassifications')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (don\'t update database)')
    
    args = parser.parse_args()
    
    try:
        print("="*80)
        print("FIXING MISCLASSIFICATIONS")
        print("="*80)
        print(f"Dry run: {args.dry_run}\n")
        
        # Fix clothing in homeware
        print("Fixing clothing items in homeware...")
        clothing_updates = fix_clothing_in_homeware(dry_run=args.dry_run)
        print(f"✅ Fixed {len(clothing_updates)} clothing items")
        for update in clothing_updates[:10]:
            print(f"   [{update['id']}] {update['name']}: {update['old_form']} → {update['new_form']}")
        
        # Fix accessories in jewellery
        print("\nFixing accessories in jewellery form...")
        accessory_updates = fix_accessories_in_jewellery(dry_run=args.dry_run)
        print(f"✅ Fixed {len(accessory_updates)} accessories")
        for update in accessory_updates:
            print(f"   [{update['id']}] {update['name']}: {update['old_core_type']} → {update['new_core_type']}")
        
        print(f"\n✅ All fixes complete!")
        if args.dry_run:
            print("   (Dry run - no changes made)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

