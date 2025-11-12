"""
Consolidate clothing-related product_form categories into a single 'clothing' category

Consolidates:
- garment (450 products)
- headwear (1 product)
- leisurewear (1 product)

Into: clothing (452 products total)
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consolidate_clothing_category():
    """
    Consolidate garment, headwear, and leisurewear into 'clothing'.
    Also update core_type for headwear and footwear products.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all products with clothing-related product_form
            cursor.execute("""
                SELECT id, name, sku, product_type_data
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' IN ('garment', 'headwear', 'leisurewear')
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} products to consolidate into 'clothing'")
            
            # Count by current category
            by_category = {}
            for product in products:
                current_form = product['product_type_data'].get('disambiguation', {}).get('product_form')
                if current_form not in by_category:
                    by_category[current_form] = 0
                by_category[current_form] += 1
            
            print("\nCurrent distribution:")
            for cat, count in sorted(by_category.items()):
                print(f"  - {cat}: {count} products")
            
            # Update all to 'clothing' and fix core_type where needed
            updated_count = 0
            core_type_updates = 0
            
            for product in products:
                product_id = product['id']
                product_name = product['name'].lower()
                sku = product['sku'].lower()
                current_form = product['product_type_data'].get('disambiguation', {}).get('product_form')
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                
                # Update product_form to 'clothing'
                type_data.setdefault('disambiguation', {})['product_form'] = 'clothing'
                
                # Update core_type for headwear and footwear
                if current_form == 'headwear':
                    # Set core_type to 'headwear'
                    type_data['core_type'] = 'headwear'
                    core_type_updates += 1
                    logger.debug(f"Product {product_id}: Set core_type to 'headwear'")
                elif current_form == 'leisurewear':
                    # Check if it's footwear (flip flops, etc.)
                    if any(term in product_name or term in sku for term in ['flip', 'flop', 'sandal', 'shoe', 'slipper']):
                        type_data['core_type'] = 'footwear'
                        core_type_updates += 1
                        logger.debug(f"Product {product_id}: Set core_type to 'footwear'")
                    else:
                        # Keep existing core_type or set to something appropriate
                        if not type_data.get('core_type'):
                            type_data['core_type'] = 'leisurewear'
                            core_type_updates += 1
                            logger.debug(f"Product {product_id}: Set core_type to 'leisurewear'")
                
                # Update the product
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(type_data), product_id))
                
                updated_count += 1
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} products...")
            
            conn.commit()
            logger.info(f"Consolidation complete. Updated {updated_count} products to 'clothing'.")
            logger.info(f"Updated core_type for {core_type_updates} products.")
            
            # Verify
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'clothing'
            """)
            final_count = cursor.fetchone()['count']
            
            # Check core_type updates
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->>'core_type' IN ('headwear', 'footwear')
            """)
            core_type_count = cursor.fetchone()['count']
            
            print(f"\n✅ Final 'clothing' category: {final_count} products")
            print(f"   (was: {sum(by_category.values())} products across {len(by_category)} categories)")
            print(f"✅ Products with core_type 'headwear' or 'footwear': {core_type_count}")
            
            return updated_count

if __name__ == '__main__':
    try:
        count = consolidate_clothing_category()
        print(f"\n✅ Successfully consolidated {count} products into 'clothing' category")
    except Exception as e:
        logger.error(f"Error consolidating clothing category: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

