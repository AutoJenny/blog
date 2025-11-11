"""
Content Search API

API endpoints for vector search and content retrieval.
"""

from flask import Blueprint, jsonify, request
import logging
from utils.vector_search.retrieval import ContentRetriever

logger = logging.getLogger(__name__)

bp = Blueprint('content_search', __name__)

# Initialize retriever (singleton)
_retriever = None


def get_retriever():
    """Get or create content retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = ContentRetriever()
    return _retriever


def register_routes(bp):
    """Register content search API routes."""
    
    @bp.route('/api/content/search', methods=['POST'])
    def api_content_search():
        """
        Search for content using semantic search.
        
        Request body:
        {
            "query": "Scottish tartan scarves",
            "chunk_types": ["product", "category"],  // optional
            "limit": 10,  // optional, default 10
            "min_score": 0.5  // optional, similarity threshold
        }
        
        Response:
        {
            "success": true,
            "results": [...],
            "query": "...",
            "query_time_ms": 45.2,
            "total_results": 5
        }
        """
        try:
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            
            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Query is required'
                }), 400
            
            chunk_types = data.get('chunk_types')
            limit = data.get('limit', 10)
            min_score = data.get('min_score')
            
            retriever = get_retriever()
            result = retriever.search(
                query=query,
                chunk_types=chunk_types,
                limit=limit,
                min_score=min_score
            )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in content search: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/api/content/chunk/<int:chunk_id>', methods=['GET'])
    def api_get_chunk(chunk_id):
        """
        Get a specific chunk by ID.
        
        Response:
        {
            "success": true,
            "chunk": {...}
        }
        """
        try:
            retriever = get_retriever()
            chunk = retriever.get_chunk_by_id(chunk_id)
            
            if not chunk:
                return jsonify({
                    'success': False,
                    'error': 'Chunk not found'
                }), 404
            
            return jsonify({
                'success': True,
                'chunk': chunk
            })
            
        except Exception as e:
            logger.error(f"Error getting chunk: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/api/products/semantic-search', methods=['POST'])
    def api_semantic_product_search():
        """
        Semantic search for products using vector embeddings.
        
        Request body:
        {
            "query": "kilt",
            "limit": 10  // optional, default 10
        }
        
        Response:
        {
            "success": true,
            "results": [
                {
                    "id": 123,
                    "name": "Balmoral Kilt",
                    "sku": "kilt-001",
                    "price": "199.99",
                    "image_url": "...",
                    "url": "...",
                    "relevance_score": 0.95,
                    "match_reason": "Name match + category match"
                }
            ],
            "query_time_ms": 45.2
        }
        """
        try:
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            
            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Query is required'
                }), 400
            
            if len(query) < 3:
                return jsonify({
                    'success': False,
                    'error': 'Query must be at least 3 characters'
                }), 400
            
            limit = data.get('limit', 10)
            
            # Use vector search to find relevant products
            try:
                retriever = get_retriever()
            except Exception as e:
                logger.error(f"Error initializing ContentRetriever: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Failed to initialize search: {str(e)}'
                }), 500
            
            try:
                search_results = retriever.search(
                    query=query,
                    chunk_types=['product'],
                    limit=limit * 2  # Get more candidates for re-ranking
                )
            except Exception as e:
                logger.error(f"Error in vector search: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Vector search failed: {str(e)}'
                }), 500
            
            if not search_results.get('success'):
                error_msg = search_results.get('error', 'Unknown error')
                logger.error(f"Vector search returned error: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Vector search failed: {error_msg}'
                }), 500
            
            # Fetch full product data and apply re-ranking
            from config.database import db_manager
            import json
            
            products = []
            seen_ids = set()
            
            for result in search_results.get('results', []):
                product_id = result.get('source_id')
                if not product_id or product_id in seen_ids:
                    continue
                seen_ids.add(product_id)
                
                # Fetch full product data
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, sku, price, image_url, url, 
                               category_ids, configurable_options, additional_data
                        FROM clan_products
                        WHERE id = %s
                    """, (product_id,))
                    
                    product = cursor.fetchone()
                    if not product:
                        continue
                    
                    # Calculate relevance score with boost factors
                    semantic_score = result.get('score', 0.0)
                    metadata = result.get('metadata', {})
                    
                    # Boost factors
                    exact_name_match = 0.0
                    name_contains = 0.0
                    category_match = 0.0
                    options_match = 0.0
                    description_match = 0.0
                    
                    product_name = (product.get('name') or '').lower()
                    query_lower = query.lower()
                    
                    # Exact name match
                    if product_name == query_lower:
                        exact_name_match = 0.5
                    # Name contains query
                    elif query_lower in product_name:
                        name_contains = 0.2
                    
                    # Category match (simple check - query might match category name)
                    category_ids = product.get('category_ids')
                    if category_ids:
                        # For now, simple boost if we have category data
                        # Future: check if query matches category name
                        category_match = 0.1
                    
                    # Options/attributes match
                    configurable_options = product.get('configurable_options')
                    additional_data = product.get('additional_data')
                    
                    if configurable_options:
                        options_str = json.dumps(configurable_options).lower()
                        if query_lower in options_str:
                            options_match = 0.15
                    
                    if additional_data:
                        additional_str = json.dumps(additional_data).lower()
                        if query_lower in additional_str:
                            options_match = max(options_match, 0.15)
                    
                    # Calculate final score
                    final_score = (semantic_score * 0.4) + \
                                 (exact_name_match * 0.3) + \
                                 (name_contains * 0.2) + \
                                 (category_match * 0.15) + \
                                 (options_match * 0.1) + \
                                 (description_match * 0.05)
                    
                    # Build match reason
                    reasons = []
                    if exact_name_match > 0:
                        reasons.append("exact name match")
                    elif name_contains > 0:
                        reasons.append("name contains query")
                    if category_match > 0:
                        reasons.append("category match")
                    if options_match > 0:
                        reasons.append("options/attributes match")
                    if semantic_score > 0.7:
                        reasons.append("high semantic similarity")
                    elif semantic_score > 0.5:
                        reasons.append("semantic match")
                    
                    match_reason = ", ".join(reasons) if reasons else "semantic match"
                    
                    products.append({
                        'id': product['id'],
                        'name': product.get('name', ''),
                        'sku': product.get('sku', ''),
                        'price': str(product.get('price', '')) if product.get('price') else None,
                        'image_url': product.get('image_url'),
                        'url': product.get('url'),
                        'supplier_name': metadata.get('supplier_name', ''),
                        'relevance_score': round(final_score, 3),
                        'match_reason': match_reason
                    })
                    
                    # Stop when we have enough
                    if len(products) >= limit:
                        break
            
            # Sort by relevance score (descending)
            products.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return jsonify({
                'success': True,
                'results': products,
                'query': query,
                'query_time_ms': search_results.get('query_time_ms', 0),
                'total_results': len(products)
            })
            
        except Exception as e:
            logger.error(f"Error in semantic product search: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

