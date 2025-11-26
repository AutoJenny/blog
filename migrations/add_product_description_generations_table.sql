-- Migration: Add table for storing generated product descriptions
-- Purpose: Store LLM-generated descriptions without overwriting originals
-- Date: 2025-01-XX

BEGIN;

CREATE TABLE IF NOT EXISTS product_description_generations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES clan_products(id) ON DELETE CASCADE,
    generated_description TEXT NOT NULL,
    llm_provider VARCHAR(50) NOT NULL,
    llm_model VARCHAR(100) NOT NULL,
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    prompt_used TEXT NOT NULL,
    system_prompt TEXT,
    include_image BOOLEAN DEFAULT FALSE,
    word_count INTEGER,
    char_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    notes TEXT,
    UNIQUE(product_id, llm_provider, llm_model, temperature, created_at)
);

CREATE INDEX IF NOT EXISTS idx_product_description_generations_product_id ON product_description_generations(product_id);
CREATE INDEX IF NOT EXISTS idx_product_description_generations_created_at ON product_description_generations(created_at DESC);

COMMENT ON TABLE product_description_generations IS 'Stores LLM-generated product descriptions for comparison and testing. Does not overwrite original descriptions.';
COMMENT ON COLUMN product_description_generations.prompt_used IS 'The full user prompt sent to the LLM';
COMMENT ON COLUMN product_description_generations.system_prompt IS 'The system prompt sent to the LLM';
COMMENT ON COLUMN product_description_generations.include_image IS 'Whether the product image was included in the generation';

COMMIT;



