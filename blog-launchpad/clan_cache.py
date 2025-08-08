#!/usr/bin/env python3
"""
Clan.com data caching system
Stores products and categories locally for fast access
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

class ClanCache:
    """Local cache for clan.com data using SQLite"""
    
    def __init__(self, db_path: str = 'clan_cache.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    sku TEXT UNIQUE NOT NULL,
                    price TEXT,
                    image_url TEXT,
                    url TEXT,
                    description TEXT,
                    category_ids TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
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
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def is_cache_fresh(self, cache_type: str, max_age_hours: int = 24) -> bool:
        """Check if cache is fresh (not older than max_age_hours)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT last_updated FROM cache_metadata 
                WHERE key = ?
            ''', (f'{cache_type}_last_update',))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            last_update = datetime.fromisoformat(result[0])
            return datetime.now() - last_update < timedelta(hours=max_age_hours)
    
    def update_cache_timestamp(self, cache_type: str):
        """Update the cache timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cache_metadata (key, value, last_updated)
                VALUES (?, ?, ?)
            ''', (f'{cache_type}_last_update', datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
    
    def store_products(self, products: List[Dict]):
        """Store products in local cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing products
            cursor.execute('DELETE FROM products')
            
            # Insert new products
            for product in products:
                cursor.execute('''
                    INSERT INTO products (id, name, sku, price, image_url, url, description, category_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            logger.info(f"Stored {len(products)} products in cache")
    
    def store_categories(self, categories: List[Dict]):
        """Store categories in local cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing categories
            cursor.execute('DELETE FROM categories')
            
            # Insert new categories
            for category in categories:
                cursor.execute('''
                    INSERT INTO categories (id, name, description, level, parent_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    category.get('id'),
                    category.get('name'),
                    category.get('description'),
                    category.get('level', 0),
                    category.get('parent_id')
                ))
            
            conn.commit()
            self.update_cache_timestamp('categories')
            logger.info(f"Stored {len(categories)} categories in cache")
    
    def get_products(self, limit: Optional[int] = None, query: str = '') -> List[Dict]:
        """Get products from local cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            sql = 'SELECT id, name, sku, price, image_url, url, description, category_ids FROM products'
            params = []
            
            if query:
                sql += ' WHERE name LIKE ? OR description LIKE ?'
                params.extend([f'%{query}%', f'%{query}%'])
            
            sql += ' ORDER BY name'
            
            if limit:
                sql += f' LIMIT {limit}'
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            products = []
            for row in rows:
                products.append({
                    'id': row[0],
                    'name': row[1],
                    'sku': row[2],
                    'price': row[3],
                    'image_url': row[4],
                    'url': row[5],
                    'description': row[6],
                    'category_ids': json.loads(row[7]) if row[7] else []
                })
            
            return products
    
    def get_categories(self) -> List[Dict]:
        """Get categories from local cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description, level, parent_id 
                FROM categories 
                ORDER BY level, name
            ''')
            
            rows = cursor.fetchall()
            categories = []
            for row in rows:
                categories.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'level': row[3],
                    'parent_id': row[4]
                })
            
            return categories
    
    def get_random_products(self, count: int = 6) -> List[Dict]:
        """Get random products from cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, sku, price, image_url, url, description, category_ids 
                FROM products 
                ORDER BY RANDOM() 
                LIMIT ?
            ''', (count,))
            
            rows = cursor.fetchall()
            products = []
            for row in rows:
                products.append({
                    'id': row[0],
                    'name': row[1],
                    'sku': row[2],
                    'price': row[3],
                    'image_url': row[4],
                    'url': row[5],
                    'description': row[6],
                    'category_ids': json.loads(row[7]) if row[7] else []
                })
            
            return products
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count products
            cursor.execute('SELECT COUNT(*) FROM products')
            product_count = cursor.fetchone()[0]
            
            # Count categories
            cursor.execute('SELECT COUNT(*) FROM categories')
            category_count = cursor.fetchone()[0]
            
            # Get last update times
            cursor.execute('''
                SELECT key, last_updated FROM cache_metadata 
                WHERE key IN ('products_last_update', 'categories_last_update')
            ''')
            
            updates = {}
            for row in cursor.fetchall():
                updates[row[0]] = row[1]
            
            return {
                'products_count': product_count,
                'categories_count': category_count,
                'last_updates': updates
            }

# Global cache instance
clan_cache = ClanCache()
