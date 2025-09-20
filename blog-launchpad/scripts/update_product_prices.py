#!/usr/bin/env python3
"""
Update Product Prices Script
Fetches real product prices from Clan.com API and updates the database
"""

import requests
import json
import time
import psycopg2
from psycopg2.extras import DictCursor
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductPriceUpdater:
    def __init__(self):
        self.api_base_url = "https://clan.com/clan/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.db_config = {
            'host': 'localhost',
            'database': 'blog',
            'user': 'postgres',
            'password': 'postgres'
        }
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def fetch_all_products_with_prices(self) -> List[Dict]:
        """Fetch all products with price data from Clan.com API"""
        logger.info("Fetching all products with prices from Clan.com API...")
        
        try:
            # First, get all basic products
            basic_url = f"{self.api_base_url}/getProducts"
            params = {'limit': 10000}  # Get all products
            
            logger.info(f"Fetching basic product list from {basic_url}")
            response = self.session.get(basic_url, params=params, timeout=30)
            response.raise_for_status()
            
            basic_data = response.json()
            if not basic_data.get('success'):
                raise Exception(f"API returned error: {basic_data}")
            
            basic_products = basic_data.get('data', [])
            logger.info(f"Fetched {len(basic_products)} basic products")
            
            # Now get detailed data for each product with prices
            detailed_products = []
            batch_size = 10  # Process in small batches to avoid rate limiting
            
            for i in range(0, len(basic_products), batch_size):
                batch = basic_products[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(basic_products) + batch_size - 1)//batch_size}")

                for product in batch:
                    # Handle new API format - product is now a dict, not a list
                    if isinstance(product, dict):
                        sku = product.get('sku')
                    elif isinstance(product, list) and len(product) > 1:
                        sku = product[1]  # Fallback for old format
                    else:
                        logger.warning(f"Unexpected product format: {product}")
                        continue
                    
                    try:
                            # Get detailed product data with price
                            detail_url = f"{self.api_base_url}/getProductData"
                            detail_params = {
                                'sku': sku
                            }
                            
                            detail_response = self.session.get(detail_url, params=detail_params, timeout=30)
                            detail_response.raise_for_status()
                            
                            detail_data = detail_response.json()
                            if detail_data.get('success') and detail_data.get('data'):
                                detailed_products.append(detail_data['data'])
                                logger.info(f"✅ Fetched price data for SKU: {sku}")
                            else:
                                logger.warning(f"⚠️ No price data for SKU: {sku}")
                            
                            # Rate limiting delay
                            time.sleep(0.5)
                            
                        except Exception as e:
                            logger.error(f"❌ Error fetching price for SKU {sku}: {e}")
                            continue
                
                # Longer delay between batches
                time.sleep(1)
            
            logger.info(f"Successfully fetched price data for {len(detailed_products)} products")
            return detailed_products
            
        except Exception as e:
            logger.error(f"Error fetching products with prices: {e}")
            return []
    
    def update_product_prices(self, products: List[Dict]) -> Dict:
        """Update product prices in the database"""
        logger.info(f"Updating prices for {len(products)} products...")
        
        stats = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'no_prices': 0,
            'errors': []
        }
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                
                for product in products:
                    stats['total_processed'] += 1
                    
                    try:
                        sku = product.get('sku')
                        if not sku:
                            logger.warning(f"Product missing SKU: {product}")
                            stats['failed_updates'] += 1
                            continue
                        
                        # Get the price
                        price = product.get('price')
                        
                        if not price or price == 0:
                            logger.warning(f"No price found for SKU: {sku}")
                            stats['no_prices'] += 1
                            continue
                        
                        # Convert price to string with 2 decimal places
                        price_str = f"{price:.2f}"
                        
                        # Update the database
                        cur.execute("""
                            UPDATE clan_products 
                            SET price = %s, last_updated = CURRENT_TIMESTAMP
                            WHERE sku = %s
                        """, (price_str, sku))
                        
                        if cur.rowcount > 0:
                            stats['successful_updates'] += 1
                            logger.info(f"✅ Updated price for SKU: {sku} - £{price_str}")
                        else:
                            logger.warning(f"⚠️ No product found with SKU: {sku}")
                            stats['failed_updates'] += 1
                        
                        # Commit every 50 updates
                        if stats['total_processed'] % 50 == 0:
                            conn.commit()
                            logger.info(f"Committed {stats['total_processed']} updates so far...")
                    
                    except Exception as e:
                        logger.error(f"❌ Error updating product {product.get('sku', 'unknown')}: {e}")
                        stats['failed_updates'] += 1
                        stats['errors'].append(str(e))
                
                # Final commit
                conn.commit()
                logger.info("Final commit completed")
        
        except Exception as e:
            logger.error(f"Database error: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    def fetch_products_by_sku(self, skus: List[str]) -> List[Dict]:
        """Fetch specific products by SKU from Clan.com API"""
        logger.info(f"Fetching {len(skus)} products by SKU from Clan.com API...")
        
        products = []
        for sku in skus:
            try:
                # Get detailed product data with price
                detail_url = f"{self.api_base_url}/getProductData"
                detail_params = {
                    'sku': sku
                }
                
                detail_response = self.session.get(detail_url, params=detail_params, timeout=30)
                detail_response.raise_for_status()
                
                detail_data = detail_response.json()
                if detail_data.get('success') and detail_data.get('data'):
                    products.append(detail_data['data'])
                    logger.info(f"✅ Fetched price data for SKU: {sku}")
                else:
                    logger.warning(f"⚠️ No price data for SKU: {sku}")
                
                # Rate limiting delay
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error fetching price for SKU {sku}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(products)} products by SKU")
        return products
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting product price update process...")
        
        # Fetch all products with prices
        products = self.fetch_all_products_with_prices()
        
        if not products:
            logger.error("❌ No products fetched from API")
            return
        
        # Update database
        stats = self.update_product_prices(products)
        
        # Print summary
        logger.info("📊 PRICE UPDATE SUMMARY:")
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Successful updates: {stats['successful_updates']}")
        logger.info(f"Failed updates: {stats['failed_updates']}")
        logger.info(f"No prices found: {stats['no_prices']}")
        logger.info(f"Success rate: {(stats['successful_updates']/stats['total_processed']*100):.1f}%")
        
        if stats['errors']:
            logger.warning(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info("✅ Product price update completed!")

if __name__ == "__main__":
    updater = ProductPriceUpdater()
    updater.run()


