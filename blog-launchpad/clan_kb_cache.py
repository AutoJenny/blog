#!/usr/bin/env python3
"""
Clan.com Knowledge Base caching system
Stores KB categories and articles in PostgreSQL for fast access
"""

import json
import logging
import hashlib
import os
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg
from psycopg.rows import dict_row
import requests
from pathlib import Path
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ClanKBCache:
    """PostgreSQL cache for clan.com Knowledge Base data"""
    
    def __init__(self, api_base_url: str = 'https://clan.com/clan/api'):
        """
        Initialize KB cache.
        
        Args:
            api_base_url: Base URL for CLAN API
        """
        self.api_base_url = api_base_url
        self.db_config = {
            'host': 'localhost',
            'dbname': 'blog',
            'user': 'autojenny',
            'password': ''
        }
        self.image_cache_dir = Path('static/images/kb')
        self.image_cache_dir.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_db_conn(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config)
    
    def init_database(self):
        """Initialize the database tables (run migration if needed)"""
        # Tables should be created via migration file
        # This method ensures tables exist for backward compatibility
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Check if tables exist, if not, they'll be created by migration
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'clan_kb_categories'
                )
            """)
            tables_exist = cursor.fetchone()[0]
            
            if not tables_exist:
                logger.warning("KB tables do not exist. Please run migration: migrations/create_clan_kb_tables.sql")
            
            conn.commit()
    
    def _extract_embedded_images(self, html_content: str) -> List[str]:
        """
        Extract image URLs from HTML content.
        
        Args:
            html_content: HTML content from article text field
            
        Returns:
            List of image URLs (only HTTP/HTTPS URLs, excludes template placeholders)
        """
        if not html_content:
            return []
        
        image_urls = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            images = soup.find_all('img')
            
            for img in images:
                src = img.get('src', '')
                if src and src.startswith('http'):
                    # Only include actual HTTP/HTTPS URLs, not template placeholders
                    image_urls.append(src)
            
            # Also check for image URLs in text (not just img tags)
            url_pattern = r'https?://[^\s<>"]+\.(jpg|jpeg|png|gif|webp|svg)'
            text_urls = re.findall(url_pattern, html_content, re.IGNORECASE)
            # Note: re.findall returns tuples for groups, so we need to reconstruct URLs
            # Let's use a better pattern
            url_pattern_full = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp|svg)'
            text_urls = re.findall(url_pattern_full, html_content, re.IGNORECASE)
            
            # Combine and deduplicate
            all_urls = list(set(image_urls + text_urls))
            
            return all_urls
            
        except Exception as e:
            logger.warning(f"Error extracting embedded images: {e}")
            return []
    
    def _build_article_hash(self, fields: Dict) -> str:
        """
        Build SHA-256 hash from article content fields for change detection.
        
        Args:
            fields: Dictionary with name, url_key, text, short_text, feature_image
            
        Returns:
            SHA-256 hash as hex string
        """
        # Sort fields for consistent hashing
        hash_fields = {
            'name': fields.get('name', ''),
            'url_key': fields.get('url_key', ''),
            'text': fields.get('text', ''),
            'short_text': fields.get('short_text', ''),
            'feature_image': fields.get('feature_image', '')
        }
        
        # Create JSON string and hash it
        hash_string = json.dumps(hash_fields, sort_keys=True)
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def download_image(self, image_url: str, article_id: int) -> Optional[str]:
        """
        Download and cache feature image locally.
        
        Args:
            image_url: URL of image to download
            article_id: Article ID for filename
            
        Returns:
            Local path to cached image, or None if download failed
        """
        if not image_url:
            return None
        
        try:
            # Generate filename from article ID and URL extension
            url_ext = os.path.splitext(image_url)[1] or '.jpg'
            filename = f"kb_article_{article_id}{url_ext}"
            local_path = self.image_cache_dir / filename
            
            # Skip if already downloaded
            if local_path.exists():
                return str(local_path.relative_to('static'))
            
            # Download image
            response = requests.get(image_url, timeout=10, stream=True)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Downloaded image for article {article_id}: {local_path}")
                return str(local_path.relative_to('static'))
            else:
                logger.warning(f"Failed to download image {image_url}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            return None
    
    def fetch_categories(self) -> List[Dict]:
        """
        Fetch all KB categories from CLAN API.
        
        Returns:
            List of category dictionaries
        """
        try:
            response = requests.get(f"{self.api_base_url}/getKnowledgebaseCategories", timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch KB categories: HTTP {response.status_code}")
                return []
            
            api_data = response.json()
            
            if not api_data.get('success') or not api_data.get('data'):
                logger.error("Invalid API response format for KB categories")
                return []
            
            return api_data['data']
            
        except Exception as e:
            logger.error(f"Error fetching KB categories: {e}")
            return []
    
    def fetch_articles(self, category_id: int) -> List[Dict]:
        """
        Fetch articles for a specific category from CLAN API.
        
        Args:
            category_id: Category ID to fetch articles for
            
        Returns:
            List of article dictionaries
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/getKnowledgebaseArticles",
                params={'category_id': category_id},
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch articles for category {category_id}: HTTP {response.status_code}")
                return []
            
            api_data = response.json()
            
            if not api_data.get('success') or not api_data.get('data'):
                return []
            
            return api_data['data']
            
        except Exception as e:
            logger.error(f"Error fetching articles for category {category_id}: {e}")
            return []
    
    def store_categories(self, categories: List[Dict]) -> int:
        """
        Store KB categories in database.
        Stores categories in order (by level) to satisfy foreign key constraints.
        
        Args:
            categories: List of category dictionaries from API
            
        Returns:
            Number of categories stored
        """
        stored_count = 0
        
        # Sort categories by level (parents before children) to satisfy FK constraints
        sorted_categories = sorted(categories, key=lambda c: int(c.get('level', 0)))
        
        # Build set of valid category IDs to check parent references
        valid_category_ids = {int(c.get('category_id', 0)) for c in categories if c.get('category_id')}
        
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            
            for category in sorted_categories:
                # Use savepoint to handle errors per-category without aborting entire transaction
                savepoint_name = f"sp_{category.get('category_id', 'unknown')}"
                try:
                    cursor.execute(f"SAVEPOINT {savepoint_name}")
                    
                    category_id = int(category.get('category_id', 0))
                    if not category_id:
                        cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                        continue
                    
                    # Parse boolean fields
                    is_active = category.get('is_active', '1') == '1'
                    
                    # Parse integer fields - check if parent exists in API response
                    parent_id_raw = category.get('parent_id')
                    parent_id = None
                    if parent_id_raw:
                        parent_id_int = int(parent_id_raw)
                        # Only set parent_id if parent exists in the categories list
                        if parent_id_int in valid_category_ids:
                            parent_id = parent_id_int
                        else:
                            # Parent doesn't exist in API response, set to NULL
                            logger.debug(f"Category {category_id} references missing parent {parent_id_int}, setting to NULL")
                    
                    level = int(category.get('level', 0))
                    position = int(category.get('position', 0))
                    sort_order = int(category.get('sort_order', 0))
                    children_count = int(category.get('children_count', 0))
                    
                    cursor.execute('''
                        INSERT INTO clan_kb_categories (
                            id, name, url_key, meta_title, meta_keywords, meta_description,
                            is_active, sort_order, parent_id, path, level, position, children_count
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            url_key = EXCLUDED.url_key,
                            meta_title = EXCLUDED.meta_title,
                            meta_keywords = EXCLUDED.meta_keywords,
                            meta_description = EXCLUDED.meta_description,
                            is_active = EXCLUDED.is_active,
                            sort_order = EXCLUDED.sort_order,
                            parent_id = EXCLUDED.parent_id,
                            path = EXCLUDED.path,
                            level = EXCLUDED.level,
                            position = EXCLUDED.position,
                            children_count = EXCLUDED.children_count,
                            last_updated = CURRENT_TIMESTAMP
                    ''', (
                        category_id,
                        category.get('name', ''),
                        category.get('url_key'),
                        category.get('meta_title') or '',
                        category.get('meta_keywords'),
                        category.get('meta_description'),
                        is_active,
                        sort_order,
                        parent_id,
                        category.get('path'),
                        level,
                        position,
                        children_count
                    ))
                    
                    cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"Error storing category {category.get('category_id')}: {e}")
                    try:
                        cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    except:
                        pass
                    continue
            
            conn.commit()
        
        logger.info(f"Stored {stored_count}/{len(categories)} KB categories")
        return stored_count
    
    def store_article(self, article: Dict, category_id: int) -> bool:
        """
        Store a single KB article in database with change detection.
        
        Args:
            article: Article dictionary from API
            category_id: Category ID this article belongs to
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            article_id = int(article.get('article_id', 0))
            if not article_id:
                return False
            
            # Parse fields
            name = article.get('name', '')
            url_key = article.get('url_key')
            feature_image = article.get('feature_image')
            short_text = article.get('short_text')
            text = article.get('text', '')
            
            # Parse boolean
            is_active = article.get('is_active', '1') == '1'
            
            # Parse integers
            user_id = int(article.get('user_id', 0)) if article.get('user_id') else None
            position = int(article.get('position', 0))
            
            # Parse decimals
            votes_sum = float(article.get('votes_sum')) if article.get('votes_sum') else None
            votes_num = int(article.get('votes_num', 0))
            rating = float(article.get('rating')) if article.get('rating') else None
            
            # Parse timestamps
            clan_created_at = None
            if article.get('created_at'):
                try:
                    clan_created_at = datetime.strptime(article['created_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            clan_updated_at = None
            if article.get('updated_at'):
                try:
                    clan_updated_at = datetime.strptime(article['updated_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # Extract embedded images from HTML content
            embedded_images = self._extract_embedded_images(text)
            
            # Build content hash
            content_fields = {
                'name': name,
                'url_key': url_key or '',
                'text': text,
                'short_text': short_text or '',
                'feature_image': feature_image or ''
            }
            article_hash = self._build_article_hash(content_fields)
            
            # Download feature image if present
            feature_image_local = None
            if feature_image:
                feature_image_local = self.download_image(feature_image, article_id)
            
            # Check if article exists and if content changed
            with self.get_db_conn() as conn:
                cursor = conn.cursor()
                
                # Get existing hash if article exists
                cursor.execute("""
                    SELECT article_content_hash, last_content_change_at
                    FROM clan_kb_articles
                    WHERE id = %s
                """, (article_id,))
                
                existing = cursor.fetchone()
                last_content_change_at = None
                
                if existing and existing[0] != article_hash:
                    # Content changed
                    last_content_change_at = datetime.now()
                    logger.info(f"Article {article_id} content changed")
                
                # Insert or update article
                embedded_images_json = json.dumps(embedded_images)
                
                cursor.execute("""
                    INSERT INTO clan_kb_articles (
                        id, category_id, name, url_key, feature_image, feature_image_local,
                        short_text, text, meta_title, meta_keywords, meta_description,
                        is_active, user_id, user_name, votes_sum, votes_num, rating,
                        position, clan_created_at, clan_updated_at,
                        article_content_hash, last_content_change_at, embedded_images
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        category_id = EXCLUDED.category_id,
                        name = EXCLUDED.name,
                        url_key = EXCLUDED.url_key,
                        feature_image = EXCLUDED.feature_image,
                        feature_image_local = COALESCE(EXCLUDED.feature_image_local, clan_kb_articles.feature_image_local),
                        short_text = EXCLUDED.short_text,
                        text = EXCLUDED.text,
                        meta_title = EXCLUDED.meta_title,
                        meta_keywords = EXCLUDED.meta_keywords,
                        meta_description = EXCLUDED.meta_description,
                        is_active = EXCLUDED.is_active,
                        user_id = EXCLUDED.user_id,
                        user_name = EXCLUDED.user_name,
                        votes_sum = EXCLUDED.votes_sum,
                        votes_num = EXCLUDED.votes_num,
                        rating = EXCLUDED.rating,
                        position = EXCLUDED.position,
                        clan_created_at = COALESCE(clan_kb_articles.clan_created_at, EXCLUDED.clan_created_at),
                        clan_updated_at = COALESCE(EXCLUDED.clan_updated_at, clan_kb_articles.clan_updated_at),
                        article_content_hash = EXCLUDED.article_content_hash,
                        last_content_change_at = COALESCE(EXCLUDED.last_content_change_at, clan_kb_articles.last_content_change_at),
                        embedded_images = EXCLUDED.embedded_images,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    article_id,
                    category_id,
                    name,
                    url_key,
                    feature_image,
                    feature_image_local,
                    short_text,
                    text,
                    article.get('meta_title') or '',
                    article.get('meta_keywords'),
                    article.get('meta_description'),
                    is_active,
                    user_id,
                    article.get('user_name'),
                    votes_sum,
                    votes_num,
                    rating,
                    position,
                    clan_created_at,
                    clan_updated_at,
                    article_hash,
                    last_content_change_at,
                    embedded_images_json
                ))
                
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing article {article.get('article_id')}: {e}")
            return False
    
    def sync_all(self) -> Dict:
        """
        Sync all KB categories and articles from CLAN API (on-demand).
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting KB sync from CLAN API...")
        
        stats = {
            'categories_fetched': 0,
            'categories_stored': 0,
            'articles_fetched': 0,
            'articles_stored': 0,
            'articles_changed': 0,
            'errors': 0
        }
        
        try:
            # Fetch all categories
            categories = self.fetch_categories()
            stats['categories_fetched'] = len(categories)
            
            if not categories:
                logger.warning("No categories fetched from API")
                return {'success': False, 'error': 'No categories fetched', **stats}
            
            # Store categories
            stats['categories_stored'] = self.store_categories(categories)
            
            # Fetch and store articles for each category
            for i, category in enumerate(categories):
                category_id = int(category.get('category_id', 0))
                if not category_id:
                    continue
                
                # Rate limiting: Add delay between requests to avoid HTTP 429
                if i > 0:
                    time.sleep(0.5)  # 500ms delay between category requests
                
                try:
                    articles = self.fetch_articles(category_id)
                    stats['articles_fetched'] += len(articles)
                    
                    for article in articles:
                        # Check if content changed before storing
                        article_id = int(article.get('article_id', 0))
                        if article_id:
                            # Get existing hash to detect changes
                            with self.get_db_conn() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT article_content_hash FROM clan_kb_articles WHERE id = %s
                                """, (article_id,))
                                existing = cursor.fetchone()
                                
                                # Build new hash
                                content_fields = {
                                    'name': article.get('name', ''),
                                    'url_key': article.get('url_key', ''),
                                    'text': article.get('text', ''),
                                    'short_text': article.get('short_text', ''),
                                    'feature_image': article.get('feature_image', '')
                                }
                                new_hash = self._build_article_hash(content_fields)
                                
                                if existing and existing[0] != new_hash:
                                    stats['articles_changed'] += 1
                        
                        if self.store_article(article, category_id):
                            stats['articles_stored'] += 1
                        else:
                            stats['errors'] += 1
                    
                    # Progress logging
                    if stats['articles_fetched'] % 50 == 0:
                        logger.info(f"Processed {stats['articles_fetched']} articles...")
                
                except Exception as e:
                    logger.error(f"Error processing category {category_id}: {e}")
                    stats['errors'] += 1
                    continue
            
            # Update cache metadata
            self.update_cache_timestamp('kb')
            
            logger.info(f"KB sync complete: {stats['categories_stored']} categories, {stats['articles_stored']} articles stored, {stats['articles_changed']} changed")
            
            return {
                'success': True,
                'message': f'KB sync complete: {stats["categories_stored"]} categories, {stats["articles_stored"]} articles',
                **stats
            }
            
        except Exception as e:
            logger.error(f"Error during KB sync: {e}")
            return {'success': False, 'error': str(e), **stats}
    
    def update_cache_timestamp(self, cache_type: str):
        """Update cache metadata timestamp"""
        with self.get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clan_cache_metadata (key, value, last_updated)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    last_updated = CURRENT_TIMESTAMP
            """, (f'kb_last_sync_at', datetime.now().isoformat()))
            conn.commit()
    
    def get_changed_articles(self, since: Optional[datetime] = None) -> List[Dict]:
        """
        Get articles that have changed since a given timestamp.
        
        Args:
            since: Optional datetime to filter changes (defaults to last 7 days)
            
        Returns:
            List of changed articles
        """
        if since is None:
            since = datetime.now() - timedelta(days=7)
        
        with self.get_db_conn() as conn:
            cursor = conn.cursor(row_factory=dict_row)
            cursor.execute("""
                SELECT id, name, url_key, category_id, last_content_change_at
                FROM clan_kb_articles
                WHERE last_content_change_at >= %s
                ORDER BY last_content_change_at DESC
            """, (since,))
            
            return cursor.fetchall()


if __name__ == '__main__':
    # Test script
    import sys
    logging.basicConfig(level=logging.INFO)
    
    cache = ClanKBCache()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'sync':
        result = cache.sync_all()
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python clan_kb_cache.py sync")

