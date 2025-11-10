#!/usr/bin/env python3
"""
Generate Embeddings Script

Processes all products and categories, creates chunks, generates embeddings,
and builds FAISS index.

Usage:
    python scripts/generate_embeddings.py [--products] [--categories] [--rebuild-index]
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.vector_search.chunking import ContentChunker
from utils.vector_search.embeddings import EmbeddingGenerator
from utils.vector_search.faiss_index import FAISSIndexManager
from config.database import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_chunks(chunk_type: str, chunker: ContentChunker, 
                   embedding_gen: EmbeddingGenerator,
                   faiss_manager: FAISSIndexManager,
                   batch_size: int = 32):
    """
    Process chunks: generate embeddings and add to FAISS index.
    
    Args:
        chunk_type: 'product' or 'category'
        chunker: ContentChunker instance
        embedding_gen: EmbeddingGenerator instance
        faiss_manager: FAISSIndexManager instance
        batch_size: Batch size for embedding generation
    """
    logger.info(f"Processing {chunk_type} chunks...")
    
    # Get all chunks that need embeddings
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, chunk_text, faiss_index_id
            FROM content_chunks
            WHERE chunk_type = %s
            ORDER BY id
        """, (chunk_type,))
        
        chunks = cursor.fetchall()
    
    logger.info(f"Found {len(chunks)} {chunk_type} chunks")
    
    # Process in batches
    processed = 0
    added_to_index = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        # Get chunk texts
        chunk_texts = [chunk['chunk_text'] for chunk in batch]
        chunk_ids = [chunk['id'] for chunk in batch]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for batch {i//batch_size + 1} ({len(batch)} chunks)...")
        embeddings = embedding_gen.generate_embeddings_batch(
            chunk_texts,
            batch_size=batch_size
        )
        
        # Filter out chunks that already have FAISS index IDs
        new_chunks = []
        new_embeddings = []
        new_chunk_ids = []
        
        for j, chunk in enumerate(batch):
            if chunk['faiss_index_id'] is None:
                new_chunks.append(chunk)
                new_embeddings.append(embeddings[j])
                new_chunk_ids.append(chunk_ids[j])
        
        if new_chunks:
            # Add to FAISS index
            import numpy as np
            embeddings_array = np.array(new_embeddings)
            faiss_ids = faiss_manager.add_vectors(embeddings_array, new_chunk_ids)
            
            # Update chunk records with FAISS index IDs and embedding metadata
            with db_manager.get_cursor() as cursor:
                for chunk_id, faiss_id in zip(new_chunk_ids, faiss_ids):
                    embedding_gen.update_chunk_embedding(chunk_id, embeddings_array[new_chunk_ids.index(chunk_id)])
                    
                    cursor.execute("""
                        UPDATE content_chunks
                        SET faiss_index_id = %s,
                            last_embedded_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (faiss_id, chunk_id))
            
            added_to_index += len(new_chunks)
        
        processed += len(batch)
        logger.info(f"Processed {processed}/{len(chunks)} chunks ({added_to_index} added to index)")
    
    logger.info(f"Completed processing {chunk_type} chunks: {processed} processed, {added_to_index} added to index")
    return processed, added_to_index


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for content chunks')
    parser.add_argument('--products', action='store_true', help='Process products')
    parser.add_argument('--categories', action='store_true', help='Process categories')
    parser.add_argument('--rebuild-index', action='store_true', help='Rebuild FAISS index from scratch')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size for embedding generation')
    
    args = parser.parse_args()
    
    # Default: process both if neither specified
    process_products = args.products or (not args.products and not args.categories)
    process_categories = args.categories or (not args.products and not args.categories)
    
    logger.info("Starting embedding generation...")
    logger.info(f"Process products: {process_products}")
    logger.info(f"Process categories: {process_categories}")
    logger.info(f"Rebuild index: {args.rebuild_index}")
    
    # Initialize components
    chunker = ContentChunker()
    embedding_gen = EmbeddingGenerator()
    faiss_manager = FAISSIndexManager()
    
    # Rebuild index if requested
    if args.rebuild_index:
        logger.info("Rebuilding FAISS index...")
        faiss_manager.create_index()
        # Clear FAISS index IDs from all chunks
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE content_chunks
                SET faiss_index_id = NULL
            """)
    else:
        # Try to load existing index
        if not faiss_manager.load_index():
            logger.info("No existing index found, creating new one...")
            faiss_manager.create_index()
    
    # Process products
    if process_products:
        logger.info("Step 1: Creating product chunks...")
        product_stats = chunker.process_all_products()
        logger.info(f"Product chunks: {product_stats}")
        
        logger.info("Step 2: Generating embeddings for products...")
        process_chunks('product', chunker, embedding_gen, faiss_manager, args.batch_size)
    
    # Process categories
    if process_categories:
        logger.info("Step 1: Creating category chunks...")
        category_stats = chunker.process_all_categories()
        logger.info(f"Category chunks: {category_stats}")
        
        logger.info("Step 2: Generating embeddings for categories...")
        process_chunks('category', chunker, embedding_gen, faiss_manager, args.batch_size)
    
    # Save index
    logger.info("Saving FAISS index...")
    if faiss_manager.save_index():
        logger.info("✅ FAISS index saved successfully")
    else:
        logger.error("❌ Failed to save FAISS index")
        return 1
    
    # Report final stats
    index_size = faiss_manager.get_index_size()
    logger.info(f"✅ Complete! FAISS index contains {index_size} vectors")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

