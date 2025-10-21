-- Migration: Add LLM Message Intercepts Table
-- Purpose: Store actual LLM messages that are sent to the API for debugging and transparency

CREATE TABLE IF NOT EXISTS llm_message_intercepts (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    intercepted_message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, section_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_llm_message_intercepts_post_section 
ON llm_message_intercepts(post_id, section_id);

CREATE INDEX IF NOT EXISTS idx_llm_message_intercepts_created_at 
ON llm_message_intercepts(created_at);

-- Add foreign key constraints if the tables exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'post') THEN
        ALTER TABLE llm_message_intercepts 
        ADD CONSTRAINT fk_llm_message_intercepts_post 
        FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'post_section') THEN
        ALTER TABLE llm_message_intercepts 
        ADD CONSTRAINT fk_llm_message_intercepts_section 
        FOREIGN KEY (section_id) REFERENCES post_section(id) ON DELETE CASCADE;
    END IF;
END $$;
