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

