"""
FAISS Index Management

Handles FAISS vector index creation, loading, saving, and updates.
"""

import os
import json
import logging
import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy import to avoid requiring faiss at module load
_faiss = None


def _import_faiss():
    """Lazy import of FAISS."""
    global _faiss
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu is required. Install with: pip install faiss-cpu"
            )
    return _faiss


class FAISSIndexManager:
    """Manages FAISS vector index for semantic search."""
    
    def __init__(self, index_path: str = "data/vector_index/products_categories.faiss",
                 metadata_path: str = "data/vector_index/products_categories_metadata.json",
                 dimension: int = 1024):
        """
        Initialize FAISS index manager.
        
        Args:
            index_path: Path to save/load FAISS index file
            metadata_path: Path to save/load metadata mapping file
            dimension: Embedding dimension (default: 1024 for e5-large)
        """
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.dimension = dimension
        self.index = None
        self.metadata = {}  # Maps faiss_index_id -> chunk_id
        
        # Ensure directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
    
    def create_index(self, use_hnsw: bool = True) -> None:
        """
        Create a new FAISS index.
        
        Args:
            use_hnsw: Whether to use HNSW (True) or Flat (False) index
        """
        faiss = _import_faiss()
        
        if use_hnsw:
            # HNSW index for fast approximate search
            # M=32: number of connections per node (higher = more accurate, slower)
            # efConstruction=200: construction time vs quality
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 50  # Search quality vs speed
            logger.info("Created HNSW index")
        else:
            # Flat index for exact search (slower but more accurate)
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("Created Flat index")
        
        self.metadata = {}
    
    def load_index(self) -> bool:
        """
        Load index and metadata from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        faiss = _import_faiss()
        
        if not self.index_path.exists():
            logger.warning(f"Index file not found: {self.index_path}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            self.dimension = self.index.d
            logger.info(f"Loaded FAISS index with dimension {self.dimension}")
            
            # Load metadata
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} chunks")
            else:
                logger.warning(f"Metadata file not found: {self.metadata_path}")
                self.metadata = {}
            
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def save_index(self) -> bool:
        """
        Save index and metadata to disk.
        
        Returns:
            True if saved successfully
        """
        if self.index is None:
            logger.error("No index to save")
            return False
        
        faiss = _import_faiss()
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            logger.info(f"Saved FAISS index to {self.index_path}")
            
            # Save metadata
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"Saved metadata to {self.metadata_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    def add_vectors(self, vectors: np.ndarray, chunk_ids: List[int]) -> List[int]:
        """
        Add vectors to index and return FAISS index IDs.
        
        Args:
            vectors: NumPy array of shape (n, dimension)
            chunk_ids: List of chunk IDs corresponding to vectors
            
        Returns:
            List of FAISS index IDs
        """
        if self.index is None:
            self.create_index()
        
        if len(vectors) == 0:
            return []
        
        # Ensure vectors are float32 and normalized
        vectors = vectors.astype(np.float32)
        
        # Get current index size (this will be the starting FAISS index ID)
        start_id = self.index.ntotal
        
        # Add vectors to index
        self.index.add(vectors)
        
        # Create FAISS index IDs
        faiss_ids = list(range(start_id, start_id + len(vectors)))
        
        # Update metadata mapping
        for faiss_id, chunk_id in zip(faiss_ids, chunk_ids):
            self.metadata[str(faiss_id)] = chunk_id
        
        logger.info(f"Added {len(vectors)} vectors to index (FAISS IDs: {faiss_ids[0]}-{faiss_ids[-1]})")
        
        return faiss_ids
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for nearest neighbors.
        
        Args:
            query_vector: Query embedding vector (shape: (dimension,))
            k: Number of results to return
            
        Returns:
            Tuple of (distances, indices) where indices are FAISS index IDs
        """
        if self.index is None:
            raise ValueError("Index not loaded or created")
        
        if self.index.ntotal == 0:
            return np.array([]), np.array([])
        
        # Ensure query is float32 and reshape to (1, dimension)
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        return distances[0], indices[0]
    
    def get_chunk_ids(self, faiss_indices: np.ndarray) -> List[int]:
        """
        Convert FAISS index IDs to chunk IDs.
        
        Args:
            faiss_indices: Array of FAISS index IDs
            
        Returns:
            List of chunk IDs
        """
        chunk_ids = []
        for faiss_idx in faiss_indices:
            if faiss_idx >= 0:  # -1 indicates no result
                chunk_id = self.metadata.get(str(int(faiss_idx)))
                if chunk_id:
                    chunk_ids.append(chunk_id)
        return chunk_ids
    
    def remove_vectors(self, faiss_indices: List[int]) -> bool:
        """
        Remove vectors from index (requires rebuilding for HNSW).
        
        Note: HNSW doesn't support direct removal. This will rebuild the index.
        
        Args:
            faiss_indices: List of FAISS index IDs to remove
            
        Returns:
            True if successful
        """
        if self.index is None:
            return False
        
        # HNSW doesn't support removal, so we need to rebuild
        # This is a simplified version - in production, you'd want to be more careful
        logger.warning("HNSW index removal requires rebuild - not implemented yet")
        return False
    
    def get_index_size(self) -> int:
        """
        Get number of vectors in index.
        
        Returns:
            Number of vectors
        """
        if self.index is None:
            return 0
        return self.index.ntotal

