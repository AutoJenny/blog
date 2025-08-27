-- =====================================================
-- CREATE SYNDICATION PIECES TABLE
-- Stores LLM-generated content for social media syndication
-- =====================================================

-- Create the syndication_pieces table
CREATE TABLE IF NOT EXISTS syndication_pieces (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,                    -- Reference to the blog post
    section_id INTEGER NOT NULL,                 -- Reference to the post section
    platform_id INTEGER NOT NULL,                -- Reference to the platform (Facebook, Twitter, etc.)
    channel_type_id INTEGER NOT NULL,            -- Reference to the channel type (feed_post, story, etc.)
    process_id INTEGER NOT NULL,                 -- Reference to the content process used
    original_content TEXT NOT NULL,              -- Original blog post section content
    generated_content TEXT NOT NULL,             -- LLM-generated syndication content
    llm_model VARCHAR(100),                     -- LLM model used (e.g., 'llama3.1:70b')
    llm_temperature DECIMAL(3,2),               -- Temperature setting used
    llm_max_tokens INTEGER,                     -- Max tokens setting used
    llm_provider VARCHAR(50),                   -- LLM provider (e.g., 'ollama')
    prompt_used TEXT,                           -- The actual prompt sent to the LLM
    processing_time_ms INTEGER,                 -- Time taken to generate (in milliseconds)
    status VARCHAR(20) DEFAULT 'generated',     -- 'generated', 'reviewed', 'approved', 'posted'
    user_notes TEXT,                            -- User notes or feedback
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_syndication_pieces_post 
        FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    CONSTRAINT fk_syndication_pieces_section 
        FOREIGN KEY (section_id) REFERENCES post_section(id) ON DELETE CASCADE,
    CONSTRAINT fk_syndication_pieces_platform 
        FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE,
    CONSTRAINT fk_syndication_pieces_channel_type 
        FOREIGN KEY (channel_type_id) REFERENCES channel_types(id) ON DELETE CASCADE,
    CONSTRAINT fk_syndication_pieces_process 
        FOREIGN KEY (process_id) REFERENCES content_processes(id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate pieces for the same section/process
    CONSTRAINT unique_section_process 
        UNIQUE (section_id, process_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_syndication_pieces_post_id ON syndication_pieces(post_id);
CREATE INDEX IF NOT EXISTS idx_syndication_pieces_section_id ON syndication_pieces(section_id);
CREATE INDEX IF NOT EXISTS idx_syndication_pieces_platform_id ON syndication_pieces(platform_id);
CREATE INDEX IF NOT EXISTS idx_syndication_pieces_status ON syndication_pieces(status);
CREATE INDEX IF NOT EXISTS idx_syndication_pieces_created_at ON syndication_pieces(created_at);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_syndication_pieces_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_syndication_pieces_updated_at
    BEFORE UPDATE ON syndication_pieces
    FOR EACH ROW
    EXECUTE FUNCTION update_syndication_pieces_updated_at();

-- Add comments for documentation
COMMENT ON TABLE syndication_pieces IS 'Stores LLM-generated content for social media syndication';
COMMENT ON COLUMN syndication_pieces.post_id IS 'Reference to the blog post being syndicated';
COMMENT ON COLUMN syndication_pieces.section_id IS 'Reference to the specific post section';
COMMENT ON COLUMN syndication_pieces.platform_id IS 'Reference to the social media platform';
COMMENT ON COLUMN syndication_pieces.channel_type_id IS 'Reference to the channel type (feed_post, story, etc.)';
COMMENT ON COLUMN syndication_pieces.process_id IS 'Reference to the content process used for generation';
COMMENT ON COLUMN syndication_pieces.original_content IS 'Original blog post section content';
COMMENT ON COLUMN syndication_pieces.generated_content IS 'LLM-generated syndication content';
COMMENT ON COLUMN syndication_pieces.llm_model IS 'LLM model used for generation';
COMMENT ON COLUMN syndication_pieces.llm_temperature IS 'Temperature setting used for generation';
COMMENT ON COLUMN syndication_pieces.llm_max_tokens IS 'Maximum tokens setting used';
COMMENT ON COLUMN syndication_pieces.llm_provider IS 'LLM provider (e.g., ollama, openai)';
COMMENT ON COLUMN syndication_pieces.prompt_used IS 'The actual prompt sent to the LLM';
COMMENT ON COLUMN syndication_pieces.processing_time_ms IS 'Time taken to generate in milliseconds';
COMMENT ON COLUMN syndication_pieces.status IS 'Current status of the piece';
COMMENT ON COLUMN syndication_pieces.user_notes IS 'User notes or feedback on the piece';
COMMENT ON COLUMN syndication_pieces.created_at IS 'When the piece was generated';
COMMENT ON COLUMN syndication_pieces.updated_at IS 'When the piece was last updated';
