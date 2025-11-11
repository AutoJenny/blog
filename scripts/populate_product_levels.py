#!/usr/bin/env python3
"""
Populate Product Levels

Parses product names and populates the product_level column in clan_products table.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
from utils.product_level import parse_product_level
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_all_product_levels():
    """
    Parse all product names and update product_level column.
    """
    updated_count = 0
    classic_count = 0
    luxury_count = 0
    essential_count = 0
    
    with db_manager.get_cursor() as cursor:
        # Get all products
        cursor.execute("""
            SELECT id, name, product_level
            FROM clan_products
            ORDER BY id
        """)
        
        products = cursor.fetchall()
        logger.info(f"Found {len(products)} products to process")
        
        for product in products:
            product_id = product['id']
            product_name = product.get('name', '')
            current_level = product.get('product_level', 'classic')
            
            # Parse level from name
            new_level = parse_product_level(product_name)
            
            # Update if different
            if new_level != current_level:
                cursor.execute("""
                    UPDATE clan_products
                    SET product_level = %s
                    WHERE id = %s
                """, (new_level, product_id))
                
                updated_count += 1
                logger.debug(f"Updated product {product_id} ({product_name[:50]}): {current_level} → {new_level}")
            
            # Count by level
            if new_level == 'classic':
                classic_count += 1
            elif new_level == 'luxury':
                luxury_count += 1
            elif new_level == 'essential':
                essential_count += 1
    
    logger.info(f"\nProduct Level Summary:")
    logger.info(f"  Classic: {classic_count}")
    logger.info(f"  Luxury: {luxury_count}")
    logger.info(f"  Essential: {essential_count}")
    logger.info(f"  Updated: {updated_count} products")
    
    return {
        'total': len(products),
        'updated': updated_count,
        'classic': classic_count,
        'luxury': luxury_count,
        'essential': essential_count
    }


if __name__ == '__main__':
    print("Populating product levels...")
    results = populate_all_product_levels()
    print(f"\nDone! Updated {results['updated']} of {results['total']} products.")
    print(f"Distribution: Classic={results['classic']}, Luxury={results['luxury']}, Essential={results['essential']}")

