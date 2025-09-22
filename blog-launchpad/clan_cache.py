#!/usr/bin/env python3
"""
Clan.com data caching system
Stores products and categories in PostgreSQL for fast access
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

class ClanCache:
    """PostgreSQL cache for clan.com data"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'dbname': 'blog',
            'user': 'autojenny',
            'password': ''
        }
        self.init_database()
    
    def get_db_conn(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config)
    
    def init_database(self):
        """Initialize the database tables"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clan_products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    sku TEXT UNIQUE NOT NULL,
                    price TEXT,
                    image_url TEXT,
                    url TEXT,
                    description TEXT,
                    category_ids JSONB,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clan_categories (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    level INTEGER DEFAULT 0,
                    parent_id INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Cache metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clan_cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def is_cache_fresh(self, cache_type: str, max_age_hours: int = 24) -> bool:
        """Check if cache is fresh (not older than max_age_hours)"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT last_updated FROM clan_cache_metadata 
                WHERE key = %s
            ''', (f'{cache_type}_last_update',))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            last_update = result[0]
            return datetime.now() - last_update < timedelta(hours=max_age_hours)
    
    def update_cache_timestamp(self, cache_type: str):
        """Update the cache timestamp"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clan_cache_metadata (key, value, last_updated)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET 
                    value = EXCLUDED.value,
                    last_updated = EXCLUDED.last_updated
            ''', (f'{cache_type}_last_update', datetime.now().isoformat(), datetime.now()))
            conn.commit()
    
    def store_products(self, products: List[Dict]):
        """Store products in PostgreSQL cache"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Clear existing products
            cursor.execute('DELETE FROM clan_products')
            
            # Insert new products
            for product in products:
                cursor.execute('''
                    INSERT INTO clan_products (id, name, sku, price, image_url, url, description, category_ids, printable_design_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        sku = EXCLUDED.sku,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        url = EXCLUDED.url,
                        description = EXCLUDED.description,
                        category_ids = EXCLUDED.category_ids,
                        printable_design_type = EXCLUDED.printable_design_type
                ''', (
                    product.get('product_id') or product.get('id'),  # Handle both new and old API formats
                    product.get('title') or product.get('name'),     # Handle both new and old API formats
                    product.get('sku'),
                    product.get('price'),
                    product.get('image') or product.get('image_url'),  # Handle both new and old API formats
                    product.get('product_url') or product.get('url'),  # Handle both new and old API formats
                    product.get('description'),
                    json.dumps(product.get('category_ids', [])),
                    product.get('printable_design_type')
                ))
            
            conn.commit()
            self.update_cache_timestamp('products')
            logger.info(f"Stored {len(products)} products in PostgreSQL cache")
    
    def store_categories(self, categories: List[Dict]):
        """Store categories in PostgreSQL cache"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Clear existing categories
            cursor.execute('DELETE FROM clan_categories')
            
            # Insert new categories
            for category in categories:
                cursor.execute('''
                    INSERT INTO clan_categories (id, name, description, level, parent_id)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    category.get('id'),
                    category.get('name'),
                    category.get('description'),
                    category.get('level', 0),
                    category.get('parent_id')
                ))
            
            conn.commit()
            self.update_cache_timestamp('categories')
            logger.info(f"Stored {len(categories)} categories in PostgreSQL cache")
    
    def get_products(self, limit: Optional[int] = None, query: str = '') -> List[Dict]:
        """Get products from PostgreSQL cache"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            sql = 'SELECT id, name, sku, price, image_url, url, description, category_ids FROM clan_products'
            params = []
            
            if query:
                sql += ' WHERE name ILIKE %s OR description ILIKE %s'
                params.extend([f'%{query}%', f'%{query}%'])
            
            sql += ' ORDER BY name'
            
            if limit:
                sql += f' LIMIT {limit}'
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            products = []
            for row in rows:
                products.append({
                    'id': row['id'],
                    'name': row['name'],
                    'sku': row['sku'],
                    'price': row['price'],
                    'image_url': row['image_url'],
                    'url': row['url'],
                    'description': row['description'],
                    'category_ids': row['category_ids'] if row['category_ids'] else []
                })
            
            return products
    
    def get_categories(self) -> List[Dict]:
        """Get categories from PostgreSQL cache"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT id, name, description, level, parent_id 
                FROM clan_categories 
                ORDER BY level, name
            ''')
            
            rows = cursor.fetchall()
            categories = []
            for row in rows:
                categories.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'level': row['level'],
                    'parent_id': row['parent_id']
                })
            
            return categories
    
    def get_random_products(self, count: int = 3, offset: int = 0) -> List[Dict]:
        """Get random products from PostgreSQL cache with offset-based variety"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Simple random selection - offset will be handled by different random seeds
            cursor.execute('''
                SELECT id, name, sku, price, image_url, url, description, category_ids 
                FROM clan_products 
                ORDER BY RANDOM() 
                LIMIT %s
            ''', (count,))
            
            rows = cursor.fetchall()
            products = []
            for row in rows:
                products.append({
                    'id': row.get('id', 0),
                    'name': row.get('name', 'Product Name'),
                    'sku': row.get('sku', ''),
                    'price': row.get('price', '29.99'),
                    'image_url': row.get('image_url', 'https://static.clan.com/media/catalog/product/cache/5/image/9df78eab33525d08d6e5fb8d27136e95/e/s/essential.jpg'),
                    'url': row.get('url', ''),
                    'description': row.get('description'),
                    'category_ids': row.get('category_ids', []) if row.get('category_ids') else []
                })
            
            return products
    
    def download_full_catalog(self) -> Dict:
        """Download the full catalog from clan.com API and store locally"""
        try:
            import requests
            import time
            
            logger.info("Starting full catalog download from clan.com...")
            
            # Download the full product list (1,116 products)
            response = requests.get("https://clan.com/clan/api/getProducts", timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to download catalog: HTTP {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
            
            api_data = response.json()
            
            if not api_data.get('success') or not api_data.get('data'):
                logger.error("Invalid API response format")
                return {'success': False, 'error': 'Invalid API response'}
            
            products = api_data['data']
            logger.info(f"Downloaded {len(products)} products from clan.com API")
            
            # Store basic product info (without detailed data)
            stored_count = 0
            for i, product in enumerate(products):
                try:
                    # Extract basic info from clan.com API response
                    product_data = {
                        'id': int(product[5]) if len(product) > 5 and product[5] else i + 1,  # Use actual product ID from API
                        'name': product[0],  # title
                        'sku': product[1],   # sku
                        'url': product[2],   # product_url - use actual URL from API
                        'description': product[3],  # description
                        'image_url': 'https://static.clan.com/media/catalog/product/cache/5/image/9df78eab33525d08d6e5fb8d27136e95/e/s/essential.jpg',  # Default image
                        'price': '29.99',  # Default price
                        'has_detailed_data': False  # Mark as needing detailed data
                    }
                    
                    if self.store_single_product(product_data):
                        stored_count += 1
                    
                    # Progress logging every 100 products
                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1}/{len(products)} products...")
                    
                except Exception as e:
                    logger.error(f"Error processing product {i}: {str(e)}")
                    continue
            
            # Update cache timestamp
            self.update_cache_timestamp('products')
            
            logger.info(f"Successfully stored {stored_count}/{len(products)} products in local cache")
            
            return {
                'success': True,
                'total_downloaded': len(products),
                'stored_count': stored_count,
                'message': f'Catalog download complete: {stored_count} products stored locally'
            }
            
        except Exception as e:
            logger.error(f"Error downloading full catalog: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_products_with_detailed_data(self, skus: List[str]) -> List[Dict]:
        """Fetch detailed data for specific SKUs from clan.com API"""
        try:
            import requests
            
            detailed_products = []
            
            for sku in skus:
                try:
                    # Fetch detailed product data
                    response = requests.get(f"https://clan.com/clan/api/getProductData?sku={sku}", timeout=10)
                    
                    if response.status_code == 200:
                        product_data = response.json()
                        
                        if product_data.get('success') and product_data.get('data'):
                            # Extract detailed info
                            detailed_product = {
                                'id': int(product_data['data'].get('product_id', 0)) if product_data['data'].get('product_id') else None,
                                'sku': sku,
                                'name': product_data['data'].get('title', ''),
                                'price': str(product_data['data'].get('price', '29.99')),
                                'image_url': product_data['data'].get('image', 'https://static.clan.com/media/catalog/product/cache/5/image/9df78eab33525d08d6e5fb8d27136e95/e/s/essential.jpg'),
                                'description': product_data['data'].get('description', ''),
                                'url': product_data['data'].get('product_url', '')  # Use product_url field from API response
                            }
                            
                            # Update local cache with detailed data
                            self.update_product_details(sku, detailed_product)
                            
                            detailed_products.append(detailed_product)
                        else:
                            logger.warning(f"No detailed data for SKU {sku}")
                    else:
                        logger.warning(f"Failed to fetch details for SKU {sku}: HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error fetching details for SKU {sku}: {str(e)}")
                    continue
            
            return detailed_products
            
        except Exception as e:
            logger.error(f"Error fetching detailed product data: {str(e)}")
            return []
    
    def update_product_details(self, sku: str, detailed_data: Dict):
        """Update product with detailed data from clan.com API"""
        try:
            conn = self.get_db_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE clan_products 
                SET price = %s, image_url = %s, has_detailed_data = TRUE
                WHERE sku = %s
            """, (
                detailed_data.get('price', '29.99'),
                detailed_data.get('image_url', ''),
                sku
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated product {sku} with detailed data")
            
        except Exception as e:
            logger.error(f"Error updating product details for {sku}: {str(e)}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Count products
            cursor.execute('SELECT COUNT(*) FROM clan_products')
            product_count = cursor.fetchone()[0]
            
            # Count categories
            cursor.execute('SELECT COUNT(*) FROM clan_categories')
            category_count = cursor.fetchone()[0]
            
            # Get last update times
            cursor.execute('''
                SELECT key, last_updated FROM clan_cache_metadata 
                WHERE key IN ('products_last_update', 'categories_last_update')
            ''')
            
            updates = {}
            for row in cursor.fetchall():
                updates[row[0]] = row[1].isoformat()
            
            return {
                'products_count': product_count,
                'categories_count': category_count,
                'last_updates': updates
            }

    def store_single_product(self, product_data: Dict) -> bool:
        """Store a single product to the database"""
        try:
            conn = self.get_db_conn()
            cursor = conn.cursor()
            
            # Extract product data
            product_id = product_data.get('id')
            name = product_data.get('name', '')
            sku = product_data.get('sku', '')
            url = product_data.get('url', '')
            image_url = product_data.get('image_url', '')
            price = product_data.get('price', '')
            description = product_data.get('description', '')
            has_detailed_data = product_data.get('has_detailed_data', True)  # Default to True for backward compatibility
            
            # Insert or update the product
            cursor.execute("""
                INSERT INTO clan_products (id, name, sku, url, image_url, price, description, has_detailed_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    sku = EXCLUDED.sku,
                    url = EXCLUDED.url,
                    image_url = EXCLUDED.image_url,
                    price = EXCLUDED.price,
                    description = EXCLUDED.description,
                    has_detailed_data = EXCLUDED.has_detailed_data
            """, (product_id, name, sku, url, image_url, price, description, has_detailed_data))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing single product: {str(e)}")
            return False

    def truncate_products(self) -> bool:
        """Truncate the products table to remove all data"""
        try:
            conn = self.get_db_conn()
            cursor = conn.cursor()
            
            cursor.execute("TRUNCATE TABLE clan_products")
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Products table truncated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error truncating products table: {str(e)}")

    def add_has_detailed_data_column(self) -> bool:
        """Add has_detailed_data column to clan_products table if it doesn't exist"""
        try:
            conn = self.get_db_conn()
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'clan_products' 
                AND column_name = 'has_detailed_data'
            """)
            
            if not cursor.fetchone():
                # Add the column
                cursor.execute("""
                    ALTER TABLE clan_products 
                    ADD COLUMN has_detailed_data BOOLEAN DEFAULT TRUE
                """)
                conn.commit()
                logger.info("Added has_detailed_data column to clan_products table")
            else:
                logger.info("has_detailed_data column already exists")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding has_detailed_data column: {str(e)}")
            return False

    def refresh_product_urls(self) -> Dict:
        """Refresh product URLs from clan.com API to fix 404 links"""
        try:
            import requests
            
            logger.info("Starting product URL refresh from clan.com...")
            
            # Download fresh product list to get correct URLs
            response = requests.get("https://clan.com/clan/api/getProducts", timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to refresh URLs: HTTP {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
            
            api_data = response.json()
            
            if not api_data.get('success') or not api_data.get('data'):
                logger.error("Invalid API response format")
                return {'success': False, 'error': 'Invalid API response'}
            
            products = api_data['data']
            updated_count = 0
            
            with self.get_db_conn() as conn:
                cursor = conn.cursor()
                
                for product in products:
                    try:
                        sku = product[1]
                        correct_url = product[2]
                        
                        # Update the URL for this SKU
                        cursor.execute("""
                            UPDATE clan_products 
                            SET url = %s 
                            WHERE sku = %s
                        """, (correct_url, sku))
                        
                        if cursor.rowcount > 0:
                            updated_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error updating URL for product {product[1]}: {str(e)}")
                        continue
                
                conn.commit()
            
            logger.info(f"Successfully updated URLs for {updated_count} products")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'URL refresh complete: {updated_count} products updated'
            }
            
        except Exception as e:
            logger.error(f"Error refreshing product URLs: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global cache instance
clan_cache = ClanCache()
