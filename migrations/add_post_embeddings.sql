-- Migration: Add support for post and producer embeddings in content_chunks
-- Also adds embedding_overrides to post_development for manual overrides

BEGIN;

-- 1. Update content_chunks constraint to include 'producer' and 'post'
ALTER TABLE content_chunks 
DROP CONSTRAINT IF EXISTS content_chunks_chunk_type_check;

ALTER TABLE content_chunks 
ADD CONSTRAINT content_chunks_chunk_type_check 
CHECK (chunk_type IN ('product', 'category', 'kb', 'producer', 'post'));

-- 2. Add index for post chunks
CREATE INDEX IF NOT EXISTS idx_content_chunks_post 
ON content_chunks(chunk_type, source_id) 
WHERE chunk_type = 'post';

-- 3. Add index for producer chunks (if not exists)
CREATE INDEX IF NOT EXISTS idx_content_chunks_producer 
ON content_chunks(chunk_type, source_id) 
WHERE chunk_type = 'producer';

-- 4. Add embedding_overrides to post_development for manual selection storage
ALTER TABLE post_development
ADD COLUMN IF NOT EXISTS embedding_overrides JSONB DEFAULT '{}'::jsonb;

-- Add comment
COMMENT ON COLUMN post_development.embedding_overrides IS 'Stores manual overrides for vector embedding similarity matches (selected products, suppliers, categories, and best match type)';

COMMIT;



