"""
Normalize product tag spellings in product_type_data

Fixes:
- jewelry -> jewellery (UK spelling)
- homewares -> homeware
- Homeware -> homeware
- Jewelry -> jewellery
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_product_tags():
    """
    Normalize tag spellings in product_type_data.
    Updates products in place.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all products with product_type_data
            cursor.execute("""
                SELECT id, name, product_type_data
                FROM clan_products
                WHERE product_type_data IS NOT NULL
            """)
            
            products = cursor.fetchall()
            logger.info(f"Processing {len(products)} products...")
            
            updated_count = 0
            
            for product in products:
                product_id = product['id']
                product_name = product['name']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                updated = False
                
                # Fix product_form - normalize spelling and case
                if type_data.get('disambiguation') and isinstance(type_data['disambiguation'], dict):
                    product_form = type_data['disambiguation'].get('product_form')
                    if product_form:
                        original = product_form
                        normalized = product_form.lower()
                        
                        # Normalize spelling first
                        if normalized == 'jewelry':
                            normalized = 'jewellery'
                        elif normalized == 'homewares':
                            normalized = 'homeware'
                        
                        # Apply normalization
                        if normalized != original.lower():
                            type_data['disambiguation']['product_form'] = normalized
                            updated = True
                            logger.debug(f"Product {product_id}: Changed product_form '{original}' -> '{normalized}'")
                        # Also fix case variations (e.g., "Jewellery" -> "jewellery")
                        elif product_form != normalized:
                            type_data['disambiguation']['product_form'] = normalized
                            updated = True
                            logger.debug(f"Product {product_id}: Changed product_form case '{original}' -> '{normalized}'")
                
                # Fix arrays (materials, patterns, decorations, occasions, styles)
                array_fields = ['materials', 'patterns', 'decorations', 'occasions', 'styles']
                for field in array_fields:
                    if type_data.get(field) and isinstance(type_data[field], list):
                        new_array = []
                        for item in type_data[field]:
                            if item:
                                # Normalize jewellery/jewelry
                                if item.lower() == 'jewelry':
                                    new_array.append('jewellery')
                                    updated = True
                                    logger.debug(f"Product {product_id}: Changed {field} 'jewelry' -> 'jewellery'")
                                elif item == 'Jewelry':
                                    new_array.append('jewellery')
                                    updated = True
                                    logger.debug(f"Product {product_id}: Changed {field} 'Jewelry' -> 'jewellery'")
                                # Normalize homeware variations
                                elif item.lower() == 'homewares':
                                    new_array.append('homeware')
                                    updated = True
                                    logger.debug(f"Product {product_id}: Changed {field} 'homewares' -> 'homeware'")
                                elif item == 'Homeware':
                                    new_array.append('homeware')
                                    updated = True
                                    logger.debug(f"Product {product_id}: Changed {field} 'Homeware' -> 'homeware'")
                                else:
                                    new_array.append(item)
                            else:
                                new_array.append(item)
                        type_data[field] = new_array
                
                # Update database if changes were made
                if updated:
                    cursor.execute("""
                        UPDATE clan_products
                        SET product_type_data = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(type_data), product_id))
                    updated_count += 1
                    if updated_count % 50 == 0:
                        logger.info(f"Updated {updated_count} products so far...")
            
            conn.commit()
            logger.info(f"Normalization complete. Updated {updated_count} products.")
            return updated_count

if __name__ == '__main__':
    try:
        count = normalize_product_tags()
        print(f"\n✅ Successfully normalized tags in {count} products")
    except Exception as e:
        logger.error(f"Error normalizing tags: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

