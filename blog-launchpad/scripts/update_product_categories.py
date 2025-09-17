#!/usr/bin/env python3
"""
Update Product Categories Script
Fetches category associations from Clan.com API and updates the database
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

class ProductCategoryUpdater:
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
    
    def fetch_category_tree(self) -> Dict:
        """Fetch the complete category tree from Clan.com API"""
        logger.info("Fetching category tree from Clan.com API...")
        
        try:
            url = f"{self.api_base_url}/getCategoryTree"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success'):
                raise Exception(f"API returned error: {data}")
            
            categories = data.get('data', [])
            logger.info(f"Fetched {len(categories)} top-level categories")
            
            # Count total categories recursively
            total_categories = self.count_categories_recursive(categories)
            logger.info(f"Total categories in tree: {total_categories}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching category tree: {e}")
            return {'success': False, 'data': []}
    
    def count_categories_recursive(self, categories: List[Dict]) -> int:
        """Count total categories recursively"""
        count = len(categories)
        for category in categories:
            if 'children' in category and category['children']:
                count += self.count_categories_recursive(category['children'])
        return count
    
    def update_category_tree(self, category_data: Dict) -> bool:
        """Update the clan_categories table with the fetched category tree"""
        logger.info("Updating clan_categories table...")
        
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                
                # Clear existing categories
                cur.execute("DELETE FROM clan_categories")
                logger.info("Cleared existing categories")
                
                # Insert new categories
                categories = category_data.get('data', [])
                self.insert_categories_recursive(cur, categories, parent_id=None, level=1)
                
                conn.commit()
                logger.info("✅ Category tree updated successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error updating category tree: {e}")
            return False
    
    def insert_categories_recursive(self, cur, categories: List[Dict], parent_id: Optional[int], level: int):
        """Recursively insert categories into the database"""
        for category in categories:
            try:
                category_id = int(category.get('id', 0))
                name = category.get('name', '')
                url = category.get('url', '')
                description = category.get('description', '')
                
                cur.execute("""
                    INSERT INTO clan_categories (id, name, level, parent_id, url, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        level = EXCLUDED.level,
                        parent_id = EXCLUDED.parent_id,
                        url = EXCLUDED.url,
                        description = EXCLUDED.description
                """, (category_id, name, level, parent_id, url, description))
                
                # Process children recursively
                children = category.get('children', [])
                if children:
                    self.insert_categories_recursive(cur, children, category_id, level + 1)
                
            except Exception as e:
                logger.error(f"Error inserting category {category}: {e}")
    
    def fetch_all_products_with_categories(self) -> List[Dict]:
        """Fetch all products with category data from Clan.com API"""
        logger.info("Fetching all products with categories from Clan.com API...")
        
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
            
            # Now get detailed data for each product with categories
            detailed_products = []
            batch_size = 10  # Process in small batches to avoid rate limiting
            
            for i in range(0, len(basic_products), batch_size):
                batch = basic_products[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(basic_products) + batch_size - 1)//batch_size}")
                
                for product in batch:
                    if isinstance(product, list) and len(product) > 1:
                        sku = product[1]
                        try:
                            # Get detailed product data with categories
                            detail_url = f"{self.api_base_url}/getProductData"
                            detail_params = {
                                'sku': sku,
                                'include_categories': '1'
                            }
                            
                            detail_response = self.session.get(detail_url, params=detail_params, timeout=30)
                            detail_response.raise_for_status()
                            
                            detail_data = detail_response.json()
                            if detail_data.get('success') and detail_data.get('data'):
                                detailed_products.append(detail_data['data'])
                                logger.info(f"✅ Fetched category data for SKU: {sku}")
                            else:
                                logger.warning(f"⚠️ No category data for SKU: {sku}")
                            
                            # Rate limiting delay
                            time.sleep(0.5)
                            
                        except Exception as e:
                            logger.error(f"❌ Error fetching categories for SKU {sku}: {e}")
                            continue
                
                # Longer delay between batches
                time.sleep(1)
            
            logger.info(f"Successfully fetched category data for {len(detailed_products)} products")
            return detailed_products
            
        except Exception as e:
            logger.error(f"Error fetching products with categories: {e}")
            return []
    
    def update_product_categories(self, products: List[Dict]) -> Dict:
        """Update product categories in the database"""
        logger.info(f"Updating categories for {len(products)} products...")
        
        stats = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'no_categories': 0,
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
                        
                        # Get category IDs
                        category_ids = self.extract_category_ids(product)
                        
                        if not category_ids:
                            logger.warning(f"No categories found for SKU: {sku}")
                            stats['no_categories'] += 1
                            continue
                        
                        # Update the database
                        cur.execute("""
                            UPDATE clan_products 
                            SET category_ids = %s, last_updated = CURRENT_TIMESTAMP
                            WHERE sku = %s
                        """, (json.dumps(category_ids), sku))
                        
                        if cur.rowcount > 0:
                            stats['successful_updates'] += 1
                            logger.info(f"✅ Updated categories for SKU: {sku} - {category_ids}")
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
    
    def extract_category_ids(self, product: Dict) -> List[int]:
        """Extract category IDs from product data"""
        category_ids = []
        
        # Check for categories array
        categories = product.get('categories', [])
        if categories and isinstance(categories, list):
            for category in categories:
                if isinstance(category, dict) and category.get('id'):
                    try:
                        category_id = int(category['id'])
                        category_ids.append(category_id)
                    except (ValueError, TypeError):
                        continue
        
        return category_ids
    
    def run(self):
        """Main execution method"""
        logger.info("🚀 Starting product category update process...")
        
        # Step 1: Update category tree
        logger.info("Step 1: Updating category tree...")
        category_data = self.fetch_category_tree()
        if category_data.get('success'):
            self.update_category_tree(category_data)
        else:
            logger.error("❌ Failed to fetch category tree")
            return
        
        # Step 2: Fetch all products with categories
        logger.info("Step 2: Fetching products with categories...")
        products = self.fetch_all_products_with_categories()
        
        if not products:
            logger.error("❌ No products fetched from API")
            return
        
        # Step 3: Update product categories
        logger.info("Step 3: Updating product categories...")
        stats = self.update_product_categories(products)
        
        # Print summary
        logger.info("📊 CATEGORY UPDATE SUMMARY:")
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Successful updates: {stats['successful_updates']}")
        logger.info(f"Failed updates: {stats['failed_updates']}")
        logger.info(f"No categories found: {stats['no_categories']}")
        logger.info(f"Success rate: {(stats['successful_updates']/stats['total_processed']*100):.1f}%")
        
        if stats['errors']:
            logger.warning(f"Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info("✅ Product category update completed!")

if __name__ == "__main__":
    updater = ProductCategoryUpdater()
    updater.run()
