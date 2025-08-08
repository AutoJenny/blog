#!/usr/bin/env python3
"""
Clan.com data caching system
Stores products and categories in PostgreSQL for fast access
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class ClanCache:
    """PostgreSQL cache for clan.com data"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'blog',
            'user': 'postgres',
            'password': 'postgres'
        }
        self.init_database()
    
    def get_db_conn(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
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
                    INSERT INTO clan_products (id, name, sku, price, image_url, url, description, category_ids)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        sku = EXCLUDED.sku,
                        price = EXCLUDED.price,
                        image_url = EXCLUDED.image_url,
                        url = EXCLUDED.url,
                        description = EXCLUDED.description,
                        category_ids = EXCLUDED.category_ids
                ''', (
                    product.get('id'),
                    product.get('name'),
                    product.get('sku'),
                    product.get('price'),
                    product.get('image_url'),
                    product.get('url'),
                    product.get('description'),
                    json.dumps(product.get('category_ids', []))
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
    
    def get_random_products(self, count: int = 6) -> List[Dict]:
        """Get random products from PostgreSQL cache"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
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

# Global cache instance
clan_cache = ClanCache()
