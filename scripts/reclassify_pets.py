"""
Reclassify pet products to 'pets' category
Ensures appropriate core_type is set
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_pet_core_type(name, sku, current_core_type):
    """
    Determine appropriate core_type for a pet product.
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    
    # If already has a valid pet core_type, use it
    valid_pet_types = ['bandana', 'pet_bowl', 'treat_bag', 'collar', 'lead', 'leash']
    
    if current_core_type and current_core_type in valid_pet_types:
        return current_core_type
    
    # Determine from name/sku
    if 'bandana' in name_lower or 'bandana' in sku_lower:
        return 'bandana'
    elif 'bowl' in name_lower and ('pet' in name_lower or 'dog' in name_lower):
        return 'pet_bowl'
    elif 'treat' in name_lower and 'bag' in name_lower:
        return 'treat_bag'
    elif 'collar' in name_lower and ('dog' in name_lower or 'pet' in name_lower):
        return 'collar'
    elif 'lead' in name_lower and ('dog' in name_lower or 'pet' in name_lower):
        return 'lead'
    elif 'leash' in name_lower and ('dog' in name_lower or 'pet' in name_lower):
        return 'leash'
    else:
        return 'bandana'  # Default for dog bandanas

def reclassify_pets():
    """
    Reclassify pet products to 'pets' category.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all true pet products
            # Only include products that are clearly pet-related
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    sku,
                    product_type_data
                FROM clan_products
                WHERE (
                    -- Pet bowls
                    (name ILIKE '%pet bowl%' OR name ILIKE '%pet bowl mat%')
                    OR (name ILIKE '%bar runner%' AND (name ILIKE '%pet%' OR name ILIKE '%dog%'))
                    -- Dog bandanas (must have "dog" in name)
                    OR (name ILIKE '%dog bandana%' OR sku ILIKE '%dog%bandana%')
                    -- Treat bags
                    OR (name ILIKE '%treat bag%' AND (name ILIKE '%dog%' OR name ILIKE '%pet%'))
                    -- Core type is pet-related
                    OR product_type_data->>'core_type' = 'pet_bowl'
                    OR product_type_data->>'core_type' = 'bandana'
                )
                -- Exclude human bandanas (must have "dog" in name for bandanas)
                AND NOT (name ILIKE '%bandana%' AND name NOT ILIKE '%dog%' AND sku NOT ILIKE '%dog%')
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} pet products to reclassify")
            
            updated_count = 0
            core_type_updates = 0
            
            for product in products:
                product_id = product['id']
                name = product['name']
                sku = product['sku']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                current_form = type_data.get('disambiguation', {}).get('product_form')
                
                # Skip if already in pets category
                if current_form == 'pets':
                    logger.debug(f"Skipping {name} - already in pets category")
                    continue
                
                # Determine appropriate core_type
                new_core_type = determine_pet_core_type(name, sku, current_core_type)
                
                # Update product_form to 'pets'
                type_data.setdefault('disambiguation', {})['product_form'] = 'pets'
                
                # Update core_type if needed
                if current_core_type != new_core_type:
                    type_data['core_type'] = new_core_type
                    core_type_updates += 1
                    logger.debug(f"Product {product_id}: Updated core_type '{current_core_type}' -> '{new_core_type}'")
                
                # Update the product
                cursor.execute("""
                    UPDATE clan_products
                    SET product_type_data = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(type_data), product_id))
                
                updated_count += 1
                logger.info(f"Updated {name} to 'pets' category")
            
            conn.commit()
            logger.info(f"Reclassification complete. Updated {updated_count} products to 'pets' category.")
            logger.info(f"Updated core_type for {core_type_updates} products.")
            
            # Verify
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'pets'
            """)
            final_count = cursor.fetchone()['count']
            
            # Show distribution by core_type
            cursor.execute("""
                SELECT 
                    product_type_data->>'core_type' as core_type,
                    COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'pets'
                GROUP BY core_type
                ORDER BY count DESC
            """)
            
            by_type = cursor.fetchall()
            
            print(f"\n✅ Final 'pets' category: {final_count} products")
            print("\nDistribution by core_type:")
            for row in by_type:
                if row['core_type']:
                    print(f"  - {row['core_type']}: {row['count']} products")
            
            return updated_count

if __name__ == '__main__':
    try:
        count = reclassify_pets()
        print(f"\n✅ Successfully reclassified {count} products to 'pets' category")
    except Exception as e:
        logger.error(f"Error reclassifying pets: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

