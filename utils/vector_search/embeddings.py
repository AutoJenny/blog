"""
Embedding Generation Module

Generates embeddings for text chunks using sentence transformers.
"""

import logging
import numpy as np
from typing import List, Optional, Tuple
from config.database import db_manager

logger = logging.getLogger(__name__)

# Lazy import to avoid requiring sentence-transformers at module load
_embedding_model = None
_embedding_model_name = None


def get_embedding_model(model_name: str = 'intfloat/e5-large-v2'):
    """
    Get or initialize the embedding model (lazy loading).
    
    Args:
        model_name: HuggingFace model name (default: e5-large-v2)
        
    Returns:
        SentenceTransformer model
    """
    global _embedding_model, _embedding_model_name
    
    if _embedding_model is None or _embedding_model_name != model_name:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            _embedding_model = SentenceTransformer(model_name)
            _embedding_model_name = model_name
            logger.info(f"Embedding model loaded successfully")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    return _embedding_model


class EmbeddingGenerator:
    """Handles embedding generation for text chunks."""
    
    def __init__(self, model_name: str = 'intfloat/e5-large-v2'):
        """
        Initialize embedding generator.
        
        Args:
            model_name: HuggingFace model name (default: e5-large-v2, 1024 dimensions)
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = None
    
    def _ensure_model_loaded(self):
        """Ensure the embedding model is loaded."""
        if self.model is None:
            self.model = get_embedding_model(self.model_name)
            # Get embedding dimension from model
            test_embedding = self.model.encode("test", normalize_embeddings=True)
            self.embedding_dim = len(test_embedding)
            logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def generate_embedding(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            normalize: Whether to normalize embeddings (default: True)
            
        Returns:
            NumPy array of embedding vector
        """
        self._ensure_model_loaded()
        
        if not text or not text.strip():
            # Return zero vector if text is empty
            if self.embedding_dim is None:
                self._ensure_model_loaded()
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        try:
            # E5 models expect "query: " or "passage: " prefix
            # For general text, use "passage: " prefix
            if not text.startswith("query: ") and not text.startswith("passage: "):
                text = f"passage: {text}"
            
            embedding = self.model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], 
                                   normalize: bool = True,
                                   batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            normalize: Whether to normalize embeddings
            batch_size: Batch size for processing
            
        Returns:
            List of NumPy arrays
        """
        self._ensure_model_loaded()
        
        if not texts:
            return []
        
        # Add "passage: " prefix if not present
        prefixed_texts = []
        for text in texts:
            if not text or not text.strip():
                prefixed_texts.append("")
            elif not text.startswith("query: ") and not text.startswith("passage: "):
                prefixed_texts.append(f"passage: {text}")
            else:
                prefixed_texts.append(text)
        
        try:
            embeddings = self.model.encode(
                prefixed_texts,
                normalize_embeddings=normalize,
                show_progress_bar=True,
                batch_size=batch_size
            )
            
            return [emb.astype(np.float32) for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension
        """
        self._ensure_model_loaded()
        if self.embedding_dim is None:
            test_emb = self.generate_embedding("test")
            self.embedding_dim = len(test_emb)
        return self.embedding_dim
    
    def update_chunk_embedding(self, chunk_id: int, embedding: np.ndarray) -> bool:
        """
        Update chunk record with embedding metadata.
        
        Args:
            chunk_id: Chunk ID
            embedding: Embedding vector
            
        Returns:
            True if successful
        """
        import json
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE content_chunks
                    SET embedding_model = %s,
                        embedding_dim = %s,
                        last_embedded_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    self.model_name,
                    len(embedding),
                    chunk_id
                ))
                return True
        except Exception as e:
            logger.error(f"Error updating chunk embedding metadata: {e}")
            return False

