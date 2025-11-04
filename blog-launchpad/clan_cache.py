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
                    price DECIMAL(10,2),
                    image_url TEXT,
                    url TEXT,
                    short_description TEXT,
                    description TEXT,
                    supplier_name TEXT,
                    supplier_description TEXT,
                    clan_created_at TIMESTAMP,
                    clan_updated_at TIMESTAMP,
                    configurable_options JSONB,
                    product_content_hash TEXT,
                    category_ids JSONB,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            
            # Ensure new columns exist on existing installations
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS short_description TEXT
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS supplier_name TEXT
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS supplier_description TEXT
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS clan_created_at TIMESTAMP
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS clan_updated_at TIMESTAMP
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS configurable_options JSONB
            ''')
            cursor.execute('''
                ALTER TABLE clan_products
                ADD COLUMN IF NOT EXISTS product_content_hash TEXT
            ''')
            cursor.execute('''
                DO $$ BEGIN
                    BEGIN
                        ALTER TABLE clan_products ALTER COLUMN price TYPE DECIMAL(10,2) USING NULLIF(price,'')::numeric;
                    EXCEPTION WHEN others THEN
                        -- ignore if already decimal or incompatible values
                    END;
                END $$;
            ''')

            # Indexes
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_clan_products_clan_created_at ON clan_products (clan_created_at)''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_clan_products_clan_updated_at ON clan_products (clan_updated_at)''')

            # Backfill first_seen_at from last_updated where missing
            cursor.execute('''
                UPDATE clan_products
                SET first_seen_at = COALESCE(first_seen_at, last_updated)
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
    
    def _build_product_hash(self, fields: Dict) -> str:
        """Build a stable content hash for change detection."""
        import hashlib
        payload = json.dumps(fields, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def store_products(self, products: List[Dict]):
        """Upsert products into PostgreSQL cache without deleting existing rows.
        Preserves first_seen_at; updates last_updated on change.
        """
        with self.get_db_conn() as conn:
            cursor = conn.cursor()

            for product in products:
                product_id = product.get('product_id') or product.get('id')
                name = product.get('title') or product.get('name')
                sku = product.get('sku')
                price = product.get('price')
                image_url = product.get('image') or product.get('image_url')
                url = product.get('product_url') or product.get('url')
                description = product.get('description')
                short_description = product.get('short_description')
                supplier_name = product.get('supplier_name')
                supplier_description = product.get('supplier_description')
                clan_created_at = product.get('created_at') or product.get('clan_created_at')
                clan_updated_at = product.get('updated_at') or product.get('clan_updated_at')
                category_ids = json.dumps(product.get('category_ids', []))
                configurable_options = json.dumps(product.get('configurable_options', None))

                # Build hash over meaningful fields
                content_fields = {
                    'name': name,
                    'sku': sku,
                    'price': price,
                    'image_url': image_url,
                    'url': url,
                    'short_description': short_description,
                    'description': description,
                    'supplier_name': supplier_name,
                    'supplier_description': supplier_description,
                    'configurable_options': product.get('configurable_options', None),
                }
                product_hash = self._build_product_hash(content_fields)

                cursor.execute('''
                    INSERT INTO clan_products (id, name, sku, price, image_url, url, short_description, description, supplier_name, supplier_description, clan_created_at, clan_updated_at, configurable_options, product_content_hash, category_ids)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        sku = EXCLUDED.sku,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        url = EXCLUDED.url,
                        short_description = EXCLUDED.short_description,
                        description = EXCLUDED.description,
                        supplier_name = EXCLUDED.supplier_name,
                        supplier_description = EXCLUDED.supplier_description,
                        clan_created_at = COALESCE(clan_products.clan_created_at, EXCLUDED.clan_created_at),
                        clan_updated_at = COALESCE(EXCLUDED.clan_updated_at, clan_products.clan_updated_at),
                        configurable_options = EXCLUDED.configurable_options,
                        product_content_hash = EXCLUDED.product_content_hash,
                        category_ids = EXCLUDED.category_ids,
                        last_updated = CURRENT_TIMESTAMP
                ''', (
                    product_id,
                    name,
                    sku,
                    price,
                    image_url,
                    url,
                    short_description,
                    description,
                    supplier_name,
                    supplier_description,
                    clan_created_at,
                    clan_updated_at,
                    configurable_options,
                    product_hash,
                    category_ids
                ))

            conn.commit()
            self.update_cache_timestamp('products')
            logger.info(f"Upserted {len(products)} products into PostgreSQL cache")
    
    def store_categories(self, categories: List[Dict]):
        """Upsert categories into PostgreSQL cache without deleting existing rows."""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()

            for category in categories:
                cursor.execute('''
                    INSERT INTO clan_categories (id, name, description, level, parent_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        level = EXCLUDED.level,
                        parent_id = EXCLUDED.parent_id,
                        last_updated = CURRENT_TIMESTAMP
                ''', (
                    category.get('id'),
                    category.get('name'),
                    category.get('description'),
                    category.get('level', 0),
                    category.get('parent_id')
                ))

            conn.commit()
            self.update_cache_timestamp('categories')
            logger.info(f"Upserted {len(categories)} categories into PostgreSQL cache")
    
    def get_products(self, limit: Optional[int] = None, query: str = '') -> List[Dict]:
        """Get products from PostgreSQL cache"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor(row_factory=dict_row)
            
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
            cursor = conn.cursor(row_factory=dict_row)
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
            cursor = conn.cursor(row_factory=dict_row)
            
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
            # Normalize price to numeric for DECIMAL column
            from decimal import Decimal, InvalidOperation
            if isinstance(price, str):
                import re
                cleaned = re.sub(r"[^0-9.]+", "", price)
                try:
                    price = Decimal(cleaned) if cleaned else None
                except InvalidOperation:
                    price = None
            short_description = product_data.get('short_description', '')
            description = product_data.get('description', '')
            supplier_name = product_data.get('supplier_name')
            supplier_description = product_data.get('supplier_description')
            clan_created_at = product_data.get('created_at') or product_data.get('clan_created_at')
            clan_updated_at = product_data.get('updated_at') or product_data.get('clan_updated_at')
            configurable_options = json.dumps(product_data.get('configurable_options', None))
            has_detailed_data = product_data.get('has_detailed_data', True)  # Default to True for backward compatibility

            # Ensure hashable, JSON-serializable fields
            price_for_hash = str(price) if price is not None else ''
            content_fields = {
                'name': name,
                'sku': sku,
                'price': price_for_hash,
                'image_url': image_url,
                'url': url,
                'short_description': short_description,
                'description': description,
                'supplier_name': supplier_name,
                'supplier_description': supplier_description,
                'configurable_options': product_data.get('configurable_options', None),
            }
            product_hash = self._build_product_hash(content_fields)
            
            # Insert or update the product
            cursor.execute("""
                INSERT INTO clan_products (id, name, sku, url, image_url, price, short_description, description, supplier_name, supplier_description, clan_created_at, clan_updated_at, configurable_options, product_content_hash, has_detailed_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    sku = EXCLUDED.sku,
                    url = EXCLUDED.url,
                    image_url = EXCLUDED.image_url,
                    price = EXCLUDED.price,
                    short_description = EXCLUDED.short_description,
                    description = EXCLUDED.description,
                    supplier_name = EXCLUDED.supplier_name,
                    supplier_description = EXCLUDED.supplier_description,
                    clan_created_at = COALESCE(clan_products.clan_created_at, EXCLUDED.clan_created_at),
                    clan_updated_at = COALESCE(EXCLUDED.clan_updated_at, clan_products.clan_updated_at),
                    configurable_options = EXCLUDED.configurable_options,
                    product_content_hash = EXCLUDED.product_content_hash,
                    has_detailed_data = EXCLUDED.has_detailed_data,
                    last_updated = CURRENT_TIMESTAMP
            """, (product_id, name, sku, url, image_url, price, short_description, description, supplier_name, supplier_description, clan_created_at, clan_updated_at, configurable_options, product_hash, has_detailed_data))
            
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
