#!/usr/bin/env python3
"""
Representative Products Selector

Selects 4-8 representative products from a category using price diversity algorithm.
Priority: Price diversity first, then producer diversity, then material variety.
"""

import logging
from typing import List, Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

class RepresentativeProductsSelector:
    """Selects representative products for Category Profiles"""
    
    def __init__(self, db_connection):
        """
        Initialize selector with database connection.
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
    
    def select_representative_products(self, category_id: int, limit: int = 8) -> List[Dict]:
        """
        Select representative products for a category.
        
        Priority order:
        1. Price diversity (select across price tiers)
        2. Producer diversity (different producers)
        3. Material variety
        
        Args:
            category_id: Category ID from clan_categories
            limit: Maximum number of products to select (default: 8)
            
        Returns:
            List of product dictionaries with id, name, sku, price, image_url, url, supplier_name
        """
        try:
            # Get all products in category
            with self.db.cursor() as cur:
                cur.execute("""
                    SELECT id, name, sku, price, image_url, url, supplier_name
                    FROM clan_products
                    WHERE category_ids @> %s::jsonb
                      AND price IS NOT NULL
                      AND price::text != ''
                    ORDER BY CAST(price AS DECIMAL) ASC
                """, (f'[{category_id}]',))
                
                products = cur.fetchall()
            
            if not products:
                logger.warning(f"No products found for category {category_id}")
                return []
            
            logger.info(f"Found {len(products)} products in category {category_id}")
            
            # Convert to list of dicts and parse prices
            product_list = []
            for product in products:
                try:
                    price = float(product[3]) if product[3] else 0.0
                    product_dict = {
                        'id': product[0],
                        'name': product[1],
                        'sku': product[2],
                        'price': price,
                        'image_url': product[4],
                        'url': product[5],
                        'supplier_name': product[6]
                    }
                    product_list.append(product_dict)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing product {product[0]}: {e}")
                    continue
            
            if not product_list:
                return []
            
            # PRIORITY 1: Price diversity
            # Divide products into price tiers
            price_tiers = 3  # Low, Medium, High
            tier_size = max(1, len(product_list) // price_tiers)
            
            representatives = []
            seen_producers = set()
            
            # Select from each price tier
            for tier in range(price_tiers):
                tier_start = tier * tier_size
                tier_end = (tier + 1) * tier_size if tier < price_tiers - 1 else len(product_list)
                tier_products = product_list[tier_start:tier_end]
                
                # Within tier, prioritize producer diversity
                for product in tier_products:
                    if len(representatives) >= limit:
                        break
                    
                    producer = product.get('supplier_name')
                    if producer and producer not in seen_producers:
                        representatives.append(product)
                        seen_producers.add(producer)
                        logger.debug(f"Selected product {product['id']} from tier {tier} (producer: {producer})")
            
            # Fill remaining slots with diverse products (if we haven't reached limit)
            if len(representatives) < limit:
                remaining = [p for p in product_list if p not in representatives]
                # Prioritize products with different producers
                for product in remaining:
                    if len(representatives) >= limit:
                        break
                    producer = product.get('supplier_name')
                    if producer and producer not in seen_producers:
                        representatives.append(product)
                        seen_producers.add(producer)
                    elif not seen_producers:  # If no producer info, just add
                        representatives.append(product)
            
            # Final fallback: fill remaining slots
            if len(representatives) < limit:
                remaining = [p for p in product_list if p not in representatives]
                representatives.extend(remaining[:limit - len(representatives)])
            
            logger.info(f"Selected {len(representatives)} representative products (target: {limit})")
            return representatives
            
        except Exception as e:
            logger.error(f"Error selecting representative products for category {category_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_representative_products_for_category(self, category_id: int, limit: int = 8) -> List[Dict]:
        """
        Convenience method that wraps select_representative_products.
        
        Args:
            category_id: Category ID
            limit: Maximum number of products
            
        Returns:
            List of product dictionaries
        """
        return self.select_representative_products(category_id, limit)


def select_representative_products(category_id: int, limit: int = 8, db_connection=None) -> List[Dict]:
    """
    Convenience function to select representative products.
    
    Args:
        category_id: Category ID from clan_categories
        limit: Maximum number of products (default: 8)
        db_connection: Database connection (if None, will create new connection)
        
    Returns:
        List of product dictionaries
    """
    if db_connection is None:
        from config.database import db_manager
        db_connection = db_manager.get_connection()
    
    selector = RepresentativeProductsSelector(db_connection)
    return selector.select_representative_products(category_id, limit)


if __name__ == '__main__':
    # Test with a category ID
    import sys
    from config.database import db_manager
    
    if len(sys.argv) > 1:
        category_id = int(sys.argv[1])
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        
        conn = db_manager.get_connection()
        selector = RepresentativeProductsSelector(conn)
        products = selector.select_representative_products(category_id, limit)
        
        print(f"\nSelected {len(products)} representative products:")
        for product in products:
            print(f"  - {product['name']} (Producer: {product.get('supplier_name', 'N/A')}, Price: £{product['price']})")
    else:
        print("Usage: python representative_products_selector.py <category_id> [limit]")
        print("Example: python representative_products_selector.py 123 8")







