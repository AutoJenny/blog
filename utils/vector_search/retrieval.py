"""
Content Retrieval Module

Provides semantic search using vector embeddings.
"""

import logging
import time
from typing import List, Dict, Optional
import numpy as np
from config.database import db_manager

from .embeddings import EmbeddingGenerator
from .faiss_index import FAISSIndexManager

logger = logging.getLogger(__name__)


class ContentRetriever:
    """Handles semantic search and content retrieval."""
    
    def __init__(self, 
                 embedding_model: str = 'intfloat/e5-large-v2',
                 index_path: str = "data/vector_index/products_categories.faiss",
                 metadata_path: str = "data/vector_index/products_categories_metadata.json"):
        """
        Initialize content retriever.
        
        Args:
            embedding_model: HuggingFace model name
            index_path: Path to FAISS index file
            metadata_path: Path to metadata mapping file
        """
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.faiss_manager = FAISSIndexManager(index_path, metadata_path)
        
        # Load index if it exists
        if not self.faiss_manager.load_index():
            logger.warning("FAISS index not found - will need to be created")
    
    def search(self, 
               query: str,
               chunk_types: Optional[List[str]] = None,
               limit: int = 10,
               min_score: Optional[float] = None) -> Dict:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query text
            chunk_types: Optional list of chunk types to filter ('product', 'category', 'kb')
            limit: Maximum number of results
            min_score: Optional minimum similarity score (L2 distance threshold)
            
        Returns:
            Dictionary with results and metadata
        """
        start_time = time.time()
        
        # Check if index is loaded
        if self.faiss_manager.index is None:
            logger.error("FAISS index not loaded - cannot perform search")
            return {
                'success': False,
                'error': 'Vector index not loaded. Please rebuild the index.',
                'results': [],
                'query': query,
                'query_time_ms': 0,
                'total_results': 0
            }
        
        try:
            # Generate query embedding
            # For queries, use "query: " prefix for E5 models
            query_text = query if query.startswith("query: ") else f"query: {query}"
            query_embedding = self.embedding_generator.generate_embedding(query_text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Failed to generate embedding: {str(e)}',
                'results': [],
                'query': query,
                'query_time_ms': 0,
                'total_results': 0
            }
        
        try:
            # Search FAISS index
            # If filtering by chunk_type, search more broadly to ensure we find matches
            # Otherwise, products dominate the top results
            search_k = limit * 10 if chunk_types else limit * 2
            distances, faiss_indices = self.faiss_manager.search(query_embedding, k=search_k)
            
            # Convert FAISS indices to chunk IDs
            chunk_ids = self.faiss_manager.get_chunk_ids(faiss_indices)
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Failed to search index: {str(e)}',
                'results': [],
                'query': query,
                'query_time_ms': 0,
                'total_results': 0
            }
        
        # Fetch chunk details from database
        results = []
        with db_manager.get_cursor() as cursor:
            # When filtering by chunk_type, we need to check more results
            check_limit = len(chunk_ids) if chunk_types else limit
            for i, chunk_id in enumerate(chunk_ids[:check_limit]):
                if chunk_id is None:
                    continue
                
                # Stop if we have enough results
                if len(results) >= limit:
                    break
                
                # Get chunk details
                cursor.execute("""
                    SELECT id, chunk_type, source_id, chunk_text, metadata,
                           embedding_model, embedding_dim
                    FROM content_chunks
                    WHERE id = %s
                """, (chunk_id,))
                
                chunk = cursor.fetchone()
                if not chunk:
                    continue
                
                # Filter by chunk_type if specified
                if chunk_types and chunk['chunk_type'] not in chunk_types:
                    continue
                
                # Calculate similarity score (convert L2 distance to similarity)
                # L2 distance: lower is better
                # Similarity: higher is better (1 / (1 + distance))
                distance = float(distances[i]) if i < len(distances) else float('inf')
                similarity_score = 1.0 / (1.0 + distance)
                
                # Apply min_score filter if specified
                if min_score is not None and similarity_score < min_score:
                    continue
                
                # Parse metadata JSON
                import json
                metadata = chunk['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                results.append({
                    'chunk_id': chunk['id'],
                    'chunk_type': chunk['chunk_type'],
                    'source_id': chunk['source_id'],
                    'chunk_text': chunk['chunk_text'],
                    'metadata': metadata,
                    'score': similarity_score,
                    'distance': distance,
                    'faiss_index_id': int(faiss_indices[i]) if i < len(faiss_indices) else None
                })
        
        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            'success': True,
            'results': results,
            'query': query,
            'query_time_ms': round(query_time_ms, 2),
            'total_results': len(results)
        }
    
    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            Chunk dictionary or None
        """
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, chunk_type, source_id, chunk_text, metadata,
                       embedding_model, embedding_dim, faiss_index_id
                FROM content_chunks
                WHERE id = %s
            """, (chunk_id,))
            
            chunk = cursor.fetchone()
            if not chunk:
                return None
            
            # Parse metadata JSON
            import json
            metadata = chunk['metadata']
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            return {
                'chunk_id': chunk['id'],
                'chunk_type': chunk['chunk_type'],
                'source_id': chunk['source_id'],
                'chunk_text': chunk['chunk_text'],
                'metadata': metadata,
                'embedding_model': chunk['embedding_model'],
                'embedding_dim': chunk['embedding_dim'],
                'faiss_index_id': chunk['faiss_index_id']
            }

