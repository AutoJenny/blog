-- Migration to create workflow_post_format table
-- This table stores format data for individual posts

CREATE TABLE workflow_post_format (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES workflow_format_template(id) ON DELETE CASCADE,
    
    -- Ensure one format per post
    UNIQUE(post_id)
);

-- Create indexes for performance
CREATE INDEX idx_workflow_post_format_post_id ON workflow_post_format(post_id);
CREATE INDEX idx_workflow_post_format_template_id ON workflow_post_format(template_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_workflow_post_format_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_workflow_post_format_updated_at
    BEFORE UPDATE ON workflow_post_format
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_post_format_updated_at();

-- Add rollback function
CREATE OR REPLACE FUNCTION rollback_workflow_post_format()
RETURNS void AS $$
BEGIN
    DROP TABLE IF EXISTS workflow_post_format CASCADE;
END;
$$ LANGUAGE plpgsql; 