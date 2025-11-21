"""
Post Matcher Module

Finds similar products, suppliers, and categories for a given post using vector search.
"""

import logging
from typing import Dict, List
from utils.vector_search.retrieval import ContentRetriever
from utils.vector_search.post_extractor import extract_post_content

logger = logging.getLogger(__name__)


def find_similar_entities(post_id: int, limit: int = 3, post_content: str = None) -> Dict:
    """
    Find top similar products, suppliers, and categories for a post.
    
    Args:
        post_id: Post ID
        limit: Number of top matches to return per type (default: 3)
        post_content: Optional post content (if not provided, will be extracted)
        
    Returns:
        Dictionary with:
        - 'products': List of product matches
        - 'suppliers': List of supplier matches
        - 'categories': List of category matches
        - Each match dict contains: id, name, score, metadata, etc.
    """
    # Extract post content if not provided
    if not post_content:
        post_content = extract_post_content(post_id)
    
    if not post_content:
        logger.warning(f"No content extracted for post_id {post_id}")
        return {
            'products': [],
            'suppliers': [],
            'categories': []
        }
    
    # Initialize retriever
    retriever = ContentRetriever()
    
    # Search each type
    products_result = retriever.search(
        post_content,
        chunk_types=['product'],
        limit=limit
    )
    
    suppliers_result = retriever.search(
        post_content,
        chunk_types=['producer'],  # Note: chunk_type is 'producer' but we call them 'suppliers' in UI
        limit=limit
    )
    
    categories_result = retriever.search(
        post_content,
        chunk_types=['category'],
        limit=limit
    )
    
    # Format results
    products = []
    if products_result.get('success') and products_result.get('results'):
        for result in products_result['results']:
            metadata = result.get('metadata', {})
            products.append({
                'id': result['source_id'],
                'name': metadata.get('product_name', f"Product {result['source_id']}"),
                'score': result['score'],
                'distance': result.get('distance'),
                'metadata': metadata
            })
    
    suppliers = []
    if suppliers_result.get('success') and suppliers_result.get('results'):
        for result in suppliers_result['results']:
            metadata = result.get('metadata', {})
            suppliers.append({
                'id': result['source_id'],
                'name': metadata.get('producer_name', f"Supplier {result['source_id']}"),
                'score': result['score'],
                'distance': result.get('distance'),
                'metadata': metadata
            })
    
    categories = []
    if categories_result.get('success') and categories_result.get('results'):
        for result in categories_result['results']:
            metadata = result.get('metadata', {})
            categories.append({
                'id': result['source_id'],
                'name': metadata.get('category_name', f"Category {result['source_id']}"),
                'score': result['score'],
                'distance': result.get('distance'),
                'metadata': metadata
            })
    
    return {
        'products': products,
        'suppliers': suppliers,
        'categories': categories
    }

