"""
CLAN Data Extractor

Extracts and validates CLAN product data for content generation.
Implements CLAN-first policy: prioritizes CLAN data, uses LLM only for gaps.
"""

import logging
import json
from typing import Dict, List, Optional
from config.database import db_manager
from utils.vector_search.retrieval import ContentRetriever
from utils.vector_search.chunking import ContentChunker

logger = logging.getLogger(__name__)


class ClanDataExtractor:
    """Extract and validate CLAN product data for content generation."""
    
    # Configurable threshold for LLM supplementation (default: 50 words)
    LLM_SUPPLEMENTATION_THRESHOLD = 50
    
    def __init__(self, llm_threshold: int = None):
        """
        Initialize CLAN data extractor.
        
        Args:
            llm_threshold: Word count threshold for LLM supplementation (default: 50)
        """
        self.llm_threshold = llm_threshold or self.LLM_SUPPLEMENTATION_THRESHOLD
        self.chunker = ContentChunker()
        self.retriever = ContentRetriever() if self._check_faiss_index() else None
    
    def _check_faiss_index(self) -> bool:
        """Check if FAISS index exists."""
        import os
        index_path = "data/vector_index/products_categories.faiss"
        return os.path.exists(index_path)
    
    def extract_product_data(self, product_id: int) -> Dict:
        """
        Extract all available CLAN product data.
        
        Args:
            product_id: Product ID from clan_products table
            
        Returns:
            Dictionary with structured product data and presence flags
        """
        with db_manager.get_cursor() as cursor:
            # Fetch product data
            cursor.execute("""
                SELECT 
                    id, sku, name, price, image_url, url,
                    short_description, description,
                    supplier_name, supplier_description,
                    configurable_options, category_ids,
                    clan_created_at, clan_updated_at,
                    specifications, producer_id
                FROM clan_products
                WHERE id = %s
            """, (product_id,))
            
            product = cursor.fetchone()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Fetch category data if category_ids exist
            categories = []
            heritage_data = {}
            
            if product.get('category_ids'):
                category_ids = product['category_ids']
                if isinstance(category_ids, list) and category_ids:
                    # Fetch categories
                    placeholders = ','.join(['%s'] * len(category_ids))
                    cursor.execute(f"""
                        SELECT id, name, description, heritage_data, parent_id, level
                        FROM clan_categories
                        WHERE id IN ({placeholders})
                    """, tuple(category_ids))
                    
                    categories = cursor.fetchall()
                    
                    # Combine heritage_data from all categories
                    for cat in categories:
                        if cat.get('heritage_data'):
                            cat_heritage = cat['heritage_data']
                            if isinstance(cat_heritage, dict):
                                # Merge heritage data (product-specific takes priority)
                                for key in ['historical_origins', 'cultural_significance', 
                                           'evolution', 'scottish_heritage_connections']:
                                    if key in cat_heritage and cat_heritage[key]:
                                        if key not in heritage_data or not heritage_data[key]:
                                            heritage_data[key] = cat_heritage[key]
            
            # Fetch producer data if producer_id exists (producers table may not exist)
            producer_data = None
            if product.get('producer_id'):
                try:
                    cursor.execute("""
                        SELECT id, name, description, location, website
                        FROM producers
                        WHERE id = %s
                    """, (product['producer_id'],))
                    producer_data = cursor.fetchone()
                except Exception as e:
                    logger.debug(f"Producers table not available or producer not found: {e}")
                    producer_data = None
            
            # Build structured data with presence flags
            product_data = {
                'product_id': product['id'],
                'sku': product.get('sku', ''),
                'name': product.get('name', ''),
                'price': str(product.get('price', '')) if product.get('price') else None,
                'image_url': product.get('image_url'),
                'url': product.get('url'),
                
                # Descriptions
                'short_description': self.chunker.clean_html(product.get('short_description')),
                'description': self.chunker.clean_html(product.get('description')),
                
                # Supplier/Producer
                'supplier_name': product.get('supplier_name', ''),
                'supplier_description': self.chunker.clean_html(product.get('supplier_description')),
                'producer_data': producer_data,
                
                # Options and specifications
                'configurable_options': product.get('configurable_options'),
                'specifications': product.get('specifications'),
                
                # Categories
                'category_ids': product.get('category_ids', []),
                'categories': categories,
                'heritage_data': heritage_data,
                
                # Timestamps
                'clan_created_at': product.get('clan_created_at'),
                'clan_updated_at': product.get('clan_updated_at'),
                
                # Presence flags (for validation)
                'has_name': bool(product.get('name')),
                'has_description': bool(product.get('description') or product.get('short_description')),
                'has_supplier': bool(product.get('supplier_name')),
                'has_heritage_data': bool(heritage_data),
                'has_specifications': bool(product.get('specifications')),
                'has_options': bool(product.get('configurable_options')),
            }
            
            return product_data
    
    def validate_data_completeness(self, product_data: Dict) -> Dict:
        """
        Check which fields are present/missing and word counts.
        
        Args:
            product_data: Product data from extract_product_data()
            
        Returns:
            Validation report with completeness scores and missing fields
        """
        def word_count(text: Optional[str]) -> int:
            """Count words in text."""
            if not text:
                return 0
            return len(text.split())
        
        # Check word counts
        desc_word_count = word_count(product_data.get('description') or product_data.get('short_description'))
        supplier_word_count = word_count(product_data.get('supplier_description'))
        heritage_word_counts = {}
        if product_data.get('heritage_data'):
            for key in ['historical_origins', 'cultural_significance', 'evolution', 'scottish_heritage_connections']:
                heritage_word_counts[key] = word_count(product_data['heritage_data'].get(key))
        
        # Check minimum requirements
        has_minimum = (
            product_data.get('has_name') and
            product_data.get('has_description') and
            product_data.get('has_supplier')
        )
        
        # Check if fields are sufficient (>= threshold) or need LLM supplementation
        needs_llm_supplement = {
            'description': desc_word_count < self.llm_threshold,
            'supplier_description': supplier_word_count < self.llm_threshold if product_data.get('supplier_description') else True,
            'heritage_data': {}
        }
        
        if product_data.get('heritage_data'):
            for key in heritage_word_counts:
                needs_llm_supplement['heritage_data'][key] = heritage_word_counts[key] < self.llm_threshold
        
        # Calculate completeness scores
        core_fields = ['name', 'description', 'supplier_name']
        core_complete = sum(1 for field in core_fields if product_data.get(f'has_{field}' if field != 'description' else 'has_description'))
        core_completeness = core_complete / len(core_fields)
        
        optional_fields = ['heritage_data', 'specifications', 'configurable_options']
        optional_complete = sum(1 for field in optional_fields if product_data.get(f'has_{field}'))
        optional_completeness = optional_complete / len(optional_fields)
        
        return {
            'has_minimum_requirements': has_minimum,
            'core_completeness': core_completeness,
            'optional_completeness': optional_completeness,
            'word_counts': {
                'description': desc_word_count,
                'supplier_description': supplier_word_count,
                'heritage_data': heritage_word_counts
            },
            'needs_llm_supplement': needs_llm_supplement,
            'missing_fields': [
                field for field in ['name', 'description', 'supplier_name']
                if not product_data.get(f'has_{field}' if field != 'description' else 'has_description')
            ],
            'threshold': self.llm_threshold
        }
    
    def format_for_prompt(self, product_data: Dict, validation: Optional[Dict] = None) -> str:
        """
        Format CLAN data for LLM prompt with priority tags.
        
        Args:
            product_data: Product data from extract_product_data()
            validation: Optional validation report from validate_data_completeness()
            
        Returns:
            Formatted string with CLAN-first tags
        """
        if validation is None:
            validation = self.validate_data_completeness(product_data)
        
        parts = []
        
        # === CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
        parts.append("=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===")
        parts.append(f"Product Name: {product_data.get('name', 'N/A')}")
        parts.append(f"Product SKU: {product_data.get('sku', 'N/A')}")
        
        if product_data.get('description'):
            parts.append(f"Product Description: {product_data['description']}")
        elif product_data.get('short_description'):
            parts.append(f"Product Description: {product_data['short_description']}")
        
        if product_data.get('supplier_name'):
            parts.append(f"Supplier: {product_data['supplier_name']}")
        
        if product_data.get('supplier_description'):
            parts.append(f"Supplier Information: {product_data['supplier_description']}")
        
        # Categories
        if product_data.get('categories'):
            category_names = [cat.get('name', '') for cat in product_data['categories'] if cat.get('name')]
            if category_names:
                parts.append(f"Category: {', '.join(category_names)}")
        
        # Heritage Data
        if product_data.get('heritage_data'):
            parts.append("Heritage Data:")
            heritage = product_data['heritage_data']
            for key in ['historical_origins', 'cultural_significance', 'evolution', 'scottish_heritage_connections']:
                if heritage.get(key):
                    label = key.replace('_', ' ').title()
                    parts.append(f"  {label}: {heritage[key]}")
        
        # Specifications
        if product_data.get('specifications'):
            parts.append(f"Specifications: {json.dumps(product_data['specifications'], indent=2)}")
        
        # Options
        if product_data.get('configurable_options'):
            parts.append(f"Available Options: {json.dumps(product_data['configurable_options'], indent=2)}")
        
        # === LLM SUPPLEMENTATION (ONLY IF CLAN DATA MISSING OR < THRESHOLD WORDS) ===
        parts.append("")
        parts.append(f"=== LLM SUPPLEMENTATION (ONLY IF CLAN DATA MISSING OR < {self.llm_threshold} WORDS) ===")
        
        needs_supplement = validation.get('needs_llm_supplement', {})
        if needs_supplement.get('description'):
            parts.append("- Historical context (description < threshold)")
        if needs_supplement.get('supplier_description'):
            parts.append("- Craftsmanship details (supplier_description < threshold or missing)")
        if needs_supplement.get('heritage_data'):
            for key, needs in needs_supplement['heritage_data'].items():
                if needs:
                    label = key.replace('_', ' ').title()
                    parts.append(f"- {label} (heritage_data.{key} < threshold or missing)")
        
        parts.append("")
        parts.append("IMPORTANT: If CLAN data exists but is < threshold, use it as the foundation and expand with LLM knowledge.")
        
        return "\n".join(parts)
    
    def find_alternative_products(self, product_id: int, limit: int = 5) -> List[Dict]:
        """
        Find alternative products for the Alternative Products section.
        
        Uses multiple strategies:
        1. Same category products (via category_ids)
        2. Vector search for similar products (semantic similarity)
        3. Price-based alternatives (cheaper/more luxury)
        4. Same producer/supplier products
        5. Cross-category alternatives (same need/occasion via vector search)
        
        Args:
            product_id: Product ID to find alternatives for
            limit: Maximum number of alternatives to return
            
        Returns:
            List of alternative products with metadata (price, category, similarity score)
        """
        alternatives = []
        seen_ids = {product_id}  # Don't include the product itself
        
        # Get product data for context
        product_data = self.extract_product_data(product_id)
        product_price = product_data.get('price')
        if product_price:
            try:
                product_price = float(product_price)
            except (ValueError, TypeError):
                product_price = None
        
        with db_manager.get_cursor() as cursor:
            # Strategy 1: Same category products
            if product_data.get('category_ids'):
                category_ids = product_data['category_ids']
                if isinstance(category_ids, list) and category_ids:
                    # Use JSONB contains operator (@>) to find products with matching categories
                    # Convert category_ids to JSONB array for comparison
                    category_ids_json = json.dumps(category_ids)
                    cursor.execute("""
                        SELECT DISTINCT p.id, p.name, p.sku, p.price, p.image_url, p.url,
                               p.supplier_name, p.short_description
                        FROM clan_products p
                        WHERE p.id != %s
                          AND p.category_ids IS NOT NULL
                          AND p.category_ids @> %s::jsonb
                        ORDER BY p.name
                        LIMIT %s
                    """, (product_id, category_ids_json, limit * 2))
                    
                    for row in cursor.fetchall():
                        if row['id'] not in seen_ids:
                            alternatives.append({
                                'id': row['id'],
                                'name': row.get('name', ''),
                                'sku': row.get('sku', ''),
                                'price': str(row.get('price', '')) if row.get('price') else None,
                                'image_url': row.get('image_url'),
                                'url': row.get('url'),
                                'supplier_name': row.get('supplier_name', ''),
                                'discovery_strategy': 'same_category',
                                'similarity_score': None
                            })
                            seen_ids.add(row['id'])
            
            # Strategy 2: Vector search for similar products
            if self.retriever and len(alternatives) < limit:
                try:
                    # Use product name for semantic search
                    search_query = product_data.get('name', '')
                    if search_query:
                        search_results = self.retriever.search(
                            query=search_query,
                            chunk_types=['product'],
                            limit=limit * 2
                        )
                        
                        for result in search_results.get('results', []):
                            alt_id = result.get('source_id')
                            if alt_id and alt_id not in seen_ids and alt_id != product_id:
                                # Get product details
                                cursor.execute("""
                                    SELECT id, name, sku, price, image_url, url, supplier_name
                                    FROM clan_products
                                    WHERE id = %s
                                """, (alt_id,))
                                
                                alt_product = cursor.fetchone()
                                if alt_product:
                                    alternatives.append({
                                        'id': alt_product['id'],
                                        'name': alt_product.get('name', ''),
                                        'sku': alt_product.get('sku', ''),
                                        'price': str(alt_product.get('price', '')) if alt_product.get('price') else None,
                                        'image_url': alt_product.get('image_url'),
                                        'url': alt_product.get('url'),
                                        'supplier_name': alt_product.get('supplier_name', ''),
                                        'discovery_strategy': 'vector_search',
                                        'similarity_score': result.get('score')
                                    })
                                    seen_ids.add(alt_product['id'])
                except Exception as e:
                    logger.warning(f"Vector search failed for alternative products: {e}")
            
            # Strategy 3: Price-based alternatives (cheaper/more luxury)
            if product_price and len(alternatives) < limit:
                # Cheaper alternatives (20-50% less)
                cheaper_max = product_price * 0.8
                cursor.execute("""
                    SELECT id, name, sku, price, image_url, url, supplier_name
                    FROM clan_products
                    WHERE id != %s
                      AND price IS NOT NULL
                      AND price < %s
                      AND price > %s
                    ORDER BY price DESC
                    LIMIT %s
                """, (product_id, product_price, cheaper_max, limit))
                
                for row in cursor.fetchall():
                    if row['id'] not in seen_ids:
                        alternatives.append({
                            'id': row['id'],
                            'name': row.get('name', ''),
                            'sku': row.get('sku', ''),
                            'price': str(row.get('price', '')) if row.get('price') else None,
                            'image_url': row.get('image_url'),
                            'url': row.get('url'),
                            'supplier_name': row.get('supplier_name', ''),
                            'discovery_strategy': 'cheaper',
                            'price_comparison': 'cheaper'
                        })
                        seen_ids.add(row['id'])
                
                # Luxury alternatives (20-50% more)
                luxury_min = product_price * 1.2
                luxury_max = product_price * 1.5
                cursor.execute("""
                    SELECT id, name, sku, price, image_url, url, supplier_name
                    FROM clan_products
                    WHERE id != %s
                      AND price IS NOT NULL
                      AND price > %s
                      AND price < %s
                    ORDER BY price ASC
                    LIMIT %s
                """, (product_id, luxury_min, luxury_max, limit))
                
                for row in cursor.fetchall():
                    if row['id'] not in seen_ids:
                        alternatives.append({
                            'id': row['id'],
                            'name': row.get('name', ''),
                            'sku': row.get('sku', ''),
                            'price': str(row.get('price', '')) if row.get('price') else None,
                            'image_url': row.get('image_url'),
                            'url': row.get('url'),
                            'supplier_name': row.get('supplier_name', ''),
                            'discovery_strategy': 'luxury',
                            'price_comparison': 'more_luxury'
                        })
                        seen_ids.add(row['id'])
            
            # Strategy 4: Same producer/supplier products
            if product_data.get('supplier_name') and len(alternatives) < limit:
                cursor.execute("""
                    SELECT id, name, sku, price, image_url, url, supplier_name
                    FROM clan_products
                    WHERE id != %s
                      AND supplier_name = %s
                    ORDER BY name
                    LIMIT %s
                """, (product_id, product_data['supplier_name'], limit))
                
                for row in cursor.fetchall():
                    if row['id'] not in seen_ids:
                        alternatives.append({
                            'id': row['id'],
                            'name': row.get('name', ''),
                            'sku': row.get('sku', ''),
                            'price': str(row.get('price', '')) if row.get('price') else None,
                            'image_url': row.get('image_url'),
                            'url': row.get('url'),
                            'supplier_name': row.get('supplier_name', ''),
                            'discovery_strategy': 'same_supplier',
                            'similarity_score': None
                        })
                        seen_ids.add(row['id'])
        
        # Limit and sort by priority (same_category > vector_search > price > supplier)
        priority_order = {'same_category': 1, 'vector_search': 2, 'cheaper': 3, 'luxury': 3, 'same_supplier': 4}
        alternatives.sort(key=lambda x: priority_order.get(x.get('discovery_strategy', ''), 99))
        
        return alternatives[:limit]

