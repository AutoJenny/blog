"""
Clean artwork category - remove non-wall-art items
Keep only items that hang on walls: paintings, plaques, maps, prints
Move stationery, homeware, haberdashery items to appropriate categories
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_new_category(name, sku, core_type):
    """
    Determine the correct category for a product currently in artwork.
    Returns (product_form, core_type)
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    core_type_lower = (core_type or '').lower()
    
    # Stationery items
    if any(term in name_lower for term in ['notebook', 'pencil case', 'stationery', 'writing', 'journal', 'diary']):
        return ('stationery', core_type or 'notebook')
    
    # Homeware items
    if any(term in name_lower for term in ['coaster', 'letter opener', 'peeler', 'embroidery kit']):
        if 'coaster' in name_lower:
            return ('homeware', 'drink_coaster')
        elif 'letter opener' in name_lower:
            return ('homeware', 'letter_opener')
        elif 'peeler' in name_lower:
            return ('homeware', 'peeler')
        elif 'embroidery' in name_lower:
            return ('homeware', 'embroidery_kit')
        else:
            return ('homeware', core_type or 'homeware')
    
    # Haberdashery items
    if any(term in name_lower for term in ['button', 'thread', 'needle', 'haberdashery']):
        return ('haberdashery', core_type or 'buttons')
    
    # Bags (should have been moved already, but check)
    if any(term in name_lower for term in ['tote bag', 'shopping bag']):
        return ('bags', core_type or 'tote_bag')
    
    # Keep as artwork (wall art)
    return ('artwork', core_type or 'artwork')

def clean_artwork_category():
    """
    Clean artwork category by moving non-wall-art items to appropriate categories.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all products currently in artwork category
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    sku,
                    product_type_data
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'artwork'
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} products in artwork category")
            
            moved_count = 0
            kept_count = 0
            by_new_category = {}
            
            for product in products:
                product_id = product['id']
                name = product['name']
                sku = product['sku']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                
                # Determine if it should stay or move
                new_form, new_core_type = determine_new_category(name, sku, current_core_type)
                
                if new_form == 'artwork':
                    # Keep as artwork
                    kept_count += 1
                    logger.debug(f"Keeping {name} as artwork")
                    continue
                
                # Move to new category
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
                logger.info(f"Moved {name} from artwork to {new_form}")
            
            conn.commit()
            logger.info(f"Cleanup complete. Moved {moved_count} products, kept {kept_count} as artwork.")
            
            # Show summary
            print(f"\n✅ Cleanup Summary:")
            print(f"   Kept as artwork: {kept_count} products")
            print(f"   Moved to other categories: {moved_count} products")
            print(f"\n   Distribution of moved products:")
            for category, count in sorted(by_new_category.items()):
                print(f"     - {category}: {count} products")
            
            # Verify final artwork count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'artwork'
            """)
            final_count = cursor.fetchone()['count']
            
            print(f"\n✅ Final artwork category: {final_count} products (wall art only)")
            
            return moved_count

if __name__ == '__main__':
    try:
        count = clean_artwork_category()
        print(f"\n✅ Successfully cleaned artwork category")
    except Exception as e:
        logger.error(f"Error cleaning artwork category: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

