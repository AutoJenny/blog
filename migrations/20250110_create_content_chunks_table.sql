-- Migration: Create content_chunks table for vector search
-- Date: 2025-01-10
-- Purpose: Store text chunks with metadata and embedding references for semantic search

CREATE TABLE IF NOT EXISTS content_chunks (
    id SERIAL PRIMARY KEY,
    chunk_type VARCHAR(20) NOT NULL CHECK (chunk_type IN ('product', 'category', 'kb')),
    source_id INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    embedding_model VARCHAR(50),
    embedding_dim INTEGER,
    faiss_index_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_embedded_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_content_chunks_type_source ON content_chunks(chunk_type, source_id);
CREATE INDEX IF NOT EXISTS idx_content_chunks_faiss_id ON content_chunks(faiss_index_id) WHERE faiss_index_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_content_chunks_metadata ON content_chunks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_content_chunks_type_embedded ON content_chunks(chunk_type, last_embedded_at) WHERE last_embedded_at IS NOT NULL;

-- Comments for documentation
COMMENT ON TABLE content_chunks IS 'Stores text chunks with metadata and embedding references for semantic search';
COMMENT ON COLUMN content_chunks.chunk_type IS 'Type of chunk: product, category, or kb (knowledge base)';
COMMENT ON COLUMN content_chunks.source_id IS 'Reference to clan_products.id or clan_categories.id';
COMMENT ON COLUMN content_chunks.chunk_text IS 'Normalized text content ready for embedding';
COMMENT ON COLUMN content_chunks.chunk_index IS 'Index for multi-chunk sources (0 for single-chunk products/categories)';
COMMENT ON COLUMN content_chunks.metadata IS 'JSONB with context: product_name, sku, supplier_name, category_ids, etc.';
COMMENT ON COLUMN content_chunks.embedding_model IS 'Model used for embedding (e.g., e5-large, bge-large)';
COMMENT ON COLUMN content_chunks.embedding_dim IS 'Dimension of embedding vector (e.g., 1024)';
COMMENT ON COLUMN content_chunks.faiss_index_id IS 'Index position in FAISS for fast lookup';

