"""
Move wall art items from other categories to artwork category
Searches clothing, accessories, homeware, etc. for paintings, prints, plaques, maps
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_artwork_core_type(name, sku, current_core_type):
    """
    Determine appropriate core_type for wall art.
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    
    # If already has a valid artwork core_type, use it
    valid_artwork_types = ['painting', 'print', 'plaque', 'map', 'picture', 'poster', 'canvas']
    
    if current_core_type and current_core_type in valid_artwork_types:
        return current_core_type
    
    # Determine from name/sku
    if 'painting' in name_lower or 'painting' in sku_lower:
        return 'painting'
    elif 'print' in name_lower or 'print' in sku_lower:
        return 'print'
    elif 'plaque' in name_lower or 'plaque' in sku_lower:
        return 'plaque'
    elif 'map' in name_lower or 'map' in sku_lower:
        return 'map'
    elif 'picture' in name_lower or 'picture' in sku_lower:
        return 'picture'
    elif 'poster' in name_lower or 'poster' in sku_lower:
        return 'poster'
    elif 'canvas' in name_lower or 'canvas' in sku_lower:
        return 'canvas'
    else:
        return 'artwork'  # Default

def is_false_positive(name, sku):
    """
    Check if a product is a false positive (not actually wall art).
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    
    # False positives: print fabric, map pocket, picture frame (empty), canvas bag
    false_positive_patterns = [
        ('print' in name_lower and ('shirt' in name_lower or 'fabric' in name_lower or 'material' in name_lower)),
        ('map' in name_lower and ('pocket' in name_lower or 'bag' in name_lower)),
        ('picture' in name_lower and 'frame' in name_lower and 'empty' in name_lower),
        ('canvas' in name_lower and ('bag' in name_lower or 'fabric' in name_lower)),
    ]
    
    return any(false_positive_patterns)

def move_wall_art_to_artwork():
    """
    Move wall art items from other categories to artwork.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all potential wall art products (excluding those already in artwork)
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    sku,
                    product_type_data
                FROM clan_products
                WHERE (
                    name ILIKE '%painting%'
                    OR name ILIKE '%print%'
                    OR name ILIKE '%plaque%'
                    OR name ILIKE '%map%'
                    OR name ILIKE '%picture%'
                    OR name ILIKE '%poster%'
                    OR name ILIKE '%canvas%'
                    OR name ILIKE '%wall art%'
                    OR name ILIKE '%framed%'
                    OR product_type_data->>'core_type' IN ('painting', 'print', 'plaque', 'map', 'picture', 'poster', 'canvas')
                )
                AND product_type_data->'disambiguation'->>'product_form' != 'artwork'
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} potential wall art products")
            
            moved_count = 0
            skipped_count = 0
            by_original_category = {}
            
            for product in products:
                product_id = product['id']
                name = product['name']
                sku = product['sku']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                current_form = type_data.get('disambiguation', {}).get('product_form')
                
                # Skip false positives
                if is_false_positive(name, sku):
                    skipped_count += 1
                    logger.debug(f"Skipping false positive: {name}")
                    continue
                
                # Determine appropriate core_type
                new_core_type = determine_artwork_core_type(name, sku, current_core_type)
                
                # Update product_form to 'artwork'
                type_data.setdefault('disambiguation', {})['product_form'] = 'artwork'
                type_data['core_type'] = new_core_type
                
                if current_form not in by_original_category:
                    by_original_category[current_form] = 0
                by_original_category[current_form] += 1
                
                # Update the product
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(type_data), product_id))
                
                moved_count += 1
                logger.info(f"Moved {name} from {current_form} to artwork")
            
            conn.commit()
            logger.info(f"Move complete. Moved {moved_count} products to artwork, skipped {skipped_count} false positives.")
            
            # Show summary
            print(f"\n✅ Move Summary:")
            print(f"   Moved to artwork: {moved_count} products")
            print(f"   Skipped (false positives): {skipped_count} products")
            print(f"\n   Moved from categories:")
            for category, count in sorted(by_original_category.items()):
                print(f"     - {category}: {count} products")
            
            # Verify final artwork count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'artwork'
            """)
            final_count = cursor.fetchone()['count']
            
            print(f"\n✅ Final artwork category: {final_count} products")
            
            return moved_count

if __name__ == '__main__':
    try:
        count = move_wall_art_to_artwork()
        print(f"\n✅ Successfully moved {count} products to artwork category")
    except Exception as e:
        logger.error(f"Error moving wall art: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

