#!/usr/bin/env python3
"""
Update Product Images Script
Fetches real product images from Clan.com API and updates the database
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

class ProductImageUpdater:
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
    
    def fetch_all_products_with_images(self) -> List[Dict]:
        """Fetch all products with image data from Clan.com API"""
        logger.info("Fetching all products with images from Clan.com API...")
        
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
            
            # Now get detailed data for each product with images
            detailed_products = []
            batch_size = 10  # Process in small batches to avoid rate limiting
            
            for i in range(0, len(basic_products), batch_size):
                batch = basic_products[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(basic_products) + batch_size - 1)//batch_size}")
                
                for product in batch:
                    if isinstance(product, list) and len(product) > 1:
                        sku = product[1]
                        try:
                            # Get detailed product data with images
                            detail_url = f"{self.api_base_url}/getProductData"
                            detail_params = {
                                'sku': sku,
                                'all_images': '1'
                            }
                            
                            detail_response = self.session.get(detail_url, params=detail_params, timeout=30)
                            detail_response.raise_for_status()
                            
                            detail_data = detail_response.json()
                            if detail_data.get('success') and detail_data.get('data'):
                                detailed_products.append(detail_data['data'])
                                logger.info(f"✅ Fetched detailed data for SKU: {sku}")
                            else:
                                logger.warning(f"⚠️ No detailed data for SKU: {sku}")
                            
                            # Rate limiting delay
                            time.sleep(0.5)
                            
                        except Exception as e:
                            logger.error(f"❌ Error fetching details for SKU {sku}: {e}")
                            continue
                
                # Longer delay between batches
                time.sleep(1)
            
            logger.info(f"Successfully fetched detailed data for {len(detailed_products)} products")
            return detailed_products
            
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    def update_product_images(self, products: List[Dict]) -> Dict:
        """Update product images in the database"""
        logger.info(f"Updating images for {len(products)} products...")
        
        stats = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'no_images': 0,
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
                        
                        # Get the best image URL
                        image_url = self.get_best_image_url(product)
                        
                        if not image_url:
                            logger.warning(f"No images found for SKU: {sku}")
                            stats['no_images'] += 1
                            continue
                        
                        # Update the database
                        cur.execute("""
                            UPDATE clan_products 
                            SET image_url = %s, last_updated = CURRENT_TIMESTAMP
                            WHERE sku = %s
                        """, (image_url, sku))
                        
                        if cur.rowcount > 0:
                            stats['successful_updates'] += 1
                            logger.info(f"✅ Updated image for SKU: {sku}")
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
                # Get detailed product data with images
                detail_url = f"{self.api_base_url}/getProductData"
                detail_params = {
                    'sku': sku,
                    'all_images': '1'
                }
                
                detail_response = self.session.get(detail_url, params=detail_params, timeout=30)
                detail_response.raise_for_status()
                
                detail_data = detail_response.json()
                if detail_data.get('success') and detail_data.get('data'):
                    products.append(detail_data['data'])
                    logger.info(f"✅ Fetched data for SKU: {sku}")
                else:
                    logger.warning(f"⚠️ No data for SKU: {sku}")
                
                # Rate limiting delay
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error fetching SKU {sku}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(products)} products by SKU")
        return products
    
    def get_best_image_url(self, product: Dict) -> Optional[str]:
        """Get the best available image URL from product data"""
        # Try different image sources in order of preference
        
        # 1. Check for main product image
        if product.get('image') and not 'essential.jpg' in product.get('image', ''):
            return product['image']
        
        # 2. Check images array for the first good image
        images = product.get('images', [])
        if images and isinstance(images, list):
            for img in images:
                if isinstance(img, dict) and img.get('url'):
                    img_url = img['url']
                    if not 'essential.jpg' in img_url and 'static.clan.com' in img_url:
                        return img_url
        
        # 3. Check for any image in the images array
        if images and isinstance(images, list):
            for img in images:
                if isinstance(img, dict) and img.get('url'):
                    img_url = img['url']
                    if 'static.clan.com' in img_url:
                        return img_url
        
        return None
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting product image update process...")
        
        # Fetch all products with images
        products = self.fetch_all_products_with_images()
        
        if not products:
            logger.error("❌ No products fetched from API")
            return
        
        # Update database
        stats = self.update_product_images(products)
        
        # Print summary
        logger.info("📊 UPDATE SUMMARY:")
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Successful updates: {stats['successful_updates']}")
        logger.info(f"Failed updates: {stats['failed_updates']}")
        logger.info(f"No images found: {stats['no_images']}")
        logger.info(f"Success rate: {(stats['successful_updates']/stats['total_processed']*100):.1f}%")
        
        if stats['errors']:
            logger.warning(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info("✅ Product image update completed!")

if __name__ == "__main__":
    updater = ProductImageUpdater()
    updater.run()
