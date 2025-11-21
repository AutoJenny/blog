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
        import json
        
        # Extract and clean fields (handle None values)
        name = (product.get('name') or '').strip()
        short_desc = self.clean_html(product.get('short_description'))
        description = self.clean_html(product.get('description'))
        supplier_name = (product.get('supplier_name') or '').strip()
        supplier_desc = self.clean_html(product.get('supplier_description'))
        
        # Extract specifications (if it's a dict, format it; if string, use as-is)
        specifications = product.get('specifications')
        specs_text = ""
        if specifications:
            if isinstance(specifications, dict):
                specs_parts = []
                for key, value in specifications.items():
                    specs_parts.append(f"{key.replace('_', ' ').title()}: {value}")
                specs_text = "\n".join(specs_parts)
            else:
                specs_text = str(specifications)
        
        # Extract additional_data (structured product attributes)
        additional_data = product.get('additional_data')
        additional_text = ""
        if additional_data:
            if isinstance(additional_data, dict):
                additional_parts = []
                for key, item in additional_data.items():
                    if isinstance(item, dict):
                        label = item.get('label', key.replace('_', ' ').title())
                        value = item.get('value', '')
                        if value:
                            additional_parts.append(f"{label}: {value}")
                    else:
                        additional_parts.append(f"{key.replace('_', ' ').title()}: {item}")
                additional_text = "\n".join(additional_parts)
            else:
                additional_text = str(additional_data)
        
        # Extract dimensions
        dimensions = product.get('dimensions', '').strip()
        
        # Extract configurable options
        configurable_options = product.get('configurable_options')
        options_text = ""
        if configurable_options:
            if isinstance(configurable_options, list):
                options_parts = []
                for option_group in configurable_options:
                    if isinstance(option_group, dict):
                        option_name = option_group.get('option', 'Option')
                        options_list = option_group.get('options', [])
                        if options_list:
                            option_values = []
                            for opt in options_list:
                                if isinstance(opt, dict):
                                    option_values.append(opt.get('label', str(opt)))
                                else:
                                    option_values.append(str(opt))
                            options_parts.append(f"{option_name}: {', '.join(option_values)}")
                options_text = "\n".join(options_parts)
            else:
                options_text = json.dumps(configurable_options)
        
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
        
        if specs_text:
            parts.append("")
            parts.append("Specifications:")
            parts.append(specs_text)
        
        if additional_text:
            parts.append("")
            parts.append("Product Details:")
            parts.append(additional_text)
        
        if dimensions:
            parts.append("")
            parts.append(f"Dimensions: {dimensions}")
        
        if options_text:
            parts.append("")
            parts.append("Available Options:")
            parts.append(options_text)
        
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
        name = (category.get('name') or '').strip()
        description = self.clean_html(category.get('description'))
        
        # Build structured text
        parts = []
        
        if name:
            parts.append(f"Category: {name}")
        
        if description:
            parts.append("")
            parts.append(description)
        
        # Add heritage data if available (handle both old string format and new dict format)
        if heritage_data:
            parts.append("")
            
            # Helper to extract narrative from either format
            def get_narrative(dimension_data):
                if isinstance(dimension_data, dict):
                    return dimension_data.get('narrative', '')
                elif isinstance(dimension_data, str):
                    return dimension_data
                return ''
            
            # Helper to extract themes and elements
            def get_themes_elements(dimension_data):
                if isinstance(dimension_data, dict):
                    themes = dimension_data.get('key_themes', [])
                    elements = dimension_data.get('significant_elements', [])
                    result = []
                    if themes:
                        result.append("Key Themes: " + ", ".join(themes))
                    if elements:
                        result.append("Significant Elements: " + ", ".join(elements))
                    return "\n".join(result)
                return ''
            
            # Historical Origins
            historical_origins = heritage_data.get('historical_origins')
            if historical_origins:
                parts.append("Historical Origins:")
                narrative = get_narrative(historical_origins)
                if narrative:
                    parts.append(narrative)
                themes_elements = get_themes_elements(historical_origins)
                if themes_elements:
                    parts.append("")
                    parts.append(themes_elements)
            
            # Cultural Significance
            cultural_significance = heritage_data.get('cultural_significance')
            if cultural_significance:
                parts.append("")
                parts.append("Cultural Significance:")
                narrative = get_narrative(cultural_significance)
                if narrative:
                    parts.append(narrative)
                themes_elements = get_themes_elements(cultural_significance)
                if themes_elements:
                    parts.append("")
                    parts.append(themes_elements)
            
            # Evolution
            evolution = heritage_data.get('evolution')
            if evolution:
                parts.append("")
                parts.append("Evolution:")
                narrative = get_narrative(evolution)
                if narrative:
                    parts.append(narrative)
                themes_elements = get_themes_elements(evolution)
                if themes_elements:
                    parts.append("")
                    parts.append(themes_elements)
            
            # Scottish Heritage Connections
            scottish_heritage = heritage_data.get('scottish_heritage_connections')
            if scottish_heritage:
                parts.append("")
                parts.append("Scottish Heritage Connections:")
                narrative = get_narrative(scottish_heritage)
                if narrative:
                    parts.append(narrative)
                themes_elements = get_themes_elements(scottish_heritage)
                if themes_elements:
                    parts.append("")
                    parts.append(themes_elements)
            
            # Industrial Legacy
            industrial_legacy = heritage_data.get('industrial_legacy')
            if industrial_legacy:
                parts.append("")
                parts.append("Industrial Legacy:")
                narrative = get_narrative(industrial_legacy)
                if narrative:
                    parts.append(narrative)
                themes_elements = get_themes_elements(industrial_legacy)
                if themes_elements:
                    parts.append("")
                    parts.append(themes_elements)
        
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
    
    def chunk_producer(self, producer: Dict) -> Dict:
        """
        Create a chunk from a producer record.
        
        Args:
            producer: Dictionary with producer fields from producers table
            
        Returns:
            Dictionary with chunk_text and metadata
        """
        # Extract and clean fields (handle None values)
        name = (producer.get('name') or '').strip()
        description = self.clean_html(producer.get('description'))
        location = (producer.get('location') or '').strip()
        heritage_details = self.clean_html(producer.get('heritage_details'))
        craftsmanship_methods = self.clean_html(producer.get('craftsmanship_methods'))
        founding_year = producer.get('founding_year')
        
        # Build structured text
        parts = []
        
        if name:
            parts.append(f"Producer: {name}")
        
        if description:
            parts.append("")
            parts.append(description)
        
        if location:
            parts.append("")
            parts.append(f"Location: {location}")
        
        if heritage_details:
            parts.append("")
            parts.append("Heritage:")
            parts.append(heritage_details)
        
        if craftsmanship_methods:
            parts.append("")
            parts.append("Craftsmanship Methods:")
            parts.append(craftsmanship_methods)
        
        if founding_year:
            parts.append("")
            parts.append(f"Founded: {founding_year}")
        
        chunk_text = "\n".join(parts).strip()
        
        # Build metadata
        metadata = {
            'producer_name': name,
            'location': location,
            'founding_year': founding_year
        }
        
        return {
            'chunk_text': chunk_text,
            'metadata': metadata
        }
    
    def save_chunk(self, chunk_type: str, source_id: int, chunk_data: Dict, 
                   chunk_index: int = 0) -> int:
        """
        Save chunk to database.
        
        Args:
            chunk_type: 'product', 'category', 'producer', 'post', or 'kb'
            source_id: Product, category, producer, post, or KB article ID
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
                       supplier_name, supplier_description, category_ids, price,
                       specifications, additional_data, dimensions, configurable_options
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
    
    def process_all_producers(self) -> Dict[str, int]:
        """
        Process all producers and create chunks.
        
        Returns:
            Dictionary with counts: {'processed': N, 'created': M, 'updated': K}
        """
        processed = 0
        created = 0
        updated = 0
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, location, founding_year,
                       heritage_details, craftsmanship_methods
                FROM producers
                ORDER BY id
            """)
            
            producers = cursor.fetchall()
            
            for producer in producers:
                try:
                    chunk_data = self.chunk_producer(producer)
                    
                    # Check if chunk exists
                    cursor.execute("""
                        SELECT id FROM content_chunks
                        WHERE chunk_type = 'producer' AND source_id = %s
                    """, (producer['id'],))
                    
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
                        self.save_chunk('producer', producer['id'], chunk_data)
                        created += 1
                    
                    processed += 1
                    
                    if processed % 50 == 0:
                        logger.info(f"Processed {processed} producers...")
                        
                except Exception as e:
                    logger.error(f"Error processing producer {producer.get('id')}: {e}")
        
        return {
            'processed': processed,
            'created': created,
            'updated': updated
        }
    
    def chunk_kb_article(self, article: Dict, category_name: Optional[str] = None) -> List[Dict]:
        """
        Create chunks from a KB article record.
        Articles may be long, so we split into multiple chunks if needed.
        
        Args:
            article: Dictionary with article fields from clan_kb_articles table
            category_name: Optional category name for context
            
        Returns:
            List of dictionaries with chunk_text and metadata (one or more chunks)
        """
        name = (article.get('name') or '').strip()
        short_text = self.clean_html(article.get('short_text'))
        text = self.clean_html(article.get('text'))
        category_id = article.get('category_id')
        url_key = article.get('url_key', '').strip()
        
        # Build structured text
        parts = []
        
        if name:
            parts.append(f"Article: {name}")
        
        if category_name:
            parts.append(f"Category: {category_name}")
        
        if short_text:
            parts.append("")
            parts.append("Summary:")
            parts.append(short_text)
        
        if text:
            parts.append("")
            parts.append("Content:")
            parts.append(text)
        
        full_text = "\n".join(parts).strip()
        
        # Determine if we need to split into multiple chunks
        # Rough estimate: ~4 characters per token, so 2000 tokens = ~8000 characters
        # We'll use 6000 characters as a safe chunk size to leave room for overlap
        max_chunk_size = 6000
        chunks = []
        
        if len(full_text) <= max_chunk_size:
            # Single chunk
            metadata = {
                'article_name': name,
                'article_id': article.get('id'),
                'category_id': category_id,
                'url_key': url_key,
                'chunk_count': 1,
                'chunk_index': 0
            }
            chunks.append({
                'chunk_text': full_text,
                'metadata': metadata
            })
        else:
            # Split into multiple chunks with overlap
            # Split by paragraphs first, then by sentences if needed
            paragraphs = full_text.split('\n\n')
            current_chunk_parts = []
            current_chunk_size = 0
            chunk_index = 0
            
            for para in paragraphs:
                para_size = len(para)
                
                # If adding this paragraph would exceed limit, finalize current chunk
                if current_chunk_size + para_size > max_chunk_size and current_chunk_parts:
                    # Create chunk
                    chunk_text = "\n\n".join(current_chunk_parts)
                    metadata = {
                        'article_name': name,
                        'article_id': article.get('id'),
                        'category_id': category_id,
                        'url_key': url_key,
                        'chunk_count': None,  # Will be set after we know total
                        'chunk_index': chunk_index
                    }
                    chunks.append({
                        'chunk_text': chunk_text,
                        'metadata': metadata
                    })
                    
                    # Start new chunk with overlap (last paragraph from previous chunk)
                    if current_chunk_parts:
                        overlap_para = current_chunk_parts[-1]
                        current_chunk_parts = [overlap_para, para]
                        current_chunk_size = len(overlap_para) + para_size
                    else:
                        current_chunk_parts = [para]
                        current_chunk_size = para_size
                    chunk_index += 1
                else:
                    current_chunk_parts.append(para)
                    current_chunk_size += para_size + 2  # +2 for \n\n
                    
                    # If paragraph itself is too large, split by sentences
                    if para_size > max_chunk_size:
                        sentences = para.split('. ')
                        for sentence in sentences:
                            sentence_size = len(sentence)
                            if current_chunk_size + sentence_size > max_chunk_size and current_chunk_parts:
                                # Finalize chunk
                                chunk_text = "\n\n".join(current_chunk_parts)
                                metadata = {
                                    'article_name': name,
                                    'article_id': article.get('id'),
                                    'category_id': category_id,
                                    'url_key': url_key,
                                    'chunk_count': None,
                                    'chunk_index': chunk_index
                                }
                                chunks.append({
                                    'chunk_text': chunk_text,
                                    'metadata': metadata
                                })
                                
                                # Start new chunk
                                current_chunk_parts = [sentence]
                                current_chunk_size = sentence_size
                                chunk_index += 1
                            else:
                                if current_chunk_parts and not current_chunk_parts[-1].endswith('.'):
                                    current_chunk_parts[-1] += '. ' + sentence
                                else:
                                    current_chunk_parts.append(sentence)
                                current_chunk_size += sentence_size + 2
            
            # Add final chunk
            if current_chunk_parts:
                chunk_text = "\n\n".join(current_chunk_parts)
                metadata = {
                    'article_name': name,
                    'article_id': article.get('id'),
                    'category_id': category_id,
                    'url_key': url_key,
                    'chunk_count': len(chunks) + 1,
                    'chunk_index': chunk_index
                }
                chunks.append({
                    'chunk_text': chunk_text,
                    'metadata': metadata
                })
            
            # Update chunk_count in all metadata
            total_chunks = len(chunks)
            for chunk in chunks:
                chunk['metadata']['chunk_count'] = total_chunks
        
        return chunks
    
    def process_all_kb_articles(self) -> Dict[str, int]:
        """
        Process all KB articles and create chunks.
        
        Returns:
            Dictionary with counts: {'processed': N, 'created': M, 'updated': K, 'chunks_created': C}
        """
        processed = 0
        created = 0
        updated = 0
        chunks_created = 0
        
        with db_manager.get_cursor() as cursor:
            # Get all active articles with their category names
            cursor.execute("""
                SELECT 
                    a.id, a.name, a.url_key, a.short_text, a.text, 
                    a.category_id, a.is_active,
                    c.name as category_name
                FROM clan_kb_articles a
                LEFT JOIN clan_kb_categories c ON a.category_id = c.id
                WHERE a.is_active = TRUE
                ORDER BY a.id
            """)
            
            articles = cursor.fetchall()
            
            for article in articles:
                try:
                    category_name = article.get('category_name')
                    chunks = self.chunk_kb_article(article, category_name)
                    
                    # Check existing chunks for this article
                    cursor.execute("""
                        SELECT id, chunk_index FROM content_chunks
                        WHERE chunk_type = 'kb' AND source_id = %s
                        ORDER BY chunk_index
                    """, (article['id'],))
                    
                    existing_chunks = cursor.fetchall()
                    existing_by_index = {chunk['chunk_index']: chunk['id'] for chunk in existing_chunks}
                    
                    # Process each chunk
                    for chunk_data in chunks:
                        chunk_index = chunk_data['metadata']['chunk_index']
                        
                        if chunk_index in existing_by_index:
                            # Update existing chunk
                            import json
                            chunk_id = existing_by_index[chunk_index]
                            cursor.execute("""
                                UPDATE content_chunks
                                SET chunk_text = %s, metadata = %s::jsonb, updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (chunk_data['chunk_text'], json.dumps(chunk_data['metadata']), chunk_id))
                            updated += 1
                        else:
                            # Create new chunk
                            self.save_chunk('kb', article['id'], chunk_data, chunk_index)
                            chunks_created += 1
                            created += 1
                    
                    # Remove any extra chunks (if article was shortened)
                    if len(chunks) < len(existing_chunks):
                        indices_to_keep = {chunk_data['metadata']['chunk_index'] for chunk_data in chunks}
                        for existing in existing_chunks:
                            if existing['chunk_index'] not in indices_to_keep:
                                cursor.execute("""
                                    DELETE FROM content_chunks
                                    WHERE id = %s
                                """, (existing['id'],))
                    
                    processed += 1
                    
                    if processed % 50 == 0:
                        logger.info(f"Processed {processed} KB articles ({chunks_created} chunks created)...")
                        
                except Exception as e:
                    logger.error(f"Error processing KB article {article.get('id')}: {e}")
        
        return {
            'processed': processed,
            'created': created,
            'updated': updated,
            'chunks_created': chunks_created
        }

