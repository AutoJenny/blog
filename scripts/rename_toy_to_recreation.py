"""
Rename 'toy' category to 'recreation' and move leisure activity products to it
Includes: cuddly toys, jigsaws, embroidery kits, games, and other leisure activities
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_recreation_core_type(name, sku, current_core_type):
    """
    Determine appropriate core_type for recreation products.
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    core_type_lower = (current_core_type or '').lower()
    
    # Toys/teddies
    if any(term in name_lower for term in ['teddy', 'bear', 'cuddly', 'toy']):
        if 'teddy' in name_lower or 'bear' in name_lower:
            return 'teddy_bear'
        else:
            return 'toy'
    
    # Jigsaws/Puzzles
    if any(term in name_lower for term in ['jigsaw', 'puzzle']):
        return 'jigsaw'
    
    # Embroidery/Cross stitch
    if any(term in name_lower for term in ['embroidery', 'cross stitch']):
        return 'embroidery_kit'
    
    # Games
    if any(term in name_lower for term in ['game', 'board game']):
        return 'game'
    
    # Keep existing if it's recreation-related
    if current_core_type in ['toy', 'teddy', 'bear', 'jigsaw', 'puzzle', 'embroidery_kit', 'game']:
        return current_core_type
    
    # Default
    return 'toy'

def is_recreation_product(name, sku, core_type, current_form):
    """
    Determine if a product should be in recreation category.
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    core_type_lower = (core_type or '').lower()
    
    # Already in recreation
    if current_form == 'recreation':
        return False
    
    # Toys/teddies
    if any(term in name_lower or term in sku_lower for term in ['teddy', 'bear', 'cuddly', 'toy']):
        return True
    
    # Jigsaws/Puzzles
    if any(term in name_lower or term in sku_lower for term in ['jigsaw', 'puzzle']):
        return True
    
    # Embroidery/Cross stitch kits (but not finished embroidery art)
    if any(term in name_lower for term in ['embroidery kit', 'cross stitch kit', 'embroidery_kit']):
        return True
    
    # Games
    if any(term in name_lower or term in sku_lower for term in ['game', 'board game']):
        return True
    
    # Core type matches
    if core_type_lower in ['toy', 'teddy', 'bear', 'jigsaw', 'puzzle', 'embroidery_kit', 'game']:
        return True
    
    return False

def rename_toy_to_recreation():
    """
    Rename 'toy' category to 'recreation' and move leisure activity products.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # First, rename existing 'toy' products to 'recreation'
            cursor.execute("""
                SELECT id, name, product_type_data
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'toy'
            """)
            
            existing_toys = cursor.fetchall()
            logger.info(f"Found {len(existing_toys)} products currently in 'toy' category")
            
            for product in existing_toys:
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                type_data.setdefault('disambiguation', {})['product_form'] = 'recreation'
                
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(type_data), product['id']))
                
                logger.info(f"Renamed {product['name']} from 'toy' to 'recreation'")
            
            # Now find and move recreation products from other categories
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    sku,
                    product_type_data
                FROM clan_products
                WHERE (
                    name ILIKE '%toy%'
                    OR name ILIKE '%teddy%'
                    OR name ILIKE '%bear%'
                    OR name ILIKE '%cuddly%'
                    OR name ILIKE '%jigsaw%'
                    OR name ILIKE '%puzzle%'
                    OR name ILIKE '%embroidery kit%'
                    OR name ILIKE '%cross stitch kit%'
                    OR name ILIKE '%game%'
                    OR name ILIKE '%board game%'
                    OR product_type_data->>'core_type' IN ('toy', 'teddy', 'bear', 'jigsaw', 'puzzle', 'embroidery_kit', 'game')
                )
                AND product_type_data->'disambiguation'->>'product_form' != 'recreation'
            """)
            
            recreation_products = cursor.fetchall()
            logger.info(f"Found {len(recreation_products)} potential recreation products in other categories")
            
            moved_count = 0
            by_original_category = {}
            
            for product in recreation_products:
                product_id = product['id']
                name = product['name']
                sku = product['sku']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                current_form = type_data.get('disambiguation', {}).get('product_form')
                
                # Check if it should be recreation
                if not is_recreation_product(name, sku, current_core_type, current_form):
                    continue
                
                # Determine appropriate core_type
                new_core_type = determine_recreation_core_type(name, sku, current_core_type)
                
                # Update product_form to 'recreation'
                type_data.setdefault('disambiguation', {})['product_form'] = 'recreation'
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
                logger.info(f"Moved {name} from {current_form} to recreation")
            
            conn.commit()
            logger.info(f"Rename and move complete. Renamed {len(existing_toys)} products, moved {moved_count} products to recreation.")
            
            # Show summary
            print(f"\n✅ Recreation Category Summary:")
            print(f"   Renamed from 'toy': {len(existing_toys)} products")
            print(f"   Moved from other categories: {moved_count} products")
            print(f"   Total in recreation: {len(existing_toys) + moved_count} products")
            print(f"\n   Moved from categories:")
            for category, count in sorted(by_original_category.items()):
                print(f"     - {category}: {count} products")
            
            # Verify final recreation count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'recreation'
            """)
            final_count = cursor.fetchone()['count']
            
            # Show distribution by core_type
            cursor.execute("""
                SELECT 
                    product_type_data->>'core_type' as core_type,
                    COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'recreation'
                GROUP BY core_type
                ORDER BY count DESC
            """)
            
            by_type = cursor.fetchall()
            
            print(f"\n✅ Final recreation category: {final_count} products")
            print("\nDistribution by core_type:")
            for row in by_type:
                if row['core_type']:
                    print(f"  - {row['core_type']}: {row['count']} products")
            
            return len(existing_toys) + moved_count

if __name__ == '__main__':
    try:
        count = rename_toy_to_recreation()
        print(f"\n✅ Successfully renamed 'toy' to 'recreation' and moved {count} products")
    except Exception as e:
        logger.error(f"Error renaming toy to recreation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

