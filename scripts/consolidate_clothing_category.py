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
            
            # Update all to 'clothing'
            updated_count = 0
            for product in products:
                product_id = product['id']
                current_form = product['product_type_data'].get('disambiguation', {}).get('product_form')
                
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = jsonb_set(
                        product_type_data,
                        '{disambiguation,product_form}',
                        %s::jsonb
                    )
                    WHERE id = %s
                """, (json.dumps('clothing'), product_id))
                
                updated_count += 1
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} products...")
            
            conn.commit()
            logger.info(f"Consolidation complete. Updated {updated_count} products to 'clothing'.")
            
            # Verify
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'clothing'
            """)
            final_count = cursor.fetchone()['count']
            
            print(f"\n✅ Final 'clothing' category: {final_count} products")
            print(f"   (was: {sum(by_category.values())} products across {len(by_category)} categories)")
            
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

