"""
Redistribute all accessories to appropriate categories
Eliminate the 'accessory' category by moving items to:
- clothing (worn accessories: ties, belts, scarves, sporrans, kilt pins, etc.)
- jewellery (jewellery items: rings, necklaces, brooches, charms, etc.)
- bags (bags, backpacks, purses, wallets)
- homeware (home items)
- pets (pet items)
- artwork (wall art)
- stationery (writing supplies)
- haberdashery (sewing supplies)
- Create new categories if needed
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_category(name, sku, core_type):
    """
    Determine the appropriate category for an accessory item.
    Returns (product_form, core_type)
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    core_type_lower = (core_type or '').lower()
    
    # Pet items
    if any(term in name_lower for term in ['dog', 'pet', 'cat']) and any(term in name_lower for term in ['bandana', 'collar', 'lead', 'treat', 'bowl']):
        if 'bandana' in name_lower:
            return ('pets', 'bandana')
        elif 'collar' in name_lower:
            return ('pets', 'collar')
        elif 'lead' in name_lower or 'leash' in name_lower:
            return ('pets', 'lead')
        elif 'treat' in name_lower:
            return ('pets', 'treat_bag')
        elif 'bowl' in name_lower:
            return ('pets', 'pet_bowl')
        else:
            return ('pets', core_type or 'pet')
    
    # Jewellery items
    jewellery_terms = ['ring', 'necklace', 'bracelet', 'earring', 'pendant', 'bangle', 'watch', 'charm', 'brooch']
    if any(term in name_lower or term in core_type_lower for term in jewellery_terms):
        return ('jewellery', core_type or 'jewellery')
    
    # Clothing accessories (worn items)
    clothing_accessory_terms = [
        'tie', 'bow tie', 'cufflink', 'belt', 'waistcoat', 'scarf', 'sporran', 
        'kilt pin', 'pin', 'badge', 'tartan bandana', 'tam', 'glove', 'sock'
    ]
    if any(term in name_lower or term in core_type_lower for term in clothing_accessory_terms):
        return ('clothing', core_type or 'accessory')
    
    # Bags
    bag_terms = ['bag', 'backpack', 'purse', 'wallet', 'pouch', 'clutch', 'tote', 'shopping bag']
    if any(term in name_lower or term in core_type_lower for term in bag_terms):
        if 'backpack' in name_lower or 'backpack' in core_type_lower:
            return ('bags', 'backpack')
        elif 'purse' in name_lower or 'purse' in core_type_lower:
            return ('bags', 'purse')
        elif 'wallet' in name_lower or 'wallet' in core_type_lower:
            return ('bags', 'wallet')
        elif 'tote' in name_lower or 'tote' in core_type_lower:
            return ('bags', 'tote_bag')
        elif 'shopping' in name_lower and 'bag' in name_lower:
            return ('bags', 'shopping_bag')
        else:
            return ('bags', core_type or 'bag')
    
    # Stationery
    if any(term in name_lower for term in ['notebook', 'pencil case', 'stationery', 'writing', 'journal', 'diary']):
        if 'pencil case' in name_lower:
            return ('stationery', 'pencil_case')
        elif 'notebook' in name_lower:
            return ('stationery', 'notebook')
        else:
            return ('stationery', core_type or 'stationery')
    
    # Homeware
    homeware_terms = ['flask', 'quaich', 'glass', 'mug', 'coaster', 'letter opener', 'peeler', 'embroidery kit', 'shoehorn', 'napkin ring', 'cheese knife']
    if any(term in name_lower for term in homeware_terms):
        if 'flask' in name_lower:
            return ('homeware', 'flask')
        elif 'quaich' in name_lower:
            return ('homeware', 'quaich')
        elif 'coaster' in name_lower:
            return ('homeware', 'drink_coaster')
        elif 'letter opener' in name_lower:
            return ('homeware', 'letter_opener')
        elif 'embroidery' in name_lower:
            return ('homeware', 'embroidery_kit')
        else:
            return ('homeware', core_type or 'homeware')
    
    # Haberdashery
    if any(term in name_lower for term in ['button', 'thread', 'needle', 'ribbon', 'haberdashery']):
        return ('haberdashery', core_type or 'buttons')
    
    # Artwork (wall art)
    if any(term in name_lower for term in ['painting', 'print', 'plaque', 'map', 'picture', 'poster', 'canvas', 'wall art']):
        if 'painting' in name_lower:
            return ('artwork', 'painting')
        elif 'print' in name_lower:
            return ('artwork', 'print')
        elif 'plaque' in name_lower:
            return ('artwork', 'plaque')
        elif 'map' in name_lower:
            return ('artwork', 'map')
        elif 'picture' in name_lower:
            return ('artwork', 'picture')
        else:
            return ('artwork', 'artwork')
    
    # Keyrings, key fobs - could be a new category or homeware
    if any(term in name_lower for term in ['keyring', 'key ring', 'key fob', 'keychain']):
        # Create new category "keyrings" or put in homeware?
        # For now, put in homeware as small personal items
        return ('homeware', 'keyring')
    
    # If we can't categorize, keep as accessory for manual review
    # But actually, let's try to categorize everything
    # Default to clothing if it seems wearable, otherwise homeware
    if any(term in name_lower for term in ['wear', 'worn', 'attach', 'pin', 'clip']):
        return ('clothing', core_type or 'accessory')
    else:
        return ('homeware', core_type or 'homeware')

def redistribute_accessories():
    """
    Redistribute all accessories to appropriate categories.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all products in accessory category
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    sku,
                    product_type_data
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'accessory'
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} products in accessory category")
            
            moved_count = 0
            by_new_category = {}
            uncategorized = []
            
            for product in products:
                product_id = product['id']
                name = product['name']
                sku = product['sku']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                
                # Determine new category
                new_form, new_core_type = determine_category(name, sku, current_core_type)
                
                # Update product_form and core_type
                type_data.setdefault('disambiguation', {})['product_form'] = new_form
                type_data['core_type'] = new_core_type
                
                if new_form not in by_new_category:
                    by_new_category[new_form] = 0
                by_new_category[new_form] += 1
                
                # Update the product
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(type_data), product_id))
                
                moved_count += 1
                if moved_count % 50 == 0:
                    logger.info(f"Processed {moved_count} products...")
            
            conn.commit()
            logger.info(f"Redistribution complete. Moved {moved_count} products from accessory category.")
            
            # Show summary
            print(f"\n✅ Redistribution Summary:")
            print(f"   Total products moved: {moved_count}")
            print(f"\n   Distribution by new category:")
            for category, count in sorted(by_new_category.items(), key=lambda x: x[1], reverse=True):
                print(f"     - {category}: {count} products")
            
            # Verify no accessories remain
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'accessory'
            """)
            remaining = cursor.fetchone()['count']
            
            if remaining == 0:
                print(f"\n✅ All accessories redistributed. None remaining in 'accessory' category.")
            else:
                print(f"\n⚠️  {remaining} products still in 'accessory' category - needs manual review")
            
            return moved_count

if __name__ == '__main__':
    try:
        count = redistribute_accessories()
        print(f"\n✅ Successfully redistributed {count} products from accessory category")
    except Exception as e:
        logger.error(f"Error redistributing accessories: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

