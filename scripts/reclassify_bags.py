"""
Reclassify bag products to 'bags' category
Excludes pencil cases and wallets
Ensures appropriate core_type is set
"""

import sys
sys.path.insert(0, '.')
from config.database import db_manager
import json
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_bag_core_type(name, sku, current_core_type):
    """
    Determine appropriate core_type for a bag product.
    """
    name_lower = name.lower()
    sku_lower = sku.lower()
    
    # If already has a valid bag core_type, use it
    valid_bag_types = [
        'backpack', 'duffle_bag', 'gym_bag', 'tote_bag', 'shopping_bag',
        'crossbody_bag', 'bum_bag', 'clutch_bag', 'drawstring_bag',
        'bag', 'purse', 'handbag'
    ]
    
    if current_core_type and current_core_type in valid_bag_types:
        return current_core_type
    
    # Determine from name/sku
    if 'backpack' in name_lower or 'backpack' in sku_lower:
        return 'backpack'
    elif 'duffle' in name_lower or 'duffle' in sku_lower:
        return 'duffle_bag'
    elif 'gym' in name_lower and 'bag' in name_lower:
        return 'gym_bag'
    elif 'tote' in name_lower or 'tote' in sku_lower:
        return 'tote_bag'
    elif 'shopping' in name_lower and 'bag' in name_lower:
        return 'shopping_bag'
    elif 'crossbody' in name_lower or 'crossbody' in sku_lower:
        return 'crossbody_bag'
    elif 'bum' in name_lower and 'bag' in name_lower:
        return 'bum_bag'
    elif 'clutch' in name_lower or 'clutch' in sku_lower:
        return 'clutch_bag'
    elif 'drawstring' in name_lower or 'drawstring' in sku_lower:
        return 'drawstring_bag'
    elif 'handbag' in name_lower or 'handbag' in sku_lower:
        return 'handbag'
    elif 'purse' in name_lower or 'purse' in sku_lower:
        # Check if it's a purse mirror (not a bag)
        if 'mirror' in name_lower:
            return None  # Not a bag
        return 'purse'
    elif 'bag' in name_lower or 'bag' in sku_lower:
        return 'bag'  # Generic bag
    else:
        return 'bag'  # Default to generic bag

def reclassify_bags():
    """
    Reclassify bag products to 'bags' category.
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all bag products (excluding pencil cases and wallets)
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    sku,
                    product_type_data
                FROM clan_products
                WHERE (
                    -- Name/SKU contains bag terms
                    (name ILIKE '%bag%' OR sku ILIKE '%bag%')
                    OR (name ILIKE '%backpack%' OR sku ILIKE '%backpack%')
                    OR (name ILIKE '%tote%' OR sku ILIKE '%tote%')
                    OR (name ILIKE '%purse%' OR sku ILIKE '%purse%')
                    OR (name ILIKE '%clutch%' OR sku ILIKE '%clutch%')
                    OR (name ILIKE '%pouch%' OR sku ILIKE '%pouch%')
                    OR (name ILIKE '%duffle%' OR sku ILIKE '%duffle%')
                    OR (name ILIKE '%drawstring%' OR sku ILIKE '%drawstring%')
                    -- Core type contains bag terms
                    OR product_type_data->>'core_type' ILIKE '%bag%'
                    OR product_type_data->>'core_type' ILIKE '%pack%'
                    OR product_type_data->>'core_type' ILIKE '%purse%'
                    OR product_type_data->>'core_type' ILIKE '%pouch%'
                )
                -- Exclude pencil cases and wallets
                AND name NOT ILIKE '%pencil case%'
                AND name NOT ILIKE '%wallet%'
                AND sku NOT ILIKE '%pencil_case%'
                AND sku NOT ILIKE '%wallet%'
                AND product_type_data->>'core_type' NOT IN ('pencil_case', 'wallet')
                -- Exclude false positives
                AND name NOT ILIKE '%charm%'
                AND product_type_data->>'core_type' != 'charm'
                -- Exclude purse mirrors (they're not bags)
                AND name NOT ILIKE '%purse mirror%'
                AND name NOT ILIKE '%mirror%purse%'
            """)
            
            products = cursor.fetchall()
            logger.info(f"Found {len(products)} bag products to reclassify")
            
            updated_count = 0
            core_type_updates = 0
            
            for product in products:
                product_id = product['id']
                name = product['name']
                sku = product['sku']
                type_data = product['product_type_data'].copy() if product['product_type_data'] else {}
                current_core_type = type_data.get('core_type')
                
                # Determine appropriate core_type
                new_core_type = determine_bag_core_type(name, sku, current_core_type)
                
                # Skip if not actually a bag (e.g., purse mirror)
                if new_core_type is None:
                    logger.debug(f"Skipping {name} - not a bag")
                    continue
                
                # Update product_form to 'bags'
                type_data.setdefault('disambiguation', {})['product_form'] = 'bags'
                
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
                if updated_count % 10 == 0:
                    logger.info(f"Updated {updated_count} products...")
            
            conn.commit()
            logger.info(f"Reclassification complete. Updated {updated_count} products to 'bags' category.")
            logger.info(f"Updated core_type for {core_type_updates} products.")
            
            # Verify
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'bags'
            """)
            final_count = cursor.fetchone()['count']
            
            # Show distribution by core_type
            cursor.execute("""
                SELECT 
                    product_type_data->>'core_type' as core_type,
                    COUNT(*) as count
                FROM clan_products
                WHERE product_type_data->'disambiguation'->>'product_form' = 'bags'
                GROUP BY core_type
                ORDER BY count DESC
            """)
            
            by_type = cursor.fetchall()
            
            print(f"\n✅ Final 'bags' category: {final_count} products")
            print("\nDistribution by core_type:")
            for row in by_type:
                if row['core_type']:
                    print(f"  - {row['core_type']}: {row['count']} products")
            
            return updated_count

if __name__ == '__main__':
    try:
        count = reclassify_bags()
        print(f"\n✅ Successfully reclassified {count} products to 'bags' category")
    except Exception as e:
        logger.error(f"Error reclassifying bags: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

