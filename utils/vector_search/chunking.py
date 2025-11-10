"""
Content Chunking Module

Extracts and normalizes text from products and categories for embedding.
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from config.database import db_manager

logger = logging.getLogger(__name__)


class ContentChunker:
    """Handles text extraction and chunking from products and categories."""
    
    def __init__(self):
        self.html_parser = BeautifulSoup
    
    def clean_html(self, html_text: Optional[str]) -> str:
        """
        Clean HTML text: strip tags, decode entities, normalize whitespace.
        
        Args:
            html_text: HTML string or None
            
        Returns:
            Cleaned plain text
        """
        if not html_text:
            return ""
        
        try:
            # Parse HTML and extract text
            soup = self.html_parser(html_text, 'html.parser')
            text = soup.get_text()
            
            # Decode HTML entities
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')
            text = text.replace('&#39;', "'")
            text = text.replace('&nbsp;', ' ')
            
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
            text = text.strip()
            
            return text
        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            # Fallback: basic tag removal
            text = re.sub(r'<[^>]+>', '', html_text)
            return text.strip()
    
    def chunk_product(self, product: Dict) -> Dict:
        """
        Create a chunk from a product record.
        
        Args:
            product: Dictionary with product fields from clan_products table
            
        Returns:
            Dictionary with chunk_text and metadata
        """
        # Extract and clean fields
        name = product.get('name', '').strip()
        short_desc = self.clean_html(product.get('short_description'))
        description = self.clean_html(product.get('description'))
        supplier_name = product.get('supplier_name', '').strip()
        supplier_desc = self.clean_html(product.get('supplier_description'))
        
        # Build structured text
        parts = []
        
        if name:
            parts.append(f"Product: {name}")
        
        if supplier_name:
            parts.append(f"Producer: {supplier_name}")
        
        if short_desc:
            parts.append("")
            parts.append(short_desc)
        
        if description:
            parts.append("")
            parts.append(description)
        
        if supplier_desc:
            parts.append("")
            parts.append("About the Producer:")
            parts.append(supplier_desc)
        
        chunk_text = "\n".join(parts).strip()
        
        # Build metadata
        metadata = {
            'product_name': name,
            'sku': product.get('sku', ''),
            'supplier_name': supplier_name,
            'category_ids': product.get('category_ids', []),
            'price': str(product.get('price', '')) if product.get('price') else None
        }
        
        return {
            'chunk_text': chunk_text,
            'metadata': metadata
        }
    
    def chunk_category(self, category: Dict, heritage_data: Optional[Dict] = None) -> Dict:
        """
        Create a chunk from a category record.
        
        Args:
            category: Dictionary with category fields from clan_categories table
            heritage_data: Optional heritage_data JSONB from category
            
        Returns:
            Dictionary with chunk_text and metadata
        """
        name = category.get('name', '').strip()
        description = self.clean_html(category.get('description'))
        
        # Build structured text
        parts = []
        
        if name:
            parts.append(f"Category: {name}")
        
        if description:
            parts.append("")
            parts.append(description)
        
        # Add heritage data if available
        if heritage_data:
            parts.append("")
            
            if heritage_data.get('historical_origins'):
                parts.append("Historical Origins:")
                parts.append(heritage_data['historical_origins'])
            
            if heritage_data.get('cultural_significance'):
                parts.append("")
                parts.append("Cultural Significance:")
                parts.append(heritage_data['cultural_significance'])
            
            if heritage_data.get('evolution'):
                parts.append("")
                parts.append("Evolution:")
                parts.append(heritage_data['evolution'])
            
            if heritage_data.get('scottish_heritage_connections'):
                parts.append("")
                parts.append("Scottish Heritage Connections:")
                parts.append(heritage_data['scottish_heritage_connections'])
        
        chunk_text = "\n".join(parts).strip()
        
        # Build metadata
        metadata = {
            'category_name': name,
            'category_id': category.get('id'),
            'parent_id': category.get('parent_id'),
            'level': category.get('level', 0)
        }
        
        # Add category path if we can determine it
        if category.get('parent_id'):
            metadata['has_parent'] = True
        
        return {
            'chunk_text': chunk_text,
            'metadata': metadata
        }
    
    def save_chunk(self, chunk_type: str, source_id: int, chunk_data: Dict, 
                   chunk_index: int = 0) -> int:
        """
        Save chunk to database.
        
        Args:
            chunk_type: 'product' or 'category'
            source_id: Product or category ID
            chunk_data: Dictionary with chunk_text and metadata
            chunk_index: Index for multi-chunk sources (0 for single chunk)
            
        Returns:
            Chunk ID
        """
        import json
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO content_chunks 
                (chunk_type, source_id, chunk_text, chunk_index, metadata, updated_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, CURRENT_TIMESTAMP)
                RETURNING id
            """, (
                chunk_type,
                source_id,
                chunk_data['chunk_text'],
                chunk_index,
                json.dumps(chunk_data['metadata'])
            ))
            
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def process_all_products(self) -> Dict[str, int]:
        """
        Process all products and create chunks.
        
        Returns:
            Dictionary with counts: {'processed': N, 'created': M, 'updated': K}
        """
        processed = 0
        created = 0
        updated = 0
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, sku, short_description, description, 
                       supplier_name, supplier_description, category_ids, price
                FROM clan_products
                ORDER BY id
            """)
            
            products = cursor.fetchall()
            
            for product in products:
                try:
                    chunk_data = self.chunk_product(product)
                    
                    # Check if chunk exists
                    cursor.execute("""
                        SELECT id FROM content_chunks
                        WHERE chunk_type = 'product' AND source_id = %s
                    """, (product['id'],))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing
                        import json
                        cursor.execute("""
                            UPDATE content_chunks
                            SET chunk_text = %s, metadata = %s::jsonb, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (chunk_data['chunk_text'], json.dumps(chunk_data['metadata']), existing['id']))
                        updated += 1
                    else:
                        # Create new
                        self.save_chunk('product', product['id'], chunk_data)
                        created += 1
                    
                    processed += 1
                    
                    if processed % 100 == 0:
                        logger.info(f"Processed {processed} products...")
                        
                except Exception as e:
                    logger.error(f"Error processing product {product.get('id')}: {e}")
        
        return {
            'processed': processed,
            'created': created,
            'updated': updated
        }
    
    def process_all_categories(self) -> Dict[str, int]:
        """
        Process all categories and create chunks.
        
        Returns:
            Dictionary with counts: {'processed': N, 'created': M, 'updated': K}
        """
        processed = 0
        created = 0
        updated = 0
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, parent_id, level, heritage_data
                FROM clan_categories
                ORDER BY id
            """)
            
            categories = cursor.fetchall()
            
            for category in categories:
                try:
                    heritage_data = category.get('heritage_data')
                    chunk_data = self.chunk_category(category, heritage_data)
                    
                    # Check if chunk exists
                    cursor.execute("""
                        SELECT id FROM content_chunks
                        WHERE chunk_type = 'category' AND source_id = %s
                    """, (category['id'],))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing
                        import json
                        cursor.execute("""
                            UPDATE content_chunks
                            SET chunk_text = %s, metadata = %s::jsonb, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (chunk_data['chunk_text'], json.dumps(chunk_data['metadata']), existing['id']))
                        updated += 1
                    else:
                        # Create new
                        self.save_chunk('category', category['id'], chunk_data)
                        created += 1
                    
                    processed += 1
                    
                    if processed % 50 == 0:
                        logger.info(f"Processed {processed} categories...")
                        
                except Exception as e:
                    logger.error(f"Error processing category {category.get('id')}: {e}")
        
        return {
            'processed': processed,
            'created': created,
            'updated': updated
        }

