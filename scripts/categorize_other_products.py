"""
Categorize products currently marked as 'other' in product_form

Categories:
- stationery (4 products)
- bags (2 products - already exists)
- pets (1 product - already exists)
- voucher (1 product)
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def categorize_other_products():
    """
    Categorize products with product_form = 'other' based on their names/types.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all products with product_form = 'other'
            cursor.execute("""
                SELECT id, name, sku, product_type_data
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'other'
                ORDER BY name
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} products with product_form = 'other'")
            
            # Categorization rules based on product name/type
            categorizations = {}
            
            for product in products:
                product_id = product['id']
                product_name = product['name'].lower()
                sku = product['sku'].lower()
                core_type = product['product_type_data'].get('core_type', '').lower() if product['product_type_data'] else ''
                
                # Determine category
                category = None
                
                # Stationery (4 products)
                if any(term in product_name for term in ['notebook', 'pen', 'pencil', 'stationery', 'writing', 'journal', 'diary']):
                    category = 'stationery'
                elif any(term in sku for term in ['notebook', 'pen', 'pencil', 'stationery', 'writing']):
                    category = 'stationery'
                
                # Bags (2 products)
                elif any(term in product_name for term in ['bag', 'tote', 'carry', 'pouch']):
                    category = 'bags'
                elif any(term in sku for term in ['bag', 'tote', 'carry']):
                    category = 'bags'
                elif core_type in ['bag', 'backpack', 'tote']:
                    category = 'bags'
                
                # Pets (1 product)
                elif any(term in product_name for term in ['pet', 'dog', 'cat', 'animal']):
                    category = 'pets'
                elif any(term in sku for term in ['pet', 'dog', 'cat']):
                    category = 'pets'
                
                # Voucher (1 product)
                elif any(term in product_name for term in ['voucher', 'gift card', 'gift certificate']):
                    category = 'voucher'
                elif any(term in sku for term in ['voucher', 'gift']):
                    category = 'voucher'
                
                if category:
                    categorizations[product_id] = {
                        'name': product['name'],
                        'sku': product['sku'],
                        'category': category
                    }
                else:
                    logger.warning(f"Could not categorize product {product_id}: {product['name']}")
            
            # Update products
            updated_count = 0
            for product_id, info in categorizations.items():
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = jsonb_set(
                        product_type_data,
                        '{disambiguation,product_form}',
                        %s::jsonb
                    )
                    WHERE id = %s
                """, (json.dumps(info['category']), product_id))
                
                logger.info(f"Product {product_id} ({info['name']}): 'other' -> '{info['category']}'")
                updated_count += 1
            
            conn.commit()
            logger.info(f"Categorization complete. Updated {updated_count} products.")
            
            # Show summary
            print("\n" + "="*80)
            print("Categorization Summary:")
            print("="*80)
            by_category = {}
            for info in categorizations.values():
                cat = info['category']
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(info['name'])
            
            for cat, names in sorted(by_category.items()):
                print(f"\n{cat.upper()} ({len(names)} products):")
                for name in names:
                    print(f"  - {name}")
            
            return updated_count

if __name__ == '__main__':
    try:
        count = categorize_other_products()
        print(f"\n✅ Successfully categorized {count} products")
    except Exception as e:
        logger.error(f"Error categorizing products: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

